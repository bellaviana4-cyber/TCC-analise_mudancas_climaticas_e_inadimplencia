"""DLM clássico por exposição/período; K por BIC, inferência condicional à seleção."""
from pathlib import Path
import json,hashlib,warnings
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.regression.linear_model import OLS
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits
import dlm_revisao as r
import dlm_validacao_final as v
import dlm_classico as classic
ROOT=r.ROOT;OUT=ROOT/'outputs/tables/dlm_selecionado'
SEED=v.SEED  # semente efetiva de wcr; registrada para rastreabilidade

def save(df,name):
 OUT.mkdir(parents=True,exist_ok=True);tmp=OUT/(name+'.tmp');df.to_csv(tmp,index=False,encoding='utf-8-sig');tmp.replace(OUT/(name+'.csv'));return df

def bh(df,pcol,qcol):
 df[qcol]=np.nan
 if len(df):df[qcol]=multipletests(np.r_[df[pcol].fillna(1).values,np.ones(48-len(df))],method='fdr_bh')[1][:len(df)]
 return df

def inputs():
 d=r.load_panel();raw=ROOT/'data/raw/atlas_desastres/atlas.csv';digest=hashlib.sha256(raw.read_bytes()).hexdigest();assert digest=='6ca29008a60a30e9f45d0f451da7750f850d8902704487798e1ef39ca3da44af'
 a=pd.read_csv(raw,sep=';',encoding='latin1',low_memory=False);a['date']=pd.to_datetime(a.Data_Evento,format='%d/%m/%Y',errors='coerce');a=a[a.date.dt.year.between(2013,2024)].copy();assert len(a)==40339
 a['uf']=a.Sigla_UF.str.strip();a['data_base']=a.date.dt.to_period('M').dt.to_timestamp();a['classe_analitica']=a.Cod_Cobrade.map(r.analytical)
 idx=pd.MultiIndex.from_frame(d[['uf','data_base']]);ex={};audit=[]
 for c,mask in r.masks(a,d).items():
  aa=a.loc[mask];counts=aa.groupby(['uf','data_base']).size().reindex(idx,fill_value=0).to_numpy();territory=aa.groupby(['uf','data_base']).Cod_IBGE_Mun.nunique().reindex(idx,fill_value=0).to_numpy()
  if c in d:assert np.array_equal(counts,d[c].to_numpy()),c
  ex[c]={'A':counts,'C':territory,'C_prop':territory/d.uf.map(r.MUNICIPIOS).to_numpy()};audit.append(dict(coluna=c,registros=int(counts.sum()),sha_atlas=digest))
 save(pd.DataFrame(audit),'auditoria');return d,ex

def cr2(f):
 """OLS CR2 target I; scalar df via tr(Q)^2/tr(Q²), with FE projection retained."""
 q=f['q'];X=f['X'];y=f['y'];G=q.uf.nunique();T=q.data_base.nunique();n=len(q);p=X.shape[1]
 # Full-rank FE parameterization used only for hat/projection, not for slope estimation.
 F=np.column_stack([pd.get_dummies(q.uf,dtype=float).to_numpy(),pd.get_dummies(q.data_base,dtype=float).to_numpy()[:,1:]])
 Z=np.column_stack([X,F]);bi=np.linalg.inv(Z.T@Z);assert np.linalg.matrix_rank(Z)==len(bi)
 score=[];L=[];cov=np.zeros((p,p))
 for uf in sorted(q.uf.unique()):
  ix=np.flatnonzero(q.uf.to_numpy()==uf);zg=Z[ix];mg=np.eye(len(ix))-zg@bi@zg.T;val,vec=np.linalg.eigh((mg+mg.T)/2)
  assert val.min()>-1e-7
  w=np.where(val>1e-10,1/np.sqrt(np.maximum(val,1e-10)),0);A=(vec*w)@vec.T
  C=f['bread']@X[ix].T@A;sc=C@f['u'][ix];cov+=np.outer(sc,sc)
  # C embedded in n dimensions followed by full OLS residual projection.
  ll=np.zeros((p,n));ll[:,ix]=C;ll-=C@zg@bi@Z.T;L.append(ll)
 return cov,np.stack(L)

