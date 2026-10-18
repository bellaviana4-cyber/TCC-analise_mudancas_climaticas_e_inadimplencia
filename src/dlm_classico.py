"""DLM irrestrito 1..10: sem spline, calendário e artefatos anteriores preservados."""
from pathlib import Path
import argparse, hashlib, json, warnings, subprocess, importlib.metadata, os
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits
import dlm_revisao as r
import dlm_validacao_final as v
ROOT=r.ROOT; OUT=ROOT/'outputs/tables/dlm_classico'; CACHE=ROOT/'data/interim/dlm_classico'; FIG=ROOT/'outputs/figures/dlm_classico'
ALPHA=.05

def save(d,name):
 OUT.mkdir(parents=True,exist_ok=True);t=OUT/(name+'.tmp');d.to_csv(t,index=False,encoding='utf-8-sig');t.replace(OUT/(name+'.csv'));return d

def ordered_lags(d,x):
 return v.calendar_lags(d,x)

def fit(q,K,start=1):
 q=q.copy();Z=q[[f'x{k}' for k in range(start,K+1)]].to_numpy();YX=r.residualize(q,np.column_stack([q.y,Z]));y=YX[:,0];X=YX[:,1:]
 if np.linalg.matrix_rank(X)!=X.shape[1]:raise ValueError('regressores sem rank completo')
 br=np.linalg.inv(X.T@X);b=br@X.T@y;u=y-X@b;G=q.uf.nunique();T=q.data_base.nunique();a=G+T-1;p=len(b);n=len(q)
 if n<=a+p:raise ValueError('graus de liberdade residuais não positivos')
 cs={'acumulado':np.ones(p),'defasado':(np.arange(start,K+1)>0).astype(float)}
 if start==0:cs['contemporaneo']=np.eye(p)[0]
 return dict(q=q,Z=Z,X=X,y=y,b=b,u=u,V=r.cr1(X,u,q.uf.to_numpy(),a),DK=r.dk(X,u,q),bread=br,B=np.eye(p),base=np.eye(p),contrasts=cs,R=np.eye(p),absorbed=a,regional=False,seasonal=False,weights=np.ones(n),K=K,start=start,n=n,df=G-1,BIC=n*np.log(u@u/n)+(a+p)*np.log(n),AIC=n*np.log(u@u/n)+2*(a+p),rank=p,condition=float(np.linalg.cond(X)))

def metadata(f,per,c,spec):
 q=f['q'];return dict(periodo=per,coluna=c,exposicao=r.label(c),nivel=r.level(c),especificacao=spec,metodo='DLM irrestrito',K=f['K'],lag_inicio=f['start'],J=np.nan,n_parametros_exposicao=len(f['b']),FE='UF + mês-ano',medida='C_prop',transformacao='primeira diferença' if spec=='Delta X' else 'identidade',ponderado=False,N=len(q),meses=q.data_base.nunique(),ufs=q.uf.nunique(),data_inicio=str(q.data_base.min().date()),data_fim=str(q.data_base.max().date()),AIC=f['AIC'],BIC=f['BIC'],rank=f['rank'],condition=f['condition'])

def bh(d,keys,pcols,size):
 for pcol in pcols:
  qcol='q_'+pcol;d[qcol]=np.nan
  for _,g in d.groupby(keys,dropna=False):
   p=g[pcol].fillna(1).to_numpy();qq=multipletests(np.r_[p,np.ones(size-len(p))],method='fdr_bh')[1][:len(p)];d.loc[g.index,qcol]=qq
 return d

