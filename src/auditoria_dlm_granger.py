"""Auditoria não destrutiva das matrizes dos DLMs e resíduos de Granger.

Usa as séries e horizontes já estimados, sem procurar resultados significativos.
Avalia posto/condicionamento e intensidade da autocorrelação; não substitui
estimação nem altera automaticamente as inferências dos notebooks originais.
"""
from __future__ import annotations
import json, os
from pathlib import Path
import numpy as np
import pandas as pd
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.stattools import acf
from statsmodels.stats.diagnostic import acorr_ljungbox
from scipy.stats import norm
from analise_estadual import load, TIPOS, OUT, design_panel, robust_cov, dm

ROOT=Path(__file__).resolve().parents[1]
AUD=ROOT/'outputs/tables/auditoria_metodologica_20261020'
AUD.mkdir(parents=True,exist_ok=True)

def auditoria_dlm(data):
    selections=pd.read_csv(OUT/'dlm_selecao.csv')
    tests=pd.read_csv(OUT/'dlm_hipoteses.csv')
    detail=[]
    for per,stop in [('Pré','2020-01'),('Total','2024-12')]:
        g=data[data.mes_ano<=stop]; ufs=sorted(g.uf.unique());t=g.mes_ano.nunique()
        y=np.stack([g[g.uf==u].y.to_numpy(float) for u in ufs])
        for tipo in TIPOS:
            xs=np.stack([g[g.uf==u]['x_'+tipo].to_numpy(float) for u in ufs])
            for crit in ['AIC','BIC']:
                rows=selections[(selections.periodo==per)&(selections.tipologia==tipo)&(selections.criterio==crit)]
                assert len(rows)==1,(per,tipo,crit)
                if rows.iloc[0].status!='estimado':continue
                K=int(rows.iloc[0].K)
                X,Y,T=design_panel(xs,y,K,t,len(ufs))
                sing=np.linalg.svd(X,compute_uv=False)
                rank=int(np.linalg.matrix_rank(X))
                cond=float(sing[0]/sing[-1]) if sing[-1]>0 else np.inf
                b=np.linalg.lstsq(X,Y,rcond=None)[0];e=Y-X@b
                for band in ['cluster_uf','dk_regra','dk6','dk12']:
                    V,df_res=robust_cov(X,e,K,27,T,band)
                    eig=np.linalg.eigvalsh(V)
                    # Comparação entre menores e maiores valores singulares da covariância
                    sv=np.linalg.svd(V,compute_uv=False)
                    cV=float(sv[0]/sv[-1]) if sv[-1]>0 else np.inf
                    nneg=int((eig<=0).sum())
                    past=tests[(tests.periodo==per)&(tests.tipologia==tipo)&(tests.criterio==crit)&(tests.covariancia==band)]
                    out={
                     'periodo':per,'tipologia':tipo,'criterio':crit,'K':K,'covariancia':band,
                     'n_obs':len(Y),'n_coef':K+1,'posto_X':rank,'cond_X':cond,
                     'min_sv_X':float(sing[-1]),'max_sv_X':float(sing[0]),
                     'cond_cov':cV,'min_eig_cov':float(eig[0]),'max_eig_cov':float(eig[-1]),
                     'n_eig_cov_nao_positivos':nneg,'cov_postocompleto':nneg==0,
                     'alerta_cond_X':cond>1e3, 'alerta_cond_cov':cV>1e6,
                     'n_rejeicoes_grade_BH':int((past.q_bh_grade<.05).sum()),
                     'endpoints_rejeitados_grade_BH':';'.join(past.loc[past.q_bh_grade<.05,'endpoint'].tolist()),
                     'soma_0K':float(b.sum()),'soma_1K':float(b[1:].sum())}
                    detail.append(out)
    d=pd.DataFrame(detail).sort_values(['periodo','tipologia','criterio','covariancia'])
    d.to_csv(AUD/'dlm_matrizes_condicionamento.csv',index=False,encoding='utf-8-sig')
    return d

def auditoria_granger(data):
    hist=pd.read_csv(OUT/'granger_aplicacoes.csv')
    rows=[]
    for item in hist.itertuples(index=False):
        if item.status!='estimado':continue
        g=data[(data.uf==item.uf)&(data.mes_ano<=('2020-01' if item.periodo=='Pré' else '2024-12'))].reset_index(drop=True)
        y=g.y.to_numpy(float);x=g['x_'+item.tipologia].to_numpy(float);n=len(y)
        ti=np.arange(7,n);p=int(item.p_lags)
        Y=y[ti];dum=(g.mes.to_numpy()[ti,None]==np.arange(2,13)[None,:]).astype(float)
        X=np.column_stack([np.ones(len(ti)),dum]+[y[ti-j] for j in range(1,p+1)]+[x[ti-j] for j in range(1,p+1)])
        b=np.linalg.lstsq(X,Y,rcond=None)[0];e=Y-X@b
        lag=min(12,max(3,len(e)//6));corr=acf(e,nlags=lag,fft=True)[1:]
        lb=float(acorr_ljungbox(e,lags=[lag],return_df=True)['lb_pvalue'].iloc[0])
        rows.append({'uf':item.uf,'periodo':item.periodo,'tipologia':item.tipologia,
         'K_Granger':p,'p_Granger':float(item.p),'q_BH_Granger':float(item.q_bh),
         'rejeita_BH':bool(item.rejeicao_bh),'n_residuos':len(e),'lag_Ljung_Box':lag,
         'p_Ljung_Box':lb, 'acf1':float(corr[0]),'maior_acf_absoluta_1a12':float(np.max(np.abs(corr))),
         'limite_heuristico_acf':float(1.96/np.sqrt(len(e))),
         'n_lags_acf_acima_limite':int((np.abs(corr)>1.96/np.sqrt(len(e))).sum()),
         'dw':float(durbin_watson(e))})
    out=pd.DataFrame(rows)
    out.to_csv(AUD/'granger_autocorrelacao_intensidade.csv',index=False,encoding='utf-8-sig')
    return out

def main():
    df=load();assert len(df)==3888
    D=auditoria_dlm(df); G=auditoria_granger(df)
    sig=D[D.n_rejeicoes_grade_BH>0]
    br=G[G.rejeita_BH]
    summary={'dlm_casos_estimaveis':int(len(D)/4),'dlm_K_superior_10':int(D[D.covariancia=='dk_regra'].K.gt(10).sum()),
     'dlm_casos_com_alerta_cond_X':int(D[D.covariancia=='dk_regra'].alerta_cond_X.sum()),
     'dlm_cov_cond_superior_1e6':int(D.alerta_cond_cov.sum()),
     'dlm_cov_eig_nao_positivos':int((D.n_eig_cov_nao_positivos>0).sum()),
     'dlm_rejeicoes_grade_bh_com_alerta_cond_cov':int(sig.alerta_cond_cov.sum()),
     'granger_estimados':len(G),'granger_apos_BH':len(br),
     'granger_BH_com_LB_rejeitado':int(br.p_Ljung_Box.lt(.05).sum())}
    (AUD/'resumo_auditoria.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print('\nDLM com rejeições corrigidas, posto e condicionamento:')
    print(sig[['periodo','tipologia','criterio','K','covariancia','cond_X','cond_cov','n_rejeicoes_grade_BH']].to_string(index=False))
    print('\nGranger BH com autocorrelação:')
    print(br[br.p_Ljung_Box<.05][['uf','periodo','tipologia','p_Ljung_Box','acf1','maior_acf_absoluta_1a12']].to_string(index=False))
if __name__=='__main__':main()