"""Revisão DLM: auditoria e estimação. Saídas históricas em dlm/ são imutáveis."""
from pathlib import Path
import json, hashlib, os, platform, warnings
import numpy as np
import pandas as pd
from scipy import stats, linalg
from patsy import dmatrix
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.stattools import adfuller, kpss
from dlm import load_panel, exposure_columns, exposure_label, exposure_level, LABELS
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/tables/dlm_revisao'
FIG=ROOT/'outputs/figures/dlm_revisao'
CACHE=ROOT/'data/interim/dlm_revisao'
SEED=20261003
PERIODS={'Total':('2013-01-01','2024-12-01'),'Pré':('2013-01-01','2020-01-01')}
MUNICIPIOS={'AC':22,'AL':102,'AP':16,'AM':62,'BA':417,'CE':184,'DF':1,'ES':78,'GO':246,'MA':217,'MT':141,'MS':79,'MG':853,'PA':144,'PB':223,'PR':399,'PE':185,'PI':224,'RJ':92,'RN':167,'RS':497,'RO':52,'RR':15,'SC':295,'SP':645,'SE':75,'TO':139}
assert sum(MUNICIPIOS.values())==5570

def save(df,name):
 OUT.mkdir(parents=True,exist_ok=True);tmp=OUT/(name+'.csv.tmp');df.to_csv(tmp,index=False,encoding='utf-8-sig');tmp.replace(OUT/(name+'.csv'));return df

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def analytical(code):
 c=str(int(code))
 if c.startswith(('12','13','14')):return 'Clima/hidrometeorologia'
 if c.startswith('2'):return 'Tecnológico/antrópico'
 if c.startswith('1'):return 'Natural não diretamente climático'
 return 'Código não classificado'

def masks(a,d):
 result={'total_desastres':np.ones(len(a),bool)}
 for c in exposure_columns(d)[1:]:
  key=c.split('_',1)[1];label=LABELS.get(key,key)
  result[c]=a['grupo_de_desastre' if c.startswith('grupo_') else 'descricao_tipologia'].eq(label).to_numpy()
 for label in sorted(a.classe_analitica.unique()):
  result['analitica_'+label]=a.classe_analitica.eq(label).to_numpy()
 return result

def support(d,x,events=None):
 x=np.asarray(x,float);z=pd.DataFrame({'uf':d.uf.to_numpy(),'t':d.data_base.to_numpy(),'x':x})
 s=z.groupby('uf').x.sum();s=s/s.sum() if s.sum()>0 else s*0
 tm=z.groupby('t').x.sum();tm=tm/tm.sum() if tm.sum()>0 else tm*0
 ss=s.sort_values(ascending=False);hhi=float((s*s).sum());ne=1/hhi if hhi else 0
 cells=int((x>0).sum());ufs=int(z.loc[z.x>0,'uf'].nunique());months=int(z.loc[z.x>0,'t'].nunique())
 within=float(z.groupby('uf').x.var().fillna(0).mean());top1=float(ss.iloc[0]);top2=float(ss.iloc[:2].sum())
 n_events=float(events.sum()) if events is not None else float(x.sum())
 if n_events<24 or cells<12 or ufs<5 or months<8 or within<=1e-16: status='não estimável'
 elif ne<5 or top1>.5 or top2>.8 or tm.max()>.25: status='exposição altamente concentrada'
 elif n_events>=100 and cells>=50 and ufs>=10 and months>=24 and ne>=10 and top1<=.3:status='estimável'
 else: status='estimável com ressalvas'
 return dict(eventos=n_events,soma_medida=float(x.sum()),uf_mes_positivos=cells,ufs_expostas=ufs,meses_positivos=months,top1=top1,top2=top2,hhi=hhi,n_eff=ne,hhi_temporal=float((tm*tm).sum()),top_mes=float(tm.max()),variacao_within=within,status=status,zeros=float((x==0).mean()),assimetria=float(stats.skew(x)) if np.std(x)>0 else np.nan,maximo=float(x.max()),mediana=float(np.median(x)),p95=float(np.quantile(x,.95)))

