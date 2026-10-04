"""Validação final DLM: novas saídas, fontes e resultados anteriores imutáveis."""
from pathlib import Path
import json, os, sys, hashlib, subprocess, importlib.metadata
import numpy as np
import pandas as pd
from scipy import stats, linalg
import dlm_revisao as r
from statsmodels.regression.linear_model import OLS
from statsmodels.stats.sandwich_covariance import cov_cluster
ROOT=r.ROOT; PREV=r.OUT; OUT=ROOT/'outputs/tables/dlm_validacao_final'; CACHE=ROOT/'data/interim/dlm_validacao_final'; FIG=ROOT/'outputs/figures/dlm_validacao_final'; SEED=20261004
for p in [OUT,CACHE,FIG]:p.mkdir(parents=True,exist_ok=True)
def save(d,name):
 t=OUT/(name+'.tmp');d.to_csv(t,index=False,encoding='utf-8-sig');t.replace(OUT/(name+'.csv'));return d

def calendar_lags(d,x):
 if d.duplicated(['uf','data_base']).any():raise ValueError('UF-mês duplicado')
 for _,g in d.groupby('uf',sort=False):
  if not g.data_base.is_monotonic_increasing or not np.all(np.diff(g.data_base.dt.to_period('M').astype(int))==1):raise ValueError('Calendário não ordenado/contínuo antes dos shifts')
 return r.lag_frame(d,x)

def seasonal_absorb(q,A,w=None):
 a=np.asarray(A,float);a=a[:,None] if a.ndim==1 else a
 w=np.ones(len(q)) if w is None else w;df=pd.DataFrame(a);g=q.uf.reset_index(drop=True)+'_'+q.data_base.dt.month.reset_index(drop=True).astype(str);t=q.data_base.reset_index(drop=True)
 out=a.copy()
 for _ in range(1000):
  before=out.copy();v=pd.DataFrame(out)
  for group in [g,t]:
   mean=v.mul(w,axis=0).groupby(group).transform('sum').div(pd.Series(w).groupby(group).transform('sum'),axis=0);v=v-mean
  out=v.to_numpy()
  if np.max(abs(out-before))<1e-12:return out
 raise RuntimeError('Absorção sazonal não convergiu')

def absorb(f,A):
 if f.get('seasonal'):return seasonal_absorb(f['q'],A,f['weights'])
 return r.residualize(f['q'],A,f['regional'],f['weights'])

def rebuild(f,Z=None,seasonal=False,contrasts=None):
 f=f.copy();q=f['q'];Z=f['Z'] if Z is None else Z;f['seasonal']=seasonal;f['Z']=Z
 v=absorb(f,np.column_stack([q.y,Z]));w=f['weights'];y=v[:,0]*np.sqrt(w);X=v[:,1:]*np.sqrt(w[:,None]);rank=np.linalg.matrix_rank(X)
 if rank<X.shape[1]:raise ValueError('Regressores sem rank completo')
 bread=np.linalg.inv(X.T@X);b=bread@X.T@y;u=y-X@b
 G=q.uf.nunique();T=q.data_base.nunique();absorbed=G*q.data_base.dt.month.nunique()+T-q.data_base.dt.month.nunique() if seasonal else f['absorbed']
 f['BIC']=len(q)*np.log((u@u)/len(q))+(absorbed+len(b))*np.log(len(q));f['AIC']=len(q)*np.log((u@u)/len(q))+2*(absorbed+len(b))
 f.update(X=X,y=y,b=b,u=u,bread=bread,V=r.cr1(X,u,q.uf.to_numpy(),absorbed),DK=r.dk(X,u,q),rank=rank,absorbed=absorbed,condition=float(np.linalg.cond(X)),df=G-1)
 if contrasts is not None:f['contrasts']=contrasts
 return f

def support(f,c):
 q=f['q'];X=f['X'];br=f['bread'];ug=sorted(q.uf.unique());window=q[[f'x{k}' for k in range(f['start'],f['K']+1)]].gt(0).any(axis=1)
 lev=np.array([np.trace(br@(X[q.uf.eq(g)].T@X[q.uf.eq(g)])) for g in ug]);lev/=lev.sum();c=np.asarray(c);v=X@br@c;cs=np.array([(v[q.uf.eq(g)]**2).sum() for g in ug]);cs/=cs.sum();ss=np.sort(cs)[::-1]
 scale=np.sqrt((X*X).sum(0));cond=float(np.linalg.cond(X/scale));months=q.loc[window,'data_base'].nunique();ufs=q.loc[window,'uf'].nunique();cells=int(window.sum())
 status='suporte mínimo insuficiente' if ufs<5 or cells<12 or months<8 else ('altamente concentrado' if 1/(cs@cs)<5 or ss[0]>.5 or ss[:2].sum()>.8 else 'com ressalvas' if cond>1000 else 'suporte mais amplo')
 return dict(ufs_janela=ufs,cells_janela=cells,meses_janela=months,ufs_x0=int(q.loc[q.x0>0,'uf'].nunique()),neff_leverage=1/(lev@lev),top_leverage=lev.max(),neff_contraste=1/(cs@cs),top1_contraste=ss[0],top2_contraste=ss[:2].sum(),uf_dominante=ug[int(cs.argmax())],condition_padronizada=cond,status_suporte=status,rank=f['rank'])

