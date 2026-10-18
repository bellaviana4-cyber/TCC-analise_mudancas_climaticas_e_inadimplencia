"""Verificação independente da proteção de seleção e preservação dos modelos."""
import json
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from dlm_inferencia_banda_regra_v3 import ROOT,OUT,bandwidth,dk_cov
import dlm_painel_log_aic as base

def verify():
 manifest=json.loads((OUT/'manifest.json').read_text())
 for path,h in manifest['inputs'].items():assert base.sha(ROOT/path)==h,path
 assert base.sha(ROOT/'src/dlm_inferencia_banda_regra_v3.py')==manifest['codigo']
 for name,h in manifest['outputs'].items():assert base.sha(OUT/name)==h,name
 r=pd.read_csv(OUT/'resultados.csv');p=pd.read_csv(OUT/'perfis.csv');c=pd.read_csv(OUT/'candidatos_conferidos.csv');old=pd.read_csv(base.OUT/'resultados.csv');sel=pd.read_csv(base.OUT/'selecao_K.csv')
 assert len(r)==840 and r.status.eq('calculado').sum()==780
 assert len(c)==39*24 and c.escolhido.sum()==39
 for keys,g in c.groupby(['periodo','exposicao']):
  assert list(g.K)==list(range(1,25)) and g.N.nunique()==1
  expected=sel[(sel.periodo==keys[0])&(sel.exposicao==keys[1])].iloc[0].K
  assert g.loc[g.escolhido,'K'].iloc[0]==expected
 scalar=r[r.endpoint.isin(['beta0','soma0K','soma1K'])&r.status.eq('calculado')]
 assert np.allclose(scalar.p_selecao,np.minimum(1,24*scalar.p))
 half=stats.t.ppf(1-.05/(2*24),scalar.df)*scalar.se
 assert np.allclose(scalar.low_selecao,scalar.estimate-half) and np.allclose(scalar.high_selecao,scalar.estimate+half)
 assert np.all(scalar.low_selecao<=scalar.low) and np.all(scalar.high_selecao>=scalar.high)
 for keys,g in r.groupby(['periodo','nivel','covariancia','endpoint']):
  assert len(g)=={'Central':1,'Grupo':4,'Tipologia':16}[keys[1]]
  for meth,col in [('holm','p_Holm_familia'),('fdr_bh','q_BH_selecao'),('fdr_by','q_BY_selecao')]:assert np.allclose(g[col],multipletests(g.p_selecao.fillna(1),method=meth)[1])
 for _,g in r.groupby(['periodo','covariancia']):assert np.allclose(g.p_Holm_global105,multipletests(g.p_selecao.fillna(1),method='holm')[1])
 assert r.loc[~r.status.eq('calculado'),'p_selecao'].isna().all()
 for cov in ['CR1','DK6']:
  x=scalar[scalar.covariancia==cov].merge(old,on=['periodo','exposicao','covariancia','endpoint'],suffixes=('_v2','_old'))
  assert np.allclose(x.K_v2,x.K_old) and np.allclose(x.estimate_v2,x.estimate_old,atol=1e-12) and np.allclose(x.se_v2,x.se_old,atol=1e-12)
 coeff=pd.read_csv(OUT/'coeficientes_todos_K.csv')
 for row in r[r.endpoint.str.startswith('conjunto')&r.status.eq('calculado')].to_dict('records'):
  z=coeff[(coeff.periodo==row['periodo'])&(coeff.exposicao==row['exposicao'])&(coeff.covariancia==row['covariancia'])&(coeff.K==row['K'])]
  if row['endpoint']=='conjunto1K':z=z[z.lag>0]
  mult=324 if row['endpoint']=='conjunto0K' else 300
  assert np.isclose(row['p_selecao'],min(1,mult*z.p.min()))
  assert np.isclose(row['estimate'],(z.estimate/z.se).abs().max())
 # Banda é função apenas do calendário comum; mesmos valores em todas exposições.
 rule=r[r.covariancia.eq('DK_regra')&r.status.eq('calculado')]
 assert set(rule.loc[rule.periodo.eq('Pré'),'T'])=={60}
 assert set(rule.loc[rule.periodo.eq('Total'),'T'])=={119}
 assert set(rule.loc[rule.periodo.eq('Pré'),'L'])=={3}
 assert set(rule.loc[rule.periodo.eq('Total'),'L'])=={4}
 assert all(row.L==bandwidth(row.T) for row in rule.itertuples())
 # Comparação da covariância DK com statsmodels usando um painel sintético
 # de T60/T119 e K1/K24: inclui correção de todos efeitos fixos.
 from statsmodels.stats.sandwich_covariance import cov_nw_groupsum
 import statsmodels.api as sm
 rngcov=np.random.default_rng(7306)
 for T in [60,119]:
  for k in [1,24]:
   q=pd.DataFrame({'uf':np.repeat(sorted(base.UFS),T),'data_base':np.tile(pd.date_range('2000-01-01',periods=T,freq='MS'),27)})
   z=rngcov.standard_normal((27*T,k+2));A=base.residualize(q,z);X=A[:,1:];y=A[:,0]
   fit=sm.OLS(y,X).fit();p_total=27+T-1+k+1
   f={'q':q,'X':X,'u':fit.resid,'bread':np.linalg.inv(X.T@X),'n':len(q),'pt':p_total}
   actual=dk_cov(f,bandwidth(T))
   expected=cov_nw_groupsum(fit,nlags=bandwidth(T),time=pd.factorize(q.data_base,sort=True)[0],use_correction=False)*len(q)/(len(q)-p_total)
   assert np.max(np.abs(actual-expected))<1e-10
 # Todos resultados DK6/DK12/CR1 iguais à v2, incluindo ajustes.
 previous=pd.read_csv(ROOT/'outputs/tables/dlm_inferencia_selecao_v2/resultados.csv')
 merged=r[r.covariancia.isin(['DK6','DK12','CR1'])].merge(previous,on=['periodo','exposicao','endpoint','covariancia'],suffixes=('_new','_v2'))
 assert len(merged)==630
 for col in ['K','estimate','p_selecao','p_Holm_familia','q_BH_selecao']:
  assert np.allclose(merged[col+'_new'],merged[col+'_v2'],atol=1e-12,equal_nan=True),col
 # Simulação de mecanismo, não calibração empírica do painel/AIC.
 # Seleção adversa max |Z| entre 24 contrastes normais, correlacionados.
 rng=np.random.default_rng(20261007);sim=[]
 for rho in [0,.5,.95]:
  z=np.sqrt(rho)*rng.standard_normal((50000,1))+np.sqrt(1-rho)*rng.standard_normal((50000,24))
  maxabs=np.abs(z).max(axis=1);naive=(maxabs>stats.norm.ppf(.975)).mean();protected=(maxabs>stats.norm.ppf(1-.05/(2*24))).mean()
  assert protected<.055
  sim.append({'rho':rho,'replicacoes':50000,'erro_sem_protecao':naive,'erro_com_protecao':protected,'objetivo':'validar mecanismo de união sob testes normais válidos; não validar CR1/DK ou AIC do painel'})
 pd.DataFrame(sim).to_csv(OUT/'validacao_simulacao.csv',index=False)
 checks={'linhas_resultados':len(r),'candidatos':len(c),'K_AIC_preservado':True,'banda_somente_T':True,'L_pre3_total4':True,'DK_statsmodels_sintetico':True,'v2_preservada':True,'coeficientes_preservados':True,'protecao24':True,'intervalos_ampliados':True,'conjuntos_sem_Wald':True,'familias_BH_BY_Holm':True,'simulacao_union_bound':True,'limite':'checks de programação e mecanismo; não provam pressupostos do painel'}
 (OUT/'validacao.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
 print(json.dumps(checks,ensure_ascii=False));print(pd.DataFrame(sim).to_string(index=False))
if __name__=='__main__':verify()
