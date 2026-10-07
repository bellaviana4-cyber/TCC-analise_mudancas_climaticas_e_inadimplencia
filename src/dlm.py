from __future__ import annotations
from pathlib import Path
import json, math, re, warnings
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "tables" / "dlm"
PERIODS = {
    "Total (2013–2024)": ("2013-01-01", "2024-12-01"),
    "Pré-pandemia (até jan/2020)": ("2013-01-01", "2020-01-01"),
}
K_GRID = (3, 6, 9, 12)
Q_GRID = (2, 3)
SEED = 20261003

LABELS = {
    "climatologico": "Climatológico", "hidrologico": "Hidrológico",
    "meteorologico": "Meteorológico", "outros": "Outros",
    "alagamentos": "Alagamentos", "chuvas_intensas": "Chuvas Intensas",
    "doencas_infecciosas": "Doenças infecciosas", "enxurradas": "Enxurradas",
    "erosao": "Erosão", "estiagem_e_seca": "Estiagem e Seca",
    "granizo": "Granizo", "incendio_florestal": "Incêndio Florestal",
    "inundacoes": "Inundações", "movimento_de_massa": "Movimento de Massa",
    "onda_de_calor_e_baixa_umidade": "Onda de Calor e Baixa Umidade",
    "onda_de_frio": "Onda de Frio", "rompimento_colapso_de_barragens": "Rompimento/Colapso de barragens",
    "tornado": "Tornado", "vendavais_e_ciclones": "Vendavais e Ciclones",
}

def exposure_columns(d):
    return ["total_desastres"] + [c for c in d if c.startswith("grupo_")] + [c for c in d if c.startswith("tipo_")]

def exposure_label(c):
    if c == "total_desastres": return "Total de desastres"
    nivel = "Grupo" if c.startswith("grupo_") else "Tipologia"
    key = re.sub(r"^(grupo_|tipo_)", "", c)
    return f"{nivel} | {LABELS.get(key, key)}"

def exposure_level(c):
    return "Total" if c == "total_desastres" else ("Grupo" if c.startswith("grupo_") else "Tipologia")

def load_panel(path=None):
    if path is None:
        path = ROOT / "data" / "processed" / "df_tcc_2013_2024.csv"
    d = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    d["data_base"] = pd.to_datetime(d["data_base"])
    d = d.sort_values(["uf", "data_base"]).reset_index(drop=True)
    assert len(d) == 3888 and d.uf.nunique() == 27 and d.data_base.nunique() == 144
    assert not d.duplicated(["uf", "data_base"]).any()
    calc = 100 * d.carteira_inadimplencia_total / d.carteira_ativa_total
    assert np.allclose(calc, d.taxa_inadimplencia, atol=1e-10, rtol=0)
    return d

def validate_atlas(path, d):
    a = pd.read_csv(path, sep=";", encoding="latin1",
                    usecols=["Data_Evento", "grupo_de_desastre", "descricao_tipologia"], low_memory=False)
    a["date"] = pd.to_datetime(a.Data_Evento, dayfirst=True, errors="coerce")
    a = a[a.date.dt.year.between(2013, 2024)]
    rows = [{"checagem":"Total", "atlas":len(a), "painel":int(d.total_desastres.sum())}]
    for nome, col in [("Climatológico","grupo_climatologico"),("Hidrológico","grupo_hidrologico"),
                      ("Meteorológico","grupo_meteorologico"),("Outros","grupo_outros")]:
        rows.append({"checagem":"Grupo "+nome, "atlas":int((a.grupo_de_desastre==nome).sum()), "painel":int(d[col].sum())})
    for col in [c for c in d if c.startswith("tipo_")]:
        key = re.sub("^tipo_", "", col); nome = LABELS.get(key, key)
        rows.append({"checagem":"Tipologia "+nome, "atlas":int((a.descricao_tipologia==nome).sum()), "painel":int(d[col].sum())})
    out = pd.DataFrame(rows); out["ok"] = out.atlas.eq(out.painel)
    assert out.ok.all()
    return out