def metadata(f,per,c,spec='Principal',method='spline',measure='C_prop'):
 B=f['base'];q=f['q'];return dict(periodo=per,coluna=c,exposicao=r.label(c),nivel=r.level(c),especificacao=spec,metodo=method,J=B.shape[1] if method=='spline' else np.nan,q_almon=2 if method=='almon' else np.nan,n_parametros_exposicao=f['Z'].shape[1],K=f['K'],lag_inicio=f['start'],FE='UF + mês-ano + UF×mês calendário' if f.get('seasonal') else 'UF + região×mês-ano' if f['regional'] else 'UF + mês-ano',ponderado=bool(np.any(f['weights']!=1)),medida=measure,transformacao='identidade' if measure=='C_prop' else 'log1p',data_inicio=str(q.data_base.min().date()),data_fim=str(q.data_base.max().date()),N=len(q),meses=q.data_base.nunique(),ufs=q.uf.nunique())

def wcr(f,R,B=4999,null=None,return_stats=False):
 X,y,b,br=f['X'],f['y'],f['b'],f['bread'];q=f['q'];g=q.uf.to_numpy();ug=np.unique(g);G=len(ug);R=np.atleast_2d(R);null=np.zeros(len(R)) if null is None else np.atleast_1d(null)
 rb=R@br@R.T
 if np.linalg.matrix_rank(rb)<len(R):return dict(p=np.nan,status='restrição sem rank',singular=B)
 b0=b-br@R.T@np.linalg.solve(rb,R@b-null);u0=y-X@b0;root=np.sqrt(f['weights']);U=np.column_stack([np.where(g==v,u0,0) for v in ug]);U=absorb(f,U/root[:,None])*root[:,None]
 T=np.stack([X[g==v].T@U[g==v] for v in ug]);A=np.stack([X[g==v].T@X[g==v] for v in ug]);factor=G/(G-1)*(len(g)-1)/(len(g)-len(b)-f['absorbed']);rv=R@f['V']@R.T
 if np.linalg.matrix_rank(rv)<len(R):return dict(p=np.nan,status='covariância observada singular',singular=B)
 obs=float((R@b-null)@np.linalg.solve(rv,R@b-null));rng=np.random.default_rng(SEED);sing=0;vals=[];nums=[];covs=[]
 for lo in range(0,B,256):
  W=rng.choice([-1.,1.],size=(min(256,B-lo),G));raw=np.einsum('gph,bh->bgp',T,W);db=raw.sum(1)@br;scores=raw-np.einsum('gpq,bq->bgp',A,db);meat=np.einsum('bgp,bgq->bpq',scores,scores);V=factor*np.einsum('ip,bpq,qj->bij',br,meat,br);vr=np.einsum('ip,bpq,jq->bij',R,V,R);z=db@R.T
  ok=np.linalg.matrix_rank(vr)==len(R);sing+=int((~ok).sum());stat=np.full(len(W),np.nan)
  stat[ok]=np.einsum('bi,bij,bj->b',z[ok],np.linalg.inv(vr[ok]),z[ok]);vals.extend(stat.tolist())
  if return_stats:nums.extend(z.tolist());covs.extend(vr.tolist())
 vals=np.asarray(vals);p=(1+(vals>=obs-1e-12).sum())/(B+1) if sing==0 else np.nan
 out=dict(p=p,mcse=np.sqrt(p*(1-p)/(B+1)) if np.isfinite(p) else np.nan,status='calculado' if sing==0 else 'indisponível: sorteios singulares',singular=sing,B=B,obs=obs)
 if return_stats:out.update(stats=vals,numer=np.array(nums),cov=np.array(covs))
 return out

def export_r(f,id,meta,profiles=False):
 q=f['q'];d=q[['uf','data_base']].reset_index(drop=True).copy();d['y']=q.y.to_numpy();d['peso']=f['weights'];d['season']=q.uf.to_numpy()+'_'+q.data_base.dt.month.astype(str).to_numpy();d['regtime']=q.regiao.to_numpy()+'_'+q.data_base.astype(str).to_numpy()
 for j in range(f['Z'].shape[1]):d[f'z{j}']=f['Z'][:,j]
 d.to_csv(CACHE/(id+'.csv'),index=False);cons=f['contrasts'].copy();cons['joint']=f['R']
 if profiles:
  D=np.tril(np.ones((len(f['B']),len(f['B']))))
  for h in range(len(f['B'])):cons[f'beta_{h}']=f['B'][h];cons[f'C_{h}']=(D@f['B'])[h]
 rows=[]
 for ep,v in cons.items():
  for i,row in enumerate(np.atleast_2d(v)):rows.append(dict(endpoint=ep,row=i,**{f'z{j}':x for j,x in enumerate(row)}))
 pd.DataFrame(rows).to_csv(CACHE/(id+'.contrasts.csv'),index=False);pd.DataFrame({'estimate':f['b']}).to_csv(CACHE/(id+'.coef.csv'),index=False)
 return dict(id=id,**meta,seasonal=bool(f.get('seasonal')),regional=bool(f['regional']))

def inversion(f,c):
 est=float(c@f['b']);se=float(np.sqrt(c@f['V']@c));rows=[];edge=False
 for width in [4,12,36]:
  grid=np.linspace(est-width*se,est+width*se,49)
  rr=[wcr(f,c,9999,null=x) for x in grid];rows=[dict(null=x,p=z['p'],status=z['status'],singular=z['singular']) for x,z in zip(grid,rr)]
  valid=all(np.isfinite(z['p']) for z in rr)
  if not valid:return rows,dict(low=np.nan,high=np.nan,status='indisponível: singularidade',resolucao=np.diff(grid)[0])
  accept=np.array([z['p']>=.05 for z in rr]);edge=bool(accept[0] or accept[-1])
  if not edge:break
 accepted=grid[accept];segments=int(np.sum(accept & ~np.r_[False,accept[:-1]]))
 return rows,dict(low=accepted.min() if len(accepted) and not edge else np.nan,high=accepted.max() if len(accepted) and not edge else np.nan,grade_min=float(grid.min()),grade_max=float(grid.max()),status='não limitado na grade' if edge else 'aproximação em grade; '+str(segments)+' componente(s)',resolucao=np.diff(grid)[0],componentes=segments)