def audit():
 for p in (OUT,FIG,CACHE):p.mkdir(parents=True,exist_ok=True)
 d=load_panel();p=ROOT/'data/processed/df_tcc_2013_2024.parquet'
 if p.exists():
  b=pd.read_parquet(p).sort_values(['uf','data_base']).reset_index(drop=True)
  for c in d.select_dtypes('number'):assert np.allclose(d[c],b[c],equal_nan=True),c
 a=pd.read_csv(ROOT/'data/raw/atlas_desastres/atlas.csv',sep=';',encoding='latin1',low_memory=False)
 dates=pd.to_datetime(a.Data_Evento,format='%d/%m/%Y',errors='coerce');invalid=int(dates.isna().sum())
 a=a.assign(date=dates,linha_original=np.arange(len(a))+2);a=a[a.date.dt.year.between(2013,2024)].copy()
 a['data_base']=a.date.dt.to_period('M').dt.to_timestamp();a['uf']=a.Sigla_UF.str.strip();a['classe_analitica']=a.Cod_Cobrade.map(analytical)
 key=['uf','Cod_IBGE_Mun','date','Cod_Cobrade'];assert not a[key].isna().any().any()
 duplicates=a.duplicated(key,keep=False)
 # Preserve lineage locally; public audit is aggregated, not raw rows.
 a.loc[duplicates].to_csv(CACHE/'duplicidades_chave.csv',index=False)
 u=a.drop_duplicates(key).copy()
 key_conflicts=a.groupby(key).agg(grupos=('grupo_de_desastre','nunique'),tipos=('descricao_tipologia','nunique'))
 assert key_conflicts[['grupos','tipos']].max().max()==1,'Chave ambígua na taxonomia: revisar manualmente'
 tax=a.groupby(['descricao_tipologia','Cod_Cobrade','classe_analitica']).agg(grupos=('grupo_de_desastre',lambda x:'; '.join(sorted(x.unique()))),registros=('uf','size')).reset_index()
 tax['observacao']=tax.apply(lambda r:'Nome não corresponde ao código de onda de calor (13310)' if r.Cod_Cobrade==13310 and r.descricao_tipologia=='Chuvas Intensas' else ('Frente fria/ZC, não código de friagem/geada' if r.Cod_Cobrade==13120 and r.descricao_tipologia=='Onda de Frio' else ('Baixa umidade (14140), não separa onda de calor' if r.Cod_Cobrade==14140 else 'Classificação analítica não atribui causalidade climática')),axis=1)
 save(tax,'taxonomia_cobrade')
 index=pd.MultiIndex.from_frame(d[['uf','data_base']]);exps={};recon=[];metrics=[];correlations=[]
 for c,mask in masks(a,d).items():
  aa=a.loc[mask];uu=u[u.linha_original.isin(aa.linha_original)]
  raw=aa.groupby(['uf','data_base']).size().reindex(index,fill_value=0).to_numpy()
  unique=uu.groupby(['uf','data_base']).size().reindex(index,fill_value=0).to_numpy()
  territory=aa.groupby(['uf','data_base']).Cod_IBGE_Mun.nunique().reindex(index,fill_value=0).to_numpy()
  prop=territory/d.uf.map(MUNICIPIOS).to_numpy()
  assert np.all(prop<=1),c
  exps[c]={'A':raw,'B':unique,'C':territory,'C_prop':prop}
  if c in d:
   assert np.array_equal(raw,d[c].to_numpy()),f'Reconciliação por UF-mês falhou: {c}'
   recon.append({'coluna':c,'atlas':int(raw.sum()),'painel':int(d[c].sum()),'max_diferenca_uf_mes':int(np.max(abs(raw-d[c]))),'ok':True})
  for per,(start,end) in PERIODS.items():
   keep=d.data_base.between(start,end).to_numpy();dd=d.loc[keep]
   for measure,x in exps[c].items():metrics.append({'periodo':per,'coluna':c,'exposicao':label(c),'nivel':level(c),'medida':measure,**support(dd,x[keep],unique[keep])})
   for m1,m2 in [('A','B'),('A','C'),('B','C'),('A','C_prop')]:
    x,y=exps[c][m1][keep],exps[c][m2][keep]
    correlations.append(dict(periodo=per,coluna=c,medida1=m1,medida2=m2,pearson=np.corrcoef(x,y)[0,1],spearman=stats.spearmanr(x,y).statistic))
 np.savez_compressed(CACHE/'exposicoes.npz',**{c+'__'+m:v for c,mm in exps.items() for m,v in mm.items()})
 save(pd.DataFrame(recon),'reconciliacao_uf_mes');save(pd.DataFrame(metrics),'suporte');save(pd.DataFrame(correlations),'correlacao_medidas')
 save(pd.DataFrame([dict(registros=len(a),ocorrencias_municipais=len(u),repeticoes_chave=len(a)-len(u),linhas_em_chaves_repetidas=int(duplicates.sum()),duplicatas_exatas=int(a.drop(columns='linha_original').duplicated().sum()),protocolos_repetidos=int(a.Protocolo_S2iD.duplicated().sum()),datas_invalidas_base_completa=invalid)]),'auditoria_resumo')
 save(pd.DataFrame({'uf':list(MUNICIPIOS),'municipios_2022':list(MUNICIPIOS.values())}),'municipios_denominador')
 # Fixed baseline 2013 credit shares; positive and normalized across UF, not observation weights.
 base=d[d.data_base.dt.year.eq(2013)].groupby('uf').carteira_ativa_total.mean();w=base/base.sum()
 save(w.rename('peso_fixo_2013').reset_index(),'pesos_credito')
 cold=a[a.descricao_tipologia.eq('Onda de Frio')]
 rows=[]
 for per,(start,end) in PERIODS.items():
  cc=cold[cold.data_base.between(start,end)]
  for uf in d.uf.unique():rows.append(dict(periodo=per,uf=uf,registros=int(cc.uf.eq(uf).sum()),participacao=float(cc.uf.eq(uf).sum()/len(cc))))
 save(pd.DataFrame(rows),'onda_frio_uf')
 return d,exps

