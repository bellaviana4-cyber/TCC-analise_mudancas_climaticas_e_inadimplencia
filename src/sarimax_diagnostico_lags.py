"""Segunda triagem justificada pela ACF residual em 3 e 6 meses."""
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import acf
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs/tables/sarimax"
INP=ROOT/"outputs/tables/segunda_etapa/series_nacionais_agregadas.csv"
d=pd.read_csv(INP,parse_dates=["data"],encoding="utf-8-sig").set_index("data")
d["y"]=100*np.log(d["I"]).diff()
d=d.iloc[4:].copy()
m=d.index.month-1
d["sin1"]=np.sin(2*np.pi*m/12)
d["cos1"]=np.cos(2*np.pi*m/12)
d["sin2"]=np.sin(4*np.pi*m/12)
d["cos2"]=np.cos(4*np.pi*m/12)
d["covid_mar"]=(d.index==pd.Timestamp("2020-03-01")).astype(int)
d["covid_abr"]=(d.index==pd.Timestamp("2020-04-01")).astype(int)
# Modelo clássico com defasagens específicas no componente AR (sem seis termos seguidos).
ordens=[
(([1,3],0,0),(0,0,0,12)),
(([1,6],0,0),(0,0,0,12)),
(([1,3,6],0,0),(0,0,0,12)),
(([1,3,6],0,0),(1,0,0,12)),
(([1,3,6],0,1),(1,0,0,12)),
(([1,3,6],0,1),(0,0,0,12)),
(([1,2,3,6],0,0),(0,0,0,12)),
(([1,3,6,12],0,0),(0,0,0,12)),
((1,0,0),(1,0,0,6)),
((1,0,1),(1,0,0,6)),
((1,0,0),(1,0,0,3)),
((2,0,0),(1,0,0,3)),
((1,0,1),(1,0,0,3)),
((2,0,1),(1,0,0,6)),
(([1,3],0,1),(1,0,0,6)),
(([3,6],0,0),(1,0,0,12)),
]
styles={"nenhum":[],"fourier1":["sin1","cos1"],
        "fourier2":["sin1","cos1","sin2","cos2"],
        "pulsos":["covid_mar","covid_abr"]}
rows=[]
for periodo,train in [("total",d.loc[:"2022-12"]),("pre",d.loc[:"2020-01"])]:
    for nome,cols in styles.items():
        if periodo=="pre" and nome=="pulsos":
            continue
        for ordem,saz in ordens:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    mod=SARIMAX(train["y"],exog=train[cols] if cols else None,
                               order=ordem,seasonal_order=saz,trend="c",
                               enforce_stationarity=True,enforce_invertibility=True)
                    fit=mod.fit(maxiter=150,disp=False)
                if not fit.mle_retvals.get("converged",False):
                    continue
                e=np.asarray(fit.filter_results.standardized_forecasts_error[0])
                lb=acorr_ljungbox(e,lags=[6,12,24],return_df=True)
                ac=acf(e,nlags=12)
                rows.append(dict(periodo=periodo,deterministicas=nome,
                        ordem=str(ordem),sazonal=str(saz),n=len(e),k=len(fit.params),
                        bic=float(fit.bic),aic=float(fit.aic),
                        lb6=float(lb.loc[6,"lb_pvalue"]),
                        lb12=float(lb.loc[12,"lb_pvalue"]),
                        lb24=float(lb.loc[24,"lb_pvalue"]),
                        acf3=float(ac[3]),acf6=float(ac[6])))
            except Exception as exc:
                print(periodo,nome,ordem,saz,type(exc).__name__)
a=pd.DataFrame(rows)
a["lb_ok"]=(a.lb6>=.05)&(a.lb12>=.05)
a.to_csv(OUT/"triagem_lags_especificos.csv",index=False,encoding="utf-8-sig")
for periodo,g in a.groupby("periodo"):
    print("\nPERIODO",periodo,"testados",len(g),"aprovados",g.lb_ok.sum())
    print("MELHORES GERAIS\n",g.nsmallest(12,"bic").round(4).to_string(index=False))
    print("MELHORES COM DIAGNOSTICO FAVORAVEL\n",g[g.lb_ok].nsmallest(12,"bic").round(4).to_string(index=False))