def load_main(per,c):
 d=r.load_panel();e=r.get_exps();row=pd.read_csv(PREV/'principais.csv');row=row[(row.periodo==per)&(row.coluna==c)].iloc[0];keep=d.data_base.between(*r.PERIODS[per]);q=calendar_lags(d.loc[keep],e[c]['C_prop'][keep]);f=r.model(q,r.basis(12,int(row.J)));f['seasonal']=False
 assert np.allclose(f['b']@f['contrasts']['acumulado'],row.acumulado_cluster_estimate,rtol=1e-9,atol=1e-10)
 return f

def panel():
 old=pd.read_csv(PREV/'principais.csv');rows=[];supports=[];manifest=[];fits={};inv=[];invgrids=[]
 for i,v in enumerate(old.itertuples()):
  f=load_main(v.periodo,v.coluna);meta=metadata(f,v.periodo,v.coluna);fits[(v.periodo,v.coluna)]=f;rows.append(dict(**meta,**{x:y for x,y in v._asdict().items() if x not in meta and x!='Index'}));supports.append(dict(**meta,endpoint='acumulado',**support(f,f['contrasts']['acumulado'])))
  central=v.coluna in r.CENTRAL;ss=support(f,f['contrasts']['acumulado']);manifest.append(export_r(f,'main_'+str(i),meta,central or ss['status_suporte']=='altamente concentrado'))
  for spec in ['Sazonalidade UF','Exclui DF']:
   ff=rebuild(f,seasonal=True) if spec=='Sazonalidade UF' else r.model(f['q'][f['q'].uf.ne('DF')],f['base']);ff['seasonal']=spec=='Sazonalidade UF';mm=metadata(ff,v.periodo,v.coluna,spec);rr=r.result_row(ff,{k:v for k,v in mm.items() if k not in ['N','K']});rr.update({k:z for k,z in wcr(ff,ff['contrasts']['acumulado'],9999 if central else 4999).items() if k!='obs'});rr['acumulado_boot_p']=rr.pop('p');rows.append(rr);supports.append(dict(**mm,endpoint='acumulado',**support(ff,ff['contrasts']['acumulado'])));manifest.append(export_r(ff,'new_'+str(i)+'_'+str(spec=='Exclui DF'),mm,central));fits[(v.periodo,v.coluna,spec)]=ff
  if central:
   grid,ci=inversion(f,f['contrasts']['acumulado']);inv.append(dict(**meta,**ci));invgrids.extend(dict(**meta,**z) for z in grid)
  print('painel',i,v.periodo,v.coluna,flush=True)
 save(pd.DataFrame(rows),'painel');save(pd.DataFrame(supports),'suporte_design');save(pd.DataFrame(inv),'bootstrap_intervalos');save(pd.DataFrame(invgrids),'bootstrap_grade');pd.DataFrame(manifest).to_csv(CACHE/'manifest.csv',index=False)
 return fits

def correct_multiverse(fits):
 d=r.load_panel();e=r.get_exps();old=pd.read_csv(PREV/'multiverse.csv');rows=[];su=[];profiles=[]
 for v in old.itertuples():
  per,c,spec=v.periodo,v.coluna,v.especificacao;main=fits[(per,c)];keep=d.data_base.between(*r.PERIODS[per]);dp=d.loc[keep];K=int(v.K);start=1 if spec=='Somente defasado' else 0;method='irrestrito' if spec.startswith('Irrestrito') else 'almon' if spec.startswith('Almon') else 'spline';J=7-int(v.J) if spec=='J alternativo' else int(v.J);B=r.basis(K,J,start,method);measure=v.medida;q=calendar_lags(dp,r.transform(e[c][measure][keep],measure))
  if spec.startswith('Exclui mar'):q=q[~q.data_base.between('2020-03-01','2021-12-01')]
  f=r.model(q,B,start,K,spec=='Região × tempo',spec=='Ponderado CA2013');f['seasonal']=False;meta=metadata(f,per,c,spec,method,measure);assert np.allclose(f['b']@f['contrasts']['acumulado'],v.acumulado_cluster_estimate,atol=1e-9,rtol=1e-8)
  row=v._asdict();row.pop('Index');row.update(meta);rows.append(row);su.append(dict(**meta,endpoint='acumulado',**support(f,f['contrasts']['acumulado'])))
  if c in r.CENTRAL:profiles.append(r.profile(f,meta))
 save(pd.DataFrame(rows),'multiverse_corrigida');save(pd.DataFrame(su),'suporte_multiverse');save(pd.concat(profiles,ignore_index=True),'perfis_multiverse')
 # Existing diagnostics now get actual design support without changing old results.
 ss=[];loo=pd.read_csv(PREV/'onda_frio_leave_out.csv')
 for v in loo.itertuples():
  f0=fits[(v.periodo,'tipo_onda_de_frio')];drop=v.retirada.split(' + ');f=r.model(f0['q'][~f0['q'].uf.isin(drop)],f0['base']);f['seasonal']=False;ss.append(dict(periodo=v.periodo,coluna=v.coluna,especificacao='Retira '+v.retirada,**support(f,f['contrasts']['acumulado'])))
 for name,extra in [('Placebo','leads'),('Interação','interaction')]:
  for key,f0 in list(fits.items()):
   if len(key)!=2:continue
   per,c=key
   if extra=='interaction' and per!='Total':continue
   f=r.model(f0['q'],f0['base'],extra=extra);f['seasonal']=False
   for ep,v in f['contrasts'].items():ss.append(dict(periodo=per,coluna=c,especificacao=name,endpoint=ep,**support(f,v)))
 save(pd.DataFrame(ss),'suporte_diagnosticos')