def label(c):
 return c[10:] if c.startswith('analitica_') else exposure_label(c)
def level(c):return 'Analítica' if c.startswith('analitica_') else exposure_level(c)

def get_exps():
 z=np.load(CACHE/'exposicoes.npz');out={}
 for k in z.files:
  c,m=k.rsplit('__',1);out.setdefault(c,{})[m]=z[k]
 return out

def basis(K=12,J=3,start=0,method='spline'):
 k=np.arange(start,K+1,dtype=float)
 if method=='irrestrito':return np.eye(len(k))
 if method=='almon':return np.column_stack([np.ones(len(k)),k/K,(k/K)**2])
 B=np.asarray(dmatrix(f'cr(k, df={J}) - 1',{'k':k}),float)
 assert B.shape==(len(k),J) and np.linalg.matrix_rank(B)==J
 return B

def lag_frame(d,x):
 q=d[['uf','data_base','regiao','taxa_inadimplencia','carteira_ativa_total','carteira_inadimplencia_total']].copy()
 q['y']=q.groupby('uf').taxa_inadimplencia.diff();q['x']=np.asarray(x)
 for k in range(13):q[f'x{k}']=q.groupby('uf').x.shift(k)
 for k in range(1,4):q[f'lead{k}']=q.groupby('uf').x.shift(-k)
 assert q.groupby('uf').head(1).x1.isna().all()
 assert q.groupby('uf').tail(1).lead1.isna().all()
 return q

def residualize(q,A,regional=False,weights=None):
 """Weighted FWL for balanced cross sections on any common set of dates."""
 a=pd.DataFrame(np.asarray(A,float)).reset_index(drop=True)
 uf=q.uf.reset_index(drop=True);t=q.data_base.reset_index(drop=True)
 if regional:t=q.regiao.reset_index(drop=True).astype(str)+'_'+t.astype(str)
 w=np.ones(len(q)) if weights is None else np.asarray(weights,float)
 assert pd.Series(w).groupby(uf).nunique().max()==1
 assert q.groupby('data_base').uf.nunique().nunique()==1
 # Each UF observed on identical dates. Weighted time/group means and UF means.
 unit=a.groupby(uf).transform('mean')
 wa=a.mul(w,axis=0);den=pd.Series(w).groupby(t).transform('sum')
 tm=wa.groupby(t).transform('sum').div(den,axis=0)
 if regional:
  rg=q.regiao.reset_index(drop=True);grand=wa.groupby(rg).transform('sum').div(pd.Series(w).groupby(rg).transform('sum'),axis=0)
 else:grand=np.average(a,axis=0,weights=w)
 return (a-unit-tm+grand).to_numpy()

def cr1(X,u,g,absorbed):
 ug=np.unique(g);scores=np.vstack([X[g==v].T@u[g==v] for v in ug]);bread=np.linalg.inv(X.T@X)
 factor=len(ug)/(len(ug)-1)*(len(g)-1)/(len(g)-X.shape[1]-absorbed)
 return factor*bread@scores.T@scores@bread

def dk(X,u,q,L=12):
 bread=np.linalg.inv(X.T@X);tt=q.data_base.to_numpy();times=np.sort(np.unique(tt))
 S=np.vstack([X[tt==v].T@u[tt==v] for v in times]);V=S.T@S
 # Calendar distance, not compressed row distance, matters after pandemic exclusion.
 for lag in range(1,L+1):
  ordinal=pd.DatetimeIndex(times).to_period('M').asi8; lookup={int(v):i for i,v in enumerate(ordinal)}
  pairs=[(i,lookup[int(v)-lag]) for i,v in enumerate(ordinal) if int(v)-lag in lookup]
  if pairs:
   G=sum(np.outer(S[i],S[j]) for i,j in pairs);V+=(1-lag/(L+1))*(G+G.T)
 return bread@V@bread

def contrast(b,V,c,df):
 est=float(c@b);se=float(np.sqrt(max(0,c@V@c)));p=float(2*stats.t.sf(abs(est/se),df)) if se>0 else np.nan
 crit=stats.t.ppf(.975,df);return dict(estimate=est,se=se,low=est-crit*se,high=est+crit*se,p=p,df=df)

def joint(b,V,R,df):
 v=R@V@R.T;q=np.linalg.matrix_rank(v);z=R@b
 if q<len(R):return np.nan
 return float(stats.f.sf(z@np.linalg.pinv(v)@z/q,q,df))