def cr2_contrast(f,V,L,c):
 c=np.asarray(c);ls=np.einsum('p,gpn->gn',c,L);Q=ls@ls.T;df=float(np.trace(Q)**2/np.sum(Q*Q));est=float(c@f['b']);se=float(np.sqrt(max(0,c@V@c)));crit=stats.t.ppf(.975,df)
 return dict(estimate=est,se=se,df=df,low=est-crit*se,high=est+crit*se,p=float(2*stats.t.sf(abs(est/se),df)))

def reconciliation(d,ex):
 old=pd.read_csv(ROOT/'outputs/tables/dlm_classico/cr2.csv');results=[]
 for per,c in [('Total','total_desastres'),('Pré','total_desastres'),('Total','tipo_onda_de_frio'),('Pré','tipo_onda_de_frio'),('Total','tipo_granizo')]:
  keep=d.data_base.between(*r.PERIODS[per]);dd=d.loc[keep];q=v.calendar_lags(dd,ex[c]['C_prop'][keep]);dx=pd.Series(ex[c]['C_prop'][keep],index=dd.index).groupby(dd.uf).diff();qd=v.calendar_lags(dd,dx.to_numpy());common=q[['y']+[f'x{k}' for k in range(11)]].notna().all(1)&qd[[f'x{k}' for k in range(11)]].notna().all(1);f=classic.fit(q.loc[common],10);V,L=cr2(f);z=cr2_contrast(f,V,L,np.ones(10));ref=old[(old.periodo==per)&(old.coluna==c)&(old.especificacao=='Principal')&(old.endpoint=='acumulado')].iloc[0]
  for k in ['estimate','se','df','low','high','p']:assert np.isclose(z[k],ref[k],rtol=2e-6,atol=1e-8),(per,c,k,z[k],ref[k])
  results.append(dict(periodo=per,coluna=c,max_diferenca=max(abs(z[k]-ref[k]) for k in z),aprovado=True))
 save(pd.DataFrame(results),'reconciliacao_cr2')

