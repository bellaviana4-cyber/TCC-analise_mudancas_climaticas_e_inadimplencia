"""Auditoria adicional de banda DK; não seleciona banda pelo p-valor.
Comparação exploratória adicionada após observar os resultados históricos.
Mantém K_AIC, amostra, estimativas, suporte e leitura principal histórica.
"""
import json
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits
import dlm_painel_log_aic as base
from dlm_inferencia_banda_regra_v3 import dk_cov, interval
ROOT=base.ROOT
OUT=ROOT/'outputs/tables/dlm_inferencia_banda_regra_v3'

def run():
 d=pd.read_csv(ROOT/'data/processed/df_tcc_2013_2024.csv',sep=';',encoding='utf-8-sig')
 d['data_base']=pd.to_datetime(d.data_base);d=d.sort_values(['uf','data_base']).reset_index(drop=True)
 a=pd.read_csv(ROOT/'data/raw/atlas_desastres/atlas.csv',sep=';',encoding='latin1',low_memory=False,usecols=['Cod_Cobrade','Data_Evento','Sigla_UF'])
 dates=pd.to_datetime(a.Data_Evento,format='%d/%m/%Y',errors='raise')
 mask=dates.between('2013-01-01','2024-12-31')&a.Cod_Cobrade.astype(int).astype(str).str.startswith(('12','13','14'))
 counts=a.loc[mask].assign(uf=a.loc[mask].Sigla_UF.str.strip(),data_base=dates[mask].dt.to_period('M').dt.to_timestamp()).groupby(['uf','data_base']).size()
 d['total_climatico']=counts.reindex(pd.MultiIndex.from_frame(d[['uf','data_base']]),fill_value=0).to_numpy()
 selections=pd.read_csv(base.OUT/'selecao_K.csv');old=pd.read_csv(OUT/'resultados.csv');rows=[];acf=[]
 for sel in selections.to_dict('records'):
  meta={k:sel[k] for k in ['periodo','exposicao','nivel','rotulo','K']}
  if not np.isfinite(sel['K']):
   for L in [3,4,6,12,18,24]:
    for ep in ['beta0','soma0K','soma1K','conjunto0K','conjunto1K']:
     rows.append({**meta,'L':L,'covariancia':'DK'+str(L),'endpoint':ep,'p_selecao':np.nan,'status':'bloqueada pela regra de suporte'})
   continue
  k=int(sel['K']);base.K=k
  q=base.transformed(d,sel['exposicao'],sel['periodo']).dropna(subset=['y']+['x'+str(j) for j in range(25)]).reset_index(drop=True)
  f=base.fit(q)
  for L in [3,4,6,12,18,24]:
   V=dk_cov(f,L);df=f['T']-1
   for ep,C in [('beta0',np.eye(k+1)[0]),('soma0K',np.ones(k+1)),('soma1K',np.r_[0,np.ones(k)])]:
    z=base.contrast(f['b'],V,C,df);lo,hi=interval(z['estimate'],z['se'],df,24)
    rows.append({**meta,'L':L,'covariancia':'DK'+str(L),'T':f['T'],'L_T':L/f['T'],'endpoint':ep,**z,'p_selecao':min(1,24*z['p']),'low_selecao':lo,'high_selecao':hi})
   betas=[base.contrast(f['b'],V,C,df) for C in np.eye(k+1)]
   for ep,start,m in [('conjunto0K',0,324),('conjunto1K',1,300)]:
    ps=[z['p'] for z in betas[start:]]
    rows.append({**meta,'L':L,'covariancia':'DK'+str(L),'T':f['T'],'L_T':L/f['T'],'endpoint':ep,'p':min(ps),'p_selecao':min(1,m*min(ps)),'status':'calculado'})
   # Validação independente contra a implementação de statsmodels.
   import statsmodels.api as sm
   from statsmodels.stats.sandwich_covariance import cov_nw_groupsum
   fit=sm.OLS(f['y'],f['X']).fit()
   expected=cov_nw_groupsum(fit,nlags=L,time=pd.factorize(q.data_base,sort=True)[0],use_correction=False)*f['n']/(f['n']-f['pt'])
   assert np.max(np.abs(V-expected))<1e-10
  # Score mensal do contraste soma0K: é HAC dos scores, não ACF de x.
  C=np.ones(k+1)
  monthly=np.vstack([f['X'][q.data_base.eq(t)].T@f['u'][q.data_base.eq(t)] for t in sorted(q.data_base.unique())])
  s=monthly@f['bread']@C;s=s-s.mean();den=s@s
  for lag in range(1,25):
   acf.append({**meta,'lag':lag,'T':f['T'],'acf_score_soma':float(s[lag:]@s[:-lag]/den),'referencia_descritiva':1.96/np.sqrt(f['T'])})
 r=pd.DataFrame(rows)
 for keys,g in r.groupby(['periodo','nivel','covariancia','endpoint']):
  r.loc[g.index,'p_Holm_familia']=multipletests(g.p_selecao.fillna(1),method='holm')[1]
 for L in [6,12]:
  a1=r[r.L.eq(L)].sort_values(['periodo','exposicao','endpoint']);b1=old[old.covariancia.eq('DK'+str(L))].sort_values(['periodo','exposicao','endpoint'])
  assert np.allclose(a1.p_Holm_familia,b1.p_Holm_familia,atol=1e-12,equal_nan=True)
 r.to_csv(OUT/'sensibilidade_banda_DK.csv',index=False,encoding='utf-8-sig')
 pd.DataFrame(acf).to_csv(OUT/'acf_scores_mensais.csv',index=False,encoding='utf-8-sig')
 report={'bandas':[3,4,6,12,18,24],'aplicacoes_estimadas':39,'covariancias_conferidas_statsmodels':234,'leitura_principal':'DK_regra principal: L3 pré/L4 total; sensibilidades exploratórias, sem escolher pelo p','ressalva':'L24/T60=0.4; sensibilidade não certifica validade finita; não controla escolha da banda','hash_codigo':base.sha(__file__),'hash_outputs':{n:base.sha(OUT/n) for n in ['sensibilidade_banda_DK.csv','acf_scores_mensais.csv']}}
 (OUT/'auditoria_banda_DK.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(r[r.status.eq('calculado')].groupby('L').apply(lambda z:int((z.p_Holm_familia<.05).sum()),include_groups=False))
 print(r[(r.endpoint=='soma0K')&(r.p_Holm_familia<.05)][['L','periodo','rotulo','p_Holm_familia']].to_string(index=False))
if __name__=='__main__':
 with threadpool_limits(limits=1):run()