def model(q,B,start=0,K=12,regional=False,weighted=False,extra=None,ycol='y'):
 q=q.dropna(subset=['y']+[f'x{k}' for k in range(13)]).copy()
 Z=q[[f'x{k}' for k in range(start,K+1)]].to_numpy()@B
 R=np.eye(Z.shape[1]);contrasts={'acumulado':B.sum(0),'defasado':B[np.arange(start,K+1)>0].sum(0),'contemporaneo':B[0] if start==0 else np.zeros(B.shape[1])}
 profiles=B.copy()
 if extra=='leads':
  keep=q[[f'lead{k}' for k in range(1,4)]].notna().all(axis=1);q=q.loc[keep];Z=Z[keep.to_numpy()]
  Z=np.column_stack([Z,q[[f'lead{k}' for k in range(1,4)]].to_numpy()]);R=np.column_stack([np.zeros((3,B.shape[1])),np.eye(3)])
  contrasts={k:np.r_[v,np.zeros(3)] for k,v in contrasts.items()};profiles=np.column_stack([B,np.zeros((len(B),3))])
 if extra=='interaction':
  post=(q.data_base>=pd.Timestamp('2020-02-01')).to_numpy().astype(float)
  Z=np.column_stack([Z,Z*post[:,None]]);R=np.column_stack([np.zeros((B.shape[1],B.shape[1])),np.eye(B.shape[1])])
  c=B.sum(0);contrasts={'pre':np.r_[c,c*0],'pos':np.r_[c,c],'diferenca':np.r_[c*0,c]};profiles=np.column_stack([B,np.zeros_like(B)])
 w=np.ones(len(q))
 if weighted:
  wt=pd.read_csv(OUT/'pesos_credito.csv').set_index('uf').peso_fixo_2013;w=q.uf.map(wt).to_numpy()
 YX=residualize(q,np.column_stack([q[ycol],Z]),regional,w)
 y=YX[:,0]*np.sqrt(w);X=YX[:,1:]*np.sqrt(w[:,None])
 assert np.linalg.matrix_rank(X)==X.shape[1],'Matriz não identificável'
 bread=np.linalg.inv(X.T@X);b=bread@X.T@y;u=y-X@b
 G=q.uf.nunique();T=q.data_base.nunique();rr=q.regiao.nunique()
 absorbed=G+(rr*(T-1) if regional else T-1)
 V=cr1(X,u,q.uf.to_numpy(),absorbed);D=dk(X,u,q)
 n=len(q);p=absorbed+len(b);sse=float(u@u)
 out=dict(q=q,Z=Z,X=X,y=y,b=b,u=u,V=V,DK=D,bread=bread,B=profiles,base=B,contrasts=contrasts,R=R,absorbed=absorbed,regional=regional,weights=w,K=K,start=start,n=n,df=G-1,BIC=n*np.log(sse/n)+p*np.log(n),AIC=n*np.log(sse/n)+2*p,rank=np.linalg.matrix_rank(X),condition=float(np.linalg.cond(X)))
 return out

def bootstrap(f,R,B=4999,seed=SEED):
 """Exact score sufficient-statistic implementation of WCR11 with FE reabsorption."""
 X,y,b,bread=f['X'],f['y'],f['b'],f['bread'];q=f['q'];g=q.uf.to_numpy();ugs=np.unique(g);G=len(ugs)
 R=np.atleast_2d(R);b0=b-bread@R.T@np.linalg.pinv(R@bread@R.T)@(R@b)
 u0=y-X@b0;w=f['weights'];root=np.sqrt(w)
 U=np.column_stack([np.where(g==v,u0,0) for v in ugs])
 # Residualize in the original WLS scale, then restore sqrt(w).
 U=residualize(q,U/root[:,None],f['regional'],w)*root[:,None]
 T=np.stack([X[g==v].T@U[g==v] for v in ugs]);A=np.stack([X[g==v].T@X[g==v] for v in ugs])
 factor=G/(G-1)*(len(g)-1)/(len(g)-len(b)-f['absorbed'])
 V=f['V'];obs=float((R@b).T@np.linalg.pinv(R@V@R.T)@(R@b))
 rng=np.random.default_rng(seed);exceed=0;valid=0
 for lo in range(0,B,256):
  nr=min(256,B-lo);W=rng.choice([-1.,1.],size=(nr,G))
  raw=np.einsum('gph,bh->bgp',T,W);db=raw.sum(axis=1)@bread
  scores=raw-np.einsum('gpq,bq->bgp',A,db)
  meat=np.einsum('bgp,bgq->bpq',scores,scores)
  vc=factor*np.einsum('ip,bpq,qj->bij',bread,meat,bread)
  rv=np.einsum('ip,bpq,jq->bij',R,vc,R);rb=db@R.T
  inv=np.linalg.pinv(rv);stat=np.einsum('bi,bij,bj->b',rb,inv,rb)
  ok=np.isfinite(stat);exceed+=int((stat[ok]>=obs-1e-12).sum());valid+=int(ok.sum())
 assert valid==B
 p=(exceed+1)/(B+1);return p,float(np.sqrt(p*(1-p)/(B+1)))