def panel(d,ex):
 models=[];candidates=[];profiles=[];diag=[];eligible=set(map(tuple,pd.read_csv(ROOT/'outputs/tables/dlm_revisao/principais.csv')[['periodo','coluna']].values));coverage=[]
 for per,dates in r.PERIODS.items():
  for c,xx in ex.items():
   if (per,c) not in eligible:coverage.append(dict(desenho='Painel',periodo=per,coluna=c,exposicao=r.label(c),nivel=r.level(c),status='não estimável na triagem prévia'));continue
   keep=d.data_base.between(*dates);dd=d.loc[keep];q=v.calendar_lags(dd,xx['C_prop'][keep]);dx=pd.Series(xx['C_prop'][keep],index=dd.index).groupby(dd.uf).diff();qd=v.calendar_lags(dd,dx.to_numpy());common=q[['y']+[f'x{k}' for k in range(11)]].notna().all(1)&qd[[f'x{k}' for k in range(11)]].notna().all(1);q=q.loc[common]
   fits={K:classic.fit(q,K) for K in range(1,11)};K=min(fits,key=lambda k:(fits[k]['BIC'],k));AIC=min(fits,key=lambda k:(fits[k]['AIC'],k));f=fits[K];meta=dict(desenho='Painel',periodo=per,coluna=c,exposicao=r.label(c),nivel=r.level(c),K=K,K_AIC=AIC,p_proprio=0,N=len(q),inicio=str(q.data_base.min().date()),fim=str(q.data_base.max().date()),BIC=f['BIC'],AIC=f['AIC'],condition=f['condition'],**v.support(f,np.ones(K)))
   for k,ff in fits.items():candidates.append(dict(desenho='Painel',periodo=per,coluna=c,K=k,p_proprio=0,N=len(q),BIC=ff['BIC'],AIC=ff['AIC'],selecionado=k==K))
   V,L=cr2(f);acc=cr2_contrast(f,V,L,np.ones(K));boot=v.wcr(f,np.ones(K),B=4999);joint=v.wcr(f,np.eye(K),B=4999)
   nullbic=len(q)*np.log(f['y']@f['y']/len(q))+f['absorbed']*np.log(len(q));meta.update(delta_BIC_sem_exposicao=f['BIC']-nullbic,estimate=acc['estimate'],low=acc['low'],high=acc['high'],se=acc['se'],df=acc['df'],p=acc['p'],p_boot=boot['p'],boot_status=boot['status'],boot_mcse=boot.get('mcse'),p_joint=joint['p'],joint_status=joint['status'],singular_boot=boot['singular']+joint['singular'],inferência='CR2/Satterthwaite; condicional a K')
   for h in range(1,K+1):
    b=cr2_contrast(f,V,L,np.eye(K)[h-1]);ch=cr2_contrast(f,V,L,(np.arange(K)<h).astype(float));profiles.append(dict(desenho='Painel',periodo=per,coluna=c,K=K,lag=h,beta=b['estimate'],beta_low=b['low'],beta_high=b['high'],beta_p=b['p'],C=ch['estimate'],C_low=ch['low'],C_high=ch['high']))
   residual=q[['uf','data_base']].copy();residual['u']=f['u'];lb=[]
   for _,g in residual.groupby('uf'):lb.append(float(acorr_ljungbox(g.u,lags=[12],return_df=True).lb_pvalue.iloc[0]))
   meta['ufs_lb12_nominal']=sum(p<.05 for p in lb);meta['diagnostico']='autocorrelação em '+str(meta['ufs_lb12_nominal'])+' UFs (Ljung–Box nominal); suporte '+meta['status_suporte']
   models.append(meta);coverage.append(dict(desenho='Painel',periodo=per,coluna=c,exposicao=r.label(c),nivel=r.level(c),status='estimado',K=K));save(pd.DataFrame(models),'painel');print('Painel',per,c,'K',K,'p CR2',meta['p'],flush=True)
 save(bh(bh(bh(pd.DataFrame(models),'p','q'),'p_boot','q_boot'),'p_joint','q_joint'),'painel');save(pd.DataFrame(profiles),'painel_perfis');save(pd.DataFrame(candidates),'painel_candidatos');return coverage

