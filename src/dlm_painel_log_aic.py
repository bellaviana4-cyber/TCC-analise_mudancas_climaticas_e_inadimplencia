"""DLM clássico com K selecionado por AIC 1..24, Δlog(I), Δlog1p(registros), painel completo TWFE.
Não importa modelos históricos nem muda transformação por resultados.
"""
from pathlib import Path
import hashlib,json,platform,warnings,unicodedata,re,importlib.metadata
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller,kpss
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/tables/dlm_painel_log_aic'; FIG=ROOT/'outputs/figures/dlm_painel_log_aic'
K=24; K_MAX=24; DK_L=6; PERIODS={'Pré':('2013-01-01','2020-01-01'),'Total':('2013-01-01','2024-12-01')}
UFS=set('AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split())
SOURCE='https://www.defesacivil.pr.gov.br/sites/defesa-civil/arquivos_restritos/files/documento/2022-10/cobrade.pdf'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def slug(s):return re.sub('[^a-z0-9]+','_',unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()).strip('_')
def save(d,name):
 OUT.mkdir(parents=True,exist_ok=True);d.to_csv(OUT/(name+'.csv'),index=False,encoding='utf-8-sig');return d

def audit():
 d=pd.read_csv(ROOT/'data/processed/df_tcc_2013_2024.csv',sep=';',encoding='utf-8-sig');d['data_base']=pd.to_datetime(d.data_base);d=d.sort_values(['uf','data_base']).reset_index(drop=True)
 assert set(d.uf)==UFS and not d.duplicated(['uf','data_base']).any()
 calendar=pd.date_range('2013-01-01','2024-12-01',freq='MS');assert len(d)==27*144
 for uf,z in d.groupby('uf'):assert np.array_equal(z.data_base.to_numpy(),calendar.to_numpy()),uf
 cols=['carteira_ativa_total','carteira_inadimplencia_total','taxa_inadimplencia']+[c for c in d if c.startswith(('grupo_','tipo_'))]+['total_desastres']
 assert not d[cols].isna().any().any() and np.isfinite(d[cols]).all().all()
 assert (d.carteira_ativa_total>0).all() and (d.carteira_inadimplencia_total>0).all() and (d.carteira_inadimplencia_total<=d.carteira_ativa_total).all()
 ti=100*d.carteira_inadimplencia_total/d.carteira_ativa_total
 assert np.allclose(ti,d.taxa_inadimplencia,atol=1e-10,rtol=0)
 path=ROOT/'data/raw/atlas_desastres/atlas.csv'
 a=pd.read_csv(path,sep=';',encoding='latin1',low_memory=False,usecols=['Protocolo_S2iD','Sigla_UF','Data_Evento','Data_Registro','Cod_Cobrade','Cod_IBGE_Mun','grupo_de_desastre','descricao_tipologia'])
 a['linha_original']=np.arange(len(a))+2;a['date']=pd.to_datetime(a.Data_Evento,format='%d/%m/%Y',errors='coerce')
 # Uma data inválida na fonte impediria determinar com segurança o recorte.
 invalid=int(a.date.isna().sum());assert invalid==0,'Data_Evento inválida: não transformar ausência em zero'
 a=a[a.date.between('2013-01-01','2024-12-31')].copy();a['uf']=a.Sigla_UF.str.strip();a['data_base']=a.date.dt.to_period('M').dt.to_timestamp()
 assert set(a.uf)<=UFS and not a[['Cod_Cobrade','Cod_IBGE_Mun','grupo_de_desastre','descricao_tipologia']].isna().any().any()
 a['codigo']=a.Cod_Cobrade.astype(int).astype(str);a['clima']=a.codigo.str.startswith(('12','13','14'))
 a['classe']=np.select([a.clima,a.codigo.str.startswith('11'),a.codigo.str.startswith('15'),a.codigo.str.startswith('2')],['Clima/hidrometeorologia','Geológico','Biológico','Tecnológico'],default='Não classificado')
 assert not a.classe.eq('Não classificado').any()
 a['grupo_COBRADE']=a.codigo.str[:2].map({'11':'Geológico','12':'Hidrológico','13':'Meteorológico','14':'Climatológico','15':'Biológico','24':'Tecnológico'})
 tax=a.groupby(['descricao_tipologia','codigo','grupo_de_desastre','grupo_COBRADE','classe'],dropna=False).size().rename('registros').reset_index();tax['incluido_total_climatico']=tax.classe.eq('Clima/hidrometeorologia')
 notes={'13310':'Código de onda de calor; Atlas rotula Chuvas Intensas','13120':'Frentes frias/Zonas de convergência; Atlas rotula Onda de Frio','14140':'Baixa umidade; não separa onda de calor'}
 tax['observacao']=tax.codigo.map(notes).fillna('Rótulo original preservado; classificação analítica por código');tax['fonte_COBRADE']=SOURCE;save(tax,'taxonomia')
 index=pd.MultiIndex.from_frame(d[['uf','data_base']]);recon=[];labels={'total_climatico':('Central','Total climático / hidrometeorológico (COBRADE 12/13/14)')}
 masks={'total_climatico':a.clima,'total_desastres':pd.Series(True,index=a.index)}
 for field,prefix in [('grupo_de_desastre','grupo_'),('descricao_tipologia','tipo_')]:
  for name in sorted(a[field].unique()):
   c=prefix+slug(name);masks[c]=a[field].eq(name);labels[c]=('Grupo' if prefix=='grupo_' else 'Tipologia',name)
 # Conciliar todas colunas históricas, inclusive total administrativo.
 for c,mask in masks.items():
  counts=a.loc[mask].groupby(['uf','data_base']).size().reindex(index,fill_value=0).to_numpy()
  if c in d:
   assert np.array_equal(counts,d[c].to_numpy()),c;recon.append(dict(coluna=c,total_atlas=int(counts.sum()),total_painel=int(d[c].sum()),max_diferenca=0))
  else:assert c=='total_climatico',c
  if c=='total_climatico':d[c]=counts
 assert sum(c.startswith(('grupo_','tipo_')) for c in d)==len(labels)-1
 save(pd.DataFrame(recon),'reconciliacao_atlas')
 key=['uf','Cod_IBGE_Mun','date','Cod_Cobrade']
 row=dict(N=len(d),UFs=27,meses=144,registros=len(a),climaticos=int(a.clima.sum()),repeticoes_chave=int(a.duplicated(key).sum()),protocolos_repetidos=int(a.Protocolo_S2iD.duplicated().sum()),protocolos_ausentes=int(a.Protocolo_S2iD.isna().sum()),datas_invalidas=invalid,max_diferenca_TI=float(abs(ti-d.taxa_inadimplencia).max()),identificador='sha256 fonte + linha original (cabeçalho=1); não deduplicar A',data_agregacao='Data_Evento',zeros='Ausência de linha na fonte conciliada, não ausência de observação de crédito')
 save(pd.DataFrame([row]),'auditoria');return d,labels

def transformed(d,c,period):
 start,end=PERIODS[period];q=d[d.data_base.between(start,end)].copy().reset_index(drop=True)
 q['y']=np.log(q.taxa_inadimplencia).groupby(q.uf).diff();q['x']=np.log1p(q[c]).groupby(q.uf).diff()
 for k in range(K_MAX+1):q['x'+str(k)]=q.groupby('uf').x.shift(k)
 assert q.groupby('uf').head(1).y.isna().all()
 for k in range(K_MAX+1):assert q.groupby('uf').head(k+1)['x'+str(k)].isna().all()
 return q

def stationarity(d,labels):
 rows=[]
 for per in PERIODS:
  for c in labels:
   q=transformed(d,c,per)
   for variable in (['y','x'] if c=='total_climatico' else ['x']):
    for uf,z in q.groupby('uf'):
     s=z[variable].dropna().to_numpy();base=dict(periodo=per,exposicao='inadimplencia' if variable=='y' else c,uf=uf,n=len(s),deterministico='intercepto',ADF_autolag='AIC',KPSS_banda='auto',inicio=str(z.loc[z[variable].notna(),'data_base'].min().date()),fim=str(z.data_base.max().date()))
     if np.ptp(s)<1e-12:
      rows.append({**base,'status':'constante; testes indisponíveis','classificacao':'indisponível'});continue
     ml=min(12,int(np.ceil(12*(len(s)/100)**.25)),len(s)//2-2);base['ADF_maxlag']=ml
     try:
      ad=adfuller(s,maxlag=ml,regression='c',autolag='AIC');base.update(ADF_estatistica=ad[0],ADF_p=ad[1],ADF_lag=ad[2],ADF_n=ad[3],ADF_IC=ad[5],**{'ADF_crit_'+k:v for k,v in ad[4].items()})
      with warnings.catch_warnings(record=True) as ww:
       warnings.simplefilter('always');kp=kpss(s,regression='c',nlags='auto')
      bound='>=0.10' if kp[1]==.1 else ('<=0.01' if kp[1]==.01 else 'interpolado')
      base.update(KPSS_estatistica=kp[0],KPSS_p=kp[1],KPSS_lag=kp[2],KPSS_limite=bound,KPSS_avisos=';'.join(str(w.message) for w in ww),**{'KPSS_crit_'+k:v for k,v in kp[3].items()})
      classification=('favorável' if ad[1]<.05 and kp[1]>=.05 else 'desfavorável' if ad[1]>=.05 and kp[1]<.05 else 'divergente' if ad[1]<.05 and kp[1]<.05 else 'inconclusivo')
      rows.append({**base,'status':'calculado','classificacao':classification})
     except (ValueError,OverflowError,np.linalg.LinAlgError) as e:rows.append({**base,'status':'indisponível: '+str(e),'classificacao':'indisponível'})
 st=save(pd.DataFrame(rows),'estacionariedade_uf');save(st.groupby(['periodo','exposicao','classificacao']).size().rename('UFs').reset_index(),'estacionariedade_resumo');return st

def residualize(q,A):
 z=pd.DataFrame(A).reset_index(drop=True);g=q.uf.reset_index(drop=True);t=q.data_base.reset_index(drop=True)
 assert q.groupby('uf').size().nunique()==1 and q.groupby('data_base').uf.nunique().eq(27).all()
 return (z-z.groupby(g).transform('mean')-z.groupby(t).transform('mean')+z.mean()).to_numpy()

def fit(q):
 q=q.dropna(subset=['y']+['x'+str(k) for k in range(K+1)]).reset_index(drop=True)
 A=residualize(q,q[['y']+['x'+str(k) for k in range(K+1)]].to_numpy());y=A[:,0];X=A[:,1:];p=X.shape[1];n=len(y);T=q.data_base.nunique();G=q.uf.nunique();pt=G+T-1+p
 rank=np.linalg.matrix_rank(X);assert rank==p,'posto incompleto'
 sd=np.std(X,axis=0);assert np.all(sd>1e-12),'variação TWFE nula';condition=np.linalg.cond(X/sd)
 assert condition<1e8,'condicionamento extremo'
 bread=np.linalg.solve(X.T@X,np.eye(p));b=np.linalg.solve(X.T@X,X.T@y);u=y-X@b
 assert n>pt and G==27
 S=np.vstack([X[q.uf.eq(uf)].T@u[q.uf.eq(uf)] for uf in sorted(q.uf.unique())]);factor=G/(G-1)*(n-1)/(n-pt);V=factor*bread@S.T@S@bread
 scores=np.vstack([X[q.data_base.eq(t)].T@u[q.data_base.eq(t)] for t in sorted(q.data_base.unique())]);meat=scores.T@scores
 for l in range(1,DK_L+1):
  cross=scores[l:].T@scores[:-l];meat+=(1-l/(DK_L+1))*(cross+cross.T)
 DK=n/(n-pt)*bread@meat@bread
 return dict(q=q,y=y,X=X,b=b,u=u,V=V,DK=DK,n=n,T=T,G=G,pt=pt,rank=rank,condition=condition,factor=factor,bread=bread,sd=sd)

def contrast(b,V,c,df):
 v=float(c@V@c);assert v>=-1e-14,'variância negativa'
 if v<=0:return dict(estimate=float(c@b),se=np.nan,p=np.nan,low=np.nan,high=np.nan,status='variância não positiva')
 est=float(c@b);se=np.sqrt(v);crit=stats.t.ppf(.975,df)
 return dict(estimate=est,se=se,p=float(2*stats.t.sf(abs(est/se),df)),low=est-crit*se,high=est+crit*se,status='calculado')
def joint(b,V,R,df):
 A=R@V@R.T;z=R@b;r=len(R)
 if np.linalg.matrix_rank(A)<r:return dict(estimate=np.nan,se=np.nan,p=np.nan,low=np.nan,high=np.nan,status='covariância conjunta sem posto',df_num=r)
 F=float(z@np.linalg.solve(A,z)/r);return dict(estimate=F,se=np.nan,p=float(stats.f.sf(F,r,df)),low=np.nan,high=np.nan,status='calculado',df_num=r)

def support(q,c):
 z=q[c];s=q.groupby('uf')[c].sum().sort_values(ascending=False);total=float(s.sum());s=s/total if total else s*0;ne=1/float(s@s) if total else 0;cells=int(z.gt(0).sum());ufs=int(q.loc[z.gt(0),'uf'].nunique());months=int(q.loc[z.gt(0),'data_base'].nunique())
 enough=total>=24 and cells>=12 and ufs>=5 and months>=8
 concentrated=ne<5 or s.iloc[0]>.5 or s.iloc[:2].sum()>.8
 return dict(registros=int(total),uf_mes_positivos=cells,ufs_expostas=ufs,meses_expostos=months,top1=float(s.iloc[0]),top2=float(s.iloc[:2].sum()),HHI=float(s@s),N_eff=ne,uf_dominante=s.index[0],suporte='insuficiente para inferência' if not enough else 'concentrado' if concentrated else 'mais amplo',elegivel=enough)

def diagnostics(f,meta):
 q=f['q'].copy();q['u']=f['u'];rows=[];lb=[]
 for uf,z in q.groupby('uf'):
  for lag in [1,6,12]:
   l=acorr_ljungbox(z.u,lags=[lag],return_df=True).iloc[0];lb.append({**meta,'uf':uf,'lag':lag,'LB':l.lb_stat,'p':l.lb_pvalue,'uso':'diagnóstico descritivo, resíduos estimados'})
 save_append(lb,'autocorrelacao_uf')
 E=q.pivot(index='data_base',columns='uf',values='u');cor=E.corr().to_numpy();idx=np.triu_indices(27,1);rho=cor[idx];cd=float(np.sqrt(2*len(E)/(27*26))*rho.sum())
 # Sob TWFE, demeaning temporal induz correlação negativa: CD ingênuo não é teste calibrado.
 group=[z.u.to_numpy() for _,z in q.groupby('uf')];lev=stats.levene(*group,center='median');corr=np.corrcoef(f['X'],rowvar=False);vifs=np.diag(np.linalg.inv(corr));h=np.einsum('ij,jk,ik->i',f['X'],f['bread'],f['X']);influence=np.abs(h*f['u']/(1-h))
 rows.append({**meta,'CD_naive':cd,'CD_p_naive':2*stats.norm.sf(abs(cd)),'CD_ressalva':'não calibrado sob TWFE; correlação negativa mecânica após remover tempo','rho_media':float(rho.mean()),'rho_abs_media':float(abs(rho).mean()),'rho_max':float(rho.max()),'rho_min':float(rho.min()),'Levene':lev.statistic,'Levene_p_descritivo':lev.pvalue,'hetero_ressalva':'Levene pressupõe independência, aqui descritivo','max_VIF':float(max(vifs)),'max_cor_lags':float(np.max(abs(corr-np.eye(K+1)))),'max_alavancagem_exposicao':float(h.max()),'maior_influencia_uf':q.iloc[int(influence.argmax())].uf,'maior_influencia_data':str(q.iloc[int(influence.argmax())].data_base.date()),'media_residuo':float(f['u'].mean()),'sd_residuo':float(np.std(f['u']))})
 save_append(rows,'diagnosticos');save_append([{**meta,'lag1':i,'lag2':j,'correlacao':corr[i,j]} for i in range(K+1) for j in range(K+1)],'correlacao_lags')
 save_append([{**meta,'uf1':E.columns[i],'uf2':E.columns[j],'rho':cor[i,j]} for i,j in zip(*idx)],'dependencia_ufs')
 # Scores por UF e contraste acumulado: concentração da incerteza, sem excluir UFs.
 C=np.ones(K+1);sc=np.array([C@f['bread']@f['X'][q.uf.eq(uf)].T@f['u'][q.uf.eq(uf)] for uf in sorted(q.uf.unique())]);shares=sc**2/(sc@sc)
 save_append([{**meta,'uf':uf,'share_variancia_acumulado':float(s),'N_eff_scores':float(1/(shares@shares))} for uf,s in zip(sorted(q.uf.unique()),shares)],'influencia_uf')
 save_append([{**meta,'uf':r.uf,'data_base':str(r.data_base.date()),'residuo':float(r.u)} for r in q.itertuples()], 'residuos')

def save_append(rows,name):
 p=OUT/(name+'.csv');d=pd.DataFrame(rows)
 if p.exists():d=pd.concat([pd.read_csv(p),d],ignore_index=True)
 save(d,name)

def validate_fit(f,meta):
 q=f['q'];Z=q[['x'+str(k) for k in range(K+1)]].to_numpy();FE=pd.concat([pd.get_dummies(q.uf,dtype=float),pd.get_dummies(q.data_base,dtype=float).iloc[:,1:]],axis=1).to_numpy();A=np.column_stack([FE,Z]);bb=np.linalg.lstsq(A,q.y.to_numpy(),rcond=None)[0];assert np.linalg.matrix_rank(A)==A.shape[1]
 from statsmodels.regression.linear_model import OLS
 explicit=OLS(q.y.to_numpy(),A).fit()
 expected_aic=f['n']*(np.log(2*np.pi)+1+np.log(f['u']@f['u']/f['n']))+2*f['pt']
 assert np.isclose(explicit.aic,expected_aic,atol=1e-8)
 delta=float(np.max(abs(bb[-(K+1):]-f['b'])));assert delta<1e-9
 u=q.y.to_numpy()-A@bb;bread=np.linalg.inv(A.T@A);scores=np.vstack([A[q.uf.eq(g)].T@u[q.uf.eq(g)] for g in sorted(q.uf.unique())]);vv=f['factor']*bread@scores.T@scores@bread;vd=float(np.max(abs(vv[-(K+1):,-(K+1):]-f['V'])));assert vd<1e-9
 c=np.ones(K+1);vsum=float(c@f['V']@c);assert np.isclose(vsum,f['V'].sum())
 from statsmodels.stats.sandwich_covariance import cov_nw_groupsum
 from statsmodels.regression.linear_model import OLS
 ff=OLS(f['y'],f['X']).fit();time=pd.factorize(q.data_base,sort=True)[0]
 vdk=cov_nw_groupsum(ff,nlags=6,time=time,use_correction=False)*f['n']/(f['n']-f['pt'])
 diffdk=float(np.max(abs(vdk-f['DK'])));assert diffdk<1e-10
 return {**meta,'AIC_dummies':explicit.aic,'AIC_FWL':expected_aic,'DK_statsmodels_max_diff':diffdk,'coef_FWL_dummies_max_diff':delta,'cov_CR1_dummies_max_diff':vd,'var_soma':vsum,'soma_todas_covariancias':float(f['V'].sum()),'passou':True}

def estimate(d,labels,st):
 global K
 candidates=[];selections=[]
 results=[];profiles=[];samples=[];validation=[];scenarios=[];models=[]
 for name in ['autocorrelacao_uf','diagnosticos','correlacao_lags','dependencia_ufs','influencia_uf','residuos','covariancias']:
  (OUT/(name+'.csv')).unlink(missing_ok=True)
 for per in PERIODS:
  for c,(level,label) in labels.items():
   full=transformed(d,c,per);window_su=support(full,c)
   q=full.dropna(subset=['y']+['x'+str(k) for k in range(K_MAX+1)]).reset_index(drop=True)
   su=support(q,c);metadata=dict(periodo=per,exposicao=c,nivel=level,rotulo=label)
   fitted={};rows=[]
   for horizon in range(1,K_MAX+1):
    K=horizon
    row={**metadata,'K':K,'N':len(q),'T':q.data_base.nunique(),'G':27,'primeira_equacao':str(q.data_base.min().date()),'ultima_equacao':str(q.data_base.max().date()),'AIC':np.nan,'delta_AIC':np.nan,'selecionado':False}
    if not (su['elegivel'] and window_su['elegivel']):row['status']='suporte insuficiente na janela ou amostra comum'
    else:
     try:
      ff=fit(q);ssr=float(ff['u']@ff['u']);ll=-ff['n']/2*(np.log(2*np.pi)+1+np.log(ssr/ff['n']))
      row.update(status='estimado',AIC=-2*ll+2*ff['pt'],BIC=-2*ll+np.log(ff['n'])*ff['pt'],loglike=ll,SSR=ssr,parametros_totais=ff['pt'],rank=ff['rank'],condition=ff['condition']);fitted[K]=ff
     except (AssertionError,np.linalg.LinAlgError) as e:row['status']='não identificável: '+str(e)
    rows.append(row)
   if fitted:
    minimum=min(row['AIC'] for row in rows if row['status']=='estimado')
    K=min(row['K'] for row in rows if row['status']=='estimado' and row['AIC']<=minimum+1e-8)
    for row in rows:
     if row['status']=='estimado':row['delta_AIC']=row['AIC']-minimum
     row['selecionado']=row['K']==K
    selections.append({**metadata,'K':K,'AIC':next(row['AIC'] for row in rows if row['selecionado']),'K_delta_AIC_ate2':','.join(str(row['K']) for row in rows if row['status']=='estimado' and row['delta_AIC']<=2),'fronteira':K in [1,K_MAX],'status':'selecionado','N':len(q)})
   else:
    K=1;selections.append({**metadata,'K':np.nan,'status':'sem candidato estimável','N':len(q)})
   candidates.extend(rows)
   meta={**metadata,'K':K if fitted else np.nan}
   if not fitted:su['elegivel']=False

   sq=q.dropna(subset=['y']+['x'+str(k) for k in range(K+1)]);samples.append({**meta,**window_su,'N_janela':len(full),'N_efetivo':len(sq),'perda_diferenca':27,'perda_lags_adicional':27*K_MAX,'primeira_equacao':str(sq.data_base.min().date()),'ultima_equacao':str(sq.data_base.max().date()),'UFs_modelo':sq.uf.nunique(),**{'efetivo_'+k:v for k,v in support(sq,c).items()}})
   endpoints={'beta0':np.eye(K+1)[0],'soma0K':np.ones(K+1),'soma1K':np.r_[0,np.ones(K)]}
   if not su['elegivel']:
    for cov in ['CR1','DK6']:
     for ep in list(endpoints)+['conjunto0K','conjunto1K']:results.append({**meta,'covariancia':cov,'endpoint':ep,'status':'suporte insuficiente','p':np.nan})
    continue
   try:f=fitted[K]
   except (AssertionError,np.linalg.LinAlgError) as e:
    for cov in ['CR1','DK6']:
     for ep in list(endpoints)+['conjunto0K','conjunto1K']:results.append({**meta,'covariancia':cov,'endpoint':ep,'status':'não identificável: '+str(e),'p':np.nan})
    continue
   models.append({**meta,'N':f['n'],'T':f['T'],'G':f['G'],'parametros_totais':f['pt'],'rank_exposicao':f['rank'],'condition_padronizada':f['condition'],'fator_CR1':f['factor'],'FE':'UF + mês-ano','AIC':f['n']*(np.log(2*np.pi)+1+np.log(f['u']@f['u']/f['n']))+2*f['pt'],'BIC':f['n']*(np.log(2*np.pi)+1+np.log(f['u']@f['u']/f['n']))+f['pt']*np.log(f['n']),'y':'Delta log(I)','x':'Delta log(1+D)','status':'exploratório; validade condicionada às hipóteses'})
   diagnostics(f,meta)
   # Validação explícita nas duas aplicações centrais; demais compartilham o mesmo código.
   if c=='total_climatico':
    chosen=K
    for kk in sorted(set([1,K_MAX,chosen]) & set(fitted)):
     K=kk;validation.append(validate_fit(fitted[kk],{**meta,'K':kk,'uso':'selecionado' if kk==chosen else 'candidato extremo'}))
    K=chosen
   for cov,V,df in [('CR1',f['V'],26),('DK6',f['DK'],f['T']-1)]:
    for ep,C in endpoints.items():results.append({**meta,'covariancia':cov,'endpoint':ep,'df':df,**contrast(f['b'],V,C,df)})
    for ep,R in [('conjunto0K',np.eye(K+1)),('conjunto1K',np.eye(K+1)[1:])]:results.append({**meta,'covariancia':cov,'endpoint':ep,'df':df,**joint(f['b'],V,R,df)})
    for k in range(K+1):profiles.append({**meta,'covariancia':cov,'lag':k,**{'beta_'+kk:v for kk,v in contrast(f['b'],V,np.eye(K+1)[k],df).items()},**{'C_'+kk:v for kk,v in contrast(f['b'],V,(np.arange(K+1)<=k).astype(float),df).items()},'banda':'IC95% pontual, não simultâneo'})
    save_append([{**meta,'covariancia':cov,'lag1':i,'lag2':j,'cov':float(V[i,j])} for i in range(K+1) for j in range(K+1)],'covariancias')
    for scenario in ['aumento persistente D: 0 para 1','pulso de um mês D: 0 para 1 para 0']:
     dx=np.log(2);acc=np.zeros(K+1)
     for h in range(K+2):
      weight=dx*((np.arange(K+1)<=h).astype(float)-(np.arange(K+1)<=h-1).astype(float) if scenario.startswith('pulso') else (np.arange(K+1)<=h).astype(float))
      resp=contrast(f['b'],V,weight,df) if np.any(weight) else dict(estimate=0,low=0,high=0)
      change=float(dx*(f['b'][h] if h<=K else 0)-(dx*f['b'][h-1] if scenario.startswith('pulso') and 1<=h<=K+1 else 0))
      scenarios.append({**meta,'covariancia':cov,'cenario':scenario,'h':h,'delta_x_inicial':dx,'resposta_delta_log_I':change,'resposta_log_I_acumulada':resp['estimate'],'variacao_relativa_I_pct':100*np.expm1(resp['estimate']),'low_pct':100*np.expm1(resp['low']),'high_pct':100*np.expm1(resp['high'])})
   print(per,c,'K AIC',K,'estimado',flush=True)
 save(pd.DataFrame(candidates),'candidatos_AIC');save(pd.DataFrame(selections),'selecao_K')
 r=pd.DataFrame(results);r['q_BH']=np.nan;r['familia']=''
 for keys,g in r.groupby(['periodo','nivel','covariancia','endpoint']):
  r.loc[g.index,'q_BH']=multipletests(g.p.fillna(1),method='fdr_bh')[1];r.loc[g.index,'familia']=' | '.join(keys)
 for df,name in [(r,'resultados'),(pd.DataFrame(profiles),'perfis'),(pd.DataFrame(samples),'amostras_suporte'),(pd.DataFrame(models),'modelos'),(pd.DataFrame(validation),'validacao'),(pd.DataFrame(scenarios),'cenarios')]:save(df,name)
 return r

def figures():
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 FIG.mkdir(parents=True,exist_ok=True);p=pd.read_csv(OUT/'perfis.csv')
 for (per,c),g in p.groupby(['periodo','exposicao']):
  fig,axes=plt.subplots(1,2,figsize=(11,4));colors={'CR1':'#136f86','DK6':'#bd6a35'}
  for cov,z in g.groupby('covariancia'):
   z=z.sort_values('lag');color=colors[cov]
   for ax,v in zip(axes,['beta','C']):
    ax.plot(z.lag,z[v+'_estimate'],marker='o',color=color,label=cov);ax.fill_between(z.lag,z[v+'_low'],z[v+'_high'],alpha=.13,color=color)
  for ax,title in zip(axes,['Perfil incremental βₖ','Resposta acumulada C(h)']):
   ax.axhline(0,color='#aaa',lw=1);ax.set(xlabel='Defasagem (meses)',ylabel='Unidade logarítmica',title=title);ax.legend();ax.spines[['top','right']].set_visible(False)
  fig.suptitle(per+' · '+g.rotulo.iloc[0]+' · IC95% pontuais');fig.tight_layout();fig.savefig(FIG/(slug(per)+'_'+c+'.svg'));plt.close(fig)

def manifest():
 inputs=[ROOT/'data/processed/df_tcc_2013_2024.csv',ROOT/'data/raw/atlas_desastres/atlas.csv',ROOT/'tcc/capitulos/c3_metodologias_tg_referencia.tex']
 m={'data':'2026-10-06','inputs':{str(p.relative_to(ROOT)):sha(p) for p in inputs},'python':platform.python_version(),'versoes':{p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','statsmodels','matplotlib','threadpoolctl']},'K_candidatos':list(range(1,25)),'selecao':'AIC em amostra comum; empate numerico 1e-8 menor K','amostra_final':'comum Kmax24','DK_largura':6,'outputs':{str(p.relative_to(ROOT)):sha(p) for p in sorted(OUT.glob('*.csv'))},'codigo':sha(__file__),'protocolo':sha(ROOT/'docs/dlm_painel_log_aic_protocolo.md')}
 (OUT/'manifest.json').write_text(json.dumps(m,indent=2,ensure_ascii=False));return m

def run():
 with threadpool_limits(limits=1):
  d,labels=audit();st=stationarity(d,labels);r=estimate(d,labels,st);figures();manifest()
 return r
if __name__=='__main__':run()
