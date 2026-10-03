"""DLM em painel UF×mês. Regras congeladas em docs/dlm_protocolo.md."""
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
from statsmodels.api import OLS
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.sandwich_covariance import cov_cluster

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs/tables/dlm"; OUT.mkdir(parents=True,exist_ok=True)
PERIODS={"Total (2013–2024)":("2013-01-01","2024-12-01"),"Pré-pandemia (até jan/2020)":("2013-01-01","2020-01-01")}
K_GRID=(3,6,9,12); Q_GRID=(2,3)

def load_panel():
    d=pd.read_parquet(ROOT/"data/processed/df_tcc_2013_2024.parquet")
    d["data_base"]=pd.to_datetime(d.data_base)
    d["taxa_inadimplencia"]=100*d.carteira_inadimplencia_total/d.carteira_ativa_total
    assert d.uf.nunique()==27 and len(d)==3888 and not d.duplicated(["uf","data_base"]).any()
    return d.sort_values(["uf","data_base"]).reset_index(drop=True)

def exposure_columns(d):
    return ["total_desastres"]+sorted(c for c in d if c.startswith("grupo_"))+sorted(c for c in d if c.startswith("tipo_"))

def estimability(d,col):
    z=d[col].fillna(0); nz=z>0; byuf=d.loc[nz].groupby("uf").size(); w=d.groupby("uf")[col].var().fillna(0)
    total=float(z.sum()); cells=int(nz.sum()); ufs=int(d.loc[nz,"uf"].nunique()); wvar=float(w.mean()); share=float(byuf.max()/byuf.sum()) if byuf.sum() else 1
    status="estimável" if total>=100 and cells>=50 and ufs>=10 and wvar>0 and share<=.75 else ("estimável com ressalvas" if total>=24 and cells>=12 and ufs>=5 and wvar>0 else "não estimável")
    return dict(eventos=total,uf_mes_positivos=cells,ufs_com_evento=ufs,variacao_within_media=wvar,concentracao_max_uf=share,estimabilidade=status)

def add_lags(d,col,K,transform="log1p"):
    out=d[["uf","data_base","taxa_inadimplencia"]].copy()
    out["x"]=np.log1p(d[col].clip(lower=0)) if transform=="log1p" else d[col].astype(float)
    g=out.groupby("uf",sort=False).x
    for k in range(K+1): out[f"x_l{k}"]=g.shift(k)
    return out

def sanity_lags(d,col):
    z=add_lags(d,col,1)
    assert z.groupby("uf").head(1).x_l1.isna().all()
    return True

def design(d,col,K,transform="log1p",time_fe="full"):
    z=add_lags(d,col,K,transform).dropna().reset_index(drop=True)
    lag=[f"x_l{k}" for k in range(K+1)]; X=z[lag].copy()
    X=pd.concat([X,pd.get_dummies(z.uf,prefix="uf",drop_first=True,dtype=float)],axis=1)
    if time_fe=="full": T=pd.get_dummies(z.data_base.dt.strftime("%Y-%m"),prefix="t",drop_first=True,dtype=float)
    elif time_fe=="month": T=pd.get_dummies(z.data_base.dt.month,prefix="m",drop_first=True,dtype=float)
    else: T=pd.DataFrame({"trend":np.arange(len(z),dtype=float)})
    X=pd.concat([X,T],axis=1); X.insert(0,"const",1.)
    return z,z.taxa_inadimplencia.astype(float),X.astype(float)

def fit_unrestricted(d,col,K,transform="log1p",time_fe="full"):
    z,y,X=design(d,col,K,transform,time_fe); m=OLS(y,X).fit(); C=cov_cluster(m,z.uf,use_correction=True)
    names=list(m.params.index); ix=[names.index(f"x_l{k}") for k in range(K+1)]
    b=m.params.iloc[ix].to_numpy(); V=C[np.ix_(ix,ix)]; one=np.ones(K+1); df=z.uf.nunique()-1; tc=stats.t.ppf(.975,df)
    se=np.sqrt(np.diag(V)); cum=float(one@b); sec=float(np.sqrt(one@V@one))
    R=np.eye(len(names))[ix]; joint=float(m.wald_test(R,cov_p=C,use_f=True,scalar=True).pvalue)
    corr=np.corrcoef(X[[f"x_l{k}" for k in range(K+1)]].to_numpy(),rowvar=False)
    s=dict(N=len(z),UFs=27,K=K,metodo="irrestrito",q=np.nan,efeito_contemporaneo=b[0],efeito_acumulado=cum,se_acumulado=sec,ci_acum_low=cum-tc*sec,ci_acum_high=cum+tc*sec,p_acumulado=float(2*stats.t.sf(abs(cum/sec),df)),p_conjunto=joint,max_corr_lags=float(np.nanmax(abs(corr-np.eye(K+1)))),condition_number_lags=float(np.linalg.cond(X[[f"x_l{k}" for k in range(K+1)]])),AIC=m.aic,BIC=m.bic)
    c=pd.DataFrame({"lag":range(K+1),"beta":b,"se":se,"ci_low":b-tc*se,"ci_high":b+tc*se})
    return s,c

