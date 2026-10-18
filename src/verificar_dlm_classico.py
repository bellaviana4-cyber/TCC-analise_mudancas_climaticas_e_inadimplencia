"""Propriedades verificáveis do DLM clássico; falhas são explícitas."""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from patsy import dmatrix
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits
import dlm_classico as c

def verify():
 tests=[]
 def ok(name,condition):
  assert condition,name;tests.append(dict(teste=name,ok=True))
 d=c.r.load_panel();ex=c.r.get_exps();q=c.ordered_lags(d,ex['total_desastres']['C_prop'])
 for k in range(1,11):ok('lag calendário '+str(k),np.allclose(q[f'x{k}'],q.groupby('uf').x.shift(k),equal_nan=True))
 try:c.ordered_lags(d.iloc[::-1],ex['total_desastres']['C_prop'][::-1]);raise AssertionError('ordenação não recusada')
 except ValueError:tests.append(dict(teste='recusa calendário desordenado',ok=True))
 bad=d.drop(d.index[10]);x=ex['total_desastres']['C_prop'];
 try:c.ordered_lags(bad,np.delete(x,10));raise AssertionError('lacuna não recusada')
 except ValueError:tests.append(dict(teste='recusa lacuna antes dos shifts',ok=True))
 a=pd.read_csv(c.OUT/'auditoria_chaves.csv').iloc[0];ok('deduplicação somente B e cobertura invariante',a.A==40339 and a.B==40238 and a.C_invariante)
 m=pd.read_csv(c.OUT/'modelos.csv');ok('552 modelos e grade46×10',len(m)==552 and len(m[m.especificacao=='Principal'])==460)
 ok('parâmetros livres e metadados',((m.n_parametros_exposicao==m.K-m.lag_inicio+1)&(m['rank']==m.n_parametros_exposicao)).all() and m.J.isna().all())
 ok('amostra comum por exposição e período',m.groupby(['periodo','coluna'])[['N','data_inicio','data_fim']].nunique().max().max()==1)
 f=c.fit(q[q.data_base>=pd.Timestamp('2013-12-01')],10);Q=f['q'];D=np.asarray(dmatrix('1 + C(uf) + C(data_base)',Q));MM=np.column_stack([f['Z'],D]);fit=sm.OLS(Q.y.to_numpy(),MM).fit();ok('FWL igual a OLS com FE explícitos',np.max(abs(fit.params[:10]-f['b']))<1e-9)
 cc=c.r.contrast(f['b'],f['V'],np.ones(10),26);ok('acumulado usa covariâncias completas',np.isclose(cc['se']**2,f['V'].sum()))
 profiles=pd.read_csv(c.OUT/'perfis_cr1.csv');last=profiles.sort_values('lag').groupby(['periodo','coluna','especificacao','K']).tail(1);joined=last.merge(m,on=['periodo','coluna','especificacao','K']);ok('curva final igual acumulado',np.allclose(joined.C,joined.acumulado_estimate,atol=1e-10))
 for _,g in m[m.especificacao=='Principal'].groupby('K'):
  expected=multipletests(np.r_[g.acumulado_p.fillna(1),[1,1]],method='fdr_bh')[1][:46];ok('BH48 K'+str(g.K.iloc[0]),np.allclose(expected,g.q_acumulado_p))
 boot=pd.read_csv(c.OUT/'bootstrap.csv');ok('bootstrap92 sem singularidade e B>=4999',len(boot)==92 and (boot.singular==0).all() and (boot.B>=4999).all())
 cr=pd.read_csv(c.OUT/'cr2.csv');ok('CR2 verificado para138 matrizes',cr.id.nunique()==138)
 ok('inferência indisponível permanece NA',cr.loc[cr.status!='calculado','p'].isna().all())
 scalar=cr[cr.endpoint=='acumulado'].merge(m[m.K==10],on=['periodo','coluna','especificacao']);ok('coeficientes Python/R',np.allclose(scalar.estimate,scalar.acumulado_estimate,atol=1e-8))
 c.save(pd.DataFrame(tests),'validacao');return pd.DataFrame(tests)

if __name__=='__main__':
 with threadpool_limits(limits=1):print(verify().to_string(index=False))