def joint_models(fits):
 d=r.load_panel();e=r.get_exps();cols=[c for c in e if c.startswith('analitica_')];rows=[];cor=[];manifest=pd.read_csv(CACHE/'manifest.csv').to_dict('records')
 for per in r.PERIODS:
  fs=[fits[(per,c)] for c in cols];f0=fs[0];Z=np.column_stack([f['Z'] for f in fs]);B=linalg.block_diag(*[f['base'] for f in fs]);contrasts={}
  for j,c in enumerate(cols):
   cc=np.zeros(Z.shape[1]);cc[3*j:3*j+3]=fs[j]['base'].sum(0);contrasts[c]=cc
  f=rebuild(f0,Z=Z,contrasts=contrasts);f['B']=B;f['R']=np.eye(Z.shape[1]);f['base']=fs[0]['base'];meta=metadata(f,per,'total_desastres','Conjunto COBRADE');manifest.append(export_r(f,'joint_'+per,meta))
  for c,cc in contrasts.items():
   z=r.contrast(f['b'],f['V'],cc,f['df']);w=wcr(f,cc,9999);rows.append(dict(periodo=per,coluna=c,exposicao=r.label(c),**z,boot_p=w['p'],boot_singular=w['singular'],**support(f,cc)))
  # Across all exposures audit block correlations after FE (not causal controls selection).
  cc=[key[1] for key in fits if len(key)==2 and key[0]==per];xx=np.column_stack([fits[(per,c)]['q'].x0 for c in cc]);res=r.residualize(f0['q'],xx);M=np.corrcoef(res.T);raw=np.corrcoef(xx.T)
  for i in range(len(cc)):
   for j in range(i):
    a=fits[(per,cc[i])];b=fits[(per,cc[j])];block=np.corrcoef(np.column_stack([a['X'],b['X']]).T)[:a['X'].shape[1],a['X'].shape[1]:]
    cor.append(dict(periodo=per,coluna1=cc[i],coluna2=cc[j],cor_x0=raw[i,j],cor_x0_FE=M[i,j],max_abs_cor_blocos=np.max(abs(block)),coocorrencias=int(((xx[:,i]>0)&(xx[:,j]>0)).sum())))
 save(pd.DataFrame(rows),'conjuntos');save(pd.DataFrame(cor),'correlacoes_exposicoes');pd.DataFrame(manifest).to_csv(CACHE/'manifest.csv',index=False)

def national_design(per,c,J=3,p=1):
 d=r.load_panel();e=r.get_exps();a=d.groupby('data_base')[['carteira_ativa_total','carteira_inadimplencia_total']].sum();I=100*a.carteira_inadimplencia_total/a.carteira_ativa_total;x=pd.DataFrame({'t':d.data_base,'x':e[c]['C']}).groupby('t').x.sum()/5570
 z=pd.DataFrame({'I':I,'x':x}).loc[slice(*r.PERIODS[per])];z['y']=z.I.diff()
 for k in range(13):z[f'x{k}']=z.x.shift(k)
 for k in [1,2]:z[f'y{k}']=z.y.shift(k)
 for k in [1,2,3]:z[f'lead{k}']=z.x.shift(-k)
 z=z.dropna(subset=['y']+[f'x{k}' for k in range(13)]+['y1','y2']);B=r.basis(12,J);Z=z[[f'x{k}' for k in range(13)]].to_numpy()@B;sea=pd.get_dummies(z.index.month,drop_first=True,dtype=float).to_numpy();X=np.column_stack([np.ones(len(z)),Z,sea,np.arange(len(z))/12]+[z[[f'y{k}' for k in range(1,p+1)]].to_numpy()] if p else [np.ones(len(z)),Z,sea,np.arange(len(z))/12]);return z,X,B

def hac_calendar(X,u,t,L):
 u=np.asarray(u);br=np.linalg.inv(X.T@X);score=X*u[:,None];V=score.T@score;ordinal=pd.DatetimeIndex(t).to_period('M').asi8;lookup={v:i for i,v in enumerate(ordinal)}
 for k in range(1,L+1):
  ix=[(i,lookup[v-k]) for i,v in enumerate(ordinal) if v-k in lookup]
  if ix:
   a,b=np.array(ix).T;cross=score[a].T@score[b];V+=(1-k/(L+1))*(cross+cross.T)
 return len(u)/(len(u)-X.shape[1])*br@V@br

def dynamic(beta,B,p,H=24):
 beta=np.asarray(beta);b=B@beta[1:1+B.shape[1]];ar=beta[-p:] if p else [];out=[]
 for h in range(H+1):out.append((b[h] if h<len(b) else 0)+sum(ar[j-1]*out[h-j] for j in range(1,p+1) if h>=j))
 return np.asarray(out)

