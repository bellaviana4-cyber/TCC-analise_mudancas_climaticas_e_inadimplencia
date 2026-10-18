# AUDITORIA REJEITADA: a calibração de dependência sob autocorrelação apresentou
# tamanho empírico excessivo. Não usar seus p-valores para inferir dependência
# ou escolher covariância; preservada apenas como evidência da verificação.
"""Diagnóstico de dependência residual com calibração sob nulidade independente.
Bootstrap estacionário independente por UF: preserva aproximadamente memória
marginal, rompe sincronização entre UFs e reestima TWFE/coeficientes do mesmo K.
Diagnóstico aproximado sob estacionariedade/memória curta, não teste exato,
nem reprodução automática de Juodis-Reese/Pesaran-Xie. Não seleciona covariância
ou modelo pelo resultado; p diagnósticos não são p dos efeitos de desastres.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits
import dlm_painel_log_aic as base
ROOT=base.ROOT;OUT=ROOT/'outputs/tables/dlm_auditoria_rejeitada_v4'
B=1999;SEED=2026100704

def load():
 d=pd.read_csv(ROOT/'data/processed/df_tcc_2013_2024.csv',sep=';',encoding='utf-8-sig')
 d['data_base']=pd.to_datetime(d.data_base);d=d.sort_values(['uf','data_base']).reset_index(drop=True)
 a=pd.read_csv(ROOT/'data/raw/atlas_desastres/atlas.csv',sep=';',encoding='latin1',low_memory=False,usecols=['Cod_Cobrade','Data_Evento','Sigla_UF'])
 dates=pd.to_datetime(a.Data_Evento,format='%d/%m/%Y',errors='raise')
 mask=dates.between('2013-01-01','2024-12-31')&a.Cod_Cobrade.astype(int).astype(str).str.startswith(('12','13','14'))
 counts=a.loc[mask].assign(uf=a.loc[mask].Sigla_UF.str.strip(),data_base=dates[mask].dt.to_period('M').dt.to_timestamp()).groupby(['uf','data_base']).size()
 d['total_climatico']=counts.reindex(pd.MultiIndex.from_frame(d[['uf','data_base']]),fill_value=0).to_numpy()
 return d

def metrics(E):
 # E: B x UF x T; séries centradas. Soma dos quadrados não cancela sinais.
 z=E-E.mean(axis=2,keepdims=True)
 ss=np.sum(z*z,axis=2)
 R=np.einsum('bit,bjt->bij',z,z)/np.sqrt(ss[:,:,None]*ss[:,None,:])
 i,j=np.triu_indices(E.shape[1],1);rho=R[:,i,j]
 return np.mean(rho*rho,axis=1),np.mean(abs(rho),axis=1)

def project(U,X,bread):
 # Reproduz efeitos de UF/mês-ano e estimação dos beta sem reconstruir dummies.
 z=U-U.mean(axis=2,keepdims=True)-U.mean(axis=1,keepdims=True)+U.mean(axis=(1,2),keepdims=True)
 n=z.shape;flat=z.reshape(n[0],-1)
 flat=flat-(flat@X@bread)@X.T
 return flat.reshape(n)

def null_bootstrap(E,f,ell,rng):
 N,T=E.shape;out=[];absolute=[]
 for start in range(0,B,100):
  size=min(100,B-start);idx=np.empty((size,N,T),dtype=int)
  idx[:,:,0]=rng.integers(T,size=(size,N))
  for t in range(1,T):
   reset=rng.random((size,N))<1/ell
   idx[:,:,t]=np.where(reset,rng.integers(T,size=(size,N)),(idx[:,:,t-1]+1)%T)
  U=E[np.arange(N)[None,:,None],idx]
  V=project(U,f['X'],f['bread']);a,b=metrics(V);out.extend(a);absolute.extend(b)
 return np.array(out),np.array(absolute)

def run():
 OUT.mkdir(parents=True,exist_ok=True);d=load();selection=pd.read_csv(base.OUT/'selecao_K.csv')
 rows=[];summary=[];acf=[];checks=[]
 for sid,sel in enumerate(selection.to_dict('records')):
  if not np.isfinite(sel['K']):continue
  k=int(sel['K']);base.K=k
  q=base.transformed(d,sel['exposicao'],sel['periodo']).dropna(subset=['y']+['x'+str(j) for j in range(25)]).reset_index(drop=True)
  f=base.fit(q);N,T=f['G'],f['T'];E=f['u'].reshape(N,T)
  assert np.allclose(project(f['y'].reshape(1,N,T),f['X'],f['bread'])[0],E,atol=1e-10)
  a,b=metrics(E[None]);meta={p:sel[p] for p in ['periodo','exposicao','nivel','rotulo','K']}
  lb=pd.read_csv(base.OUT/'autocorrelacao_uf.csv');z=lb[(lb.periodo==sel['periodo'])&(lb.exposicao==sel['exposicao'])&(lb.lag==12)]
  summary.append({**meta,'T':T,'UFs':N,'rho_abs_media':float(b[0]),'rho_quadrado_media':float(a[0]),'LB12_nominal_UFs':int(z.p.lt(.05).sum()),'LB12_Holm_UFs':int((multipletests(z.p,method='holm')[1]<.05).sum()),'max_VIF':float(np.diag(np.linalg.inv(np.corrcoef(f['X'],rowvar=False))).max())})
  for ell in [3,6,12]:
   rng=np.random.default_rng(SEED+sid*100+ell)
   sim,sima=null_bootstrap(E,f,ell,rng);p=(1+int((sim>=a[0]).sum()))/(B+1)
   rows.append({**meta,'T':T,'bloco_medio':ell,'B':B,'seed':SEED+sid*100+ell,'observado_rho2':float(a[0]),'nulo_rho2_mediana':float(np.median(sim)),'nulo_rho2_q95':float(np.quantile(sim,.95)),'observado_abs':float(b[0]),'nulo_abs_mediana':float(np.median(sima)),'p_diagnostico':p,'mc_se':float(np.sqrt(p*(1-p)/(B+1))),'status':'calibração aproximada; estacionariedade/memória curta; fixed K; não pós-seleção formal'})
  checks.append({**meta,'FWL_reprojetado':True,'B_por_bloco':B,'residuos_uf_media_max':float(abs(E.mean(axis=1)).max()),'residuos_tempo_media_max':float(abs(E.mean(axis=0)).max())})
  print(sel['periodo'],sel['rotulo'],'diagnóstico calibrado',flush=True)
 r=pd.DataFrame(rows)
 for _,g in r.groupby(['periodo','nivel','bloco_medio']):
  # Inclui família planejada mesmo com categorias não elegíveis.
  m={'Central':1,'Grupo':4,'Tipologia':16}[g.nivel.iloc[0]]
  ps=np.r_[g.p_diagnostico.to_numpy(),np.ones(m-len(g))]
  r.loc[g.index,'p_Holm_diagnostico']=multipletests(ps,method='holm')[1][:len(g)]
 for name,t in [('dependencia_calibrada',r),('resumo_diagnosticos',pd.DataFrame(summary)),('validacao_projecao',pd.DataFrame(checks))]:t.to_csv(OUT/(name+'.csv'),index=False,encoding='utf-8-sig')
 manifest={'B':B,'seed':SEED,'blocos_medios':[3,6,12],'metodo':'bootstrap estacionário marginal independente por UF, reprojeção TWFE e beta; estatística omnibus média rho²','limite':'calibração aproximada condicionada a K e desenho; sob memória curta/estacionariedade; não valida exogeneidade/raiz unitária nem inferência seletiva','papel':'diagnóstico complementar; sem regra de escolher covariância por preteste','inputs':{str(p.relative_to(ROOT)):base.sha(p) for p in [ROOT/'data/processed/df_tcc_2013_2024.csv',ROOT/'data/raw/atlas_desastres/atlas.csv',base.OUT/'selecao_K.csv']},'codigo':base.sha(__file__),'outputs':{p.name:base.sha(p) for p in OUT.glob('*.csv')}}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 print(r[r.exposicao.eq('total_climatico')][['periodo','bloco_medio','observado_rho2','nulo_rho2_q95','p_diagnostico','p_Holm_diagnostico']].to_string(index=False))
if __name__=='__main__':
 with threadpool_limits(limits=1):run()
