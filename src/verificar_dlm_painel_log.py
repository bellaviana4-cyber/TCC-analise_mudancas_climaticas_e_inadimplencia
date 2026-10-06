"""Verificações essenciais dos artefatos e calendário/lag por UF."""
import json
import numpy as np,pandas as pd
from dlm_painel_log import ROOT,OUT,K,PERIODS,sha,transformed,fit
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits

def verify():
 manifest=json.loads((OUT/'manifest.json').read_text())
 for p,h in manifest['inputs'].items():assert sha(ROOT/p)==h,p
 for p,h in manifest['outputs'].items():assert sha(ROOT/p)==h,p
 assert manifest['codigo']==sha(ROOT/'src/dlm_painel_log.py') and manifest['protocolo']==sha(ROOT/'docs/dlm_painel_log_protocolo.md')
 # Determinístico, dois padrões distintos por UF; não é dado/modelo empírico.
 dates=pd.date_range('2013-01-01',periods=15,freq='MS');parts=[]
 for uf,scale in [('AC',1),('SP',3)]:
  z=pd.DataFrame({'uf':uf,'data_base':dates,'taxa_inadimplencia':np.exp(scale*np.arange(15)/100),'D':np.arange(15)*scale});parts.append(z)
 fixture=pd.concat(parts,ignore_index=True)
 q=transformed(fixture,'D','Total')
 for uf,z in q.groupby('uf'):
  raw=fixture[fixture.uf.eq(uf)];expected=np.diff(np.log1p(raw.D))
  assert np.allclose(z.x.iloc[1:],expected)
  for k in range(K+1):
   assert z['x'+str(k)].iloc[:k+1].isna().all()
   assert np.allclose(z['x'+str(k)].iloc[k+1:],expected[:len(expected)-k])
  assert np.allclose(z.y.iloc[1:],.01 if uf=='AC' else .03)
 r=pd.read_csv(OUT/'resultados.csv');m=pd.read_csv(OUT/'modelos.csv');s=pd.read_csv(OUT/'amostras_suporte.csv');assert len(m)==40 and len(s)==42 and (m.G==27).all()
 assert s.N_efetivo.eq(s.periodo.map({'Pré':2106,'Total':3699})).all()
 assert s.primeira_equacao.eq('2013-08-01').all();assert len(r)==42*10
 for keys,g in r.groupby(['periodo','nivel','covariancia','endpoint']):assert np.allclose(g.q_BH,multipletests(g.p.fillna(1),method='fdr_bh')[1])
 for keys,g in pd.read_csv(OUT/'covariancias.csv').groupby(['periodo','exposicao','covariancia']):
  V=g.pivot(index='lag1',columns='lag2',values='cov').to_numpy();row=r[(r.periodo==keys[0])&(r.exposicao==keys[1])&(r.covariancia==keys[2])&(r.endpoint=='soma0K')].iloc[0]
  assert np.allclose(V,V.T,atol=1e-12);assert np.isclose(V.sum(),row.se**2)
 p=pd.read_csv(OUT/'perfis.csv');sc=pd.read_csv(OUT/'cenarios.csv')
 for keys,g in sc.groupby(['periodo','exposicao','covariancia','cenario']):
  g=g.sort_values('h');beta=p[(p.periodo==keys[0])&(p.exposicao==keys[1])&(p.covariancia==keys[2])].sort_values('lag').beta_estimate.to_numpy();imp=np.zeros(8);imp[0]=np.log(2)
  if keys[3].startswith('pulso'):imp[1]=-np.log(2)
  expected=np.convolve(imp,beta)[:8];assert np.allclose(g.resposta_delta_log_I,expected);assert np.allclose(g.resposta_log_I_acumulada,np.cumsum(expected));assert np.allclose(g.variacao_relativa_I_pct,100*np.expm1(np.cumsum(expected)))
 nb=json.loads((ROOT/'notebooks/22_dlm_painel_diferencas_logaritmicas.ipynb').read_text());codes=[c for c in nb['cells'] if c['cell_type']=='code'];assert len(codes)==10 and [c['execution_count'] for c in codes]==list(range(1,11));assert not any(o['output_type']=='error' for c in codes for o in c['outputs'])
 v=pd.read_csv(OUT/'validacao.csv');assert v.passou.all() and (v.coef_FWL_dummies_max_diff<1e-9).all() and (v.DK_statsmodels_max_diff<1e-10).all()
 assert 'https://cdn' not in (ROOT/'outputs/reports/relatorio_dlm_painel_log.html').read_text()
 print(json.dumps({'status':'passou','modelos':40,'aplicacoes_planejadas':42,'celulas_notebook':10,'calendario_lags_UF':'passou','BH':'passou','cov_soma':'passou','cenarios_convolucao':'passou','hashes':'passou'},ensure_ascii=False))
if __name__=='__main__':
 with threadpool_limits(limits=1):verify()