def audits():
 for p in [OUT,CACHE,FIG]:p.mkdir(parents=True,exist_ok=True)
 d=r.load_panel();a=pd.read_csv(ROOT/'data/raw/atlas_desastres/atlas.csv',sep=';',encoding='latin1',low_memory=False)
 a['date']=pd.to_datetime(a.Data_Evento,format='%d/%m/%Y',errors='coerce');a=a[a.date.dt.year.between(2013,2024)].copy();a['uf']=a.Sigla_UF.str.strip();a['data_base']=a.date.dt.to_period('M').dt.to_timestamp()
 key=['uf','Cod_IBGE_Mun','date','Cod_Cobrade'];u=a.drop_duplicates(key,keep='first');idx=['uf','data_base'];before=a.groupby(idx).Cod_IBGE_Mun.nunique();after=u.groupby(idx).Cod_IBGE_Mun.nunique();assert before.equals(after)
 assert len(a)==40339 and len(u)==40238 and not a[key].isna().any().any()
 save(pd.DataFrame([dict(A=len(a),B=len(u),repeticoes_chave=len(a)-len(u),C_invariante=True,regra='UF + IBGE município + data evento + COBRADE; keep-first somente B; C=nunique município')]),'auditoria_chaves')
 # Taxonomia consistente dentro de cada chave, necessária para keep-first B por categoria.
 assert a.groupby(key)[['grupo_de_desastre','descricao_tipologia']].nunique().max().max()==1
 a['classe_analitica']=a.Cod_Cobrade.map(r.analytical);ex=r.get_exps();index=pd.MultiIndex.from_frame(d[['uf','data_base']]);recon=[]
 for col,mask in r.masks(a,d).items():
  aa=a.loc[mask];counts=aa.groupby(['uf','data_base']).size().reindex(index,fill_value=0).to_numpy();territory=aa.groupby(['uf','data_base']).Cod_IBGE_Mun.nunique().reindex(index,fill_value=0).to_numpy()
  prop=territory/d.uf.map(r.MUNICIPIOS).to_numpy();assert np.array_equal(counts,ex[col]['A']) and np.array_equal(territory,ex[col]['C']) and np.allclose(prop,ex[col]['C_prop'],atol=0,rtol=0),col
  recon.append(dict(coluna=col,A_total=int(counts.sum()),cobertura_cache_igual_atlas=True))
 save(pd.DataFrame(recon),'reconciliacao_atlas')
 cips=pd.read_csv(r.OUT/'cips.csv');save(cips,'cips_dependente_preservado');save(pd.read_csv(r.OUT/'cips_exposicoes.csv'),'cips_exposicoes_preservado')
 rows=[]
 for per,dates in r.PERIODS.items():
  keep=d.data_base.between(*dates);dd=d.loc[keep].copy();series={'I':dd.taxa_inadimplencia.to_numpy(),**{c:e['C_prop'][keep] for c,e in ex.items()}}
  for name,x in series.items():
   z=dd[['uf','data_base']].copy();z['x']=x
   for trans in ['nivel','delta']:
    xx=z.x if trans=='nivel' else z.groupby('uf').x.diff()
    for uf in z.uf.unique():
     a=xx[z.uf.eq(uf)].dropna().to_numpy();row=dict(periodo=per,serie=name,transformacao=trans,uf=uf,N=len(a),adf_p=np.nan,kpss_p=np.nan)
     if len(np.unique(a))<3 or np.std(a)<1e-12:row.update(status='indisponível: constante/quase constante',concordancia=False)
     else:
      try:
       with warnings.catch_warnings():
        warnings.simplefilter('ignore');ad=adfuller(a,maxlag=3,regression='c',autolag='BIC');row.update(adf_p=ad[1],adf_lag=ad[2]);kp=kpss(a,regression='c',nlags='auto')
       row.update(adf_p=ad[1],adf_lag=ad[2],kpss_p=kp[1],kpss_lag=kp[2],status='calculado',concordancia=bool(ad[1]<ALPHA and kp[1]>=ALPHA))
      except (ValueError,OverflowError,np.linalg.LinAlgError) as e:row.update(status='indisponível: '+str(e),concordancia=False)
     rows.append(row)
 st=save(pd.DataFrame(rows),'estacionariedade_uf')
 summary=st.groupby(['periodo','serie','transformacao']).agg(UFs=('uf','size'),calculaveis=('status',lambda x:sum(x=='calculado')),concordantes=('concordancia','sum')).reset_index();summary['fracao_todas_ufs']=summary.concordantes/summary.UFs;save(summary,'estacionariedade_resumo')
 return d,ex

def export(f,id,meta):
 q=f['q'];dat=q[['uf','data_base','y']].reset_index(drop=True).copy();zn=[f'z{j}' for j in range(len(f['b']))]
 for j,z in enumerate(zn):dat[z]=f['Z'][:,j]
 dat.to_csv(CACHE/(id+'.csv'),index=False);pd.DataFrame({'estimate':f['b']}).to_csv(CACHE/(id+'.coef.csv'),index=False)
 rows=[]
 for ep,c in f['contrasts'].items():rows.append(dict(endpoint=ep,**dict(zip(zn,c))))
 for j,k in enumerate(range(f['start'],f['K']+1)):
  rows.append(dict(endpoint=f'beta_{k}',**dict(zip(zn,np.eye(len(zn))[j]))));rows.append(dict(endpoint=f'C_{k}',**dict(zip(zn,(np.arange(len(zn))<=j).astype(float)))))
 pd.DataFrame(rows).to_csv(CACHE/(id+'.contrasts.csv'),index=False)
 return dict(id=id,**meta)

