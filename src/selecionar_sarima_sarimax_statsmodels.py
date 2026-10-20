"""Busca automática reproduzível (grade BIC) usando statsmodels.

Statsmodels não possui auto_arima. Para cada UF/período ou Brasil,
compara o melhor SARIMA e o melhor SARIMAX por BIC *separadamente*.
Mantém os dados de treino/teste, as 16 tipologias originais e as seleções
estaduais de exógenas previamente justificadas por posto/suporte.
Não usa p-valores, nem RMSE do teste, para escolher ordens.
Registra todos os warnings retornados pelas tentativas e não convergências.

Adicionalmente estima SARIMA com a ordem do melhor SARIMAX, viabilizando
uma comparação pareada com estrutura temporal idêntica, distinta de uma
comparação de modelos independentemente selecionados.
"""
from __future__ import annotations
import os,sys,time,ast,json,warnings,argparse,hashlib
from pathlib import Path
import pandas as pd,numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.multitest import multipletests
from scipy.stats import chi2
from analise_estadual import load,TIPOS
from sarimax_revisao_final import MODELS,PERIODS,series_for_unit,screen_by_support,predicted_1step
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/tables/sarimax_criterios_independentes_20261020'
OUT.mkdir(parents=True,exist_ok=True)

# Nenhum warning é silenciado: coleta-se categoria, mensagem e modelo.
def fit_one(y,order,seasonal,X=None,maxiter=120):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        with np.errstate(all='ignore'):
            mod=SARIMAX(np.asarray(y,float),exog=None if X is None else np.asarray(X,float),
                        order=order,seasonal_order=seasonal,trend='c',
                        enforce_stationarity=True,enforce_invertibility=True)
            res=mod.fit(disp=False,maxiter=maxiter,method='lbfgs')
    notes=sorted({str(w.category.__name__)+': '+str(w.message).replace('\n',' ')[:210] for w in caught})
    return res,bool(res.mle_retvals.get('converged',False)),notes

def pick(candidates):
    eligible=[x for x in candidates if x['convergiu'] and np.isfinite(x['BIC'])]
    return min(eligible,key=lambda x:(x['BIC'],x['idx'])) if eligible else None

def one_unit(df,uf,period):
    y,x,D,months=series_for_unit(df,uf,period)
    ntrain=PERIODS[period][2]
    if uf=='Brasil':
        idx=list(range(16))
        if np.linalg.matrix_rank(x[:ntrain])!=16:return {'unidade':uf,'periodo':period,'status':'posto nacional insuficiente'},[],[]
    else:
        idx,excl,cnt=screen_by_support(x,D,ntrain,period)
        if not idx:return {'unidade':uf,'periodo':period,'status':'nenhuma exógena elegível'},[],[]
    z=x[:ntrain,idx];means=z.mean(axis=0);scale=z.std(axis=0)
    Z=(x[:,idx]-means)/scale
    cand=[];fitobjs={}
    for j,(order,seasonal) in enumerate(MODELS):
        for flavor in ['SARIMA','SARIMAX']:
            tr=Z[:ntrain] if flavor=='SARIMAX' else None
            r={'unidade':uf,'periodo':period,'modelo':flavor,'idx':j,'ordem':str(order),
               'sazonal':str(seasonal),'n_exog':len(idx),'n_train':ntrain}
            try:
                fitted,converged,warns=fit_one(y[:ntrain],order,seasonal,tr)
                # Tenta novamente caso maxiter seja insuficiente; registra ambas as tentativas.
                if not converged:
                    fit2,conv2,notes2=fit_one(y[:ntrain],order,seasonal,tr,maxiter=240)
                    warns=sorted(set(warns+['primeira tentativa sem convergência']+notes2))
                    if conv2 or not converged:fitted,converged=fit2,conv2
                r.update(convergiu=converged,BIC=float(fitted.bic),AIC=float(fitted.aic),
                         ljungbox_p=float(acorr_ljungbox(fitted.resid,lags=[12],return_df=True).lb_pvalue.iloc[0]),
                         n_warnings=len(warns),warnings=' | '.join(warns),n_iteracoes=int(fitted.mle_retvals.get('iterations',0)))
                if converged and np.isfinite(r['BIC']):fitobjs[(flavor,j)]=fitted
            except Exception as exc:r.update(convergiu=False,erro=repr(exc)[:240],BIC=np.nan,n_warnings=0,warnings='')
            cand.append(r)
    best_base=pick([c for c in cand if c['modelo']=='SARIMA']);best_x=pick([c for c in cand if c['modelo']=='SARIMAX'])
    row={'unidade':uf,'periodo':period,'status':'estimado' if best_base and best_x else 'sem candidato convergido',
         'n_exog':len(idx),'tipologias':';'.join(TIPOS[i] for i in idx),'n_treino':ntrain,
         'n_teste':len(y)-ntrain,'posto_original_treino':int(np.linalg.matrix_rank(x[:ntrain]))}
    coefs=[]
    if not best_base or not best_x:return row,cand,coefs
    rb=fitobjs[('SARIMA',best_base['idx'])];rx=fitobjs[('SARIMAX',best_x['idx'])]
    # Estimativa de x via BIC, mantendo apenas y e x do treino.
    bpred=predicted_1step(rb,y,None,ntrain);xpred=predicted_1step(rx,y,Z,ntrain)
    row.update(ordem_sarima=best_base['ordem'],sazonal_sarima=best_base['sazonal'],
               ordem_sarimax=best_x['ordem'],sazonal_sarimax=best_x['sazonal'],
               bic_sarima=float(rb.bic),bic_sarimax=float(rx.bic),
               delta_BIC=float(rx.bic-rb.bic),
               rmse_sarima=bpred['rmse'],rmse_sarimax=xpred['rmse'],
               melhora_RMSE_pct=100*(1-xpred['rmse']/bpred['rmse']),
               mae_sarima=bpred['mae'],mae_sarimax=xpred['mae'],
               ljungbox_sarima=float(best_base['ljungbox_p']),
               ljungbox_sarimax=float(best_x['ljungbox_p']),
               warnings_sarima=int(best_base['n_warnings']),
               warnings_sarimax=int(best_x['n_warnings']))
    # Comparação pareada sob ordem escolhida pelo SARIMAX, sem novo ajuste a x.
    samebase=fitobjs.get(('SARIMA',best_x['idx']))
    if samebase is not None:
        pa=predicted_1step(samebase,y,None,ntrain)
        lr=max(0.,2*(rx.llf-samebase.llf));p=float(chi2.sf(lr,len(idx)))
        row.update(bic_sarima_ordem_sarimax=float(samebase.bic),
                   delta_BIC_pareado=float(rx.bic-samebase.bic),
                   rmse_sarima_ordem_sarimax=pa['rmse'],
                   melhora_RMSE_pareado_pct=100*(1-xpred['rmse']/pa['rmse']),
                   LR_condicional=lr,p_conjunto_condicional=p)
    for j,tip in enumerate(idx):
        par='x'+str(j+1)
        if par not in rx.param_names: continue
        ix=rx.param_names.index(par)
        coefs.append({'unidade':uf,'periodo':period,'tipologia':TIPOS[tip],
                      'coef_original':float(rx.params[ix]/scale[j]),
                      'se_original':float(rx.bse[ix]/scale[j]),
                      'p_individual':float(rx.pvalues[ix]),'crit':'BIC independente',
                      'n_exog_modelo':len(idx)})
    return row,cand,coefs

