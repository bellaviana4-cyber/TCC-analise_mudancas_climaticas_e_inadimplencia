"""Auditoria integrada e sensibilidades nacionais finitas; protocolo de 05/10/2026."""
from pathlib import Path
import sys,json,hashlib
import pandas as pd,numpy as np
from scipy import stats
from statsmodels.regression.linear_model import OLS
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.sandwich_covariance import S_hac_simple
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import dlm_selecionado as ds
import dlm_revisao as r
import dlm_validacao_final as v
import dlm_classico as classic
out=ROOT/'outputs/tables/revisao_integrada';out.mkdir(exist_ok=True)
with threadpool_limits(limits=1):
 d,ex=ds.inputs();checks=[]
 s=pd.read_csv(ROOT/'outputs/tables/segunda_etapa/series_nacionais_agregadas.csv',parse_dates=['data']).set_index('data');agg=d.groupby('data_base')[['carteira_ativa_total','carteira_inadimplencia_total','total_desastres']].sum();I=100*agg.carteira_inadimplencia_total/agg.carteira_ativa_total
 assert np.allclose(I,s.I,atol=1e-12);assert np.array_equal(agg.total_desastres,s['Total nacional']);checks.extend(['Taxa nacional Granger = DLM','Contagem mensal nacional Granger = Atlas/painel'])
 for name in ['painel','nacional']:
  m=pd.read_csv(ds.OUT/(name+'.csv'))
  for p,q in [('p','q'),('p_joint','q_joint')]+([('p_boot','q_boot')] if name=='painel' else []):
   adj=multipletests(np.r_[m[p].fillna(1),np.ones(48-len(m))],method='fdr_bh')[1][:len(m)];assert np.allclose(adj,m[q],rtol=1e-11,atol=1e-15);checks.append(name+' BH48 '+q)
  g=pd.read_csv(ds.OUT/(name+'_candidatos.csv'));assert g.groupby(['periodo','coluna']).selecionado.sum().eq(1).all();checks.append(name+' uma escolha por cenário')
  for c,e in ex.items():assert np.isfinite(e['C_prop']).all() and np.min(e['C_prop'])>=0 and np.max(e['C_prop'])<=1
 n=pd.read_csv(ds.OUT/'nacional.csv');rows=[];influence=[];stability=[]
 for row in n.itertuples():
  dates=r.PERIODS[row.periodo];exp=pd.DataFrame({'t':d.data_base,'C':ex[row.coluna]['C'],'A':ex[row.coluna]['A']}).groupby('t').sum();z=pd.DataFrame({'I':I,'x':exp.C/5570,'A':exp.A}).loc[dates[0]:dates[1]];z['y']=z.I.diff()
  for k in range(1,11):z[f'x{k}']=z.x.shift(k)
  for j in [1,2]:z[f'y{j}']=z.y.shift(j)
  z=z.dropna();ctrl=np.column_stack([np.ones(len(z)),pd.get_dummies(z.index.month,drop_first=True,dtype=float),np.arange(len(z))/12]);X=np.column_stack([ctrl,z[[f'y{j}' for j in range(1,row.p_proprio+1)]],z[[f'x{k}' for k in range(1,row.K+1)]]]);fit=OLS(z.y,X).fit();H=fit.get_robustcov_results(cov_type='HAC',maxlags=12,use_correction=True,use_t=True);V=H.cov_params();b=fit.params.to_numpy()[-row.K:];W=V[-row.K:,-row.K:];ev=np.linalg.eigvalsh(W);R=np.eye(X.shape[1])[-row.K:];F=float(H.f_test(R).fvalue);p=float(stats.f.sf(F,row.K,fit.df_resid));assert np.isclose(p,row.p_joint,atol=1e-15,rtol=1e-10);assert np.isclose(sum(b),row.estimate,atol=1e-9);assert np.all(np.diff(z.index.to_period('M').astype(int))==1)
  inf=fit.get_influence();cook=inf.cooks_distance[0];dominant=int(np.argmax(cook))

  # Keep the full monthly score timeline after leaving one estimating observation out.
  good=np.arange(len(z))!=dominant;xf=X[good];yf=z.y.to_numpy()[good];bf=np.linalg.lstsq(xf,yf,rcond=None)[0];br=np.linalg.inv(xf.T@xf);scores=X*(z.y.to_numpy()-X@bf)[:,None];scores[~good]=0;neff=int(good.sum());df=neff-X.shape[1];vf=br@S_hac_simple(scores,nlags=12)@br*neff/df;cs=np.zeros(X.shape[1]);cs[-row.K:]=1;acc=r.contrast(bf,vf,cs,df);bw=bf[-row.K:];vw=vf[-row.K:,-row.K:];pj=float(stats.f.sf(float(bw@np.linalg.solve(vw,bw))/row.K,row.K,df));influence.append(dict(periodo=row.periodo,coluna=row.coluna,exposicao=row.exposicao,K=row.K,AR=row.p_proprio,mes_omitido=str(z.index[dominant].date()),N_efetivo=neff,estimate=acc['estimate'],low=acc['low'],high=acc['high'],p=acc['p'],p_joint=pj,estimate_principal=row.estimate,q_principal=row.q,q_joint_principal=row.q_joint))
  if row.periodo=='Total':
   post=(z.index>='2020-03-01').astype(float);extra=np.column_stack([post,post[:,None]*X[:,ctrl.shape[1]:]]);xb=np.column_stack([X,extra]);fb=OLS(z.y,xb).fit();rb=fb.get_robustcov_results(cov_type='HAC',maxlags=12,use_correction=True,use_t=True);nc=extra.shape[1];rr=np.eye(xb.shape[1])[-nc:];rx=np.eye(xb.shape[1])[-row.K:];rank=np.linalg.matrix_rank(xb);pb=float(rb.f_test(rr).pvalue) if rank==xb.shape[1] else np.nan;px=float(rb.f_test(rx).pvalue) if rank==xb.shape[1] else np.nan;stability.append(dict(periodo=row.periodo,coluna=row.coluna,exposicao=row.exposicao,K=row.K,AR=row.p_proprio,rank_completo=rank==xb.shape[1],p_mudanca=pb,p_interacao_exposicao=px,N=len(z),GL=fb.df_resid))

  rows.append({'periodo':row.periodo,'coluna':row.coluna,'exposicao':row.exposicao,'K':row.K,'AR':row.p_proprio,'N':len(z),'BIC':fit.bic,'rank_cov_lags':np.linalg.matrix_rank(W),'cond_cov_lags':np.linalg.cond(W),'min_autovalor_cov_lags':ev.min(),'F_conjunto':F,'p_conjunto_reproduzido':p,'cook_maximo':cook.max(),'mes_maior_cook':str(z.index[dominant].date()),'meses_exposicao_positiva':int((z.x>0).sum()),'janela_AIC':row.K_AIC,'pontos_percentuais_por_municipio':row.estimate/5570})
 checks.append('46 nacionais: soma, Wald-F/HAC, calendário e covariância reproduzidos')
 pd.DataFrame(rows).to_csv(out/'nacional_diagnosticos.csv',index=False,encoding='utf-8-sig')

 assert len(influence)==46 and len(stability)==24
 assert all(item['rank_completo'] for item in stability)
 for records,name,size,cols in [(influence,'nacional_influencia',48,['p','p_joint']),(stability,'nacional_estabilidade',24,['p_mudanca','p_interacao_exposicao'])]:
  frame=pd.DataFrame(records)
  for pcol in cols:frame['q_'+pcol]=multipletests(np.r_[frame[pcol].fillna(1),np.ones(size-len(frame))],method='fdr_bh')[1][:len(frame)]
  frame.to_csv(out/(name+'.csv'),index=False,encoding='utf-8-sig')

 panel=pd.read_csv(ds.OUT/'painel.csv');prows=[]
 for per,c in [('Total','total_desastres'),('Pré','tipo_alagamentos')]:
  keep=d.data_base.between(*r.PERIODS[per]);dd=d.loc[keep];q=v.calendar_lags(dd,ex[c]['C_prop'][keep]);dx=pd.Series(ex[c]['C_prop'][keep],index=dd.index).groupby(dd.uf).diff();qd=v.calendar_lags(dd,dx.to_numpy());common=q[['y']+[f'x{k}' for k in range(11)]].notna().all(1)&qd[[f'x{k}' for k in range(11)]].notna().all(1);q=q.loc[common];row=panel[(panel.periodo==per)&(panel.coluna==c)].iloc[0];f=classic.fit(q,int(row.K));F=np.column_stack([q[[f'x{k}' for k in range(1,int(row.K)+1)]],pd.get_dummies(q.uf,dtype=float),pd.get_dummies(q.data_base,dtype=float).iloc[:,1:]]);explicit=OLS(q.y,F).fit();assert np.allclose(explicit.params.to_numpy()[:int(row.K)],f['b'],atol=1e-10);assert np.allclose(explicit.resid,f['u'],atol=1e-10);res=pd.DataFrame({'uf':q.uf,'t':q.data_base,'u':f['u']}).pivot(index='t',columns='uf',values='u');corr=res.corr().to_numpy();pairs=corr[np.triu_indices(27,1)];prows.append({'periodo':per,'coluna':c,'K':int(row.K),'N':len(q),'max_diferenca_beta_OLS_FE':np.max(abs(explicit.params.to_numpy()[:int(row.K)]-f['b'])),'correlacao_residual_media_absoluta_entre_UFs':np.mean(abs(pairs)),'correlacao_residual_maxima_absoluta_entre_UFs':np.max(abs(pairs))})
 checks.append('Painel total e Alagamentos pré: FWL = OLS com dummies explícitas')
 pd.DataFrame(prows).to_csv(out/'painel_conferencia.csv',index=False,encoding='utf-8-sig')
 result={'status':'aprovado','checagens':checks,'nota':'Conferência e sensibilidades finitas conforme protocolo; influência refaz o ajuste sem a linha de maior Cook, mantendo calendário HAC. Não certifica pressupostos nem corrige seleção.','bootstrap_seed_efetiva':v.SEED,'painel_modelos':46,'nacional_modelos':46,'Granger_reestimado':False}
 (out/'auditoria.json').write_text(json.dumps(result,indent=2,ensure_ascii=False));print(json.dumps(result,ensure_ascii=False,indent=2));print(pd.DataFrame(rows).sort_values('cond_cov_lags',ascending=False).head(6).to_string(index=False));print(prows)
