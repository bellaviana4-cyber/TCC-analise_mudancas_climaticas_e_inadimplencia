"""Comparações SARIMA–SARIMAX por UF e nacional, com diagnóstico de estimabilidade.

A análise não escolhe regressores por p-valores ou pelo desempenho do teste.
As 16 exógenas foram auditadas no treino e na amostra completa antes de qualquer
redução. A redução estadual é baseada somente em suporte/rank do treinamento.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.statespace.sarimax import SARIMAX

from analise_estadual import load, TIPOS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs' / 'tables' / 'sarimax_revisao_20261019'
OUT.mkdir(parents=True, exist_ok=True)
EXPECTED_HASH = '46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36'
# Critérios fixados ex ante e aplicados exclusivamente no treino.
MIN_MESES_COM_OCORRENCIA = 3
MAX_EXOG = {'Pré': 9, 'Total': 12}
MAX_COND = 1_000.0
MODELS = [
    ((0,0,0), (1,0,0,12)),
    ((1,0,0), (1,0,0,12)),
    ((0,0,1), (1,0,0,12)),
    ((1,0,1), (1,0,0,12)),
    ((1,0,0), (0,0,1,12)),
]
COLUMNS_X = ['x_'+t for t in TIPOS]
PERIODS = {'Pré': ('2020-01', '2019-01', 72, 12),
           'Total': ('2024-12', '2022-12', 119, 24)}


def paired_lags(a):
    arr = np.asarray(a, dtype=float)
    return float(acorr_ljungbox(arr[np.isfinite(arr)], lags=[12], return_df=True)['lb_pvalue'].iloc[0])


def fit(y, order, seasonal_order, x=None, maxiter=110):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        mod = SARIMAX(np.asarray(y, float),
                     exog=None if x is None else np.asarray(x, float),
                     order=order, seasonal_order=seasonal_order, trend='c',
                     enforce_stationarity=True, enforce_invertibility=True)
        result = mod.fit(disp=False, maxiter=maxiter, method='lbfgs')
    return result, bool(result.mle_retvals.get('converged', False))


def predicted_1step(result, yall, xall, ntrain):
    # Previsão condicional, 1 passo: estado atualizado com y realizado até t-1.
    # Quando contemporâneo, x_t é observado, nunca inferido no instante t-1.
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        mod = SARIMAX(np.asarray(yall,float),
                     exog=None if xall is None else np.asarray(xall,float),
                     order=result.model.order,
                     seasonal_order=result.model.seasonal_order,
                     trend='c', enforce_stationarity=True, enforce_invertibility=True)
        filtered = mod.filter(result.params)
        pred = np.asarray(filtered.get_prediction(start=ntrain,
                          end=len(yall)-1,dynamic=False).predicted_mean,float)
    true=np.asarray(yall[ntrain:],float)
    assert len(pred)==len(true) and np.isfinite(pred).all()
    return {'rmse':float(np.sqrt(np.mean((pred-true)**2))),
            'mae':float(np.mean(np.abs(pred-true))),
            'n_teste':len(true)}


def full_exog_audit(xtrain,xall,typologies):
    xt=np.asarray(xtrain,float);xa=np.asarray(xall,float)
    ptp=np.ptp(xt,axis=0)
    duplicates=[]
    for j in range(len(typologies)):
        for k in range(j):
            if np.allclose(xt[:,j],xt[:,k],rtol=0,atol=1e-12):
                duplicates.append([typologies[k],typologies[j]])
    return {'posto_treino':int(np.linalg.matrix_rank(xt)),
            'posto_completo':int(np.linalg.matrix_rank(xa)),
            'n_exog_original':int(xt.shape[1]),
            'n_constantes_treino':int((ptp<1e-12).sum()),
            'n_constantes_total':int((np.ptp(xa,axis=0)<1e-12).sum()),
            'tipologias_constantes_treino':[typologies[j] for j in np.where(ptp<1e-12)[0]],
            'duplicadas_treino':duplicates}


def screen_by_support(x, D, ntrain, period):
    """Seleção determinística, só por suporte e independência no treino.

    A ordem utiliza meses com registro, com empate decidido pela ordem TIPOS.
    Sem seleção de sinais, p-valores ou desempenho fora da amostra.
    """
    xtrain=np.asarray(x[:ntrain],float)
    dtrain=np.asarray(D[:ntrain],float)
    counts=(dtrain>0).sum(axis=0)
    choices=sorted(range(16),key=lambda i:(-counts[i],i))
    included=[];exclusions={}
    for j in choices:
        if counts[j]<MIN_MESES_COM_OCORRENCIA:
            exclusions[TIPOS[j]]='menos de 3 meses positivos no treinamento'
            continue
        if np.ptp(xtrain[:,j])<1e-12:
            exclusions[TIPOS[j]]='exposição transformada constante no treino'
            continue
        if len(included)>=MAX_EXOG[period]:
            exclusions[TIPOS[j]]='limite de parcimônia aplicado antes do ajuste'
            continue
        candidate=included+[j]
        Z=xtrain[:,candidate]
        scale=np.std(Z,axis=0)
        Zn=(Z-Z.mean(axis=0))/scale
        if np.linalg.matrix_rank(Zn)<len(candidate):
            exclusions[TIPOS[j]]='dependência linear no treinamento'
            continue
        if np.linalg.cond(Zn)>MAX_COND:
            exclusions[TIPOS[j]]='condicionamento elevado no treinamento'
            continue
        included.append(j)
    included=sorted(included)
    assert not included or np.linalg.matrix_rank(xtrain[:,included])==len(included)
    return included,exclusions,counts


def choose_baseline(ytrain,period,unit):
    candidates=[];results=[]
    for order,seasonal in MODELS:
        rec={'periodo':period,'unidade':unit,'ordem':str(order),'sazonal':str(seasonal)}
        try:
            res,ok=fit(ytrain,order,seasonal)
            rec.update(convergiu=ok,bic_treino=float(res.bic),aic_treino=float(res.aic),
                       lb12_treino=paired_lags(res.resid))
            if ok and np.isfinite(res.bic):results.append((rec,res))
        except Exception as err:
            rec.update(convergiu=False,erro=repr(err)[:150])
        candidates.append(rec)
    if not results:return None,candidates,'nenhum candidato convergiu'
    adequate=[a for a in results if a[0]['lb12_treino']>=0.05]
    pool=adequate if adequate else results
    selected=min(pool,key=lambda a:a[0]['bic_treino'])
    status='BIC entre candidatos com Ljung-Box não rejeitado' if adequate else 'BIC entre convergidos; Ljung-Box rejeita em todos'
    return selected,candidates,status


def series_for_unit(df,unit,period):
    end,cut,ntr,nte=PERIODS[period]
    if unit=='Brasil':
        # A taxa nacional é ponderada pelos denominadores: não é média de UFs.
        full=(df[df.mes_ano<=end].groupby('mes_ano',sort=True)
              [['carteira_ativa_total','carteira_inadimplencia_total',*TIPOS]].sum())
        y=100*np.log(100*full.carteira_inadimplencia_total/full.carteira_ativa_total).diff().iloc[1:].to_numpy(float)
        X=np.log1p(full[TIPOS]).diff().iloc[1:].to_numpy(float)
        D=full[TIPOS].iloc[1:].to_numpy(float)
        months=full.index[1:].to_numpy()
    else:
        subset=df[(df.uf==unit)&(df.mes_ano<=end)].dropna(subset=['y']).sort_values('mes_ano')
        y=100*subset.y.to_numpy(float)
        X=subset[COLUMNS_X].to_numpy(float)
        D=subset[TIPOS].to_numpy(float)
        months=subset.mes_ano.to_numpy()
    assert len(y)==ntr+nte and len(X)==len(y)
    assert np.all(np.isfinite(y)) and np.all(np.isfinite(X))
    assert (months[ntr-1]==cut), (unit,period,months[ntr-1],cut)
    return y,X,D,months


def one_model(df,unit,period,audits,cands,models,coefs):
    y,x,D,months=series_for_unit(df,unit,period)
    end,cut,ntrain,ntest=PERIODS[period]
    audit=full_exog_audit(x[:ntrain],x,TIPOS)
    audit.update(periodo=period,unidade=unit,n_treino=ntrain,n_total=len(y),
                 cond_treino=float(np.linalg.cond(x[:ntrain])) if audit['posto_treino']==16 else np.nan,
                 cond_completo=float(np.linalg.cond(x)) if audit['posto_completo']==16 else np.nan)
    audits.append(audit)
    selected,candidates,selection_status=choose_baseline(y[:ntrain],period,unit)
    cands.extend(candidates)
    row={'periodo':period,'unidade':unit,'n_treino':ntrain,'n_teste':ntest,
         'rank_original_treino':audit['posto_treino'],
         'rank_original_total':audit['posto_completo'],
         'n_exog_original':16,'seleciona_base':selection_status,
         'comparacao':'sazonal s=12; ordens ARMA identicas dentro do par',
         'exogenas_contemporaneas':'conhecidas no mes t; previsao condicional'}
    if selected is None:
        models.append({**row,'status':'sem baseline convergido'});return
    baserec,refit=selected
    order=refit.model.order;seasonal=refit.model.seasonal_order
    row.update(ordem=str(order),sazonal=str(seasonal),
               bic_sarima_treino=float(refit.bic),
               lb_sarima_treino=paired_lags(refit.resid))
    try:
        basepred=predicted_1step(refit,y,None,ntrain)
        row.update(rmse_sarima=basepred['rmse'],mae_sarima=basepred['mae'])
    except Exception as err:
        models.append({**row,'status':'erro de previsão SARIMA: '+repr(err)[:140]});return
    # Em ambas as análises, X é selecionada olhando APENAS para os meses de treino.
    if unit=='Brasil':
        idx=list(range(16));excluded={}
        if audit['posto_treino']!=16 or audit['posto_completo']!=16:
            models.append({**row,'status':'16 exógenas nacionais não identificáveis'});return
        z=x[:ntrain];std=z.std(axis=0)
        if float(np.linalg.cond((z-z.mean(axis=0))/std))>MAX_COND:
            models.append({**row,'status':'nacional mal condicionado no treino'});return
    else:
        idx,excluded,count=screen_by_support(x,D,ntrain,period)
    row.update(n_exog_incluidas=len(idx),tipologias_incluidas=';'.join(TIPOS[j] for j in idx),
               tipologias_excluidas=json.dumps(excluded,ensure_ascii=False),
               suporte_minimo=MIN_MESES_COM_OCORRENCIA if unit!='Brasil' else np.nan,
               limite_exogenas=MAX_EXOG[period] if unit!='Brasil' else 16)
    if not idx:
        models.append({**row,'status':'nenhuma exógena atende aos critérios no treino'});return
    z=x[:ntrain,idx];means=z.mean(axis=0);std=z.std(axis=0)
    assert np.all(std>0)
    zx=(x[:,idx]-means)/std
    assert np.linalg.matrix_rank(zx[:ntrain])==len(idx)
    row.update(cond_exog_padronizada=float(np.linalg.cond(zx[:ntrain])),
               posto_exog_treino=int(np.linalg.matrix_rank(zx[:ntrain])))
    try:
        rx,ok=fit(y[:ntrain],order,seasonal,zx[:ntrain],maxiter=180)
        if not ok:
            rx,ok=fit(y[:ntrain],order,seasonal,zx[:ntrain],maxiter=340)
        row.update(convergiu_sarimax_treino=ok,bic_sarimax_treino=float(rx.bic),
                   lb_sarimax_treino=paired_lags(rx.resid))
        if not ok:
            models.append({**row,'status':'SARIMAX não convergiu no treino'});return
        pred=predicted_1step(rx,y,zx,ntrain)
        row.update(rmse_sarimax=pred['rmse'],mae_sarimax=pred['mae'],
                   variacao_rmse_pct=100*(pred['rmse']/basepred['rmse']-1),
                   variacao_mae_pct=100*(pred['mae']/basepred['mae']-1),
                   delta_bic_treino=float(rx.bic-refit.bic))
        # LR e teste conjunto no treino; modelos aninhados, estrutura ARMA idêntica.
        LR=max(0.,float(2*(rx.llf-refit.llf)))
        row.update(lr_treino=LR,gl_lr=len(idx),p_conjunto_treino=float(chi2.sf(LR,len(idx))))
        row['status']='estimado e comparado no teste cronológico'
        for j,i in enumerate(idx):
            try:
                b=float(rx.params[rx.param_names.index('x'+str(j+1))]);
                se=float(rx.bse[rx.param_names.index('x'+str(j+1))]);
                pv=float(rx.pvalues[rx.param_names.index('x'+str(j+1))]);
            except (ValueError,IndexError) as err:
                raise RuntimeError(f'parâmetro ausente: {j+1}') from err
            coefs.append({'periodo':period,'unidade':unit,'tipologia':TIPOS[i],
                          'coef_original':b/std[j], 'erro_padrao_original':se/std[j],
                          'coef_padronizado':b,'erro_padrao_padronizado':se,
                          'p':pv,'n_train':ntrain,'convergencia':ok})
    except Exception as err:
        row.update(status='erro na estimação/previsão: '+repr(err)[:200])
    models.append(row)


def run(mode):
    src=Path(os.getenv('TCC_BASE_CSV',str(ROOT/'data/processed/df_tcc_2013_2024.csv')))
    assert hashlib.sha256(src.read_bytes()).hexdigest()==EXPECTED_HASH, 'SHA-256 da base diverge'
    df=load()
    audits=[];cands=[];models=[];coefs=[]
    units=['Brasil'] if mode=='nacional' else sorted(df.uf.unique())
    for period in PERIODS:
        for i,uf in enumerate(units,1):
            one_model(df,uf,period,audits,cands,models,coefs)
            row=models[-1]
            print(f'{mode} {period} {i}/{len(units)} {uf} | original {row["rank_original_treino"]}/16 | exog {row.get("n_exog_incluidas",0)} | {row["status"]} | RMSE delta {row.get("variacao_rmse_pct",float("nan")):.3f}%',flush=True)
    pd.DataFrame(audits).to_csv(OUT/f'{mode}_auditoria_posto.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(cands).to_csv(OUT/f'{mode}_candidatos_sarima.csv',index=False,encoding='utf-8-sig')
    o=pd.DataFrame(models)
    if 'p_conjunto_treino' in o:
        ps=o.p_conjunto_treino.to_numpy(float)
        q=np.full(len(o),np.nan)
        yes=np.isfinite(ps)
        if yes.any():q[yes]=multipletests(ps[yes],method='fdr_bh')[1]
        o['q_conjunto_bh']=q
    o.to_csv(OUT/f'{mode}_comparacao_modelos.csv',index=False,encoding='utf-8-sig')
    c=pd.DataFrame(coefs)
    if len(c):
        c['q_bh_global']=multipletests(np.nan_to_num(c.p,nan=1).clip(0,1),method='fdr_bh')[1]
        c['q_bh_por_modelo']=np.nan
        for _,ind in c.groupby(['unidade','periodo']).groups.items():
            c.loc[ind,'q_bh_por_modelo']=multipletests(np.nan_to_num(c.loc[ind,'p'],nan=1).clip(0,1),method='fdr_bh')[1]
        c.to_csv(OUT/f'{mode}_coeficientes.csv',index=False,encoding='utf-8-sig')
    else:pd.DataFrame(columns=['periodo','unidade','tipologia','p']).to_csv(OUT/f'{mode}_coeficientes.csv',index=False,encoding='utf-8-sig')
    summary={'amostra':'2013-2019/2020 e 2013-2024','modo':mode,'n_modelos':len(o),
             'n_comparaveis':int(o.status.eq('estimado e comparado no teste cronológico').sum()),
             'n_melhor_rmse':int((o.variacao_rmse_pct<0).sum()) if 'variacao_rmse_pct' in o else 0,
             'n_melhor_bic':int((o.delta_bic_treino<0).sum()) if 'delta_bic_treino' in o else 0,
             'n_LB_sarimax_nao_rejeita':int((o.lb_sarimax_treino>=.05).sum()) if 'lb_sarimax_treino' in o else 0,
             'n_LB_sarima_nao_rejeita':int((o.lb_sarima_treino>=.05).sum()) if 'lb_sarima_treino' in o else 0,
             'n_rejeicoes_conjunto_BH':int((o.q_conjunto_bh<.05).sum()) if 'q_conjunto_bh' in o else 0,
             'n_rejeicoes_coef_global_BH':int((c.q_bh_global<.05).sum()) if 'q_bh_global' in c else 0,
             'mediana_delta_RMSE_pct':float(o.variacao_rmse_pct.median()) if 'variacao_rmse_pct' in o else None,
             'criterio_selecao':'apenas treino: suporte>=3 meses, posto completo, cond<=1000 e cap 9 ou 12 (estaduais)',
             'exog_t':'Δlog(1+D), contemporâneo, conhecido no teste',
             'y':'100 Δlog(CI/CA), Brasil calculado por soma das carteiras'}
    (OUT/f'{mode}_resumo.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print('RESUMO '+mode+': '+json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('modo',choices=['estadual','nacional']);run(ap.parse_args().modo)