def dynamic_jacobian(beta,B,p,H=24):
 beta=np.asarray(beta,float);jac=np.empty((H+1,len(beta)))
 for j in range(len(beta)):
  step=1e-5*max(1,abs(beta[j]));plus=beta.copy();minus=beta.copy();plus[j]+=step;minus[j]-=step;jac[:,j]=(dynamic(plus,B,p,H)-dynamic(minus,B,p,H))/(2*step)
 return jac

def national():
 prev=pd.read_csv(PREV/'nacional.csv');central=prev[prev.q_global_p_acumulado<.05];rows=[];prof=[];infl=[];place=[]
 from statsmodels.stats.diagnostic import acorr_ljungbox
 for v in central.itertuples():
  per,c,p=v.periodo,v.coluna,int(v.p_proprio);z,X,B=national_design(per,c,p=p);fullfit=OLS(z.y,X).fit();V=hac_calendar(X,fullfit.resid,z.index,12);assert np.allclose(fullfit.params[1:4]@B.sum(0),v.acumulado_direto,rtol=1e-8);assert np.allclose(V,fullfit.get_robustcov_results(cov_type='HAC',maxlags=12,use_correction=True).cov_params(),atol=1e-7,rtol=1e-7)
  ar=fullfit.params[-p:] if p else [];stable=np.all(abs(np.roots(np.r_[1,-np.asarray(ar)]))<1) if p else True
  inf=fullfit.get_influence();exp=z.x;top=exp.sort_values(ascending=False).index[:3];peak=top[0];models=[('Principal',z,X,B,p,12),('HAC6',z,X,B,p,6),('HAC18',z,X,B,p,18)]
  for J in [4]:zz,xx,bb=national_design(per,c,J,p);models.append(('J4',zz,xx,bb,p,12))
  for pp in [0,1,2]:zz,xx,bb=national_design(per,c,3,pp);models.append(('AR'+str(pp),zz,xx,bb,pp,12))
  for year in sorted(z.index.year.unique()):
   keep=z.index.year!=year;models.append(('Retira ano '+str(year),z.loc[keep],X[keep],B,p,12))
  for t in top:
   keep=z.index!=t;models.append(('Retira mês '+str(t.date()),z.loc[keep],X[keep],B,p,12))
  keep=~((z.index>=peak)&(z.index<=peak+pd.DateOffset(months=12)));models.append(('Retira janela dominante',z.loc[keep],X[keep],B,p,12))
  for spec,zz,xx,bb,pp,L in models:
   f=OLS(zz.y,xx).fit();rank=np.linalg.matrix_rank(xx)
   if rank<xx.shape[1]:rows.append(dict(periodo=per,coluna=c,especificacao=spec,status='não estimável: rank'));continue
   VV=hac_calendar(xx,f.resid,zz.index,L);contrast=np.zeros(xx.shape[1]);contrast[1:1+bb.shape[1]]=bb.sum(0);rr=r.contrast(f.params,VV,contrast,f.df_resid);ars=f.params[-pp:] if pp else [];st=bool(np.all(abs(np.roots(np.r_[1,-np.asarray(ars)]))<1)) if pp else True
   rows.append(dict(periodo=per,coluna=c,exposicao=r.label(c),especificacao=spec,status='calculado',**rr,rank=rank,n=len(zz),AR=pp,J=bb.shape[1],HAC=L,estavel=st,condition=float(np.linalg.cond(xx/np.sqrt((xx*xx).sum(0)))),mes_dominante=str(peak.date()),participacao_mes=float(exp.max()/exp.sum()),ljungbox12_p=float(acorr_ljungbox(f.resid,lags=[12]).lb_pvalue.iloc[0])))
   if spec=='Principal' and st:
    resp=dynamic(f.params,bb,pp);jac=dynamic_jacobian(f.params,bb,pp)
    cv=jac@VV@jac.T;D=np.tril(np.ones((25,25)));cum=D@resp;vc=D@cv@D.T;crit=stats.t.ppf(.975,f.df_resid)
    for h in range(25):prof.append(dict(periodo=per,coluna=c,exposicao=r.label(c),h=h,resposta=resp[h],low=resp[h]-crit*np.sqrt(max(0,cv[h,h])),high=resp[h]+crit*np.sqrt(max(0,cv[h,h])),C=cum[h],C_low=cum[h]-crit*np.sqrt(max(0,vc[h,h])),C_high=cum[h]+crit*np.sqrt(max(0,vc[h,h])),metodo='Delta/HAC12, covariância completa; ponto a ponto'))
  for j,t in enumerate(z.index):infl.append(dict(periodo=per,coluna=c,data=str(t.date()),exposicao=z.x.iloc[j],hat=inf.hat_matrix_diag[j],cook=inf.cooks_distance[0][j],residuo=fullfit.resid.iloc[j]))
  kk=z[['lead1','lead2','lead3']].notna().all(1);XP=np.column_stack([X[kk],z.loc[kk,['lead1','lead2','lead3']]]);fit=OLS(z.loc[kk,'y'],XP).fit();vv=hac_calendar(XP,fit.resid,z.index[kk],12);R=np.column_stack([np.zeros((3,X.shape[1])),np.eye(3)]);place.append(dict(periodo=per,coluna=c,p=r.joint(fit.params,vv,R,fit.df_resid),N=int(kk.sum())))
  print('nacional',per,c,flush=True)
 save(pd.DataFrame(rows),'nacional_robustez');save(pd.DataFrame(prof),'nacional_dinamica');save(pd.DataFrame(infl),'nacional_influencia');save(r.fdr_table(pd.DataFrame(place),['p'],4),'nacional_placebos')