def profile(f,metadata,draws=9999):
 B=f['B'];b=B@f['b'];V=B@f['V']@B.T;D=np.tril(np.ones((len(b),len(b))));cum=D@b;VC=D@V@D.T
 rng=np.random.default_rng(SEED);e=rng.multivariate_normal(np.zeros(len(f['b'])),f['V'],size=draws,check_valid='raise')
 e/=np.sqrt(rng.chisquare(f['df'],size=draws)/f['df'])[:,None]
 rows=[]
 for name,est,cov,err in [('beta',b,V,e@B.T),('C',cum,VC,e@B.T@D.T)]:
  se=np.sqrt(np.maximum(np.diag(cov),0));crit=float(np.quantile(np.max(abs(err)/np.maximum(se,1e-20),axis=1),.95));point=stats.t.ppf(.975,f['df'])
  for j in range(len(est)):
   rows.append(dict(**metadata,tipo_perfil=name,lag=j+f['start'],estimate=est[j],se=se[j],low=est[j]-point*se[j],high=est[j]+point*se[j],sim_low=est[j]-crit*se[j],sim_high=est[j]+crit*se[j],p=2*stats.t.sf(abs(est[j]/se[j]),f['df']),crit_sim=crit))
 return pd.DataFrame(rows)

def diagnostics(f):
 q=f['q'];r=pd.DataFrame({'uf':q.uf.to_numpy(),'t':q.data_base.to_numpy(),'u':f['u']/np.sqrt(f['weights'])})
 pivot=r.pivot(index='t',columns='uf',values='u');corr=pivot.corr().to_numpy();N=pivot.shape[1];T=pivot.shape[0];pairs=corr[np.triu_indices(N,1)]
 cd=np.sqrt(2*T/(N*(N-1)))*pairs.sum()
 for k in [1,12]:r[f'u{k}']=r.groupby('uf').u.shift(k)
 aux=r.dropna(subset=['u1']);Q=q.loc[aux.index] if q.index.equals(r.index) else q.reset_index(drop=True).loc[aux.index]
 # Only use consecutive calendar months (pandemic robustness has a gap).
 prev=r.groupby('uf').t.shift(1);valid=(r.t.dt.to_period('M').astype('int64')-prev.dt.to_period('M').astype('int64')).eq(1).fillna(False)
 aux=r.loc[valid].dropna(subset='u1');Q=q.reset_index(drop=True).loc[aux.index]
 xx=aux[['u1']].to_numpy();yy=aux.u.to_numpy();aa=np.linalg.inv(xx.T@xx);bb=aa@xx.T@yy;uu=yy-xx@bb;VV=cr1(xx,uu,Q.uf.to_numpy(),0)
 pp=contrast(bb,VV,np.ones(1),Q.uf.nunique()-1)['p']
 return dict(cd_stat=cd,cd_p=2*stats.norm.sf(abs(cd)),correlacao_transversal_media=pairs.mean(),rho1=r[['u','u1']].corr().iloc[0,1],rho12=r[['u','u12']].corr().iloc[0,1],autocorr_cluster_p=pp,hetero_corr=float(stats.spearmanr(f['u']**2,f['Z'][:,0]).statistic))

def export_r(f,id):
 dr=f['q'][['uf','data_base']].reset_index(drop=True).copy();dr['y']=f['q'].y.to_numpy()
 for j in range(f['Z'].shape[1]):dr[f'z{j}']=f['Z'][:,j]
 temp=CACHE/(id+'.csv.tmp');dr.to_csv(temp,index=False);temp.replace(CACHE/(id+'.csv'))
 assert (CACHE/(id+'.csv')).stat().st_size>100
 cons={k:v.tolist() for k,v in f['contrasts'].items()};cons['joint']=f['R'].tolist()
 (CACHE/(id+'.json')).write_text(json.dumps(cons))
 np.savez_compressed(CACHE/(id+'.npz'),b=f['b'],V=f['V'],DK=f['DK'],basis=f['B'],contrast=list(f['contrasts'].values()))

