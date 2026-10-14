"""Auditoria auxiliar das especificações SARIMA, antes da comparação com desastres."""
from pathlib import Path
from itertools import product
import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import acf

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs/tables/sarimax"
INP=ROOT/"outputs/tables/segunda_etapa/series_nacionais_agregadas.csv"
OUT.mkdir(parents=True,exist_ok=True)
df=pd.read_csv(INP,parse_dates=["data"],encoding="utf-8-sig").set_index("data")
df["y"]=100*np.log(df["I"]).diff()
df=df.iloc[4:].copy()
t=np.arange(len(df))
for k in [1,2]:
    df[f"sin{k}"]=np.sin(2*np.pi*k*(df.index.month-1)/12)
    df[f"cos{k}"]=np.cos(2*np.pi*k*(df.index.month-1)/12)
df["covid_mar2020"]=(df.index==pd.Timestamp("2020-03-01")).astype(int)
df["covid_abr2020"]=(df.index==pd.Timestamp("2020-04-01")).astype(int)
df["covid_2020_21"]=((df.index>=pd.Timestamp("2020-03-01"))&(df.index<=pd.Timestamp("2021-12-01"))).astype(int)
base_determin=["sin1","cos1","sin2","cos2"]
options={
"sem_deterministicas":[],
"harmonicos_1":["sin1","cos1"],
"harmonicos_2":base_determin,
"harmonicos_2_pandemia":base_determin+["covid_mar2020","covid_abr2020"],
"harmonicos_2_regime":base_determin+["covid_2020_21"],
"harmonicos_2_regime_pulsos":base_determin+["covid_2020_21","covid_mar2020","covid_abr2020"],
}
orders=[
((0,0,0),(0,0,0,12)),
((1,0,0),(0,0,0,12)),
((2,0,0),(0,0,0,12)),
((3,0,0),(0,0,0,12)),
((4,0,0),(0,0,0,12)),
((0,0,1),(0,0,0,12)),
((0,0,2),(0,0,0,12)),
((1,0,1),(0,0,0,12)),
((2,0,1),(0,0,0,12)),
((1,0,2),(0,0,0,12)),
((1,0,0),(1,0,0,12)),
((1,0,1),(1,0,0,12)),
((2,0,0),(1,0,0,12)),
((2,0,1),(1,0,0,12)),
((1,0,1),(0,0,1,12)),
((2,0,0),(0,0,1,12)),
((1,0,0),(0,0,1,12)),
((2,0,2),(0,0,0,12)),
]
rows=[]
for period,train in [("total",df.loc[:"2022-12"]),("pre",df.loc[:"2020-01"])]:
    for style,extra in options.items():
        if period=="pre" and "pandemia" in style or (period=="pre" and "regime" in style):
            continue
        # Pre-pandemia uses only up to 2 Fourier terms, no pandemic pulse.
        for order,seasonal in orders:
            x=train[extra] if extra else None
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    mod=SARIMAX(train["y"],exog=x,order=order,seasonal_order=seasonal,
                               trend="c",enforce_stationarity=True,enforce_invertibility=True)
                    fit=mod.fit(disp=False,maxiter=100)
                if not fit.mle_retvals.get("converged",False):
                    continue
                err=np.asarray(fit.filter_results.standardized_forecasts_error[0])
                resid=np.asarray(fit.resid)
                lb=acorr_ljungbox(err,lags=[6,12,24],return_df=True)
                rows.append(dict(periodo=period,deterministicas=style,ordem=str(order),
                                 sazonal=str(seasonal),k=len(fit.params),n=len(train),
                                 aic=float(fit.aic),bic=float(fit.bic),
                                 lb6=float(lb.loc[6,"lb_pvalue"]),lb12=float(lb.loc[12,"lb_pvalue"]),
                                 lb24=float(lb.loc[24,"lb_pvalue"]),
                                 acf1=float(acf(err,nlags=24)[1]),
                                 acf2=float(acf(err,nlags=24)[2]),
                                 acf3=float(acf(err,nlags=24)[3]),
                                 acf4=float(acf(err,nlags=24)[4]),
                                 acf6=float(acf(err,nlags=24)[6]),
                                 acf12=float(acf(err,nlags=24)[12])))
            except Exception as exc:
                print("Falhou",period,style,order,seasonal,str(exc)[:90])
r=pd.DataFrame(rows)
r["lb_ok"]=(r.lb6>=.05)&(r.lb12>=.05)
r.to_csv(OUT/"triagem_residual.csv",index=False,encoding="utf-8-sig")
print("CANDIDATOS:",len(r))
for p,g in r.groupby("periodo"):
    print("\nPERIODO:",p,"aprovados:",g.lb_ok.sum())
    print("MELHORES BIC GERAIS\n",g.nsmallest(12,"bic").round(4).to_string(index=False))
    print("MELHORES BIC APROVADOS\n",g[g.lb_ok].nsmallest(12,"bic").round(4).to_string(index=False))
    print("POR DETERMINISTICAS\n",g.groupby("deterministicas").agg(n=("bic","size"),n_ok=("lb_ok","sum"),min_bic=("bic","min")).round(3).to_string())