def validate_external(fits):
 from wildboottest.wildboottest import WildboottestCL
 rows=[]
 cases=[('Total','total_desastres'),('Total','tipo_onda_de_frio')]
 for per,c in cases:
  f=fits[(per,c)];q=f['q'];Z=f['Z'];D=pd.get_dummies(q.uf,dtype=float).to_numpy();T=pd.get_dummies(q.data_base,drop_first=True,dtype=float).to_numpy();full=np.column_stack([Z,D,T]);y=q.y.to_numpy();groups=pd.factorize(q.uf)[0];ugs=np.unique(q.uf)
  for endpoint,ff in [('acumulado',f),('interacao',r.model(q,f['base'],extra='interaction'))]:
   if endpoint=='interacao':Z=ff['Z'];full=np.column_stack([Z,D,T]);cc=ff['contrasts']['diferenca']
   else:cc=ff['contrasts']['acumulado']
   R=np.r_[cc,np.zeros(full.shape[1]-len(cc))];boot=WildboottestCL(full,y,groups,R,4999,seed=SEED,parallel=False);boot.get_scores('11',True,True,True)
   # Same weights, sorted by UF in both implementations.
   W=np.random.default_rng(SEED).choice([-1.,1.],size=(4999,len(ugs)));order=np.argsort([ugs.tolist().index(q.uf.iloc[np.flatnonzero(groups==g)[0]]) for g in np.unique(groups)])
   boot.v=W[:,[ugs.tolist().index(q.uf.iloc[np.flatnonzero(groups==g)[0]]) for g in np.unique(groups)]].T;boot.get_numer();boot.get_denom();boot.get_tboot();boot.get_vcov();boot.get_tstat();ours=wcr(ff,cc,4999,return_stats=True)
   err=float(np.max(abs(np.asarray(boot.t_boot)**2-ours['stats'])));assert err<1e-5,(per,c,endpoint,err)
   assert np.allclose(boot.numer,ours['numer'][:,0],atol=1e-8)
   assert np.allclose(boot.denom,ours['cov'][:,0,0],atol=1e-8)
   rows.append(dict(periodo=per,coluna=c,endpoint=endpoint,implementacao='wildboottest0.3.2 FE explícitos; pesos idênticos',B=4999,max_diff_stat=err,p=ours['p'],passou=True))
  # Joint null: independent explicit-FE OLS refit and statsmodels cov_cluster.
  f=fits[(per,c)];full=np.column_stack([f['Z'],D,T]);R=np.column_stack([np.eye(f['Z'].shape[1]),np.zeros((f['Z'].shape[1],full.shape[1]-f['Z'].shape[1]))]);b=OLS(y,full).fit().params;br=np.linalg.inv(full.T@full);b0=b-br@R.T@np.linalg.solve(R@br@R.T,R@b);u0=y-full@b0;W=np.random.default_rng(SEED).choice([-1.,1.],size=(99,len(ugs)));ours=wcr(f,f['R'],99,return_stats=True);errs=[]
  for j,ww in enumerate(W):
   ys=full@b0+u0*np.array([ww[ugs.tolist().index(g)] for g in q.uf]);fit=OLS(ys,full).fit();vc=cov_cluster(fit,q.uf,use_correction=True);rb=R@fit.params;vv=R@vc@R.T;st=float(rb@np.linalg.solve(vv,rb));errs.append(abs(st-ours['stats'][j]))
  assert max(errs)<1e-5;rows.append(dict(periodo=per,coluna=c,endpoint='joint',implementacao='statsmodels refit FE explícitos/cov_cluster; pacote wildboottest só escalar',B=99,max_diff_stat=max(errs),p=ours['p'],passou=True))
 save(pd.DataFrame(rows),'validacao_bootstrap_externa')

def atlas_audit():
 a=pd.read_csv(ROOT/'data/raw/atlas_desastres/atlas.csv',sep=';',encoding='latin1',low_memory=False);dates=[c for c in a if 'data' in c.lower()];a['data_evento']=pd.to_datetime(a.Data_Evento,format='%d/%m/%Y',errors='coerce');a=a[a.data_evento.dt.year.between(2013,2024)].copy();year=a.data_evento.dt.year
 rows=[]
 for yy,g in a.groupby(year):rows.append(dict(ano=yy,registros=len(g),municipios=g.Cod_IBGE_Mun.nunique(),protocolos_distintos=g.Protocolo_S2iD.nunique(),protocolos_ausentes=int(g.Protocolo_S2iD.isna().sum())))
 reg=pd.to_datetime(a.Data_Registro,format='%d/%m/%Y',errors='coerce');a['atraso_dias']=(reg-a.data_evento).dt.days;lag=a.groupby(year).atraso_dias.agg(['count','median','max']).reset_index();save(lag,'atlas_atraso_registro');save(pd.DataFrame(rows),'atlas_anos');(OUT/'atlas_campos.json').write_text(json.dumps(dict(campos_datas=dates,campos=list(a.columns),duracao='Nenhuma duração física preenchida; campos auditados, não inferir duração pelo registro'),ensure_ascii=False,indent=2))