def persist(mode,per,models,candidates,coefs):
    a=pd.DataFrame(models);b=pd.DataFrame(candidates);c=pd.DataFrame(coefs)
    if 'p_conjunto_condicional' in a:
        valid=a.p_conjunto_condicional.notna();a['q_conjunto_BH']=np.nan
        if valid.any():a.loc[valid,'q_conjunto_BH']=multipletests(a.loc[valid,'p_conjunto_condicional'],method='fdr_bh')[1]
    if len(c):
        c['q_individual_BH_global']=multipletests(np.nan_to_num(c.p_individual,nan=1).clip(0,1),method='fdr_bh')[1]
    for name,d in [('modelos',a),('candidatos',b),('coeficientes',c)]:
        d.to_csv(OUT/f'{mode}_{per}_{name}.csv',index=False,encoding='utf-8-sig')
    return a,b,c

def run(mode,period):
    src=Path(os.environ.get('TCC_BASE_CSV',str(ROOT/'data/processed/df_tcc_2013_2024.csv')))
    sha=hashlib.sha256(src.read_bytes()).hexdigest()
    assert sha=='46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36', 'Base diferente da versão verificada; não reutilizar checkpoints'
    d=load();units=['Brasil'] if mode=='nacional' else sorted(d.uf.unique())
    models=[];candidates=[];coefs=[];clock=time.monotonic()
    oldfiles=[OUT/f'{mode}_{period}_{key}.csv' for key in ['modelos','candidatos','coeficientes']]
    if oldfiles[0].exists():
        models=pd.read_csv(oldfiles[0]).replace({np.nan:None}).to_dict('records')
        candidates=pd.read_csv(oldfiles[1]).replace({np.nan:None}).to_dict('records') if oldfiles[1].exists() else []
        coefs=pd.read_csv(oldfiles[2]).replace({np.nan:None}).to_dict('records') if oldfiles[2].exists() else []
        print('REANUDANDO',mode,period,'concluidos=',len(models),flush=True)
    done={m['unidade'] for m in models}
    for i,uf in enumerate(units,1):
        if uf in done:continue
        row,ca,co=one_unit(d,uf,period)
        models.append(row);candidates.extend(ca);coefs.extend(co)
        persist(mode,period,models,candidates,coefs)
        print(f'{mode} {period} {i}/{len(units)} {uf} status={row["status"]} exog={row.get("n_exog")} '
          f'BIC_delta={row.get("delta_BIC",float("nan")):.3f} RMSE_melhora={row.get("melhora_RMSE_pct",float("nan")):.2f}% '
          f'tempo={time.monotonic()-clock:.1f}s',flush=True)
    print('DONE',mode,period,'modelos',len(models),'tempo',time.monotonic()-clock,flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('modo',choices=['estadual','nacional']);parser.add_argument('periodo',choices=['Pré','Total']);a=parser.parse_args()
    run(a.modo,a.periodo)