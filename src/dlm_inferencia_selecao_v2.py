"""Inferência simultânea conservadora para modelos selecionados por AIC.

Bonferroni sobre a grade planejada protege seleção arbitrária do horizonte,
desde que a inferência pontual de cada projeção seja válida. Não implementa
PoSI exato, inferência seletiva condicional, bootstrap ou causalidade.
"""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits
import dlm_painel_log_aic as base

ROOT=base.ROOT
OUT=ROOT/'outputs/tables/dlm_inferencia_selecao_v2'
ALPHA=.05
M_SCALAR=24
M_BETA=sum(k+1 for k in range(1,25)) # 324
M_LAG=sum(k for k in range(1,25)) # 300
M_SCENARIOS=2*sum(k+2 for k in range(1,25)) # 696

def interval(est,se,df,m):
 critical=stats.t.ppf(1-ALPHA/(2*m),df)
 return float(est-critical*se),float(est+critical*se)

def dk_cov(f,L):
 q=f['q'];scores=np.vstack([f['X'][q.data_base.eq(t)].T@f['u'][q.data_base.eq(t)] for t in sorted(q.data_base.unique())])
 meat=scores.T@scores
 for l in range(1,L+1):
  cross=scores[l:].T@scores[:-l]
  meat+=(1-l/(L+1))*(cross+cross.T)
 return f['n']/(f['n']-f['pt'])*f['bread']@meat@f['bread']