def finalize():
 panel=pd.read_csv(OUT/'painel.csv');cr=pd.read_csv(OUT/'cr2.csv');
 jointmask=cr.especificacao.eq('Conjunto COBRADE') & cr.endpoint.str.startswith('analitica_');cr.loc[jointmask,'coluna']=cr.loc[jointmask,'endpoint'];cr.loc[jointmask,'exposicao']=cr.loc[jointmask,'coluna'].map(r.label);cr.loc[jointmask,'endpoint']='acumulado';su=pd.read_csv(OUT/'suporte_design.csv');oldm=pd.read_csv(OUT/'multiverse_corrigida.csv');e=r.get_exps();d=r.load_panel();classification=[];scenarios=[];stability=[]
 checked=OUT/'bootstrap_checado.csv'
 if checked.exists():
  cb=pd.read_csv(checked)
  for vv in cb[cb.design=='Principal'].itertuples():
   ix=(panel.periodo==vv.periodo)&(panel.coluna==vv.coluna)&(panel.especificacao=='Principal');panel.loc[ix,('acumulado_boot_p' if vv.endpoint=='acumulado' else 'joint_boot_p')]=vv.p
 for spec,idx in panel.groupby('especificacao').groups.items():
  for p in ['acumulado_cluster_p','acumulado_boot_p','joint_cluster_p']:
   if p in panel:panel.loc[idx,'q_'+p]=r.fdr_table(panel.loc[idx,[p]].copy(),[p],48)['q_global_'+p]
 for (spec,ep),idx in cr.groupby(['especificacao','endpoint']).groups.items():
  if ep.startswith(('beta_','C_')):continue
  size=(2 if ep=='joint' else 6) if spec=='Conjunto COBRADE' else 48;vals=cr.loc[idx,'p'].fillna(1).to_numpy();cr.loc[idx,'q']=r.multipletests(np.r_[vals,np.ones(max(0,size-len(vals)))],method='fdr_bh')[1][:len(vals)]
 save(cr,'cr2');save(panel,'painel')
 for v in panel[panel.especificacao=='Principal'].itertuples():
  ss=su[(su.periodo==v.periodo)&(su.coluna==v.coluna)&(su.especificacao=='Principal')].iloc[0];cc=cr[(cr.periodo==v.periodo)&(cr.coluna==v.coluna)&(cr.especificacao=='Principal')&(cr.endpoint=='acumulado')].iloc[0];jj=cr[(cr.periodo==v.periodo)&(cr.coluna==v.coluna)&(cr.especificacao=='Principal')&(cr.endpoint=='joint')].iloc[0]
  xx=e[v.coluna]['C_prop'][d.data_base.between(*r.PERIODS[v.periodo])];delta=float(np.median(xx[xx>0]));scenarios.append(dict(periodo=v.periodo,coluna=v.coluna,exposicao=v.exposicao,cenario='0 → mediana positiva de cobertura',delta=delta,delta_pp=100*delta,estimate=cc.estimate*delta,low=cc.low*delta,high=cc.high*delta,df=cc.df,metodo='CR2/Satterthwaite',precisao='IC inclui ambos os sinais' if cc.low<0<cc.high else 'IC de um sinal, condicionado ao modelo'))
  candidates=oldm[(oldm.periodo==v.periodo)&(oldm.coluna==v.coluna)&(oldm.medida=='C_prop')];new=panel[(panel.periodo==v.periodo)&(panel.coluna==v.coluna)&(panel.especificacao!='Principal')];alt=pd.concat([candidates,new],ignore_index=True)
  for a in alt.itertuples():stability.append(dict(periodo=v.periodo,coluna=v.coluna,especificacao=a.especificacao,principal=v.acumulado_cluster_estimate,alternativa=a.acumulado_cluster_estimate,muda_sinal=bool(a.acumulado_cluster_estimate*v.acumulado_cluster_estimate<0),delta_em_SE=(a.acumulado_cluster_estimate-v.acumulado_cluster_estimate)/cc.se))
  changes=int((alt.acumulado_cluster_estimate*v.acumulado_cluster_estimate<0).sum());classification.append(dict(periodo=v.periodo,coluna=v.coluna,exposicao=v.exposicao,suporte=ss.status_suporte,inferencia_acumulado=cc.status,inferencia_conjunta=jj.status,estabilidade_sinal=f'{changes} de {len(alt)} sensibilidades na mesma unidade mudam sinal',evidencia='associação acumulada após BH/CR2' if cc.q<.05 else 'sem rejeição acumulada BH/CR2; não equivale a ausência',perfil='teste conjunto BH/HTZ rejeita' if jj.q<.05 else 'inferência conjunta indisponível' if jj.status!='calculado' else 'sem rejeição conjunta BH/HTZ',interpretacao_temporal='descrever curva e incerteza, sem duração inferida por p',relevancia='ver cenário e IC; sem margem de equivalência arbitrária'))
 save(pd.DataFrame(classification),'classificacao');save(pd.DataFrame(scenarios),'cenarios');save(pd.DataFrame(stability),'estabilidade')
 for name in ['perfis','placebos','interacao','onda_frio_rastreio_A','onda_frio_leave_out','nacional','nacional_perfis','taxonomia_cobrade','suporte','cips','cips_exposicoes','decomposicao']:
  save(pd.read_csv(PREV/(name+'.csv')),name+'_preservado')
 versions={x:importlib.metadata.version(x) for x in ['numpy','pandas','scipy','statsmodels','patsy','matplotlib','pyarrow','nbformat','ipython','wildboottest']};(ROOT/'requirements-dlm-validacao-final.lock.txt').write_text('\n'.join(f'{k}=={v}' for k,v in versions.items())+'\n');(OUT/'versoes.json').write_text(json.dumps(versions,indent=2))

