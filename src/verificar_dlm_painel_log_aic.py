"""Verifica seleção, amostra, lags, inferência e execução sem reestimar Granger."""
import json
import numpy as np,pandas as pd
from statsmodels.stats.multitest import multipletests
from dlm_painel_log_aic import ROOT,OUT,K_MAX,sha,transformed

def verify():
 manifest=json.loads((OUT/'manifest.json').read_text())
 for path,h in manifest['inputs'].items():assert sha(ROOT/path)==h,path
 for path,h in manifest['outputs'].items():assert sha(ROOT/path)==h,path
 assert manifest['codigo']==sha(ROOT/'src/dlm_painel_log_aic.py')
 assert manifest['protocolo']==sha(ROOT/'docs/dlm_painel_log_aic_protocolo.md')
 # Calendário determinístico independente, com diferenças distintas por UF.
 dates=pd.date_range('2013-01-01',periods=60,freq='MS')
 fixture=pd.concat([pd.DataFrame({'uf':uf,'data_base':dates,'taxa_inadimplencia':np.exp(scale*np.arange(60)/100),'D':scale*np.arange(60)**2}) for uf,scale in [('AC',1),('SP',3)]],ignore_index=True)
 q=transformed(fixture,'D','Total')
 for uf,z in q.groupby('uf'):
  raw=fixture[fixture.uf.eq(uf)];expected=np.diff(np.log1p(raw.D))
  assert np.allclose(z.y.iloc[1:],.01 if uf=='AC' else .03)
  for k in range(K_MAX+1):
   assert z['x'+str(k)].iloc[:k+1].isna().all()
   assert np.allclose(z['x'+str(k)].iloc[k+1:],expected[:len(expected)-k])
 common=q.dropna(subset=['y']+['x'+str(k) for k in range(K_MAX+1)])
 assert common.data_base.min()==pd.Timestamp('2015-02-01')
 candidates=pd.read_csv(OUT/'candidatos_AIC.csv');sel=pd.read_csv(OUT/'selecao_K.csv');models=pd.read_csv(OUT/'modelos.csv');support=pd.read_csv(OUT/'amostras_suporte.csv');results=pd.read_csv(OUT/'resultados.csv')
 assert len(candidates)==42*24 and len(sel)==42 and len(models)==39 and len(results)==420
 assert (models.G==27).all() and support.UFs_modelo.eq(27).all()
 assert support.N_efetivo.eq(support.periodo.map({'Pré':1620,'Total':3213})).all()
 assert support.primeira_equacao.eq('2015-02-01').all()
 for keys,g in candidates.groupby(['periodo','exposicao']):
  assert list(g.K)==list(range(1,25)) and g.N.nunique()==1 and g['T'].nunique()==1
  assert g.primeira_equacao.eq('2015-02-01').all()
  available=g[g.status.eq('estimado')].sort_values('K')
  selection=sel[(sel.periodo==keys[0])&(sel.exposicao==keys[1])].iloc[0]
  if not len(available):assert pd.isna(selection.K) and not g.selecionado.any();continue
  n=available.N.to_numpy();rss=available.SSR.to_numpy();pt=27+available['T']-1+available.K+1
  assert np.allclose(available.parametros_totais,pt)
  aic=n*(np.log(2*np.pi)+1+np.log(rss/n))+2*pt
  assert np.allclose(available.AIC,aic)
  assert np.all(np.diff(rss)<=1e-12), 'SQR cresce em modelos aninhados na mesma amostra'
  minimum=available.AIC.min();chosen=int(available.loc[available.AIC.le(minimum+1e-8),'K'].min())
  assert selection.K==chosen and g.selecionado.sum()==1
  assert int(g.loc[g.selecionado,'K'].iloc[0])==chosen
  assert np.allclose(available.delta_AIC,available.AIC-minimum)
  model=models[(models.periodo==keys[0])&(models.exposicao==keys[1])].iloc[0]
  assert model.K==chosen and model.N==g.N.iloc[0]
 for keys,g in results.groupby(['periodo','nivel','covariancia','endpoint']):
  assert len(g)=={'Central':1,'Grupo':4,'Tipologia':16}[keys[1]]
  assert np.allclose(g.q_BH,multipletests(g.p.fillna(1),method='fdr_bh')[1])
 assert results.loc[results.status.ne('calculado') & results.status.ne('covariância conjunta sem posto'),'p'].isna().all()
 covariance=pd.read_csv(OUT/'covariancias.csv')
 for keys,g in covariance.groupby(['periodo','exposicao','covariancia']):
  V=g.pivot(index='lag1',columns='lag2',values='cov').to_numpy()
  row=results[(results.periodo==keys[0])&(results.exposicao==keys[1])&(results.covariancia==keys[2])&(results.endpoint=='soma0K')].iloc[0]
  assert V.shape==(int(row.K)+1,int(row.K)+1)
  assert np.allclose(V,V.T,atol=1e-12) and np.linalg.eigvalsh(V).min()>-1e-12
  assert np.isclose(V.sum(),row.se**2)
 profiles=pd.read_csv(OUT/'perfis.csv');sc=pd.read_csv(OUT/'cenarios.csv')
 for keys,g in sc.groupby(['periodo','exposicao','covariancia','cenario']):
  g=g.sort_values('h');beta=profiles[(profiles.periodo==keys[0])&(profiles.exposicao==keys[1])&(profiles.covariancia==keys[2])].sort_values('lag').beta_estimate.to_numpy()
  pulse=np.zeros(len(beta)+1);pulse[0]=np.log(2)
  if keys[3].startswith('pulso'):pulse[1]=-np.log(2)
  expected=np.convolve(pulse,beta)[:len(pulse)]
  assert np.allclose(g.resposta_delta_log_I,expected)
  assert np.allclose(g.resposta_log_I_acumulada,np.cumsum(expected))
  assert np.allclose(g.variacao_relativa_I_pct,100*np.expm1(np.cumsum(expected)))
 v=pd.read_csv(OUT/'validacao.csv')
 assert len(v)==4 and set(v.K)=={1,24} and v.passou.all()
 assert np.allclose(v.AIC_dummies,v.AIC_FWL,atol=1e-8)
 assert (v.coef_FWL_dummies_max_diff<1e-9).all() and (v.cov_CR1_dummies_max_diff<1e-9).all() and (v.DK_statsmodels_max_diff<1e-10).all()
 nb=json.loads((ROOT/'notebooks/23_dlm_painel_selecao_aic_1a24.ipynb').read_text());code=[c for c in nb['cells'] if c['cell_type']=='code']
 assert len(code)==9 and [c['execution_count'] for c in code]==list(range(1,10))
 assert not any(o['output_type']=='error' for c in code for o in c['outputs'])
 report=(ROOT/'outputs/reports/relatorio_dlm_painel_log_aic.html').read_text()
 assert 'src="https://' not in report and '__DATA__' not in report
 print(json.dumps({'status':'passou','candidatos':len(candidates),'modelos':len(models),'amostra_comum':'passou','AIC_minimo_contagem_FE':'passou','lags_24_UF':'passou','BH':'passou','cov_soma':'passou','convolucao':'passou','dummies_CR1_DK_AIC':'passou','notebook_executado':len(code)},ensure_ascii=False))
if __name__=='__main__':verify()
