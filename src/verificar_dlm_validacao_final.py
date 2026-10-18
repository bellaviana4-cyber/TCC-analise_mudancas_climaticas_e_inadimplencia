"""Testes de propriedades independentes da validação final."""
import json
import numpy as np
import pandas as pd
from numpy.testing import assert_allclose
from dlm_validacao_final import *
from patsy import dmatrix

def verify():
 checks=[]
 def check(name,fn):fn();checks.append(dict(verificacao=name,passou=True))
 def source():
  cp=json.loads((PREV/'checkpoint.json').read_text())
  for name,h in cp['arquivos'].items():assert r.sha(ROOT/name)==h
 check('Primeira revisão intacta e hashes íntegros',source)
 def meta():
  v=pd.read_csv(OUT/'multiverse_corrigida.csv');s=v[v.metodo=='spline'];assert_allclose(s.J,s['rank']);assert v[v.metodo=='irrestrito'].n_parametros_exposicao.eq(v[v.metodo=='irrestrito'].K+1).all();assert v[v.metodo=='almon'].q_almon.eq(2).all();assert v[v.metodo=='almon'].n_parametros_exposicao.eq(3).all()
 check('Metadados de spline/Almon/irrestrito correspondem à dimensão',meta)
 def shifts():
  d=r.load_panel();q=r.lag_frame(d,np.arange(len(d)))
  for _,g in q.groupby('uf'):
   assert g.data_base.is_monotonic_increasing;assert np.all(np.diff(g.data_base.dt.to_period('M').astype(int))==1)
   for k in range(1,13):assert_allclose(g[f'x{k}'].iloc[k:],g.x.iloc[:-k]);assert g[f'x{k}'].iloc[:k].isna().all()
   for k in range(1,4):assert_allclose(g[f'lead{k}'].iloc[:-k],g.x.iloc[k:])
 check('Todos os lags/leads, ordenação e calendário',shifts)
 def calendar_fail():
  d=r.load_panel()
  for dd in [d.iloc[::-1],d[d.data_base.ne(pd.Timestamp('2015-03-01'))]]:
   try:calendar_lags(dd,np.ones(len(dd)))
   except ValueError:continue
   raise AssertionError('Calendário inválido aceito')
 check('Rejeita calendário fora de ordem/com lacuna antes de shift',calendar_fail)
 def season():
  f=load_main('Pré','total_desastres');ff=rebuild(f,seasonal=True);q=f['q'];D=dmatrix('0+C(uf):C(month)+C(t)',dict(uf=q.uf.to_numpy(),month=q.data_base.dt.month.to_numpy(),t=q.data_base.astype(str).to_numpy()));D=np.asarray(D);D=D[:,linalg.qr(D,mode='economic',pivoting=True)[2][:np.linalg.matrix_rank(D)]];X=np.column_stack([f['Z'],D]);fit=OLS(q.y,X).fit();assert_allclose(ff['b'],fit.params[:3],atol=1e-9);assert_allclose(D.T@ff['X'],0,atol=1e-8);assert ff['absorbed']==np.linalg.matrix_rank(D)
 check('Sazonalidade UF: projeção e rank equivalem a FE explícitos',season)
 def contrast_support():
  f=load_main('Pré','tipo_onda_de_frio');s=support(f,f['contrasts']['acumulado']);assert s['ufs_janela']==6 and s['ufs_x0']==4;assert_allclose(s['top_leverage'],.906765,atol=1e-6)
  f2=f.copy();f2['X']=f['X']*np.array([2,5,.3]);f2['bread']=np.linalg.inv(f2['X'].T@f2['X']);s2=support(f2,f['contrasts']['acumulado']*np.array([2,5,.3]));assert_allclose(s['neff_contraste'],s2['neff_contraste'],atol=1e-9)
 check('Suporte da janela e invariância do contraste à escala',contrast_support)
 def national_gap():
  z,X,B=national_design('Total','tipo_onda_de_frio');keep=z.index.year!=2020;V=hac_calendar(X[keep],OLS(z.y[keep],X[keep]).fit().resid,z.index[keep],12);assert np.linalg.eigvalsh(V).min()>-1e-8
  assert z.loc['2021-01-01','x1']==z.loc['2020-12-01','x0'];assert z.loc['2021-01-01','x1']!=z.loc['2019-12-01','x0'] or z.loc['2020-12-01','x0']==z.loc['2019-12-01','x0']
 check('HAC e lags em calendário com lacuna',national_gap)
 def dynamic_test():
  B=r.basis();b=np.r_[0,np.zeros(3),.5];b[1]=1;out=dynamic(b,B,1);inc=B@b[1:4];assert_allclose(out[1],inc[1]+.5*out[0]);assert_allclose(out[13],.5*out[12]);assert_allclose(dynamic(b[:-1],B,0)[13:],0)
 check('Resposta dinâmica: propagação AR e cauda após lag12',dynamic_test)
 def dynamic_variance():
  B=r.basis();b=np.r_[0,[.2,.3,.1],.5];h=12;jac=dynamic_jacobian(b,B,1)[h];powers=np.arange(h,-1,-1);expected=np.zeros(5);expected[1:4]=(.5**powers)@B;expected[-1]=np.sum(powers[ powers>0 ]*.5**(powers[powers>0]-1)*(B@b[1:4])[powers>0]);assert_allclose(jac,expected,atol=1e-7)
  V=np.eye(5)*.02+np.ones((5,5))*.01;assert_allclose(jac@V@jac,expected@V@expected,atol=1e-8);assert abs(jac@V@jac-jac@np.diag(np.diag(V))@jac)>1e-5
 check('Delta nacional: derivadas AR/exposição e covariâncias cruzadas',dynamic_variance)
 def external():
  d=pd.read_csv(OUT/'validacao_bootstrap_externa.csv');assert len(d)==6;assert d.passou.all();assert d.max_diff_stat.max()<1e-5
 check('Bootstrap externo escalares e refits conjuntos independentes',external)
 def cr2():
  d=pd.read_csv(OUT/'cr2.csv');assert d.id.nunique()==140;old=pd.read_csv(PREV/'cr2.csv');a=d[(d.especificacao=='Principal')&(d.endpoint=='acumulado')];b=old[(old.design=='main')&(old.endpoint=='acumulado')];merged=a.merge(b,on=['periodo','coluna']);assert_allclose(merged.p_x,merged.p_y,atol=1e-8);assert_allclose(merged.df_x,merged.df_y,atol=1e-8);valid=d.status.eq('calculado');assert d.loc[valid,'df'].gt(0).all();assert d.loc[~valid,'p'].isna().all();assert d.loc[valid,'p'].between(0,1).all()
 check('CR2: 140 modelos reconciliados e indisponibilidade explícita',cr2)
 def intervals():
  d=pd.read_csv(OUT/'bootstrap_intervalos.csv');assert len(d)==11;assert d.resolucao.gt(0).all();limited=~d.status.str.contains('não limitado');assert (d.loc[limited,'low']<=d.loc[limited,'high']).all();assert d.loc[~limited,'low'].isna().all()
 check('Inversão bootstrap: resolução e regiões reportadas',intervals)
 def ranks():
  x=pd.read_csv(OUT/'bootstrap_checado.csv');assert len(x)==278;assert x.B.ge(4999).all();assert x.loc[x.singular.gt(0),'p'].isna().all();assert x.loc[x.status.eq('calculado'),'singular'].eq(0).all()
 check('Rank por sorteio:278hipóteses sem pseudoinversa silenciosa',ranks)
 save(pd.DataFrame(checks),'validacao');return pd.DataFrame(checks)
if __name__=='__main__':print(verify().to_string(index=False))
