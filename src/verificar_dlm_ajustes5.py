"""Verificações numéricas da extensão; reconstrução nacional independente do construtor."""
import json,hashlib
import numpy as np,pandas as pd
from statsmodels.regression.linear_model import OLS
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits
import dlm_ajustes5 as a

def verify():
 n=0;load=lambda name:pd.read_csv(a.OUT/(name+'.csv'))
 P=load('painel');N=load('nacional');J=load('nacional_conjunto');E=load('nacional_igualdade')
 for d in [P,N]:
  assert np.allclose(d.p_busca,np.minimum(d.M*d.p,1),rtol=1e-9,atol=1e-12);assert (d.low<=d.estimate).all() and (d.high>=d.estimate).all();n+=3
 for d,groups in [(P,[(g,48) for _,g in P.groupby('L')]),(N,[(N[N.principal],96),(N[~N.principal],48)]),(J,[(J[J.principal],48),(J[~J.principal],48)]),(E,[(E,24)])]:
  for g,size in groups:
   for method,suffix in [('fdr_bh','BH'),('fdr_by','BY')]:
    x=multipletests(np.r_[g.p_busca.fillna(1),np.ones(size-len(g))],method=method)[1][:len(g)];assert np.allclose(g['p_busca_'+suffix],x);n+=1
 assert len(P)==138 and len(N[N.principal])==91 and len(J[J.principal])==45;assert (load('conferencia_DK').max_diferenca<1e-8).all();n+=4
 baseline=pd.read_csv(a.ROOT/'outputs/tables/dlm_selecionado/painel.csv');base=P[P.L==12].merge(baseline,on=['periodo','coluna'],suffixes=('_novo','_antigo'));assert np.array_equal(base.K_novo,base.K_antigo);assert np.allclose(base.estimate_novo,base.estimate_antigo,atol=1e-9);n+=2
 d,ex=a.ds.inputs();agg=d.groupby('data_base')[['carteira_ativa_total','carteira_inadimplencia_total']].sum();rate=100*agg.carteira_inadimplencia_total/agg.carteira_ativa_total;mac=load('controles_macro').set_index('data');mac.index=pd.to_datetime(mac.index)
 for (per,col,mode),g in N.groupby(['periodo','coluna','modo']):
  m=g.iloc[0];xx=pd.DataFrame({'data':d.data_base,'x':ex[col]['C']}).groupby('data').x.sum()/5570;z=pd.DataFrame({'I':rate,'x':xx}).loc[slice(*a.r.PERIODS[per])];z['y']=z.I.diff()
  for k in range(1,11):z['x'+str(k)]=z.x.shift(k)
  for j in [1,2]:z['y'+str(j)]=z.y.shift(j)
  z=z.join(mac[['selic_mensal_lag1','ipca_mensal_lag1','atividade_crescimento_lag1']]).dropna();K=int(m.K);ar=int(m.AR)
  controls=np.column_stack([np.eye(12)[z.index.month-1][:,1:],np.arange(len(z))/12,z[['selic_mensal_lag1','ipca_mensal_lag1','atividade_crescimento_lag1']]])
  masks=[np.ones(len(z),dtype=bool)] if mode=='Comum' else [np.asarray(z.index<'2020-03-01'),np.asarray((z.index>='2020-03-01')&(z.index<'2022-01-01')),np.asarray(z.index>='2022-01-01')];mat=[controls];indices=[];offset=controls.shape[1]
  for mask in masks:
   cols=np.column_stack([np.ones(len(z)),z[['y'+str(j) for j in range(1,ar+1)]],z[['x'+str(k) for k in range(1,K+1)]]]);mat.append(cols*mask[:,None]);indices.append(np.arange(offset+1+ar,offset+1+ar+K));offset+=cols.shape[1]
  fit=OLS(z.y.to_numpy(),np.column_stack(mat)).fit();rob=fit.get_robustcov_results(cov_type='HAC',maxlags=12,use_correction=True,use_t=True);cov=rob.cov_params()
  assert np.isclose(fit.bic,m.BIC);n+=1
  R=np.eye(offset)[np.concatenate(indices)];pj=float(rob.f_test(R).pvalue);ref=J[(J.periodo==per)&(J.coluna==col)&(J.modo==mode)].iloc[0];assert np.isclose(pj,ref.p,rtol=1e-6,atol=1e-12);n+=1
  if mode=='Regimes':
   RR=[]
   for ix in indices[1:]:
    for i,j in zip(indices[0],ix):c=np.zeros(offset);c[j]=1;c[i]=-1;RR.append(c)
   pe=float(rob.f_test(np.asarray(RR)).pvalue);ref=E[E.coluna==col].iloc[0];assert np.isclose(pe,ref.p,rtol=1e-6,atol=1e-12);n+=1
  for (_,row),ix in zip(g.iterrows(),indices):
   c=np.zeros(offset);c[ix]=1;out=a.contrast(fit.params,cov,c,fit.df_resid,int(row.M))
   for key in ['estimate','se','p','low','high','p_busca']:assert np.isclose(out[key],row[key],atol=1e-9);n+=1
 assert load('nacional_candidatos').query("selecionado").status.eq('admissível').all();n+=1
 assert load('taxonomia').registros.iloc[0]==40339;assert len(mac)==144 and mac.notna().all().all();n+=2
 manifest=json.loads((a.OUT/'manifest.json').read_text())
 for name,sha in manifest.items():
  path=a.ROOT/'docs/dlm_ajustes5_protocolo.md' if name=='protocolo_sha256' else a.OUT/name;assert hashlib.sha256(path.read_bytes()).hexdigest()==sha;n+=1
 result={'verificacoes':n,'status':'aprovado','painel_DK_independente':138,'nacionais_reconstruidos':len(N.groupby(['periodo','coluna','modo'])),'regra':'projeções/contrastes e multiplicidade; validade inferencial continua aproximada'};(a.OUT/'validacao.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(result)
if __name__=='__main__':
 with threadpool_limits(limits=1):verify()