def estimability(d, c):
    x = d[c].fillna(0).astype(float); nz = x.gt(0)
    sums = d.loc[nz].groupby("uf")[c].sum()
    total = float(x.sum()); cells = int(nz.sum()); ufs = int(d.loc[nz,"uf"].nunique())
    within = float(d.groupby("uf")[c].var().fillna(0).mean())
    conc = float(sums.max()/sums.sum()) if sums.sum() else 1.0
    if total >= 100 and cells >= 50 and ufs >= 10 and within > 0 and conc <= .75:
        status = "estimável"
    elif total >= 24 and cells >= 12 and ufs >= 5 and within > 0:
        status = "estimável com ressalvas"
    else:
        status = "não estimável"
    return dict(eventos=total, uf_mes_positivos=cells, ufs_com_evento=ufs,
                variacao_within_media=within, concentracao_max_uf=conc, estimabilidade=status)

def stationarity_one(s):
    s = pd.Series(s).dropna().astype(float)
    if len(s) < 30 or s.nunique() < 3: return np.nan, np.nan
    try: adf = adfuller(s, regression="c", autolag="BIC", maxlag=min(12, max(1, len(s)//4)))[1]
    except Exception: adf = np.nan
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore"); kp = kpss(s, regression="c", nlags="auto")[1]
    except Exception: kp = np.nan
    return float(adf), float(kp)

def stationarity_y(d):
    rows=[]
    for per,(ini,fim) in PERIODS.items():
        z=d[d.data_base.between(ini,fim)].copy(); z["dy"]=z.groupby("uf").taxa_inadimplencia.diff()
        tw=z.taxa_inadimplencia-z.groupby("uf").taxa_inadimplencia.transform("mean")-z.groupby("data_base").taxa_inadimplencia.transform("mean")+z.taxa_inadimplencia.mean()
        for nome,serie in [("I em nível",z.taxa_inadimplencia),("I em nível após TWFE",tw),("ΔI",z.dy)]:
            tests=[stationarity_one(g.v) for _,g in z.assign(v=serie).groupby("uf")]
            ap=np.array([t[0] for t in tests]); kp=np.array([t[1] for t in tests]); valid=np.isfinite(ap)
            fisher=stats.chi2.sf(-2*np.log(np.clip(ap[valid],1e-300,1)).sum(),2*valid.sum())
            rows.append(dict(periodo=per,serie=nome,adf_rejeita_prop=np.mean(ap<.05),adf_fisher_p=fisher,
                             kpss_nao_rejeita_prop=np.mean(kp>=.05),concordancia_estacionaria_prop=np.mean((ap<.05)&(kp>=.05))))
    return pd.DataFrame(rows)

def build_common(d, c, transform="log1p"):
    q=d[["uf","data_base","taxa_inadimplencia"]].copy()
    q["y"]=q.groupby("uf").taxa_inadimplencia.diff()
    q["x"]=np.log1p(d[c].clip(lower=0)).to_numpy() if transform=="log1p" else d[c].astype(float).to_numpy()
    for k in range(13): q[f"x{k}"]=q.groupby("uf").x.shift(k)
    assert q.groupby("uf").head(1).x1.isna().all(), "leakage entre UFs"
    q=q.dropna(subset=["y"]+[f"x{k}" for k in range(13)]).reset_index(drop=True)
    assert q.groupby("uf").size().nunique()==1
    return q

def twoway(q, A):
    f=pd.DataFrame(np.asarray(A,float)); uf=q.uf.reset_index(drop=True); tm=q.data_base.reset_index(drop=True)
    return (f-f.groupby(uf).transform("mean")-f.groupby(tm).transform("mean")+f.mean()).to_numpy()

def prepare(q):
    M=np.column_stack([q.y.to_numpy(),q[[f"x{k}" for k in range(13)]].to_numpy()])
    R=twoway(q,M)
    return dict(y=R[:,0],Xall=R[:,1:],groups=q.uf.to_numpy(),time=q.data_base.to_numpy(),
                absorbed=q.uf.nunique()+q.data_base.nunique()-1)

def ols(y,X):
    inv=np.linalg.pinv(X.T@X,rcond=1e-12); b=inv@(X.T@y); u=y-X@b
    return b,u,inv,float(u@u)

def cluster_cov(X,u,g,absorbed):
    inv=np.linalg.pinv(X.T@X,rcond=1e-12); meat=np.zeros((X.shape[1],X.shape[1])); ug=np.unique(g)
    for value in ug:
        m=g==value; score=X[m].T@u[m]; meat+=np.outer(score,score)
    factor=(len(ug)/(len(ug)-1))*((len(g)-1)/max(1,len(g)-X.shape[1]-absorbed))
    return factor*inv@meat@inv

def dk_cov(X,u,time,L=12):
    inv=np.linalg.pinv(X.T@X,rcond=1e-12); times=np.unique(time)
    S=np.vstack([X[time==t].T@u[time==t] for t in times]); Omega=S.T@S; L=min(L,len(times)-1)
    for lag in range(1,L+1):
        w=1-lag/(L+1); G=S[lag:].T@S[:-lag]; Omega+=w*(G+G.T)
    return inv@Omega@inv

def linear_test(b,V,c,df=26):
    c=np.asarray(c,float); est=float(c@b); se=float(np.sqrt(max(c@V@c,0))); t=est/se if se else np.nan
    p=float(2*stats.t.sf(abs(t),df)); crit=stats.t.ppf(.975,df)
    return est,se,est-crit*se,est+crit*se,p

def joint_test(b,V,df2=26):
    q=len(b); F=float(b@np.linalg.pinv(V)@b/q); return F,float(stats.f.sf(F,q,df2))

def lag_metrics(X):
    Z=(X-X.mean(0))/np.where(X.std(0,ddof=1)>0,X.std(0,ddof=1),1)
    R=np.corrcoef(Z,rowvar=False)
    return float(np.max(np.abs(R-np.eye(len(R))))),float(np.linalg.cond(Z)),float(np.max(np.diag(np.linalg.pinv(R))))

def fit(pre,K,method="Irrestrito",qdeg=None):
    Xlags=pre["Xall"][:,:K+1]; y=pre["y"]
    if method=="Almon":
        kk=np.arange(K+1.); P=np.column_stack([kk**j for j in range(qdeg+1)]); X=Xlags@P; contrast=P.T@np.ones(K+1)
    else:
        P=None; X=Xlags; contrast=np.ones(K+1)
    b,u,inv,sse=ols(y,X); C=cluster_cov(X,u,pre["groups"],pre["absorbed"]); DK=dk_cov(X,u,pre["time"])
    cum=linear_test(b,C,contrast,26); cum_dk=linear_test(b,DK,contrast,max(1,len(np.unique(pre["time"]))-1))
    F,pjoint=joint_test(b,C,26); _,pjoint_dk=joint_test(b,DK,max(1,len(np.unique(pre["time"]))-1))
    beta=P@b if P is not None else b; Vbeta=P@C@P.T if P is not None else C
    se=np.sqrt(np.clip(np.diag(Vbeta),0,None)); crit=stats.t.ppf(.975,26); plag=2*stats.t.sf(np.abs(beta/se),26)
    n=len(y); ktotal=pre["absorbed"]+len(b); aic=n*np.log(sse/n)+2*ktotal; bic=n*np.log(sse/n)+np.log(n)*ktotal
    mc,cond,vif=lag_metrics(Xlags)
    coefs=pd.DataFrame({"lag":range(K+1),"beta":beta,"se":se,"ci_low":beta-crit*se,"ci_high":beta+crit*se,"p_lag":plag})
    return dict(method=method,q=qdeg,b=b,u=u,X=X,contrast=contrast,AIC=aic,BIC=bic,
                efeito_acumulado=cum[0],se_acumulado=cum[1],ci95_low=cum[2],ci95_high=cum[3],p_acumulado=cum[4],
                p_acumulado_dk=cum_dk[4],p_conjunto=pjoint,p_conjunto_dk=pjoint_dk,F_conjunto=F,
                max_corr=mc,condition_number=cond,max_vif=vif,coefs=coefs)

def run_primary(data_path=None, out=OUT):
    out=Path(out); out.mkdir(parents=True,exist_ok=True); d=load_panel(data_path)
    stationarity_y(d).to_csv(out/"estacionariedade_painel.csv",index=False,encoding="utf-8-sig")
    audits=[]; results=[]; coef=[]; ktab=[]
    for period,(ini,fim) in PERIODS.items():
        dp=d[d.data_base.between(ini,fim)].copy()
        for col in exposure_columns(d):
            aud=estimability(dp,col); audits.append(dict(periodo=period,exposicao=exposure_label(col),coluna=col,nivel=exposure_level(col),**aud))
            if aud["estimabilidade"]=="não estimável": continue
            qdf=build_common(dp,col); pre=prepare(qdf); cand=[]
            for K in K_GRID:
                fu=fit(pre,K); cand.append((fu["BIC"],K,fu)); ktab.append(dict(periodo=period,exposicao=exposure_label(col),nivel=exposure_level(col),K=K,AIC=fu["AIC"],BIC=fu["BIC"],max_corr=fu["max_corr"],condition_number=fu["condition_number"],max_vif=fu["max_vif"]))
            _,K,fu=min(cand,key=lambda z:(z[0],z[1])); trigger=fu["max_corr"]>.80 or fu["condition_number"]>30; final=fu
            if trigger:
                ac=[(fit(pre,K,"Almon",q)["BIC"],q,fit(pre,K,"Almon",q)) for q in Q_GRID if q<K]
                if ac: _,_,final=min(ac,key=lambda z:(z[0],z[1]))
            row=dict(periodo=period,exposicao=exposure_label(col),nivel=exposure_level(col),N=len(qdf),UFs=qdf.uf.nunique(),K=K,metodo=final["method"],q=final["q"],almon_acionado=trigger,
                     efeito_contemporaneo=float(final["coefs"].iloc[0].beta),efeito_acumulado=final["efeito_acumulado"],ci95_low=final["ci95_low"],ci95_high=final["ci95_high"],p_acumulado=final["p_acumulado"],p_acumulado_dk=final["p_acumulado_dk"],
                     F_conjunto=final["F_conjunto"],p_conjunto=final["p_conjunto"],p_conjunto_dk=final["p_conjunto_dk"],estimabilidade=aud["estimabilidade"],max_corr_lags_irrestrito=fu["max_corr"],condition_number_irrestrito=fu["condition_number"],max_vif_irrestrito=fu["max_vif"])
            results.append(row); cc=final["coefs"].copy();cc["periodo"]=period;cc["exposicao"]=exposure_label(col);cc["nivel"]=exposure_level(col);coef.append(cc)
    A=pd.DataFrame(audits); R=pd.DataFrame(results); C=pd.concat(coef,ignore_index=True); K=pd.DataFrame(ktab)
    sizes=A.groupby(["periodo","nivel"]).size().to_dict()
    for pcol in ["p_acumulado","p_conjunto"]:
        R["q_"+pcol]=np.nan
        for key,idx in R.groupby(["periodo","nivel"]).groups.items():
            vals=R.loc[idx,pcol].fillna(1).to_numpy(); m=sizes[key]
            R.loc[idx,"q_"+pcol]=multipletests(np.r_[vals,np.ones(m-len(vals))],method="fdr_bh")[1][:len(vals)]
    C["q_lag"]=np.nan
    for key,idx in C.groupby(["periodo","nivel"]).groups.items():
        vals=C.loc[idx,"p_lag"].fillna(1).to_numpy(); m=sizes[key]*4
        C.loc[idx,"q_lag"]=multipletests(np.r_[vals,np.ones(m-len(vals))],method="fdr_bh")[1][:len(vals)]
    A.to_csv(out/"estimabilidade.csv",index=False,encoding="utf-8-sig");R.to_csv(out/"resultados_principais.csv",index=False,encoding="utf-8-sig");C.to_csv(out/"coeficientes_lags.csv",index=False,encoding="utf-8-sig");K.to_csv(out/"selecao_K.csv",index=False,encoding="utf-8-sig")
    return A,R,C,K

if __name__ == "__main__":
    run_primary()