def result_row(f,meta,boot=False):
 r=dict(**meta,N=f['n'],UFs=f['q'].uf.nunique(),K=f['K'],AIC=f['AIC'],BIC=f['BIC'],condition=f['condition'],rank=f['rank'])
 for name,c in f['contrasts'].items():
  for infer,V,df in [('cluster',f['V'],f['df']),('dk',f['DK'],f['q'].data_base.nunique()-1)]:
   rr=contrast(f['b'],V,c,df)
   r.update({name+'_'+infer+'_'+k:v for k,v in rr.items()})
 r['joint_cluster_p']=joint(f['b'],f['V'],f['R'],f['df']);r['joint_dk_p']=joint(f['b'],f['DK'],f['R'],f['q'].data_base.nunique()-1)
 if boot:
  BB=9999 if 'onda_de_frio' in meta['coluna'] or meta['coluna'] in CENTRAL else 4999
  c=f['contrasts'].get('acumulado',f['contrasts'].get('diferenca'))
  r['boot_B']=BB;r['acumulado_boot_p'],r['acumulado_boot_mcse']=bootstrap(f,c,BB)
  r['joint_boot_p'],r['joint_boot_mcse']=bootstrap(f,f['R'],BB)
  if 'defasado' in f['contrasts']:r['defasado_boot_p'],_=bootstrap(f,f['contrasts']['defasado'],BB)
 return r
CENTRAL={'tipo_onda_de_frio','tipo_granizo','tipo_alagamentos','tipo_chuvas_intensas','tipo_inundacoes','tipo_onda_de_calor_e_baixa_umidade'}

def transform(x,measure):return x if measure=='C_prop' else np.log1p(x)

def fit_main():
 d=load_panel();exps=get_exps();aud=pd.read_csv(OUT/'suporte.csv');rows=[];prof=[];cand=[];fits={};effective=[]
 for per,(start,end) in PERIODS.items():
  dp=d[d.data_base.between(start,end)].copy()
  for c,xx in exps.items():
   s=aud[(aud.periodo==per)&(aud.coluna==c)&(aud.medida=='C_prop')].iloc[0]
   if s.status=='não estimável':continue
   q=lag_frame(dp,xx['C_prop'][d.data_base.between(start,end)])
   cc=[]
   for J in [3,4]:
    f=model(q,basis(12,J));cc.append((f['BIC'],J,f));cand.append(dict(periodo=per,coluna=c,J=J,AIC=f['AIC'],BIC=f['BIC'],N=f['n']))
   _,J,f=min(cc,key=lambda z:(z[0],z[1]));meta=dict(periodo=per,coluna=c,exposicao=label(c),nivel=level(c),J=J,medida='C_prop',suporte=s.status)
   print('principal',per,c,'J',J,flush=True)
   rows.append(result_row(f,meta,True));prof.append(profile(f,meta));fits[(per,c)]=(J,f)
   id='main_'+per.replace('Pré','Pre')+'_'+str(list(exps).index(c));export_r(f,id)
   ix=f['q'].index;effective.append(dict(**meta,**support(dp.loc[ix],xx['C_prop'][d.data_base.between(start,end)][dp.index.get_indexer(ix)],xx['B'][d.data_base.between(start,end)][dp.index.get_indexer(ix)])))
 save(pd.DataFrame(rows),'principais');save(pd.concat(prof,ignore_index=True),'perfis');save(pd.DataFrame(cand),'spline_candidatos');save(pd.DataFrame(effective),'suporte_amostra_efetiva')
 return d,exps,fits