def almon_matrix(K,q): return np.vander(np.arange(K+1,dtype=float),N=q+1,increasing=True)

def fit_almon(d,col,K,q,transform="log1p",time_fe="full"):
    z,y,Xu=design(d,col,K,transform,time_fe); lag=[f"x_l{k}" for k in range(K+1)]; P=almon_matrix(K,q); Z=Xu[lag].to_numpy()@P
    X=Xu.drop(columns=lag).copy()
    for j in range(q+1): X[f"almon{j}"]=Z[:,j]
    m=OLS(y,X).fit(); C=cov_cluster(m,z.uf,use_correction=True); names=list(m.params.index); ia=[names.index(f"almon{j}") for j in range(q+1)]
    a=m.params.iloc[ia].to_numpy(); Va=C[np.ix_(ia,ia)]; b=P@a; V=P@Va@P.T; one=np.ones(K+1); df=26; tc=stats.t.ppf(.975,df)
    se=np.sqrt(np.diag(V)); cum=float(one@b); sec=float(np.sqrt(one@V@one)); R=np.eye(len(names))[ia]
    s=dict(N=len(z),UFs=27,K=K,metodo="Almon",q=q,efeito_contemporaneo=b[0],efeito_acumulado=cum,se_acumulado=sec,ci_acum_low=cum-tc*sec,ci_acum_high=cum+tc*sec,p_acumulado=float(2*stats.t.sf(abs(cum/sec),df)),p_conjunto=float(m.wald_test(R,cov_p=C,use_f=True,scalar=True).pvalue),AIC=m.aic,BIC=m.bic)
    c=pd.DataFrame({"lag":range(K+1),"beta":b,"se":se,"ci_low":b-tc*se,"ci_high":b+tc*se})
    return s,c

def add_fdr(S,col):
    S["q_"+col]=np.nan
    for _,ix in S.groupby(["periodo","nivel"]).groups.items(): S.loc[ix,"q_"+col]=multipletests(S.loc[ix,col].fillna(1),method="fdr_bh")[1]
    return S

def run():
    d=load_panel(); cols=exposure_columns(d); sanity_lags(d,cols[0]); audits=[]; summaries=[]; coefs=[]
    for per,(a,b) in PERIODS.items():
        dp=d[d.data_base.between(a,b)].copy()
        for col in cols:
            nivel="Total" if col=="total_desastres" else ("Grupo" if col.startswith("grupo_") else "Tipologia")
            aud=estimability(dp,col); audits.append(dict(periodo=per,exposicao=col,nivel=nivel,**aud))
            if aud["estimabilidade"]=="não estimável": continue
            cand=[]
            for K in K_GRID:
                try:
                    s,c=fit_unrestricted(dp,col,K); cand.append((s["BIC"],K,s,c))
                except Exception: pass
            if not cand: continue
            _,K,s,c=min(cand,key=lambda x:(x[0],x[1]))
            unstable=s["max_corr_lags"]>.8 or s["condition_number_lags"]>30; chosen=s; cc=c
            if unstable:
                ac=[]
                for q in Q_GRID:
                    if q<K:
                        try:
                            sa,ca=fit_almon(dp,col,K,q); ac.append((sa["BIC"],q,sa,ca))
                        except Exception: pass
                if ac: _,q,chosen,cc=min(ac,key=lambda x:(x[0],x[1]))
            chosen.update(periodo=per,exposicao=col,nivel=nivel,transformacao="log1p",time_fe="UF FE + mês-ano FE",estimabilidade=aud["estimabilidade"],almon_acionado=unstable)
            summaries.append(chosen); coefs.append(cc.assign(periodo=per,exposicao=col,nivel=nivel,metodo=chosen["metodo"],K=K,q=chosen["q"]))
    A=pd.DataFrame(audits); S=pd.DataFrame(summaries); C=pd.concat(coefs,ignore_index=True) if coefs else pd.DataFrame()
    if len(S): S=add_fdr(add_fdr(S,"p_acumulado"),"p_conjunto")
    A.to_csv(OUT/"estimabilidade.csv",index=False); S.to_csv(OUT/"resultados.csv",index=False); C.to_csv(OUT/"coeficientes_lags.csv",index=False)
    return A,S,C
