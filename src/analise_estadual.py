"""Revisão estadual do TCC: Granger, DLM, SARIMA/SARIMAX.
Entrada local: data/processed/df_tcc_2013_2024.csv com 27 UFs e 144 meses.
Todas as decisões e restrições amostrais são documentadas em saídas.
"""
from __future__ import annotations
import argparse, json, warnings, csv, hashlib, os
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.tsa.statespace.sarimax import SARIMAX

TIPOS = ['tipo_alagamentos','tipo_chuvas_intensas','tipo_doencas_infecciosas','tipo_enxurradas','tipo_erosao','tipo_estiagem_e_seca','tipo_granizo','tipo_incendio_florestal','tipo_inundacoes','tipo_movimento_de_massa','tipo_onda_de_calor_e_baixa_umidade','tipo_onda_de_frio','tipo_outros','tipo_rompimento_colapso_de_barragens','tipo_tornado','tipo_vendavais_e_ciclones']
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.getenv('TCC_OUTPUT_DIR',str(ROOT/'outputs/tables/revisao_estadual_20261019')));OUT.mkdir(parents=True,exist_ok=True)
SOURCE=Path(os.getenv('TCC_BASE_CSV',str(ROOT/'data/processed/df_tcc_2013_2024.csv')))

def load():
    df=pd.read_csv(SOURCE,sep=';',encoding='utf-8-sig');df['data']=pd.to_datetime(df['mes_ano']+'-01');df=df.sort_values(['uf','data']).reset_index(drop=True)
    assert len(df)==3888 and df.uf.nunique()==27 and df.data.nunique()==144 and not df.duplicated(['uf','data']).any()
    assert len(TIPOS)==16 and not df[TIPOS].isna().any().any()
    assert np.allclose(100*df.carteira_inadimplencia_total/df.carteira_ativa_total,df.taxa_inadimplencia,rtol=0,atol=1e-9)
    assert np.isfinite(np.log(df.taxa_inadimplencia)).all() and (df[TIPOS]>=0).all().all()
    for c in ['taxa_inadimplencia']+TIPOS:
        df[('y' if c=='taxa_inadimplencia' else 'x_'+c)]=df.groupby('uf')[c].transform(lambda v: np.log(v).diff() if c=='taxa_inadimplencia' else np.log1p(v).diff())
    return df

def bh(df,groupcols,pcol='p',outcol='q_bh'):
    # Família planejada de 16 tipologias por UF×período (ou endpoint DLM).
    # Ausência de estimativa nunca é interpretada como p observado; um p=1
    # apenas ocupa a posição planejada para tornar o ajuste conservador.
    df[outcol]=np.nan
    for _,inds in df.groupby(groupcols,sort=False,dropna=False).groups.items():
        ps=df.loc[inds,pcol].to_numpy(float)
        assert len(ps)<=16, f'Família deveria ter até 16 tipologias, recebeu {len(ps)} para {groupcols}'
        full=np.r_[np.nan_to_num(ps,nan=1.0).clip(0,1),np.ones(16-len(ps))]
        q=multipletests(full,method='fdr_bh')[1][:len(ps)]
        q[~np.isfinite(ps)]=np.nan
        df.loc[inds,outcol]=q
    df['rejeicao_nominal']=df[pcol].lt(.05) & df[pcol].notna()
    df['rejeicao_bh']=df[outcol].lt(.05) & df[outcol].notna()
    return df