def fit_robustness(d,exps,fits):
 rows=[];place=[];inter=[];loo=[];diag=[];prof=[];rmanifest=[]
 for (per,c),(J,main) in fits.items():
  start,end=PERIODS[per];keep=d.data_base.between(start,end).to_numpy();dp=d.loc[keep];q=lag_frame(dp,exps[c]['C_prop'][keep]);meta=dict(periodo=per,coluna=c,exposicao=label(c),nivel=level(c),J=J)
  diag.append(dict(**meta,**diagnostics(main)))
  # No Cartesian product: change one design decision at a time.
  specs=[('J alternativo',basis(12,7-J),0,12,False,False,None,None)]
  for m in ['A','B','C']:specs.append(('Exposição '+m,basis(12,J),0,12,False,False,None,m))
  specs += [('Irrestrito K3',basis(3,method='irrestrito'),0,3,False,False,None,None),('Irrestrito K6',basis(6,method='irrestrito'),0,6,False,False,None,None),('Almon K12 q2',basis(12,method='almon'),0,12,False,False,None,None),('Somente defasado',basis(12,J,start=1),1,12,False,False,None,None),('Região × tempo',basis(12,J),0,12,True,False,None,None),('Ponderado CA2013',basis(12,J),0,12,False,True,None,None)]
  if per=='Total':specs.append(('Exclui mar2020-dez2021',basis(12,J),0,12,False,False,'pandemic',None))
  sudden=['alagamentos','enxurradas','inundacoes','granizo','vendavais','tornado','movimento_de_massa'];slow=['estiagem','incendio','calor']
  if any(v in c for v in sudden+slow):specs.append(('Mecanismo K6',basis(6,J),0,6,False,False,None,None))
  for name,B,ks,K,rg,wt,cut,m in specs:
   qq=q if m is None else lag_frame(dp,transform(exps[c][m][keep],m))
   if cut:qq=qq[~qq.data_base.between('2020-03-01','2021-12-01')]
   f=model(qq,B,ks,K,rg,wt)
   rows.append(result_row(f,dict(**meta,especificacao=name,medida=m or 'C_prop'),boot=name=='Somente defasado'))
   if c in CENTRAL:prof.append(profile(f,dict(**meta,especificacao=name,medida=m or 'C_prop')))
  # placebos use lag basis retained from primary selection
  f=model(q,basis(12,J),extra='leads');place.append(result_row(f,meta,True));export_r(f,'leads_'+per.replace('Pré','Pre')+'_'+str(list(exps).index(c)))
  if per=='Total':
   f=model(q,basis(12,J),extra='interaction');inter.append(result_row(f,meta,True));export_r(f,'interaction_'+str(list(exps).index(c)))
   for name,BB in [('pre',f['B']),('pos',np.column_stack([f['base'],f['base']])),('diferenca',np.column_stack([np.zeros_like(f['base']),f['base']]))]:
    ff=f.copy();ff['B']=BB;prof.append(profile(ff,dict(**meta,especificacao='Interação '+name,medida='C_prop')))
  if c=='tipo_onda_de_frio':
   shares=dp.assign(x=exps[c]['A'][keep]).groupby('uf').x.sum().sort_values(ascending=False);dominant=shares.index[:2].tolist()
   for drop in [[v] for v in dp.uf.unique()]+[dominant]:
    qq=q[~q.uf.isin(drop)];ds=dp[~dp.uf.isin(drop)];x=exps[c]['C_prop'][keep][~dp.uf.isin(drop).to_numpy()];events=exps[c]['B'][keep][~dp.uf.isin(drop).to_numpy()]
    ss=support(ds,x,events)
    f=model(qq,basis(12,J));row=result_row(f,dict(**meta,retirada=' + '.join(drop),uf_exposta=bool(any(shares[v]>0 for v in drop)),**ss))
    loo.append(row)
  print('robustez',per,c,flush=True)
 save(pd.DataFrame(rows),'multiverse');save(pd.DataFrame(place),'placebos');save(pd.DataFrame(inter),'interacao');save(pd.DataFrame(loo),'onda_frio_leave_out');save(pd.DataFrame(diag),'diagnosticos');save(pd.concat(prof,ignore_index=True),'perfis_robustez')
 return rows

def national():
 from statsmodels.regression.linear_model import OLS
 from statsmodels.stats.diagnostic import acorr_ljungbox
 d=load_panel();exps=get_exps();results=[];profiles=[];candidates=[]
 agg=d.groupby('data_base')[['carteira_ativa_total','carteira_inadimplencia_total']].sum()
 I=100*agg.carteira_inadimplencia_total/agg.carteira_ativa_total
 save(pd.DataFrame({'data_base':I.index,'taxa_br_ponderada':I.values}),'taxa_nacional')
 for per,(start,end) in PERIODS.items():
  for c,xx in exps.items():
   exposure=pd.DataFrame({'t':d.data_base,'municipios':xx['C'],'B':xx['B']}).groupby('t').sum()
   zz=pd.DataFrame({'I':I,'x':exposure.municipios/5570,'B_events':exposure.B}).loc[start:end]
   if zz.B_events.sum()<24 or (zz.B_events>0).sum()<12:continue
   zz['y']=zz.I.diff()
   for k in range(13):zz[f'x{k}']=zz.x.shift(k)
   for k in [1,2]:zz[f'y{k}']=zz.y.shift(k)
   zz=zz.dropna();y=zz.y.to_numpy();J=3;B=basis(12,J);Z=zz[[f'x{k}' for k in range(13)]].to_numpy()@B
   seasonal=pd.get_dummies(zz.index.month,drop_first=True,dtype=float).to_numpy();trend=np.arange(len(zz))/12
   cc=[]
   for p in [0,1,2]:
    X=np.column_stack([np.ones(len(zz)),Z,seasonal,trend]+[zz[[f'y{k}' for k in range(1,p+1)]].to_numpy()] if p else [np.ones(len(zz)),Z,seasonal,trend])
    f=OLS(y,X).fit();cc.append((f.bic,p,f,X));candidates.append(dict(periodo=per,coluna=c,p=p,J=J,AIC=f.aic,BIC=f.bic,N=len(y)))
   _,p,f,X=min(cc,key=lambda v:(v[0],v[1]));rob=f.get_robustcov_results(cov_type='HAC',maxlags=12,use_correction=True,use_t=True)
   V=rob.cov_params()[1:4,1:4];b=f.params[1:4];cv=B.sum(0);rr=contrast(b,V,cv,f.df_resid);q=np.zeros((3,len(f.params)));q[:,1:4]=np.eye(3)
   results.append(dict(periodo=per,coluna=c,exposicao=label(c),nivel=level(c),N=len(y),p_proprio=p,J=J,acumulado_direto=rr['estimate'],low=rr['low'],high=rr['high'],p_acumulado=rr['p'],p_conjunto=float(rob.f_test(q).pvalue),ljungbox12_p=float(acorr_ljungbox(f.resid,lags=[12],return_df=True).lb_pvalue.iloc[0])))
   beta=B@b;VB=B@V@B.T;C=np.tril(np.ones((13,13)));resp=[]
   ar=f.params[-p:] if p else np.array([])
   for h in range(13):resp.append(beta[h]+sum(ar[j-1]*resp[h-j] for j in range(1,p+1) if h-j>=0))
   for h in range(13):
    ch=C[h];se=np.sqrt(ch@VB@ch);crit=stats.t.ppf(.975,f.df_resid)
    profiles.append(dict(periodo=per,coluna=c,exposicao=label(c),lag=h,beta=beta[h],C_direto=float(ch@beta),C_low=float(ch@beta-crit*se),C_high=float(ch@beta+crit*se),resposta_dinamica=resp[h],C_dinamico=sum(resp[:h+1])))
 save(pd.DataFrame(results),'nacional');save(pd.DataFrame(profiles),'nacional_perfis');save(pd.DataFrame(candidates),'nacional_candidatos')

