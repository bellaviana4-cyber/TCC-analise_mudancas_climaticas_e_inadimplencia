"""Extensão exploratória clássica; protocolo registrado antes dos novos ajustes."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
from scipy import stats
from statsmodels.regression.linear_model import OLS
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.sandwich_covariance import cov_nw_groupsum
from threadpoolctl import threadpool_limits
import dlm_selecionado as ds
import dlm_revisao as r
import dlm_validacao_final as v
import dlm_classico as classic
import controles_macro_dlm as macro
ROOT=r.ROOT;OUT=ROOT/'outputs/tables/dlm_ajustes5'

def save(rows,name):
 d=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows);OUT.mkdir(parents=True,exist_ok=True);p=OUT/(name+'.csv');tmp=p.with_suffix('.tmp');d.to_csv(tmp,index=False,encoding='utf-8-sig');tmp.replace(p);return d

def adjust(d,field,size):
 assert len(d)<=size
 p=np.r_[d[field].fillna(1),np.ones(size-len(d))]
 for method,label in [('fdr_bh','BH'),('fdr_by','BY')]:d[field+'_'+label]=multipletests(p,method=method)[1][:len(d)]
 return d

def contrast(b,V,c,df,M):
 a=r.contrast(np.asarray(b),V,np.asarray(c),df);crit=stats.t.ppf(1-.05/(2*M),df);a.update(M=M,p_busca=min(M*a['p'],1) if np.isfinite(a['p']) else np.nan,low=a['estimate']-crit*a['se'],high=a['estimate']+crit*a['se']);return a

def panel(d,ex):
 rows=[];profiles=[];candidates=[];deps=[];pairs=[];checks=[]
 eligible=set(map(tuple,pd.read_csv(ROOT/'outputs/tables/dlm_revisao/principais.csv')[['periodo','coluna']].values))
 for per,dates in r.PERIODS.items():
  for c,xx in ex.items():
   if (per,c) not in eligible:continue
   keep=d.data_base.between(*dates);dd=d.loc[keep];q=v.calendar_lags(dd,xx['C_prop'][keep]);dx=pd.Series(xx['C_prop'][keep],index=dd.index).groupby(dd.uf).diff();qd=v.calendar_lags(dd,dx.to_numpy());common=q[['y']+[f'x{k}' for k in range(11)]].notna().all(1)&qd[[f'x{k}' for k in range(11)]].notna().all(1);q=q.loc[common]
   fits={K:classic.fit(q,K) for K in range(1,11)};K=min(fits,key=lambda k:(fits[k]['BIC'],k));f=fits[K];n=len(q);T=q.data_base.nunique();df=T-1;factor=T/(T-1)*(n-1)/(n-f['absorbed']-K)
   for k,ff in fits.items():candidates.append(dict(periodo=per,coluna=c,K=k,AR=0,N=n,BIC=ff['BIC'],status='admissível',selecionado=k==K))
   residual=q[['uf','data_base']].copy();residual['u']=f['u'];corr=residual.pivot(index='data_base',columns='uf',values='u').corr();ij=np.triu_indices(len(corr),1);cc=corr.to_numpy()[ij];deps.append(dict(periodo=per,coluna=c,exposicao=r.label(c),pares=len(cc),media_abs=float(np.mean(abs(cc))),mediana_abs=float(np.median(abs(cc))),q90_abs=float(np.quantile(abs(cc),.9)),max_abs=float(max(abs(cc)))))
   for i,j in zip(*ij):pairs.append(dict(periodo=per,coluna=c,UF1=corr.index[i],UF2=corr.index[j],correlacao=corr.iloc[i,j]))
   for L in [6,12,18]:
    raw=r.dk(f['X'],f['u'],q,L);time=pd.Categorical(q.data_base,categories=sorted(q.data_base.unique())).codes;ind=cov_nw_groupsum(OLS(f['y'],f['X']).fit(),nlags=L,time=time,use_correction=False);err=float(np.max(abs(raw-ind)));assert np.allclose(raw,ind,rtol=1e-8,atol=1e-9);checks.append(dict(periodo=per,coluna=c,L=L,max_diferenca=err))
    V=raw*factor;a=contrast(f['b'],V,np.ones(K),df,10);pj=r.joint(f['b'],V,np.eye(K),df)
    rows.append(dict(periodo=per,coluna=c,exposicao=r.label(c),nivel=r.level(c),K=K,AR=0,N=n,T=T,L=L,BIC=f['BIC'],correcao=factor,inicio=str(q.data_base.min().date()),fim=str(q.data_base.max().date()),p_joint=pj,p_joint_busca=min(10*pj,1) if np.isfinite(pj) else np.nan,**a))
    for h in range(1,K+1):
     b=contrast(f['b'],V,np.eye(K)[h-1],df,55);cv=contrast(f['b'],V,(np.arange(K)<h).astype(float),df,55);profiles.append(dict(periodo=per,coluna=c,L=L,K=K,lag=h,beta=b['estimate'],beta_low=b['low'],beta_high=b['high'],beta_p_busca=b['p_busca'],C=cv['estimate'],C_low=cv['low'],C_high=cv['high'],M_perfil=55))
   print('DK',per,c,K,flush=True)
 frame=pd.DataFrame(rows)
 for L,g in frame.groupby('L'):
  g=adjust(adjust(g.copy(),'p_busca',48),'p_joint_busca',48);frame.loc[g.index,g.columns]=g
 save(frame,'painel');save(profiles,'painel_perfis');save(candidates,'painel_candidatos');save(deps,'dependencia_ufs');save(pairs,'correlacoes_ufs');save(checks,'conferencia_DK')

def design(z,K,ar,regimes):
 season=pd.get_dummies(z.index.month,drop_first=True,dtype=float).to_numpy();base=np.column_stack([season,np.arange(len(z))/12,z[['selic_mensal_lag1','ipca_mensal_lag1','atividade_crescimento_lag1']].to_numpy()]);parts=[base];blocks=[];ncol=base.shape[1]
 for regime,mask in regimes.items():
  zz=np.column_stack([np.ones(len(z)),z[[f'y{j}' for j in range(1,ar+1)]].to_numpy(),z[[f'x{k}' for k in range(1,K+1)]].to_numpy()])*mask[:,None];parts.append(zz);blocks.append(dict(regime=regime,ar=list(range(ncol+1,ncol+1+ar)),x=list(range(ncol+1+ar,ncol+1+ar+K))));ncol+=zz.shape[1]
 return np.column_stack(parts),blocks

def national(d,ex):
 mac=macro.fetch();agg=d.groupby('data_base')[['carteira_ativa_total','carteira_inadimplencia_total']].sum();I=100*agg.carteira_inadimplencia_total/agg.carteira_ativa_total
 allrows=[];joints=[];equals=[];profiles=[];candidates=[];coverage=[]
 for per,dates in r.PERIODS.items():
  for c,xx in ex.items():
   exp=pd.DataFrame({'t':d.data_base,'C':xx['C'],'A':xx['A']}).groupby('t').sum();z=pd.DataFrame({'I':I,'x':exp.C/5570,'A':exp.A}).loc[dates[0]:dates[1]];z['y']=z.I.diff()
   for k in range(1,11):z[f'x{k}']=z.x.shift(k)
   for j in [1,2]:z[f'y{j}']=z.y.shift(j)
   z=z.join(mac.drop(columns=['selic_mensal','ipca_mensal','ibc_br_sa','atividade_crescimento']));modes=['Comum'] if per=='Pré' else ['Comum','Regimes']
   if z.A.sum()<24 or (z.A>0).sum()<12:
    for mode in modes:coverage.append(dict(periodo=per,coluna=c,modo=mode,status='não estimável: exposição rara na triagem prévia'))
    continue
   z=z.dropna();assert len(z)==(134 if per=='Total' else 75)
   for mode in modes:
    regimes={'Comum':np.ones(len(z),dtype=bool)} if mode=='Comum' else {'Até fev/2020':np.asarray(z.index<'2020-03-01'),'Mar/2020–dez/2021':np.asarray((z.index>='2020-03-01')&(z.index<'2022-01-01')),'Jan/2022–dez/2024':np.asarray(z.index>='2022-01-01')};fits={};local=[]
    for K in range(1,11):
     for ar in [0,1,2]:
      X,blocks=design(z,K,ar,regimes);n,p=X.shape;rank=np.linalg.matrix_rank(X);reason='posto incompleto' if rank<p else 'df<30' if n-p<30 else 'N<3p' if n<3*p else ''
      row=dict(periodo=per,coluna=c,modo=mode,K=K,AR=ar,N=n,parametros=p,posto=rank,status=reason or 'admissível',BIC=np.nan,selecionado=False)
      if not reason:
       fit=OLS(z.y.to_numpy(),X).fit();fits[K,ar]=(fit,X,blocks);row['BIC']=fit.bic
      local.append(row)
    if not fits:
     coverage.append(dict(periodo=per,coluna=c,modo=mode,status='nenhum candidato admissível'));candidates+=local;continue
    K,ar=min(fits,key=lambda kp:(fits[kp][0].bic,sum(kp),*kp));fit,X,blocks=fits[K,ar];rob=fit.get_robustcov_results(cov_type='HAC',maxlags=12,use_correction=True,use_t=True);V=rob.cov_params();M=90 if mode=='Regimes' else 30;primary=per=='Pré' or mode=='Regimes';meta=dict(periodo=per,coluna=c,exposicao=r.label(c),nivel=r.level(c),modo=mode,principal=primary,K=K,AR=ar,N=len(z),parametros=X.shape[1],df=fit.df_resid,BIC=fit.bic,inicio=str(z.index.min().date()),fim=str(z.index.max().date()),candidatos_admissiveis=len(fits),condition=float(np.linalg.cond(X)),ljungbox12_p=float(acorr_ljungbox(fit.resid,lags=[12],return_df=True).lb_pvalue.iloc[0]))
    exposure=sum([b['x'] for b in blocks],[]);R=np.eye(X.shape[1])[exposure];pj=r.joint(fit.params,V,R,fit.df_resid);joints.append(dict(**meta,p=pj,p_busca=min(30*pj,1) if np.isfinite(pj) else np.nan))
    for block in blocks:
     cs=np.zeros(X.shape[1]);cs[block['x']]=1;a=contrast(fit.params,V,cs,fit.df_resid,M);co=fit.params[block['ar']];rho=float(max(abs(np.roots(np.r_[1,-co])))) if ar else 0
     allrows.append(dict(**{k:v for k,v in meta.items() if k!='df'},regime=block['regime'],raiz_AR=rho,AR_estavel=rho<1,meses_regime=int(regimes[block['regime']].sum()),**a))
     for h in range(1,K+1):
      cb=np.zeros(X.shape[1]);cb[block['x'][h-1]]=1;cc=np.zeros(X.shape[1]);cc[block['x'][:h]]=1;b=contrast(fit.params,V,cb,fit.df_resid,495 if mode=='Regimes' else 165);cv=contrast(fit.params,V,cc,fit.df_resid,495 if mode=='Regimes' else 165);profiles.append(dict(periodo=per,coluna=c,modo=mode,regime=block['regime'],K=K,lag=h,beta=b['estimate'],beta_low=b['low'],beta_high=b['high'],beta_p_busca=b['p_busca'],C=cv['estimate'],C_low=cv['low'],C_high=cv['high'],M_perfil=b['M']))
    if mode=='Regimes':
     RR=[]
     for block in blocks[1:]:
      for i,j in zip(blocks[0]['x'],block['x']):cc=np.zeros(X.shape[1]);cc[j]=1;cc[i]=-1;RR.append(cc)
     pe=r.joint(fit.params,V,np.asarray(RR),fit.df_resid);equals.append(dict(**meta,p=pe,p_busca=min(30*pe,1) if np.isfinite(pe) else np.nan))
    for row in local:row['selecionado']=(row['K'],row['AR'])==(K,ar)
    candidates+=local;coverage.append(dict(periodo=per,coluna=c,modo=mode,status='estimado',K=K,AR=ar));print('Macro',per,c,mode,K,ar,flush=True)
 frame=pd.DataFrame(allrows);joint=pd.DataFrame(joints)
 for main,size in [(True,96),(False,48)]:
  g=adjust(frame[frame.principal==main].copy(),'p_busca',size);frame.loc[g.index,g.columns]=g
 for main,size in [(True,48),(False,48)]:
  g=adjust(joint[joint.principal==main].copy(),'p_busca',size);joint.loc[g.index,g.columns]=g
 save(frame,'nacional');save(joint,'nacional_conjunto');save(adjust(pd.DataFrame(equals),'p_busca',24),'nacional_igualdade');save(profiles,'nacional_perfis');save(candidates,'nacional_candidatos');save(coverage,'cobertura_nacional')

def taxonomy(d):
 a=pd.read_csv(ROOT/'data/raw/atlas_desastres/atlas.csv',sep=';',encoding='latin1',low_memory=False);a['date']=pd.to_datetime(a.Data_Evento,format='%d/%m/%Y',errors='coerce');a=a[a.date.dt.year.between(2013,2024)].copy();a['classe_analitica']=a.Cod_Cobrade.map(r.analytical);rows=[];codes=[]
 groups={'11':'Geológico','12':'Hidrológico','13':'Meteorológico','14':'Climatológico','15':'Biológico'}
 descriptions={13310:'Onda de calor',13120:'Frentes frias/Zonas de convergência',14140:'Baixa umidade do ar',13214:'Chuvas intensas',13212:'Tempestade de raios',13321:'Friagem',13322:'Geadas'}
 for c,mask in r.masks(a,d).items():
  aa=a[mask];classed=aa.Cod_Cobrade.astype(int).astype(str).str[:2];cl=classed.isin(['12','13','14']);pct=float(cl.mean());alerts=[]
  for (admin,typ,code),n in aa.groupby(['grupo_de_desastre','descricao_tipologia','Cod_Cobrade']).size().items():
   prefix=str(int(code))[:2];norm=groups.get(prefix,'Tecnológico' if prefix.startswith('2') else 'não mapeado');desc=descriptions.get(int(code),'Consultar tabela COBRADE pelo código');codes.append(dict(coluna=c,grupo_atlas=admin,tipologia_atlas=typ,codigo=int(code),grupo_COBRADE=norm,descricao_COBRADE_especifica=desc,registros=n))
   if admin!=norm:alerts.append(f'{int(code)}: grupo Atlas {admin}; grupo COBRADE {norm}')
   if int(code)==13310 and c=='tipo_chuvas_intensas':alerts.append('13310 (Onda de calor) aparece sob Chuvas intensas')
  if c=='tipo_onda_de_frio':alerts.append('Agregado inclui 13120 (frentes frias/ZC), 13321 (friagem) e 13322 (geadas)')
  if c=='tipo_onda_de_calor_e_baixa_umidade':alerts.append('14140 identifica baixa umidade; não identifica exclusivamente onda de calor')
  if c=='tipo_outros':alerts.append('Agregado reúne códigos naturais e tecnológicos: não exclusivamente climático')
  rows.append(dict(coluna=c,exposicao=r.label(c),nivel=r.level(c),registros=len(aa),fracao_hidrometeorologica=pct,escopo='Hidrometeorológico por código' if pct==1 else 'Complementar/misto',alertas='; '.join(sorted(set(alerts))) or 'Nenhuma divergência de grupo nesta comparação; associação não atribui mudanças climáticas'))
 save(rows,'taxonomia');save(codes,'taxonomia_codigos')

def main():
 with threadpool_limits(limits=1):
  d,ex=ds.inputs();taxonomy(d);panel(d,ex);national(d,ex)
 manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.csv'))};manifest['protocolo_sha256']=hashlib.sha256((ROOT/'docs/dlm_ajustes5_protocolo.md').read_bytes()).hexdigest();(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
 for name in ['painel','nacional','nacional_conjunto','nacional_igualdade']:
  f=pd.read_csv(OUT/(name+'.csv'));f=f[f.L==12] if name=='painel' else f[f.principal] if 'principal' in f and name!='nacional_igualdade' else f;print(name,'N',len(f),'BY',int((f.p_busca_BY<.05).sum()),'BH',int((f.p_busca_BH<.05).sum()),flush=True)
if __name__=='__main__':main()
