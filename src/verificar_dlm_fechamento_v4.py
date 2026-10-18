# AUDITORIA REJEITADA: a calibração de dependência sob autocorrelação apresentou
# tamanho empírico excessivo. Não usar seus p-valores para inferir dependência
# ou escolher covariância; preservada apenas como evidência da verificação.
"""Conferência da reprojeção TWFE, estatística e mecanismo de calibração."""
import json
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits
import dlm_fechamento_diagnosticos_v4 as a
from dlm_inferencia_banda_regra_v3 import bandwidth


def verify():
 r=pd.read_csv(a.OUT/'dependencia_calibrada.csv');s=pd.read_csv(a.OUT/'resumo_diagnosticos.csv')
 assert len(r)==117 and len(s)==39
 assert set(r.B)=={1999} and set(r.bloco_medio)=={3,6,12}
 assert ((r.p_diagnostico>=1/2000)&(r.p_diagnostico<=1)).all()
 for _,g in r.groupby(['periodo','nivel','bloco_medio']):
  m={'Central':1,'Grupo':4,'Tipologia':16}[g.nivel.iloc[0]]
  expected=multipletests(np.r_[g.p_diagnostico,np.ones(m-len(g))],method='holm')[1][:len(g)]
  assert np.allclose(expected,g.p_Holm_diagnostico)
 # Checar estatística contra pandas e projeção contra dummies explícitas.
 rng=np.random.default_rng(4107);N,T,k=27,24,3
 uf=np.repeat(np.arange(N),T);time=np.tile(np.arange(T),N)
 Xraw=rng.normal(size=(N*T,k));q=pd.DataFrame({'uf':uf,'data_base':time})
 X=a.base.residualize(q,Xraw);bread=np.linalg.inv(X.T@X)
 U=rng.normal(size=(7,N,T));R=a.project(U,X,bread)
 Z=np.column_stack([np.ones(N*T),pd.get_dummies(uf,drop_first=True,dtype=float),pd.get_dummies(time,drop_first=True,dtype=float),Xraw])
 beta=np.linalg.lstsq(Z,U.reshape(7,-1).T,rcond=None)[0];explicit=(U.reshape(7,-1).T-Z@beta).T.reshape(7,N,T)
 assert np.max(abs(R-explicit))<1e-10
 mean2,meanabs=a.metrics(R)
 for j in range(7):
  rho=pd.DataFrame(R[j].T).corr().to_numpy()[np.triu_indices(N,1)]
  assert np.isclose(mean2[j],np.mean(rho**2)) and np.isclose(meanabs[j],np.mean(abs(rho)))
 manifest=json.loads((a.OUT/'manifest.json').read_text())
 for p,h in manifest['inputs'].items():assert a.base.sha(a.ROOT/p)==h
 for p,h in manifest['outputs'].items():assert a.base.sha(a.OUT/p)==h
 assert manifest['codigo']==a.base.sha(a.__file__)
 # Experimento pequeno de funcionamento sob nulidade conhecida, não certificado.
 oldB=a.B;a.B=199;sim=[]
 for T in [60,119]:
  N=27;q=pd.DataFrame({'uf':np.repeat(sorted(a.base.UFS),T),'data_base':np.tile(np.arange(T),N)})
  X=a.base.residualize(q,rng.normal(size=(N*T,2)));bread=np.linalg.inv(X.T@X)
  f={'X':X,'bread':bread}
  for rho in [0,.5]:
   rejected=0
   for rep in range(50):
    noise=rng.normal(size=(N,T+200))*np.linspace(.5,2,N)[:,None];E=np.zeros_like(noise)
    for t in range(1,T+200):E[:,t]=rho*E[:,t-1]+noise[:,t]
    E=a.project(E[:,200:][None],X,bread)[0]
    observed=a.metrics(E[None])[0][0];draws,_=a.null_bootstrap(E,f,6,rng)
    p=(1+np.sum(draws>=observed))/(a.B+1);rejected+=p<.05
   rate=rejected/50
   sim.append({'T':T,'rho_AR1':rho,'replicacoes':50,'B':a.B,'bloco_medio':6,'taxa_rejeicao_nulo':rate,'limite':'experimento pequeno heteroscedástico estacionário; não valida cenário real, seleção AIC ou cobertura DK'})
 a.B=oldB
 pd.DataFrame(sim).to_csv(a.OUT/'simulacao_mecanismo_diagnostico.csv',index=False)
 checks={'aplicacoes':39,'calibracoes':117,'FWL_dummies_max_diff':float(np.max(abs(R-explicit))),'estatistica_pandas':True,'Holm_recalculado':True,'hashes':True,'banda_final_pre':bandwidth(60),'banda_final_total':bandwidth(119),'limite':'verificações computacionais; não prova validade finita, exogeneidade ou estacionariedade'}
 (a.OUT/'validacao.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
 print(json.dumps(checks,ensure_ascii=False));print(pd.DataFrame(sim).to_string(index=False))
if __name__=='__main__':
 with threadpool_limits(limits=1):verify()