def estimate(d,ex):
 planned=pd.read_csv(r.OUT/'principais.csv')[['periodo','coluna']];rows=[];profiles=[];man=[];supports=[];boots=[]
 central={'total_desastres','tipo_onda_de_frio','tipo_granizo','tipo_alagamentos','tipo_chuvas_intensas','tipo_inundacoes','tipo_onda_de_calor_e_baixa_umidade'}
 for per,c in planned.itertuples(index=False,name=None):
  keep=d.data_base.between(*r.PERIODS[per]);dd=d.loc[keep];x=ex[c]['C_prop'][keep];q=ordered_lags(dd,x);dx=pd.Series(x,index=dd.index).groupby(dd.uf).diff().to_numpy();qd=ordered_lags(dd,dx)
  common=q[['y']+[f'x{k}' for k in range(11)]].notna().all(axis=1)&qd[[f'x{k}' for k in range(11)]].notna().all(axis=1)
  q=q.loc[common].copy();qd=qd.loc[common].copy()
  assert q.data_base.min()==pd.Timestamp('2013-12-01')
  for spec,K,start,data in [('Principal',k,1,q) for k in range(1,11)]+[('Com contemporâneo',10,0,q),('Delta X',10,1,qd)]:
   id=f'{per}_{c}_{spec}_{K}'.replace('/','_').replace(' ','_');f=fit(data,K,start);meta=metadata(f,per,c,spec);out=meta.copy()
   for ep,cv in [('acumulado',f['V']),('dk',f['DK'])]:
    cc=r.contrast(f['b'],cv,f['contrasts']['acumulado'],f['df'] if ep=='acumulado' else f['q'].data_base.nunique()-1);out.update({ep+'_'+k:z for k,z in cc.items()});out['joint_'+ep+'_p']=r.joint(f['b'],cv,f['R'],f['df'] if ep=='acumulado' else f['q'].data_base.nunique()-1)
   rows.append(out)
   sf=f.copy()
   if spec=='Delta X':sf['q']=q # support refers to levels of recorded exposure, not just positive changes
   supports.append({**meta,**v.support(sf,f['contrasts']['acumulado']),'suporte_janela':'cobertura em nível'})
   D=np.tril(np.ones((len(f['b']),len(f['b']))));cum=D@f['b'];vc=D@f['V']@D.T
   for j,k in enumerate(range(start,K+1)):
    bci=r.contrast(f['b'],f['V'],np.eye(len(f['b']))[j],f['df']);cci=r.contrast(f['b'],f['V'],D[j],f['df']);profiles.append(dict(**meta,lag=k,beta=bci['estimate'],beta_low=bci['low'],beta_high=bci['high'],C=cci['estimate'],C_low=cci['low'],C_high=cci['high'],inferência='CR1S ponto a ponto'))
   if K==10:man.append(export(f,id,meta))
   if spec=='Principal' and K==10:
    for endpoint,R in [('acumulado',f['contrasts']['acumulado']),('joint',f['R'])]:
     z=v.wcr(f,R,B=9999 if c in central else 4999);boots.append(dict(**meta,endpoint=endpoint,**z))
  save(pd.DataFrame(rows),'modelos');save(pd.DataFrame(man),'manifest');save(pd.DataFrame(profiles),'perfis_cr1');save(pd.DataFrame(supports),'suporte_design');save(pd.DataFrame(boots),'bootstrap')
  print('DLM clássico',per,c,'concluído',flush=True)
 save(pd.DataFrame(man),'manifest');pd.DataFrame(man).to_csv(CACHE/'manifest.csv',index=False)

def inference_r():
 subprocess.run([os.getenv('DLM_R_EXEC','Rscript'),str(ROOT/'src/dlm_classico_inferencia.R'),str(ROOT)],check=True)

def finalize():
 d=pd.read_csv(OUT/'modelos.csv');d=bh(d,['especificacao','K'],['acumulado_p','joint_acumulado_p','dk_p','joint_dk_p'],48)
 main=d[d.especificacao=='Principal'];d['q_grade_acumulado_p']=np.nan;d['q_grade_joint_acumulado_p']=np.nan
 for p in ['acumulado_p','joint_acumulado_p']:
  vals=np.r_[main[p].fillna(1),np.ones(480-len(main))];d.loc[main.index,'q_grade_'+p]=multipletests(vals,method='fdr_bh')[1][:len(main)]
 save(d,'modelos');b=pd.read_csv(OUT/'bootstrap.csv');save(bh(b,['endpoint'],['p'],48),'bootstrap')
 if (OUT/'cr2.csv').exists():
  cr=pd.read_csv(OUT/'cr2.csv');cr['q']=np.nan
  for _,g in cr[cr.endpoint.isin(['acumulado','joint'])].groupby(['especificacao','endpoint']):cr.loc[g.index,'q']=multipletests(np.r_[g.p.fillna(1),np.ones(48-len(g))],method='fdr_bh')[1][:len(g)]
  save(cr,'cr2')
  assert np.allclose(cr[cr.endpoint=='acumulado'].estimate,d[d.K==10].acumulado_estimate,atol=1e-8) # manifest/model order preserved
 selectors=d[d.especificacao=='Principal'].groupby(['periodo','coluna']).BIC.idxmin();save(d.loc[selectors].reset_index(drop=True),'bic_comparacao')
 versions={p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','statsmodels','patsy','nbformat','ipython','matplotlib','threadpoolctl']};(OUT/'versoes.json').write_text(json.dumps(versions,indent=2))

def run():
 with threadpool_limits(limits=1):
  d,ex=audits();estimate(d,ex)
 inference_r();finalize()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--finalizar',action='store_true');a=p.parse_args();finalize() if a.finalizar else run()