def run():
 OUT.mkdir(parents=True,exist_ok=True)
 # Ler dados sem sobrescrever qualquer resultado histórico.
 d=pd.read_csv(ROOT/'data/processed/df_tcc_2013_2024.csv',sep=';',encoding='utf-8-sig')
 d['data_base']=pd.to_datetime(d.data_base);d=d.sort_values(['uf','data_base']).reset_index(drop=True)
 a=pd.read_csv(ROOT/'data/raw/atlas_desastres/atlas.csv',sep=';',encoding='latin1',low_memory=False,usecols=['Cod_Cobrade','Data_Evento','Sigla_UF'])
 dates=pd.to_datetime(a.Data_Evento,format='%d/%m/%Y',errors='raise')
 mask=dates.between('2013-01-01','2024-12-31')&a.Cod_Cobrade.astype(int).astype(str).str.startswith(('12','13','14'))
 counts=a.loc[mask].assign(uf=a.loc[mask].Sigla_UF.str.strip(),data_base=dates[mask].dt.to_period('M').dt.to_timestamp()).groupby(['uf','data_base']).size()
 d['total_climatico']=counts.reindex(pd.MultiIndex.from_frame(d[['uf','data_base']]),fill_value=0).to_numpy()
 selection=pd.read_csv(base.OUT/'selecao_K.csv');historical=pd.read_csv(base.OUT/'resultados.csv')
 candidate_reference=pd.read_csv(base.OUT/'candidatos_AIC.csv')
 rows=[];profiles=[];scenarios=[];candidates=[];allcoeff=[]
 for sel in selection.to_dict('records'):
  per,e=sel['periodo'],sel['exposicao'];meta={k:sel[k] for k in ['periodo','exposicao','nivel','rotulo']}
  if not np.isfinite(sel['K']):
   for cov in ['DK6','DK12','CR1']:
    for ep in ['beta0','soma0K','soma1K','conjunto0K','conjunto1K']:
     rows.append({**meta,'K':None,'covariancia':cov,'endpoint':ep,'status':'bloqueada pela regra de suporte','p_selecao':None,'estimate':None})
   continue
  full=base.transformed(d,e,per)
  q=full.dropna(subset=['y']+['x'+str(k) for k in range(25)]).reset_index(drop=True)
  assert base.support(full,e)['elegivel'] and base.support(q,e)['elegivel']
  chosen=int(sel['K']);fits={};aics={}
  for k in range(1,25):
   base.K=k
   try:f=base.fit(q)
   except (AssertionError,np.linalg.LinAlgError):continue
   aic=f['n']*(np.log(2*np.pi)+1+np.log(f['u']@f['u']/f['n']))+2*f['pt']
   ref=candidate_reference[(candidate_reference.periodo==per)&(candidate_reference.exposicao==e)&(candidate_reference.K==k)].iloc[0]
   assert ref.status=='estimado' and np.isclose(ref.AIC,aic,atol=1e-7)
   fits[k]=f;aics[k]=aic
   candidates.append({**meta,'K':k,'AIC':aic,'N':f['n'],'T':f['T'],'escolhido':k==chosen})
   for cov,V,df in [('CR1',f['V'],26),('DK6',f['DK'],f['T']-1),('DK12',dk_cov(f,12),f['T']-1)]:
    for lag in range(k+1):
     z=base.contrast(f['b'],V,np.eye(k+1)[lag],df)
     allcoeff.append({**meta,'K':k,'lag':lag,'covariancia':cov,**z})
  assert chosen==min(k for k,v in aics.items() if v<=min(aics.values())+1e-8)
  f=fits[chosen];k=chosen
  for cov,V,df in [('CR1',f['V'],26),('DK6',f['DK'],f['T']-1),('DK12',dk_cov(f,12),f['T']-1)]:
   cm={**meta,'K':k,'covariancia':cov,'N':f['n'],'T':f['T'],'df':df}
   for ep,C in [('beta0',np.eye(k+1)[0]),('soma0K',np.ones(k+1)),('soma1K',np.r_[0,np.ones(k)])]:
    z=base.contrast(f['b'],V,C,df);lo,hi=interval(z['estimate'],z['se'],df,M_SCALAR)
    if cov!='DK12':
     old=historical[(historical.periodo==per)&(historical.exposicao==e)&(historical.covariancia==cov)&(historical.endpoint==ep)].iloc[0]
     assert np.isclose(old.estimate,z['estimate'],atol=1e-12) and np.isclose(old.se,z['se'],atol=1e-12)
    rows.append({**cm,**z,'endpoint':ep,'multiplicador_selecao':M_SCALAR,'p_selecao':min(1,M_SCALAR*z['p']),'low_selecao':lo,'high_selecao':hi,'estatistica':'contraste t; Bonferroni nos 24 K'})
   beta=[]
   for lag in range(k+1):
    z=base.contrast(f['b'],V,np.eye(k+1)[lag],df);beta.append(z)
    cum=base.contrast(f['b'],V,(np.arange(k+1)<=lag).astype(float),df)
    blo,bhi=interval(z['estimate'],z['se'],df,M_BETA);clo,chi=interval(cum['estimate'],cum['se'],df,M_BETA)
    profiles.append({**cm,'lag':lag,'beta':z['estimate'],'beta_se':z['se'],'beta_low_selecao':blo,'beta_high_selecao':bhi,'C':cum['estimate'],'C_se':cum['se'],'C_low_selecao':clo,'C_high_selecao':chi,'multiplicador':M_BETA})
   for ep,start,m in [('conjunto0K',0,M_BETA),('conjunto1K',1,M_LAG)]:
    b=beta[start:];pmin=min(v['p'] for v in b)
    rows.append({**cm,'endpoint':ep,'estimate':max(abs(v['estimate']/v['se']) for v in b),'p':pmin,'p_selecao':min(1,m*pmin),'multiplicador_selecao':m,'status':'calculado','estatistica':'max |t|; união dos coeficientes em todos K; não Wald F'})
   for name in ['aumento persistente D: 0 para 1','pulso de um mês D: 0 para 1 para 0']:
    for h in range(k+2):
     c=np.log(2)*((np.arange(k+1)<=h).astype(float)-(np.arange(k+1)<=h-1).astype(float) if name.startswith('pulso') else (np.arange(k+1)<=h).astype(float))
     if np.any(c):
      z=base.contrast(f['b'],V,c,df);lo,hi=interval(z['estimate'],z['se'],df,M_SCENARIOS)
     else:z={'estimate':0};lo=hi=0
     scenarios.append({**cm,'cenario':name,'h':h,'estimate_log':z['estimate'],'pct':100*np.expm1(z['estimate']),'low_pct_selecao':100*np.expm1(lo),'high_pct_selecao':100*np.expm1(hi),'multiplicador':M_SCENARIOS})
  print(per,e,'K AIC',chosen,'conferido; seleção protegida',flush=True)
 r=pd.DataFrame(rows)
 for keys,g in r.groupby(['periodo','nivel','covariancia','endpoint']):
  ps=g.p_selecao.fillna(1).to_numpy()
  for method,col in [('holm','p_Holm_familia'),('fdr_bh','q_BH_selecao'),('fdr_by','q_BY_selecao')]:r.loc[g.index,col]=multipletests(ps,method=method)[1]
  r.loc[g.index,'n_familia']=len(g)
  r.loc[g.index,'familia']=' | '.join(keys)
 # Ajuste global dos cinco endpoints e das 21 exposições por período/covariância.
 for keys,g in r.groupby(['periodo','covariancia']):
  assert len(g)==105
  r.loc[g.index,'p_Holm_global105']=multipletests(g.p_selecao.fillna(1),method='holm')[1]
 for name,t in [('resultados',r),('perfis',pd.DataFrame(profiles)),('cenarios',pd.DataFrame(scenarios)),('candidatos_conferidos',pd.DataFrame(candidates)),('coeficientes_todos_K',pd.DataFrame(allcoeff))]:t.to_csv(OUT/(name+'.csv'),index=False,encoding='utf-8-sig')
 manifest={'metodo':'Bonferroni simultâneo entre todos K planejados; Holm entre exposições; DK6 principal, DK12 sensibilidade, CR1 comparação','K_final':'exclusivamente escolhido por AIC, sem reexpansão da amostra','M_scalar':M_SCALAR,'M_coef_completo':M_BETA,'M_coef_defasado':M_LAG,'M_cenarios':M_SCENARIOS,'familias':'periodo × nivel × covariancia × endpoint; global105 também reportado','limite':'proteção de seleção depende da validade uniforme dos testes pontuais; CR1/DK e t são aproximações, não PoSI exato nem inferência seletiva condicional','inputs':{str(p.relative_to(ROOT)):base.sha(p) for p in [ROOT/'data/processed/df_tcc_2013_2024.csv',ROOT/'data/raw/atlas_desastres/atlas.csv',base.OUT/'selecao_K.csv']},'codigo':base.sha(__file__),'outputs':{p.name:base.sha(p) for p in OUT.glob('*.csv')}}
 manifest['codigo_base']=base.sha(ROOT/'src/dlm_painel_log_aic.py')
 manifest['protocolo']=base.sha(ROOT/'docs/dlm_inferencia_selecao_v2_protocolo.md')
 manifest['capitulo_v2']=base.sha(ROOT/'tcc/capitulos/c3_metodologias_tg_referencia_v2.tex')
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 print(r[(r.endpoint=='soma0K')&(r.p_Holm_familia<.05)][['periodo','rotulo','covariancia','K','p_selecao','p_Holm_familia','q_BH_selecao']].to_string(index=False))
 return r

if __name__=='__main__':
 with threadpool_limits(limits=1):run()