def granger(df):
    records=[];diags=[]
    for periodo,stop in [('Pré','2020-01'),('Total','2024-12')]:
        for uf,g in df[df.mes_ano<=stop].groupby('uf',sort=True):
            g=g.reset_index(drop=True);y=g['y'].to_numpy(float)
            for tipo in TIPOS:
                x=g['x_'+tipo].to_numpy(float)
                # Escolha p por BIC, utilizando amostra comum de pmax=6 em cada UF×recorte.
                pmax=6;t=np.arange(1+pmax,len(y));Y=y[t]; dummies=(g['mes'].to_numpy()[t,None]==np.arange(2,13)[None,:]).astype(float)
                if len(t)<30 or np.ptp(x[1:])<1e-12:
                    records.append(dict(uf=uf,periodo=periodo,tipologia=tipo,status='exposição transformada constante',n_eff=len(t),p_lags=np.nan));continue
                fits=[]
                for p in range(1,pmax+1):
                    X=np.column_stack([np.ones(len(t)),dummies]+[y[t-j] for j in range(1,p+1)]+[x[t-j] for j in range(1,p+1)])
                    if np.linalg.matrix_rank(X)!=X.shape[1] or not np.isfinite(X).all():continue
                    beta,*_=np.linalg.lstsq(X,Y,rcond=None);e=Y-X@beta;RSS=e@e
                    if RSS<=0:continue
                    bic=len(Y)*np.log(RSS/len(Y))+X.shape[1]*np.log(len(Y))
                    fits.append((bic,p,X,beta,e,RSS))
                if not fits:
                    records.append(dict(uf=uf,periodo=periodo,tipologia=tipo,status='sem modelo de posto completo na grade',n_eff=len(t),p_lags=np.nan));continue
                bic,p,X,beta,e,RSS=min(fits,key=lambda z:(z[0],z[1]));dof=len(Y)-X.shape[1];j0=X.shape[1]-p
                # F conjunto para H0: coeficientes de x_{t-1..t-p}=0, no modelo BIC selecionado.
                X0=X[:,:j0];b0=np.linalg.lstsq(X0,Y,rcond=None)[0];e0=Y-X0@b0;RSS0=e0@e0
                F=max(0,(RSS0-RSS)/p)/(RSS/dof);pv=float(stats.f.sf(F,p,dof))
                lb=float(acorr_ljungbox(e,lags=[min(12,max(3,len(e)//6))],return_df=True)['lb_pvalue'].iloc[0])
                records.append(dict(uf=uf,periodo=periodo,tipologia=tipo,status='estimado',n_eff=len(t),p_lags=p,criterio='BIC (lags 1..6; amostra comum)',BIC=bic,F=F,df_num=p,df_den=dof,p=pv,ljungbox_p=lb,diagnostico='sem rejeição LB nominal' if lb>=.05 else 'autocorrelação residual LB nominal',n_positivos=int((g[tipo]>0).sum())))
    o=pd.DataFrame(records);bh(o,['periodo','uf']);o.to_csv(OUT/'granger_aplicacoes.csv',index=False,encoding='utf-8-sig');o[o.rejeicao_nominal].to_csv(OUT/'granger_rejeicoes_nominais.csv',index=False,encoding='utf-8-sig');o[o.rejeicao_bh].to_csv(OUT/'granger_rejeicoes_bh.csv',index=False,encoding='utf-8-sig');return o

def dm(A):
    return A-A.mean(axis=0,keepdims=True)-A.mean(axis=1,keepdims=True)+A.mean(axis=(0,1),keepdims=True)

def design_panel(arrx,y,K,T,G):
    # arrx [G,144], same y; start base period 2013-01, diff requires t>=1 and 24 lags -> t>=25.
    tt=np.arange(25,T);v=dm(y[:,tt,None])[:,:,0].reshape(-1)
    X=dm(np.stack([arrx[:,tt-k] for k in range(K+1)],axis=2)).reshape(-1,K+1)
    return X,v,len(tt)

def robust_cov(X,e,K,G,T,kind):
    N=len(e);p=K+1;ptotal=G+T-1+p; bread=np.linalg.pinv(X.T@X,hermitian=True)
    if kind=='cluster_uf':
        s=np.einsum('gtk,gt->gk',X.reshape(G,T,p),e.reshape(G,T))
        meat=s.T@s
        factor=G/(G-1)*(N-1)/(N-ptotal)
        return factor*bread@meat@bread, G-1
    if kind=='dk_regra':L=int(np.floor(4*(T/100)**(2/9)))
    elif kind=='dk6':L=6
    elif kind=='dk12':L=12
    else:raise ValueError(kind)
    scores=np.einsum('gtk,gt->tk',X.reshape(G,T,p),e.reshape(G,T))
    meat=scores.T@scores
    for h in range(1,min(T,L+1)):
        lag=scores[h:].T@scores[:-h];meat+=(1-h/(L+1))*(lag+lag.T)
    factor=N/(N-ptotal)
    return factor*bread@meat@bread, T-1

def wald(beta,cov,df_res,endpoint):
    K=len(beta)-1;p=K+1
    if endpoint=='beta0':C=np.eye(p)[[0]]
    elif endpoint=='soma0K':C=np.ones((1,p))
    elif endpoint=='soma1K':C=np.concatenate([np.zeros((1,1)),np.ones((1,p-1))],axis=1)
    elif endpoint=='conjunto0K':C=np.eye(p)
    elif endpoint=='conjunto1K':C=np.eye(p)[1:]
    else:raise ValueError(endpoint)
    if not C.size:return None
    diff=C@beta;V=C@cov@C.T;rank=np.linalg.matrix_rank(V,tol=1e-15);r=C.shape[0]
    if rank<r or np.min(np.linalg.eigvalsh(V))<=0:return dict(p=np.nan,status='covariância singular no contraste')
    if r==1:
        se=float(np.sqrt(V[0,0]));t=float(diff[0]/se);pv=float(2*stats.t.sf(abs(t),df_res));ci=stats.t.ppf(.975,df_res)*se
        return dict(p=pv,estimate=float(diff[0]),se=se,ic_inf=float(diff[0]-ci),ic_sup=float(diff[0]+ci),estatistica=t,df_num=1,status='calculado')
    stat=float(diff@np.linalg.solve(V,diff)/r);return dict(p=float(stats.f.sf(stat,r,df_res)),estimate=np.nan,se=np.nan,ic_inf=np.nan,ic_sup=np.nan,estatistica=stat,df_num=r,status='calculado')

def fe_re_tests(X,y,G,T,K):
    """Testes clássicos de painel na amostra comum com dummies temporais.
    Resultados com ressalvas: F clássico e LM assumem especificação homocedástica.
    RE GLS quasi-demeaned por estimativas de componentes de variância.
    """
    N=G*T;p=K+1
    # X e y são pré TWFE; para FE usar DM.
    XX=X.reshape(G,T,p);yy=y.reshape(G,T)
    tt=np.tile(np.eye(T)[:,1:],(G,1))
    pooled=np.column_stack([np.ones(N),tt,X]);bp=np.linalg.lstsq(pooled,y,rcond=None)[0];ep=y-pooled@bp;rsspool=float(ep@ep);dfpool=N-pooled.shape[1]
    fex=dm(XX).reshape(N,p);fey=dm(yy[:,:,None]).reshape(N);bf=np.linalg.lstsq(fex,fey,rcond=None)[0];ef=fey-fex@bf;rssfe=float(ef@ef);dffe=N-(G+T-1+p)
    F=max(0,(rsspool-rssfe)/(G-1))/(rssfe/dffe);pF=float(stats.f.sf(F,G-1,dffe))
    rr=ep.reshape(G,T);ratio=float((rr.sum(axis=1)**2).sum()/(ep@ep));lm=G*T/(2*(T-1))*max(0,ratio-1)**2;pLM=float(.5*stats.chi2.sf(lm,1)) if ratio>1 else 1.0
    sigmae2=rssfe/dffe; sigma_u2=max(0,float(np.var(rr.mean(axis=1),ddof=1)-sigmae2/T));theta=1-np.sqrt(sigmae2/(sigmae2+T*sigma_u2)) if sigma_u2>0 else 0.0
    # transformed including constant and month dummies, GLS with RE state intercept
    R=np.column_stack([np.ones(N),tt,X]);R3=R.reshape(G,T,-1);Rq=(R3-theta*R3.mean(axis=1,keepdims=True)).reshape(N,-1);yq=(yy-theta*yy.mean(axis=1,keepdims=True)).reshape(N)
    br=np.linalg.lstsq(Rq,yq,rcond=None)[0][-p:]
    Sxx=fex.T@fex;Vf=sigmae2*np.linalg.pinv(Sxx)
    Sr=np.linalg.pinv(Rq.T@Rq);Vr=sigmae2*Sr[-p:,-p:]
    diff=bf-br;V=Vf-Vr;evals=np.linalg.eigvalsh(V)
    if np.min(evals)>1e-12:
        H=float(diff@np.linalg.solve(V,diff));pH=float(stats.chi2.sf(H,p));hausman='calculado'
    else:H=np.nan;pH=np.nan;hausman='diferença de covariâncias não definida positiva (teste clássico indisponível)'
    return dict(teste_F=F,p_F=pF,teste_LM=lm,p_LM=pLM,teste_Hausman=H,p_Hausman=pH,status_Hausman=hausman,theta_RE=theta,sigma2_RE=sigma_u2,ssr_FE=rssfe,ssr_pooled=rsspool,coef_FE=str(bf.tolist()),coef_RE=str(br.tolist()))

def dlm(df):
    selected=[];tests=[];candidates=[];comparacoes=[];diagnostics=[]
    for periodo,stop in [('Pré','2020-01'),('Total','2024-12')]:
        g=df[df.mes_ano<=stop].copy();ufs=sorted(g.uf.unique());G=len(ufs);TT=g.mes_ano.nunique()
        y=np.stack([g[g.uf==u].y.to_numpy(float) for u in ufs]);assert G==27
        for tipo in TIPOS:
            x=np.stack([g[g.uf==u]['x_'+tipo].to_numpy(float) for u in ufs]);
            # Histórico: aplica mínimo de 5 UFs contemporaneamente expostas na amostra de equações.
            tt=np.arange(25,TT);contemporaneous=(g[g.mes_ano.isin(sorted(g.mes_ano.unique())[25:])].groupby('uf')[tipo].sum()>0)
            n_ufs=int(contemporaneous.sum());npos=int((np.stack([g[g.uf==u][tipo].to_numpy(float) for u in ufs])[:,tt]>0).sum())
            if n_ufs<5 or npos<10:
                for crit in ['AIC','BIC']:selected.append(dict(periodo=periodo,tipologia=tipo,criterio=crit,status='suporte insuficiente',K=np.nan,N=G*len(tt),UFs_contemporaneas=n_ufs))
                continue
            fit={}
            for K in range(1,25):
                X,Y,T=design_panel(x,y,K,TT,G)
                if np.linalg.matrix_rank(X)!=K+1:continue
                b=np.linalg.lstsq(X,Y,rcond=None)[0];e=Y-X@b;RSS=e@e
                if RSS<=0:continue
                ptotal=G+T-1+K+1;n=len(Y);ll=-n/2*(np.log(2*np.pi)+1+np.log(RSS/n));aic=-2*ll+2*ptotal;bic=-2*ll+np.log(n)*ptotal
                fit[K]=(aic,bic,b,e,X,Y,T,RSS)
                candidates.append(dict(periodo=periodo,tipologia=tipo,K=K,AIC=aic,BIC=bic,N=n,parametros=ptotal,SSR=RSS,loglike=ll,status='estimado'))
            if not fit:
                for crit in ['AIC','BIC']:selected.append(dict(periodo=periodo,tipologia=tipo,criterio=crit,status='posto insuficiente',K=np.nan,N=G*len(tt)))
                continue
            for crit,pos in [('AIC',0),('BIC',1)]:
                K=min(fit,key=lambda v:(fit[v][pos],v));aic,bic,b,e,X,Y,T,RSS=fit[K]
                selected.append(dict(periodo=periodo,tipologia=tipo,criterio=crit,status='estimado',K=K,AIC=aic,BIC=bic,N=len(Y),meses=T,UFs_contemporaneas=n_ufs,uf_mes_positivos=npos))
                for covlabel in ['cluster_uf','dk_regra','dk6','dk12']:
                    cov,df_res=robust_cov(X,e,K,G,T,covlabel)
                    for endpoint in ['beta0','soma0K','soma1K','conjunto0K','conjunto1K']:
                        test=wald(b,cov,df_res,endpoint)
                        if test is not None:tests.append(dict(periodo=periodo,tipologia=tipo,criterio=crit,K=K,covariancia=covlabel,endpoint=endpoint,gl_residuais=df_res,**test))
                if crit=='BIC':
                    # Two-way FE residual cross-uf dependence distribution
                    E=e.reshape(G,T);C=np.corrcoef(E);tri=C[np.triu_indices(G,1)];n_LB=int(sum(float(acorr_ljungbox(E[i],lags=[min(12,T//4)],return_df=True)['lb_pvalue'].iloc[0])<.05 for i in range(G)));fe_results=fe_re_tests(np.stack([x[:,tt-k] for k in range(K+1)],axis=2).reshape(-1,K+1),y[:,tt].reshape(-1),G,T,K)
                    diagnostics.append(dict(periodo=periodo,tipologia=tipo,K=K,media_correlacao=float(tri.mean()),media_absoluta=float(np.abs(tri).mean()),p95_absoluto=float(np.quantile(np.abs(tri),.95)),mediana_absoluta=float(np.median(np.abs(tri))),n_UFs_LB_p05=n_LB,**fe_results))
    d=pd.DataFrame(tests);bh(d,['periodo','criterio','covariancia','endpoint']);d['p_grade_bonferroni']=(d['p']*24).clip(upper=1.0);bh(d,['periodo','criterio','covariancia','endpoint'],pcol='p_grade_bonferroni',outcol='q_bh_grade');d['rejeicao_nominal']=d['p'].lt(.05);d['rejeicao_bh']=d['q_bh'].lt(.05);d['rejeicao_bh_grade']=d['q_bh_grade'].lt(.05);d.to_csv(OUT/'dlm_hipoteses.csv',index=False,encoding='utf-8-sig');pd.DataFrame(selected).to_csv(OUT/'dlm_selecao.csv',index=False,encoding='utf-8-sig');pd.DataFrame(candidates).to_csv(OUT/'dlm_candidatos.csv',index=False,encoding='utf-8-sig');pd.DataFrame(diagnostics).to_csv(OUT/'dlm_diagnosticos_fe_re.csv',index=False,encoding='utf-8-sig');d[d.rejeicao_bh].to_csv(OUT/'dlm_rejeicoes_bh.csv',index=False,encoding='utf-8-sig');return d

if __name__=='__main__':
    import os,time
    os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['granger','dlm']);stage=ap.parse_args().stage
    df=load();t0=time.time();ans=granger(df) if stage=='granger' else dlm(df)
    print(stage,'done',len(ans),'seconds',round(time.time()-t0,1));print('statuses\n',ans.status.value_counts().to_string());print('rejections BH:',int(ans.rejeicao_bh.sum()))