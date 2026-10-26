"""SARIMAX por tipologia e geral com lags 0..24 ou somente 3..24.

São ajustados modelos SARIMA de referência (mesmas ordens e amostra) e
SARIMAX univariados climáticos, um por tipologia em cada UF/período,
além da análise Brasil ponderada por carteira. Os blocos consecutivos
0..K são previamente auditados e comparados pelo BIC do treino.
Ao definir TCC_SARIMAX_LAG_INICIAL=3, os blocos passam a ser 3..K
e os resultados são gravados numa pasta separada (sem alterar 0..24).

O SARIMAX geral combina os lags selecionados individualmente, tentando
incluir as 16 tipologias. Sem posto ou suporte, reduz o conjunto por
critério determinístico independente dos valores-p do modelo conjunto;
as exclusões ficam explícitas. Inferência permanece pós-seleção exploratória.

Uso: python src/sarimax_por_tipologia_k0_24_20261026.py --fase individuais
     --uf MG --periodo Total
     python src/sarimax_por_tipologia_k0_24_20261026.py --fase gerais
     python src/sarimax_por_tipologia_k0_24_20261026.py --fase consolidar
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.stats.multitest import multipletests

from analise_estadual import TIPOS, load
from sarimax_revisao_final import MODELS, PERIODS, MAX_COND, predicted_1step, series_for_unit
from sarimax_todas_tipologias_20261026 import lb12_arma_inovacoes_padronizadas
from sarimax_com_defasagens import lag_design

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/processed/df_tcc_2013_2024.csv"
MIN_LAG = int(os.environ.get("TCC_SARIMAX_LAG_INICIAL", "0"))
if MIN_LAG not in (0, 3):
    raise ValueError("TCC_SARIMAX_LAG_INICIAL deve ser 0 ou 3")
OUT = ROOT / ("outputs/tables/sarimax_por_tipologia_k0_24_20261026" if MIN_LAG == 0
              else "outputs/tables/sarimax_por_tipologia_k3_24_20261026")
UNITS = OUT / "unidades"
HASH = "46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36"
MAX_LAG = 24
KS = tuple(range(MIN_LAG, MAX_LAG + 1))
RESERVE_TEMPORAL = 5
MIN_POS = 3
N_ITER = (70, 150)


def unit_path(period, unit, kind):
    return UNITS / ("pre" if period == "Pré" else "total") / f"{unit}_{kind}.csv"


def fit_model(y, order, seasonal, X=None):
    last=None; warnings_set=[]
    for iteration in N_ITER:
        with warnings.catch_warnings(record=True) as detected:
            warnings.simplefilter("always")
            with np.errstate(all="ignore"):
                from statsmodels.tsa.statespace.sarimax import SARIMAX
                model = SARIMAX(y,exog=X,order=order,seasonal_order=seasonal,
                               trend="c",enforce_stationarity=True,enforce_invertibility=True)
                last = model.fit(method="lbfgs",maxiter=iteration,disp=False)
        warnings_set.extend(str(w.message)[:110] for w in detected)
        if last.mle_retvals.get("converged",False):break
    return last, bool(last.mle_retvals.get("converged",False)), sorted(set(warnings_set))


def data_for(df, period, unit):
    y,x,d,dates=series_for_unit(df,unit,period)
    train0=PERIODS[period][2]
    nt=train0-MAX_LAG
    assert len(y)==train0+PERIODS[period][3]
    assert nt >= 40
    return (y[MAX_LAG:],x,d,nt,train0)


def audit_matrix(A, nt):
    p=A.shape[1]
    s=A[:nt].std(axis=0)
    missing=int(np.sum(s<=1e-12))
    if missing:
        return None,dict(status="regressora constante no treino",n_constantes=missing,posto=np.nan,condicao=np.nan)
    avg=A[:nt].mean(axis=0)
    Z=(A-avg)/s
    rank=int(np.linalg.matrix_rank(Z[:nt]))
    if rank<p:return None,dict(status="posto incompleto",n_constantes=0,posto=rank,condicao=np.nan)
    cond=float(np.linalg.cond(Z[:nt]))
    if not np.isfinite(cond) or cond>MAX_COND:
        return None,dict(status="condicionamento elevado",n_constantes=0,posto=rank,condicao=cond)
    if nt<=p+RESERVE_TEMPORAL:
        return None,dict(status="graus de liberdade insuficientes",n_constantes=0,posto=rank,condicao=cond)
    return (Z,s),dict(status="identificável",n_constantes=0,posto=rank,condicao=cond)


def baseline_for(y,nt,period,unit):
    candidates=[]; good=[]
    for order, seasonal in MODELS:
        row=dict(periodo=period,unidade=unit,modelo="SARIMA",ordem=str(order),
                 sazonal=str(seasonal),n_treino=nt)
        try:
            fit, converged, ws=fit_model(y[:nt],order,seasonal)
            row.update(status="estimado" if converged else "não convergiu",
                       BIC=float(fit.bic),AIC=float(fit.aic),avisos=" | ".join(ws))
            if converged and np.isfinite(fit.bic):good.append((fit,row))
        except Exception as exc:
            row.update(status="falha",erro=repr(exc)[:180])
        candidates.append(row)
    if not good:return None,candidates
    return min(good,key=lambda z:(z[1]["BIC"],z[1]["ordem"])),candidates


def persist(part,period,unit,name):
    loc=unit_path(period,unit,name)
    loc.parent.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(part).to_csv(loc,index=False,encoding="utf-8-sig")


def individually(df,period,unit):
    if unit_path(period,unit,"resumo").exists() and unit_path(period,unit,"candidatos").exists():
        print(period,unit,"já finalizado; preservando checkpoint",flush=True)
        return
    yy,x,d,nt,train0=data_for(df,period,unit)
    chosen, baselines=baseline_for(yy,nt,period,unit)
    if chosen is None:
        persist([dict(periodo=period,unidade=unit,status="sem SARIMA de referência")],period,unit,"resumo")
        persist(baselines,period,unit,"bases")
        return
    baseline,base_info=chosen
    order,seasonal=baseline.model.order,baseline.model.seasonal_order
    base_pred=predicted_1step(baseline,yy,None,nt)
    base_lp=lb12_arma_inovacoes_padronizadas(baseline)
    persist(baselines,period,unit,"bases")
    rows=[]; audited=[]; coeffs=[]
    for j, typ in enumerate(TIPOS):
        pos=int(np.sum(d[:train0,j]>0))
        feasible=[]
        for K in KS:
            reg={"periodo":period,"unidade":unit,"tipologia":typ,"K":K,
                 "n_treino_comum":nt,"n_teste":len(yy)-nt,
                 "n_ocorrencias_meses_treino":pos,"n_exog":K-MIN_LAG+1,
                 "ordem":str(order),"sazonal":str(seasonal)}
            if pos<MIN_POS:
                reg["status"]="suporte menor que três meses positivos"
                audited.append(reg)
                continue
            A=lag_design(x,[j],MAX_LAG,tuple(range(MIN_LAG,K+1)))
            standardized, audit=audit_matrix(A,nt)
            reg.update(audit)
            if standardized is None:
                audited.append(reg)
                continue
            Z,sd=standardized
            try:
                fitted,ok,ws=fit_model(yy[:nt],order,seasonal,Z[:nt])
                reg.update(status="estimado" if ok else "não convergiu",
                           BIC=float(fitted.bic),AIC=float(fitted.aic),
                           avisos=" | ".join(ws),convergiu=bool(ok))
                if ok and np.isfinite(fitted.bic):
                    feasible.append((K,fitted,Z,sd,reg))
            except Exception as exc:
                reg.update(status="falha numérica",erro=repr(exc)[:180],convergiu=False)
            audited.append(reg)
        common={"periodo":period,"unidade":unit,"tipologia":typ,"status":"não estimável",
                "n_treino":nt,"n_teste":len(yy)-nt,"n_ocorrencias_meses_treino":pos,
                "bic_sarima":float(baseline.bic),"rmse_sarima":base_pred["rmse"],
                "ordem":str(order),"sazonal":str(seasonal),
                "n_candidatos_estimaveis":len(feasible)}
        if feasible:
            K,fitted,Z,sd,rec=min(feasible,key=lambda z:(z[1].bic,z[0]))
            pred=predicted_1step(fitted,yy,Z,nt)
            ncols=K-MIN_LAG+1
            raw_coeff=np.asarray([fitted.params[fitted.param_names.index(f"x{a+1}")]/sd[a]
                                  for a in range(ncols)])
            raw_sd=float(x[:train0,j].std())
            # Escores padronizados em unidade da resposta 100*Delta log I,
            # para um pulso no X transformado igual a 1 desvio-padrão.
            delta=float(raw_coeff.sum()*raw_sd)
            row={**common,"status":"estimado","K":K,"K_max_testado":MAX_LAG,
                 "bic_sarimax":float(fitted.bic),"delta_BIC":float(fitted.bic-baseline.bic),
                 "rmse_sarimax":pred["rmse"],"mae_sarimax":pred["mae"],
                 "melhora_rmse_pct":100*(1-pred["rmse"]/base_pred["rmse"]),
                 "soma_beta":float(raw_coeff.sum()),
                 "impulso_padronizado_100dlogI":delta,
                 "associacao_acumulada_pct":float(100*np.expm1(delta/100)),
                 "n_exog":ncols,"lb12_padronizado":lb12_arma_inovacoes_padronizadas(fitted),
                 "lb12_sarima":base_lp,
                 "criterio":"menor BIC do treino entre candidatos convergidos"}
            for a in range(ncols):
                kpar=fitted.param_names.index(f"x{a+1}")
                coeffs.append(dict(periodo=period,unidade=unit,tipologia=typ,K=K,lag=MIN_LAG+a,
                                   coef_original=float(raw_coeff[a]),
                                   se_original=float(fitted.bse[kpar]/sd[a]),
                                   p_condicional=float(fitted.pvalues[kpar])))
            # Wald acumulado, exploratório e condicionado a toda a seleção.
            names=[fitted.param_names.index(f"x{a+1}") for a in range(ncols)]
            cov=np.asarray(fitted.cov_params())[np.ix_(names,names)]
            v=float(np.sum(cov/np.outer(sd,sd)))
            if v>0:
                row["p_soma_condicional"]=float(2*norm.sf(abs(raw_coeff.sum()/np.sqrt(v))))
            else:row["p_soma_condicional"]=np.nan
            rows.append(row)
        else:
            rows.append(common)
        print(period,unit,typ,"K="+str(rows[-1].get("K","—")),"candidatos=",len(feasible),flush=True)
        # Checkpoint por tipologia: recuperável em execução interrompida.
        persist(audited,period,unit,"candidatos_parcial")
        persist(rows,period,unit,"resumo_parcial")
        persist(coeffs,period,unit,"coeficientes_parcial")
    persist(audited,period,unit,"candidatos")
    persist(coeffs,period,unit,"coeficientes")
    persist(rows,period,unit,"resumo")


def combined(df,period,unit):
    outfile=unit_path(period,unit,"geral")
    if outfile.exists():return
    file=unit_path(period,unit,"resumo")
    if not file.exists():return
    chosen=pd.read_csv(file,encoding="utf-8-sig")
    if "K" not in chosen or not chosen.K.notna().any():
        persist([dict(periodo=period,unidade=unit,
                      status="nenhuma tipologia individual estimável",
                      n_tipologias_requisitadas=16,n_tipologias_incluidas=0,
                      numero_regressoras=0,
                      exclusoes=json.dumps({t:"modelo individual não estimável" for t in TIPOS},ensure_ascii=False))],
                period,unit,"geral")
        return
    yy,x,d,nt,train0=data_for(df,period,unit)
    ord1=ast.literal_eval(str(chosen.ordem.dropna().iloc[0]))
    seasonal=ast.literal_eval(str(chosen.sazonal.dropna().iloc[0]))
    baseline,ok,_=fit_model(yy[:nt],ord1,seasonal)
    if not ok:
        persist([dict(periodo=period,unidade=unit,status="baseline não convergiu")],period,unit,"geral")
        return
    included=[]; excluded={}; matrices=[]
    by_name={r.tipologia:r for r in chosen.itertuples() if r.status=="estimado" and pd.notna(r.K)}
    support=[(j,int(np.sum(d[:train0,j]>0))) for j in range(16)]
    # Priorização determinística por suporte, sem p-valores do modelo geral.
    for j,pos in sorted(support,key=lambda q:(-q[1],q[0])):
        typ=TIPOS[j]
        if typ not in by_name:
            excluded[typ]="modelo individual não estimável"
            continue
        k=int(by_name[typ].K)
        A=lag_design(x,[j],MAX_LAG,tuple(range(MIN_LAG,k+1)))
        trial=np.column_stack(matrices+[A]) if matrices else A
        checked, audit=audit_matrix(trial,nt)
        if checked is None:
            excluded[typ]=audit["status"]
            continue
        included.append((j,k))
        matrices.append(A)
    basic={"periodo":period,"unidade":unit,"status":"sem tipologia conjunta estimável",
           "n_treino":nt,"n_teste":len(yy)-nt,
           "ordem":str(ord1),"sazonal":str(seasonal),
           "n_tipologias_requisitadas":16,"n_tipologias_incluidas":len(included),
           "tipologias_incluidas":";".join(TIPOS[j] for j,k in included),
           "defasagens_incluidas":";".join(f"{TIPOS[j]}:{k}" for j,k in included),
           "exclusoes":json.dumps(excluded,ensure_ascii=False),
           "bic_sarima":float(baseline.bic),
           "rmse_sarima":predicted_1step(baseline,yy,None,nt)["rmse"]}
    if not matrices:
        persist([basic],period,unit,"geral")
        return
    block=np.column_stack(matrices)
    inspected, audit=audit_matrix(block,nt)
    assert inspected is not None
    Z,sd=inspected
    try:
        fitted,ok,ws=fit_model(yy[:nt],ord1,seasonal,Z[:nt])
        basic.update(status="estimado" if ok else "não convergiu",
                     bic_sarimax=float(fitted.bic),convergiu=bool(ok),
                     numero_regressoras=Z.shape[1],condicao=audit["condicao"],
                     avisos=" | ".join(ws))
        if ok:
            forecast=predicted_1step(fitted,yy,Z,nt)
            basic.update(delta_BIC=float(fitted.bic-baseline.bic),
                         rmse_sarimax=forecast["rmse"],
                         mae_sarimax=forecast["mae"],
                         melhora_rmse_pct=100*(1-forecast["rmse"]/basic["rmse_sarima"]),
                         lb12_padronizado=lb12_arma_inovacoes_padronizadas(fitted))
    except Exception as exc:
        basic.update(status="falha numérica",erro=repr(exc)[:200])
    persist([basic],period,unit,"geral")
    print("geral",period,unit,basic["status"],len(included),"tipologias",flush=True)


def consolidate():
    def gather(name):
        frames=[]
        for file in sorted(UNITS.glob(f"*/*_{name}.csv")):
            try:
                df=pd.read_csv(file,encoding="utf-8-sig")
                if len(df):frames.append(df)
            except pd.errors.EmptyDataError:pass
        return pd.concat(frames,ignore_index=True) if frames else pd.DataFrame()
    OUT.mkdir(parents=True,exist_ok=True)
    summaries={}
    for name in ("resumo","candidatos","coeficientes","geral","bases"):
        df=gather(name)
        if name=="resumo" and not df.empty and "p_soma_condicional" in df:
            df["q_soma_BH_exploratorio"]=np.nan
            for per,group in df.groupby("periodo"):
                ix=group.index[group.p_soma_condicional.notna()]
                if len(ix):df.loc[ix,"q_soma_BH_exploratorio"]=multipletests(df.loc[ix,"p_soma_condicional"],method="fdr_bh")[1]
        df.to_csv(OUT/f"{name}.csv",index=False,encoding="utf-8-sig")
        summaries[name+"_linhas"]=len(df)
        if name=="resumo" and not df.empty:
            summaries["univariados_estimados"]=int(df.status.eq("estimado").sum())
            est=df[df.status.eq("estimado")]
            summaries["K_escolhidos"]=est.K.value_counts().sort_index().to_dict()
            summaries["delta_BIC_menor_zero"]=int(est.delta_BIC.lt(0).sum())
            summaries["RMSE_melhora"]=int(est.melhora_rmse_pct.gt(0).sum())
        if name=="geral" and not df.empty:
            summaries["gerais_estimados"]=int(df.status.eq("estimado").sum())
            summaries["gerais_BIC_melhor"]=int(df.delta_BIC.lt(0).sum())
    summary={**summaries,"amostra_comum_max_lag":MAX_LAG,
             "lag_inicial":MIN_LAG,
             "lags_testados":list(KS),"periodos":list(PERIODS),
             "modelos_individuais_planejados":16*2*28,
             "modelos_gerais_planejados":2*28,
             "base_sha256":HASH,
             "regra":f"BIC treino, blocos [{MIN_LAG}..K] consecutivos, amostra comum 24 meses; rank/condição/graus de liberdade auditados candidato a candidato",
             "nacional":"carteira agregada ponderada por UF, não média simples das taxas",
             "inferência":"valores-p e BH condicionais à escolha de K e ordens; exploratórios, não causalidade",
             "previsao":("um passo condicional, X contemporâneo realizado disponível"
                         if MIN_LAG == 0 else
                         "um passo com X dos meses t-3 e anteriores, potencialmente conhecido antes do mês previsto")}
    (OUT/"resumo.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2,default=str),flush=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--fase",choices=["individuais","gerais","consolidar"],default="individuais")
    ap.add_argument("--periodo",choices=["Pré","Total","ambos"],default="ambos")
    ap.add_argument("--uf",default="todas")
    args=ap.parse_args()
    assert hashlib.sha256(BASE.read_bytes()).hexdigest()==HASH
    if args.fase=="consolidar":return consolidate()
    df=load()
    periods=list(PERIODS) if args.periodo=="ambos" else [args.periodo]
    units=sorted(df.uf.unique())+["Brasil"] if args.uf=="todas" else [args.uf]
    assert set(units)<=set(df.uf.unique())|{"Brasil"}
    for period in periods:
        for unit in units:
            if args.fase=="individuais":individually(df,period,unit)
            else:combined(df,period,unit)


if __name__=="__main__":
    main()
