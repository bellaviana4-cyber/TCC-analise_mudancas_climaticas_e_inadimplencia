"""SARIMA e SARIMAX estaduais do TCC: estimabilidade das 16 exógenas e teste temporal.
Executar após recuperar a base mensal original com hash verificado.
"""
from __future__ import annotations
import argparse,json,time,warnings
from pathlib import Path
import numpy as np,pandas as pd
from scipy import stats
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.diagnostic import acorr_ljungbox,het_arch
from analise_estadual import load,TIPOS,bh,OUT

ORDERS=[((0,0,0),(0,0,0,0)),((1,0,0),(0,0,0,0)),((0,0,1),(0,0,0,0)),((1,0,1),(0,0,0,0)),((0,0,0),(1,0,0,12)),((1,0,0),(1,0,0,12)),((0,0,1),(1,0,0,12))]

def fit(y,order,seasonal,x=None,maxiter=70):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        m=SARIMAX(y,exog=x,order=order,seasonal_order=seasonal,trend='c',enforce_stationarity=True,enforce_invertibility=True,concentrate_scale=False)
        r=m.fit(disp=False,maxiter=maxiter,method='lbfgs')
        converged=bool(r.mle_retvals.get('converged',False))
        return r,converged

def diag(r):
    e=np.asarray(r.resid,dtype=float); e=e[np.isfinite(e)]
    if len(e)<24:return dict(ljungbox_p=np.nan,arch_p=np.nan,normalidade_p=np.nan)
    # Descontar parâmetros ARMA em testes LB; diagnóstico e não confirmação do modelo
    lb=float(acorr_ljungbox(e,lags=[12],return_df=True)['lb_pvalue'].iloc[0]);arch=float(het_arch(e,nlags=min(6,len(e)//5))[1]);norm=float(stats.jarque_bera(e).pvalue)
    return dict(ljungbox_p=lb,arch_p=arch,normalidade_p=norm)

def forecast_fixed(result,y_all,x_all,ntrain):
    # Filtragem com parâmetros ESTIMADOS APENAS NO TREINO; previsão de 1 passo
    # atualiza o estado com y observado até t-1, sem reestimar os parâmetros.
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        mf=SARIMAX(y_all,exog=x_all,order=result.model.order,seasonal_order=result.model.seasonal_order,trend='c',enforce_stationarity=True,enforce_invertibility=True,concentrate_scale=False)
        rf=mf.filter(result.params)
        yh=np.asarray(rf.get_prediction(start=ntrain,end=len(y_all)-1,dynamic=False).predicted_mean)
    y_true=np.asarray(y_all[ntrain:]);return dict(MAE=float(np.mean(np.abs(y_true-yh))),RMSE=float(np.sqrt(np.mean((y_true-yh)**2))),n_test=len(y_true)),yh

def main(period):
    d=load();t0=time.time();outbase=[];outmod=[];outcoef=[];outsearch=[]
    for uf,g in d.groupby('uf',sort=True):
        g=g[g.mes_ano<=('2020-01' if period=='Pré' else '2024-12')].copy().dropna(subset=['y']).reset_index(drop=True)
        y=(100*g.y).to_numpy(float);exog=g[['x_'+c for c in TIPOS]].to_numpy(float)
        train_end='2019-01' if period=='Pré' else '2022-12'
        ntrain=int(np.count_nonzero(g.mes_ano<=train_end));n=len(g)
        assert (ntrain,n-ntrain)==((72,12) if period=='Pré' else (119,24)),(uf,period,ntrain,n)
        candidates=[]
        for order,seasonal in ORDERS:
            try:
                r,ok=fit(y[:ntrain],order,seasonal)
                dg=diag(r);rec=dict(periodo=period,uf=uf,order=str(order),seasonal=str(seasonal),BIC=float(r.bic),AIC=float(r.aic),convergiu=ok,**dg)
                rec['adequado_LB']=dg['ljungbox_p']>=.05
                candidates.append((rec,r))
                outsearch.append(rec)
            except Exception as err:
                outsearch.append(dict(periodo=period,uf=uf,order=str(order),seasonal=str(seasonal),erro=str(err)[:140],convergiu=False))
        elig=[a for a in candidates if a[0].get('convergiu') and np.isfinite(a[0]['BIC'])]
        valid=[a for a in elig if a[0]['adequado_LB']]
        if valid: sel=min(valid,key=lambda a:a[0]['BIC']);status_base='convergido e não rejeita LB12 nominal no treino'
        elif elig: sel=min(elig,key=lambda a:a[0]['BIC']);status_base='convergido, mas Ljung–Box 12 rejeita no treino'
        else:
            outbase.append(dict(periodo=period,uf=uf,status='nenhum SARIMA convergido',n_treino=ntrain,n_teste=n-ntrain));outmod.append(dict(periodo=period,uf=uf,status='não executado: SARIMA indisponível'));continue
        rec,rbase=sel;maebase,yhat=forecast_fixed(rbase,y,None,ntrain)
        try:rbase_all,base_conv_all=fit(y,rbase.model.order,rbase.model.seasonal_order,maxiter=95)
        except Exception as e:rbase_all=None;base_conv_all=False
        outbase.append(dict(periodo=period,uf=uf,status=status_base,n_treino=ntrain,n_teste=n-ntrain,SARIMA_order=str(rbase.model.order),SARIMA_seasonal=str(rbase.model.seasonal_order),BIC_treino=rec['BIC'],AIC_treino=rec['AIC'],**maebase,**diag(rbase),BIC_total=float(rbase_all.bic) if rbase_all is not None and base_conv_all else np.nan,convergiu_total=base_conv_all))
        ranks=np.linalg.matrix_rank(exog);rtrain=np.linalg.matrix_rank(exog[:ntrain]); zeros=int(np.sum(np.ptp(exog,axis=0)<1e-12));zeros_train=int(np.sum(np.ptp(exog[:ntrain],axis=0)<1e-12))
        model=dict(periodo=period,uf=uf,n=n,n_treino=ntrain,n_teste=n-ntrain,rank_total=ranks,rank_treino=rtrain,exogenas_pedidas=16,constantes_total=zeros,constantes_treino=zeros_train,SARIMA_order=str(rbase.model.order),SARIMA_seasonal=str(rbase.model.seasonal_order),BIC_SARIMA_total=float(rbase_all.bic) if rbase_all is not None and base_conv_all else np.nan,RMSE_SARIMA=maebase['RMSE'],MAE_SARIMA=maebase['MAE'])
        if ranks!=16:
            model.update(status='16 coeficientes não identificáveis no período: posto deficiente',n_exogenas_identificaveis=ranks);outmod.append(model);continue
        # Full sample: inferência descritiva mesmo sem teste fora da amostra.
        try: rx,conv=fit(y,rbase.model.order,rbase.model.seasonal_order,exog,maxiter=160)
        except Exception as e:
            model.update(status='falha de estimação 16 exógenas: '+str(e)[:140],n_exogenas_identificaveis=16);outmod.append(model);continue
        model.update(convergiu=conv,BIC_total=float(rx.bic),AIC_total=float(rx.aic),loglike_total=float(rx.llf),n_exogenas_identificaveis=16,**{'sarimax_'+k:v for k,v in diag(rx).items()})
        if not conv:
            model.update(status='não convergiu com 16 exógenas: inferência indisponível');outmod.append(model);continue
        if rbase_all is not None and base_conv_all:
            LR=max(0,2*(rx.llf-rbase_all.llf));model.update(LR=LR,gl_LR=16,p_conjunto=float(stats.chi2.sf(LR,16)),delta_BIC=float(rx.bic-rbase_all.bic))
        else:model.update(LR=np.nan,p_conjunto=np.nan,delta_BIC=np.nan)
        exogname=['x'+str(i+1) for i in range(16)];pvals=np.array([rx.pvalues[rx.param_names.index(name)] for name in exogname]);q=multipletests(np.clip(np.nan_to_num(pvals,nan=1),0,1),method='fdr_bh')[1]
        for c,name,pval,qv in zip(TIPOS,exogname,pvals,q):
            idx=rx.param_names.index(name);beta=float(rx.params[idx]);se=float(rx.bse[idx]);outcoef.append(dict(periodo=period,uf=uf,tipologia=c,coeficiente=beta,se=se,IC_inf=beta-1.96*se,IC_sup=beta+1.96*se,p=float(pval),q_bh=float(qv),rejeicao_nominal=bool(pval<.05),rejeicao_bh=bool(qv<.05),diagnostico_LB=model.get('sarimax_ljungbox_p')))
        if rtrain==16:
            try:
                tr,convt=fit(y[:ntrain],rbase.model.order,rbase.model.seasonal_order,exog[:ntrain],maxiter=160)
                model.update(convergiu_treino=convt,BIC_treino=float(tr.bic))
                if convt:
                    fore,_=forecast_fixed(tr,y,exog,ntrain)
                    model.update(RMSE_SARIMAX=fore['RMSE'],MAE_SARIMAX=fore['MAE'],variacao_RMSE_pct=100*(fore['RMSE']/maebase['RMSE']-1),status='16 exógenas estimadas; comparação preditiva condicional viável')
                else:model.update(status='16 exógenas estimadas no total, mas treino não convergiu')
            except Exception as err:model.update(status='16 exógenas estimadas no total, falha no treino: '+str(err)[:120])
        else:model.update(status='16 exógenas estimadas somente no período completo; teste preditivo não identificável (posto do treino insuficiente)')
        outmod.append(model)
        print(period,uf,'16-var rank',ranks,'train',rtrain,'convergiu',conv,'RMSE',model.get('RMSE_SARIMAX'),flush=True)
    for name,records in [('sarima_candidatos_'+period+'.csv',outsearch),('sarima_referencia_'+period+'.csv',outbase),('sarimax_modelos_'+period+'.csv',outmod),('sarimax_coeficientes_'+period+'.csv',outcoef)]:
        (pd.DataFrame(records) if records else pd.DataFrame(columns=['periodo','uf','tipologia','coeficiente','se','IC_inf','IC_sup','p','q_bh','rejeicao_nominal','rejeicao_bh','diagnostico_LB']) if name.startswith('sarimax_coeficientes') else pd.DataFrame(records)).to_csv(OUT/name,index=False,encoding='utf-8-sig')
    print(period,'DONE in',round(time.time()-t0,2),'seconds, baselines',len(outbase),'rank16',sum(r.get('rank_total')==16 for r in outmod),'converged full',sum(r.get('convergiu') is True for r in outmod),'train rank16',sum(r.get('rank_treino')==16 for r in outmod),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('periodo',choices=['Pré','Total']);main(parser.parse_args().periodo)