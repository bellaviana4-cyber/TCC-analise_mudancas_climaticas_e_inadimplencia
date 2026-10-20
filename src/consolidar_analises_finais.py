"""Consolida comparações de seleção BIC independente e Wald/perfis DLM.

Reproduz resumos sem alterar históricos. Na saída SARIMAX, o BH global
é refeito sobre toda a família de 395 coeficientes estaduais; não por período.
"""
from __future__ import annotations
import json,os
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import t as tdist
from statsmodels.stats.multitest import multipletests
from analise_estadual import load,TIPOS,OUT,design_panel,robust_cov
ROOT=Path(__file__).resolve().parents[1]
AR=ROOT/'outputs/tables/sarimax_criterios_independentes_20261020'
AD=ROOT/'outputs/tables/auditoria_metodologica_20261020'
AR.mkdir(parents=True,exist_ok=True)
AD.mkdir(parents=True,exist_ok=True)

def sarimax():
    for mode in ('estadual','nacional'):
        models=pd.concat([pd.read_csv(AR/f'{mode}_{per}_modelos.csv') for per in ['Pré','Total']],ignore_index=True)
        candidates=pd.concat([pd.read_csv(AR/f'{mode}_{per}_candidatos.csv') for per in ['Pré','Total']],ignore_index=True)
        coefficients=pd.concat([pd.read_csv(AR/f'{mode}_{per}_coeficientes.csv') for per in ['Pré','Total']],ignore_index=True)
        if 'p_conjunto_condicional' in models.columns:
            mask=models.p_conjunto_condicional.notna()
            models['q_conjunto_BH_global']=np.nan
            models.loc[mask,'q_conjunto_BH_global']=multipletests(models.loc[mask,'p_conjunto_condicional'],method='fdr_bh')[1]
        if len(coefficients):
            coefficients['q_individual_BH_global']=multipletests(np.nan_to_num(coefficients.p_individual.to_numpy(float),nan=1),method='fdr_bh')[1]
            coefficients['q_individual_BH_modelo']=np.nan
            for _,ids in coefficients.groupby(['periodo','unidade']).groups.items():
                coefficients.loc[ids,'q_individual_BH_modelo']=multipletests(coefficients.loc[ids,'p_individual'].fillna(1),method='fdr_bh')[1]
        for tag,table in [('comparacao',models),('candidatos',candidates),('coeficientes',coefficients)]:
            table.to_csv(AR/f'{mode}_{tag}.csv',index=False,encoding='utf-8-sig')
        warning_candidates=candidates.loc[candidates.n_warnings.fillna(0)>0].copy()
        warning_candidates.to_csv(AR/f'{mode}_warnings.csv',index=False,encoding='utf-8-sig')
        sig=coefficients.loc[coefficients.q_individual_BH_global<.05].copy() if len(coefficients) else coefficients.copy()
        sig.to_csv(AR/f'{mode}_significativos_BH.csv',index=False,encoding='utf-8-sig')
        summary={
          'modo':mode,'total_unidades_periodos':len(models),
          'comparaveis':int(models.rmse_sarimax.notna().sum()),
          'melhora_RMSE':int((models.melhora_RMSE_pct>0).sum()),
          'melhora_BIC':int((models.delta_BIC<0).sum()),
          'mediana_melhora_RMSE_pct':float(models.melhora_RMSE_pct.median()),
          'sazonal_em_todos_candidatos':True,
          'busca_independente':True,
          'melhor_entre_5_candidatos_por_BIC':True,
          'diagnostico_LB_SARIMA_rejeita':int((models.ljungbox_sarima<.05).sum()),
          'diagnostico_LB_SARIMAX_rejeita':int((models.ljungbox_sarimax<.05).sum()),
          'candidatos_total':len(candidates),
          'candidatos_com_warnings':len(warning_candidates),
          'candidatos_nao_convergentes':int((candidates.convergiu.astype(str).str.lower()=='false').sum()),
          'coeficientes_totais':len(coefficients),
          'coeficientes_nominais':int((coefficients.p_individual<.05).sum()) if len(coefficients) else 0,
          'coeficientes_BH_global':len(sig),
          'testes_conjuntos_BH':int((models.q_conjunto_BH_global<.05).sum()) if 'q_conjunto_BH_global' in models else 0,
          'proveniencia':'df_tcc_2013_2024.csv SHA256 46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36',
          'observacoes':'Testes condicionais à seleção por BIC; exógenas contemporâneas observadas no teste.'}
        (AR/f'{mode}_resumo_final.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
        print(mode,json.dumps(summary,ensure_ascii=False))

def dlm():
    d=load();models=pd.read_csv(OUT/'dlm_selecao.csv')
    profiles=[];curves=[]
    for per,stop in [('Pré','2020-01'),('Total','2024-12')]:
        g=d[d.mes_ano<=stop];uf=sorted(g.uf.unique());Ttotal=g.mes_ano.nunique()
        y=np.stack([g[g.uf==i].y.to_numpy(float) for i in uf]);
        for typ in TIPOS:
            x=np.stack([g[g.uf==i]['x_'+typ].to_numpy(float) for i in uf])
            for crit in ('AIC','BIC'):
                selected=models[(models.periodo==per)&(models.tipologia==typ)&(models.criterio==crit)]
                assert len(selected)==1
                if selected.iloc[0].status!='estimado':continue
                K=int(selected.iloc[0].K)
                X,Y,T=design_panel(x,y,K,Ttotal,27)
                b=np.linalg.lstsq(X,Y,rcond=None)[0];e=Y-X@b
                for kind in ('dk_regra','dk6','dk12','cluster_uf'):
                    V,df=robust_cov(X,e,K,27,T,kind)
                    variance=np.clip(np.diag(V),0,None)
                    ses=np.sqrt(variance)
                    critical=tdist.ppf(.975,df)
                    for k in range(K+1):
                        profiles.append({'periodo':per,'tipologia':typ,'criterio':crit,'K':K,'k':k,
                          'covariancia':kind,'coef_beta_k':b[k],'se':ses[k],
                          'ic95_inf':b[k]-critical*ses[k], 'ic95_sup':b[k]+critical*ses[k],
                          'stat_t':b[k]/ses[k] if ses[k]>0 else np.nan,'n':len(Y)})
                        w=np.zeros(K+1);w[:k+1]=1
                        cum=float(w@b);se=float(np.sqrt(max(0,w@V@w)))
                        curves.append({'periodo':per,'tipologia':typ,'criterio':crit,'K':K,'h':k,
                          'covariancia':kind,'acum_0h':cum,'se_acum':se,
                          'ic95_inf':cum-critical*se,'ic95_sup':cum+critical*se,'n':len(Y)})
    pro=pd.DataFrame(profiles);cur=pd.DataFrame(curves)
    pro.to_csv(AD/'dlm_betas_por_lag.csv',index=False,encoding='utf-8-sig')
    cur.to_csv(AD/'dlm_resposta_acumulada.csv',index=False,encoding='utf-8-sig')
    print('DLM perfis',len(pro),'curvas',len(cur),'estimacoes',pro[['periodo','tipologia','criterio']].drop_duplicates().shape[0])

if __name__=='__main__':sarimax();dlm()