def decomposition():
 d=load_panel();exps=get_exps();r=pd.read_csv(OUT/'principais.csv');rows=[]
 for row in r[r.coluna.isin(CENTRAL)].itertuples():
  start,end=PERIODS[row.periodo];keep=d.data_base.between(start,end);dp=d.loc[keep];q=lag_frame(dp,exps[row.coluna]['C_prop'][keep])
  for target in ['carteira_inadimplencia_total','carteira_ativa_total']:
   q['aux']=np.log(q[target]).groupby(q.uf).diff();f=model(q,basis(12,row.J),ycol='aux')
   rows.append(result_row(f,dict(periodo=row.periodo,coluna=row.coluna,exposicao=label(row.coluna),target=target)))
 save(pd.DataFrame(rows),'decomposicao')

def fdr_table(r,pcols,total):
 for p in pcols:
  if p not in r:continue
  vals=r[p].fillna(1).to_numpy();assert len(vals)<=total
  r['q_global_'+p]=multipletests(np.r_[vals,np.ones(total-len(vals))],method='fdr_bh')[1][:len(vals)]
  r['by_global_'+p]=multipletests(np.r_[vals,np.ones(total-len(vals))],method='fdr_by')[1][:len(vals)]
  if 'nivel' in r:
   for (per,lev),idx in r.groupby(['periodo','nivel']).groups.items():
    m=1 if lev=='Total' else (4 if lev=='Grupo' else (16 if lev=='Tipologia' else 3))
    vv=r.loc[idx,p].fillna(1).to_numpy();r.loc[idx,'q_local_'+p]=multipletests(np.r_[vv,np.ones(max(0,m-len(vv)))],method='fdr_bh')[1][:len(vv)]
 return r

def final_fdr():
 for name,size,cols in [('principais',48,['acumulado_cluster_p','joint_cluster_p','acumulado_boot_p','joint_boot_p','acumulado_dk_p','joint_dk_p']),('placebos',48,['joint_cluster_p','joint_boot_p','joint_dk_p']),('interacao',24,['diferenca_cluster_p','joint_cluster_p','acumulado_boot_p','joint_boot_p','diferenca_dk_p','joint_dk_p']),('nacional',48,['p_acumulado','p_conjunto'])]:
  r=pd.read_csv(OUT/(name+'.csv'));save(fdr_table(r,cols,size),name)
 cr=OUT/'cr2.csv'
 if cr.exists():
  r=pd.read_csv(cr);r['q_global_p']=np.nan
  if 'df_raw' not in r:r['df_raw']=r['df']
  invalid=r['df_raw'].le(0)|r.p.isna()
  r['status_inferencia']=np.where(invalid,'não disponível / suporte insuficiente para aproximação','calculado')
  r.loc[invalid,'df']=np.nan
  # one family per endpoint and design; preserving planned counts
  for (design,endpoint),idx in r.groupby(['design','endpoint']).groups.items():
   m=24 if design=='interaction' else (4 if design=='coldtrace' else 48);v=r.loc[idx,'p'].fillna(1).to_numpy();r.loc[idx,'q_global_p']=multipletests(np.r_[v,np.ones(m-len(v))],method='fdr_bh')[1][:len(v)]
  save(r,'cr2')

def stationarity_complement():
 from dlm import stationarity_y
 save(stationarity_y(load_panel()),'adf_kpss_complementar')

def run_all():
 audit();stationarity_complement();d,e,f=fit_main();fit_robustness(d,e,f);national();decomposition();final_fdr()

if __name__=='__main__':run_all()
