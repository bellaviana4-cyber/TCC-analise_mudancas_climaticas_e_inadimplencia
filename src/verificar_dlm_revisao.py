"""Invariant checks. No test requires a category to be significant."""
from pathlib import Path
import numpy as np
import pandas as pd
from numpy.testing import assert_allclose
from dlm_revisao import *

def verify():
 checks=[]
 def check(name,fn):fn();checks.append({'verificacao':name,'passou':True})
 d=load_panel();e=get_exps()
 def lags():
  q=lag_frame(d,np.arange(len(d)));assert q.groupby('uf').head(1).x1.isna().all();assert q.groupby('uf').tail(1).lead1.isna().all()
  for _,g in q.groupby('uf'):
   assert_allclose(g.x1.iloc[1:],g.x.iloc[:-1]);assert_allclose(g.lead1.iloc[:-1],g.x.iloc[1:])
 check('Lags e leads: valores e limites por UF',lags)
 def dedup():
  a=pd.DataFrame({'uf':['SC']*4,'mun':[1,1,2,1],'date':['2019-01-01']*4,'code':[1,1,1,2]});assert len(a.drop_duplicates(['uf','mun','date','code']))==3
  audit=pd.read_csv(OUT/'auditoria_resumo.csv');assert audit.registros.iloc[0]-audit.ocorrencias_municipais.iloc[0]==audit.repeticoes_chave.iloc[0]
 check('Chave municipal preserva municípios e códigos diferentes',dedup)
 def recon():
  for c in exposure_columns(d):assert_allclose(d[c],e[c]['A'],atol=0)
  assert pd.read_csv(OUT/'reconciliacao_uf_mes.csv').ok.all()
 check('Atlas reconciliado em todas as células UF-mês',recon)
 def spline():
  rng=np.random.default_rng(1)
  for J in [3,4]:
   B=basis(12,J);theta=rng.normal(size=J);L=rng.normal(size=(50,13));V=np.eye(J)*.3+np.ones((J,J))*.04
   assert_allclose((L@B)@theta,L@(B@theta));VB=B@V@B.T;C=np.tril(np.ones((13,13)));c=C[-1]@B
   assert_allclose(C[-1]@VB@C[-1],c@V@c);assert_allclose((C@B@theta)[-1],np.sum(B@theta));assert np.linalg.eigvalsh(VB).min()>-1e-10
 check('Spline, reconstrução beta, covariância e C(h)',spline)
 def inter():
  rng=np.random.default_rng(2);B=basis();b=rng.normal(size=6);V=np.eye(6);c=B.sum(0);pre=np.r_[c,c*0];post=np.r_[c,c];diff=np.r_[c*0,c]
  assert_allclose((post-pre)@b,diff@b);assert_allclose((post-pre)@V@(post-pre),diff@V@diff)
 check('Contrastes pré, pós e diferença',inter)
 def weights():
  w=pd.read_csv(OUT/'pesos_credito.csv').set_index('uf').peso_fixo_2013;assert (w>0).all();assert_allclose(w.sum(),1)
  ww=d.uf.map(w);assert ww.groupby(d.uf).nunique().max()==1
  base=d[d.ano==2013].groupby('uf').carteira_ativa_total.mean();assert_allclose(w.sort_index(),(base/base.sum()).sort_index())
 check('Pesos fixos e período-base',weights)
 def neff():
  dd=pd.DataFrame({'uf':['A','B'],'data_base':pd.to_datetime(['2013-01-01']*2)})
  assert_allclose(support(dd,[1,1])['n_eff'],2);assert_allclose(support(dd,[1,0])['n_eff'],1)
 check('N_eff uniforme e concentrado',neff)
 def fdr():
  rr=pd.DataFrame({'p':[.01,.04,.5]});rr=fdr_table(rr,['p'],4);assert_allclose(rr.q_global_p,[.04,.08,2/3])
 check('BH preserva família planejada',fdr)
 def fwl():
  from statsmodels.regression.linear_model import OLS
  q=lag_frame(d,e['total_desastres']['C_prop']);f=model(q,basis());qq=f['q'];D=pd.get_dummies(qq.uf,drop_first=True,dtype=float);T=pd.get_dummies(qq.data_base,drop_first=True,dtype=float)
  full=np.column_stack([np.ones(len(qq)),f['Z'],D,T]);fit=OLS(qq.y.to_numpy(),full).fit();assert_allclose(f['b'],fit.params[1:4],atol=1e-10)
 check('Absorção FE equivale a dummies explícitas',fwl)
 def wild():
  # Compare fast bootstrap with direct null-imposed refitting/reabsorption, same 19 draws.
  q=lag_frame(d,e['tipo_onda_de_frio']['C_prop']);f=model(q,basis());R=np.atleast_2d(f['contrasts']['acumulado']);b=f['b'];inv=f['bread'];b0=b-inv@R.T@np.linalg.inv(R@inv@R.T)@(R@b)
  u0=f['y']-f['X']@b0;g=f['q'].uf.to_numpy();G=np.unique(g);rng=np.random.default_rng(SEED);obs=float((R@b).T@np.linalg.inv(R@f['V']@R.T)@(R@b));cnt=0
  for W in rng.choice([-1.,1.],size=(19,len(G))):
   perturb=u0*np.array([W[np.where(G==v)[0][0]] for v in g]);ystar=f['X']@b0+residualize(f['q'],perturb[:,None])[:,0];bs=inv@f['X'].T@ystar;us=ystar-f['X']@bs;V=cr1(f['X'],us,g,f['absorbed']);tt=float((R@bs).T@np.linalg.inv(R@V@R.T)@(R@bs));cnt+=tt>=obs-1e-12
  assert_allclose(bootstrap(f,R,19)[0],(cnt+1)/20)
 check('WCR11 rápido equivale a reestimação sob H0 com FE',wild)
 def loo():
  a=pd.read_csv(OUT/'onda_frio_leave_out.csv');assert len(a)==56
  assert (a[a.retirada.str.contains(' + ',regex=False)].UFs==25).all();assert (a[~a.retirada.str.contains(' + ',regex=False)].UFs==26).all()
  for per in ['Total','Pré']:assert a[a.periodo==per].retirada.nunique()==28
 check('Leave-out: 27 individuais e duas dominantes por período',loo)
 def integrity():
  r=pd.read_csv(OUT/'principais.csv');assert len(r)==46;assert r.K.eq(12).all();assert r.J.isin([3,4]).all();assert r.boot_B.ge(4999).all();assert (r["rank"]==r.J).all()
  for col in r:
   if col.endswith('_p'):assert r[col].dropna().between(0,1).all()
  p=pd.read_csv(OUT/'perfis.csv');assert p.groupby(['periodo','coluna','tipo_perfil']).size().eq(13).all()
  assert_allclose(p[p.tipo_perfil=='C'].sort_values(['periodo','coluna','lag']).groupby(['periodo','coluna']).tail(1).estimate,r.sort_values(['periodo','coluna']).acumulado_cluster_estimate)
 check('Saídas: horizonte, rank, bootstrap, probabilidades e acumulado',integrity)
 def cross_language():
  r=pd.read_csv(OUT/'principais.csv');c=pd.read_csv(OUT/'cr2.csv');m=c[(c.design=='main')&(c.endpoint=='acumulado')].merge(r,on=['periodo','coluna'])
  assert len(m)==len(r);assert_allclose(m.estimate,m.acumulado_cluster_estimate,atol=1e-8)
  valid=c.status_inferencia.eq('calculado');assert c.loc[valid,'df'].gt(0).all();assert c.loc[valid,'p'].between(0,1).all()
  unavailable=~valid;assert c.loc[unavailable,'p'].isna().all()
 check('CR2: igualdade Python/R e indisponibilidade inferencial explícita',cross_language)
 def national_rate():
  x=d.groupby('data_base')[['carteira_ativa_total','carteira_inadimplencia_total']].sum();br=pd.read_csv(OUT/'taxa_nacional.csv')
  assert_allclose(br.taxa_br_ponderada,100*x.carteira_inadimplencia_total/x.carteira_ativa_total)
 check('Taxa nacional: razão de somas e não média simples',national_rate)
 save(pd.DataFrame(checks),'validacao');return pd.DataFrame(checks)
if __name__=='__main__':print(verify().to_string(index=False))