def checkpoint():
 import datetime
 files=[ROOT/'README.md',ROOT/'docs/dlm_validacao_final_resultados.md',ROOT/'docs/dlm_validacao_final_checkpoint.md',ROOT/'docs/dlm_validacao_final_protocolo.md',ROOT/'src/dlm_validacao_final.py',ROOT/'src/dlm_validacao_final_inferencia.R',ROOT/'src/dlm_validacao_final_relatorio.py',ROOT/'src/verificar_dlm_validacao_final.py',ROOT/'requirements-dlm-validacao-final.lock.txt',ROOT/'data/processed/df_tcc_2013_2024.csv',ROOT/'data/processed/df_tcc_2013_2024.parquet',ROOT/'data/raw/atlas_desastres/atlas.csv']+list(OUT.glob('*.csv'))+list(OUT.glob('*.txt'))+list(FIG.glob('*.svg'))
 nb=ROOT/'notebooks/18_validacao_final_dlm.ipynb'
 if nb.exists():files.append(nb)
 cp=dict(status='executado e validado',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),origem='c64589abc0f886a4e55e73b32328f8b0206376aa',arquivos={str(p.relative_to(ROOT)):r.sha(p) for p in files})
 (OUT/'checkpoint.json').write_text(json.dumps(cp,ensure_ascii=False,indent=2));return cp

def resume():
 cp=json.loads((OUT/'checkpoint.json').read_text())
 for p,h in cp['arquivos'].items():assert r.sha(ROOT/p)==h,'Hash divergente: '+p
 return cp

def run_all():
 # Previous source tables are protected by their original checkpoint.
 cp=json.loads((PREV/'checkpoint.json').read_text())
 for p,h in cp['arquivos'].items():assert r.sha(ROOT/p)==h
 fits=panel();checked_bootstraps();correct_multiverse(fits);joint_models(fits);national();validate_external(fits);atlas_audit()
 exe=os.getenv('DLM_R_EXEC','Rscript');script=ROOT/'src/dlm_validacao_final_inferencia.R'
 if (OUT/'cr2.csv').exists():(OUT/'cr2.csv').unlink()
 cmd=[exe,str(script),str(ROOT)] if Path(exe).name=='Rscript' else [exe,'--vanilla','--slave','--file='+str(script),'--args',str(ROOT)]
 subprocess.run(cmd,check=True);finalize();alternative_scenarios()
 from verificar_dlm_validacao_final import verify
 verify()
 from dlm_validacao_final_relatorio import figures,documentation,report
 figures();documentation();report(ROOT.parent/'relatorio_dlm_validacao_final.html');checkpoint()

def checked_bootstraps():
 rows=[];old=pd.read_csv(PREV/'principais.csv')
 for i,v in enumerate(old.itertuples()):
  f=load_main(v.periodo,v.coluna);BB=9999 if v.coluna in r.CENTRAL else 4999
  for ep,R in [('acumulado',f['contrasts']['acumulado']),('joint',f['R'])]:rows.append(dict(periodo=v.periodo,coluna=v.coluna,design='Principal',endpoint=ep,**wcr(f,R,BB)))
  lead=r.model(f['q'],f['base'],extra='leads');rows.append(dict(periodo=v.periodo,coluna=v.coluna,design='Placebo',endpoint='joint',**wcr(lead,lead['R'],BB)))
  if v.periodo=='Total':
   inter=r.model(f['q'],f['base'],extra='interaction')
   for ep,R in [('diferenca',inter['contrasts']['diferenca']),('joint',inter['R'])]:rows.append(dict(periodo=v.periodo,coluna=v.coluna,design='Interação',endpoint=ep,**wcr(inter,R,BB)))
  for spec in ['Sazonalidade UF','Exclui DF']:
   ff=rebuild(f,seasonal=True) if spec=='Sazonalidade UF' else r.model(f['q'][f['q'].uf.ne('DF')],f['base']);rows.append(dict(periodo=v.periodo,coluna=v.coluna,design=spec,endpoint='joint',**wcr(ff,ff['R'],BB)))
  print('bootstrap rank',i,v.coluna,flush=True)
 out=pd.DataFrame(rows)
 for (design,ep),idx in out.groupby(['design','endpoint']).groups.items():
  size=24 if design=='Interação' else 48;out.loc[idx,'q']=r.fdr_table(out.loc[idx,['p']].copy(),['p'],size).q_global_p
 save(out,'bootstrap_checado');return out

def alternative_scenarios():
 d=r.load_panel();e=r.get_exps();m=pd.read_csv(OUT/'multiverse_corrigida.csv');rows=[]
 for v in m[m.especificacao.str.startswith('Exposição ')].itertuples():
  xx=e[v.coluna][v.medida][d.data_base.between(*r.PERIODS[v.periodo])];med=float(np.median(xx[xx>0]));delta=float(np.log1p(med));rows.append(dict(periodo=v.periodo,coluna=v.coluna,exposicao=v.exposicao,medida=v.medida,mediana_positiva=med,delta_log1p=delta,estimate=v.acumulado_cluster_estimate*delta,low=v.acumulado_cluster_low*delta,high=v.acumulado_cluster_high*delta,metodo='CR1 comparativo, não CR2',cenario='0 → mediana positiva da medida; cenários não equivalentes fisicamente'))
 save(pd.DataFrame(rows),'cenarios_alternativos')

if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--reproduzir',action='store_true');a.add_argument('--retomar',action='store_true');opt=a.parse_args()
 if opt.reproduzir:run_all()
 elif opt.retomar:print(json.dumps(resume(),ensure_ascii=False,indent=2))
 else:a.error('Use --reproduzir ou --retomar')