def national(d,ex):
 models=[];candidates=[];profiles=[];coverage=[];agg=d.groupby('data_base')[['carteira_ativa_total','carteira_inadimplencia_total']].sum();I=100*agg.carteira_inadimplencia_total/agg.carteira_ativa_total
 for per,dates in r.PERIODS.items():
  for c,xx in ex.items():
   exp=pd.DataFrame({'t':d.data_base,'C':xx['C'],'A':xx['A']}).groupby('t').sum();z=pd.DataFrame({'I':I,'x':exp.C/5570,'A':exp.A}).loc[dates[0]:dates[1]];z['y']=z.I.diff()
   for k in range(1,11):z[f'x{k}']=z.x.shift(k)
   for j in [1,2]:z[f'y{j}']=z.y.shift(j)
   if z.A.sum()<24 or (z.A>0).sum()<12:coverage.append(dict(desenho='Nacional',periodo=per,coluna=c,exposicao=r.label(c),nivel=r.level(c),status='não estimável na triagem prévia'));continue
   z=z.dropna();season=pd.get_dummies(z.index.month,drop_first=True,dtype=float).to_numpy();trend=np.arange(len(z))/12;control=np.column_stack([np.ones(len(z)),season,trend]);fits={}
   for K in range(1,11):
    for ar in [0,1,2]:
     X=np.column_stack([control,z[[f'y{j}' for j in range(1,ar+1)]].to_numpy(),z[[f'x{k}' for k in range(1,K+1)]].to_numpy()]);fit=OLS(z.y,X).fit()
     if np.linalg.matrix_rank(X)<X.shape[1]:continue
     fits[K,ar]=(fit,X);candidates.append(dict(desenho='Nacional',periodo=per,coluna=c,K=K,p_proprio=ar,N=len(z),BIC=fit.bic,AIC=fit.aic,selecionado=False))
   if not fits:coverage.append(dict(desenho='Nacional',periodo=per,coluna=c,exposicao=r.label(c),nivel=r.level(c),status='rank insuficiente'));continue
   K,ar=min(fits,key=lambda kp:(fits[kp][0].bic,sum(kp),*kp));ka,pa=min(fits,key=lambda kp:(fits[kp][0].aic,sum(kp),*kp));fit,X=fits[K,ar];rob=fit.get_robustcov_results(cov_type='HAC',maxlags=12,use_correction=True,use_t=True);V=rob.cov_params();cs=np.zeros(X.shape[1]);cs[-K:]=1;acc=r.contrast(fit.params,V,cs,fit.df_resid);R=np.eye(X.shape[1])[-K:];joint=float(rob.f_test(R).pvalue);arcoef=fit.params[control.shape[1]:control.shape[1]+ar].to_numpy();rho=max(abs(np.roots(np.r_[1,-arcoef]))) if ar else 0
   baseX=np.column_stack([control,z[[f'y{j}' for j in range(1,ar+1)]].to_numpy()]);null=OLS(z.y,baseX).fit()
   meta=dict(desenho='Nacional',periodo=per,coluna=c,exposicao=r.label(c),nivel=r.level(c),K=K,K_AIC=ka,p_proprio=ar,p_AIC=pa,N=len(z),inicio=str(z.index.min().date()),fim=str(z.index.max().date()),BIC=fit.bic,AIC=fit.aic,delta_BIC_sem_exposicao=fit.bic-null.bic,p=acc['p'],estimate=acc['estimate'],low=acc['low'],high=acc['high'],p_joint=joint,df=fit.df_resid,condition=float(np.linalg.cond(X)),ljungbox12_p=float(acorr_ljungbox(fit.resid,lags=[12],return_df=True).lb_pvalue.iloc[0]),raiz_AR=float(rho),AR_estavel=bool(rho<1),inferência='HAC12; condicional a K e p próprio')
   for h in range(1,K+1):
    cb=np.zeros(len(cs));cb[-K+h-1]=1;b=r.contrast(fit.params,V,cb,fit.df_resid);cc=np.zeros(len(cs));cc[-K:-K+h if h<K else None]=1;cv=r.contrast(fit.params,V,cc,fit.df_resid);profiles.append(dict(desenho='Nacional',periodo=per,coluna=c,K=K,lag=h,beta=b['estimate'],beta_low=b['low'],beta_high=b['high'],beta_p=b['p'],C=cv['estimate'],C_low=cv['low'],C_high=cv['high']))
   meta['diagnostico']=('AR estável' if rho<1 else 'AR instável')+'; '+('autocorrelação residual nominal' if meta['ljungbox12_p']<.05 else 'Ljung–Box12 sem rejeição nominal');models.append(meta)
   for candidate in candidates:
    if candidate['periodo']==per and candidate['coluna']==c:candidate['selecionado']=(candidate['K'],candidate['p_proprio'])==(K,ar)
   coverage.append(dict(desenho='Nacional',periodo=per,coluna=c,exposicao=r.label(c),nivel=r.level(c),status='estimado',K=K));print('Nacional',per,c,'K',K,'AR',ar,'p',acc['p'],flush=True)
 save(bh(bh(pd.DataFrame(models),'p','q'),'p_joint','q_joint'),'nacional');save(pd.DataFrame(profiles),'nacional_perfis');save(pd.DataFrame(candidates),'nacional_candidatos');return coverage

def main():
 with threadpool_limits(limits=1):
  d,ex=inputs();reconciliation(d,ex);cov=panel(d,ex)+national(d,ex);save(pd.DataFrame(cov),'cobertura')
  for name in ['painel','nacional']:
   m=pd.read_csv(OUT/(name+'.csv'));print(name,'K',m.K.value_counts().to_dict(),'BH acumulado',int((m.q<.05).sum()),'BH conjunto',int((m.q_joint<.05).sum()))
if __name__=='__main__':main()
