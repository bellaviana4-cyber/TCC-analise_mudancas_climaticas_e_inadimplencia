"""Sensibilidade DLM 90 dias: apenas lags 3..K, K em 3..24.

Preserva integralmente os resultados históricos K=1..24 (lags 0..K).
Estima TWFE UF + mês-ano na mesma amostra comum histórica (24 lags),
com covariância DK por regra, DK6 e DK12. Bonferroni da grade e Holm
por família de exposições são explicitamente exploratórios.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits

from analise_estadual import TIPOS, dm, robust_cov

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/df_tcc_2013_2024.csv"
TAX = ROOT / "outputs/tables/dlm_painel_log_aic/taxonomia.csv"
OLD = ROOT / "outputs/tables/dlm_painel_log_aic/selecao_K.csv"
OUT = ROOT / "outputs/tables/dlm_lags_3a24_20261026"
HASH = "46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36"
K_VALUES = tuple(range(3, 25))
M_JOINT = sum(k - 2 for k in K_VALUES)
PERIODS = {"Pré": "2020-01", "Total": "2024-12"}
BANDS = ("dk_regra", "dk6", "dk12")


def read_panel():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == HASH
    d = pd.read_csv(SOURCE, sep=";", encoding="utf-8-sig")
    d = d.sort_values(["uf", "mes_ano"]).reset_index(drop=True)
    assert len(d) == 3888 and d.uf.nunique() == 27
    tax = pd.read_csv(TAX, encoding="utf-8-sig")
    # Cada tipologia tem classificação climática unívoca na auditoria COBRADE.
    assert tax.groupby("descricao_tipologia").incluido_total_climatico.nunique().max() == 1
    clima = tax.loc[tax.incluido_total_climatico, "descricao_tipologia"].drop_duplicates()
    import unicodedata
    import re
    def slug(s):
        a = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
        return re.sub("[^a-z0-9]+", "_", a).strip("_")
    columns = ["tipo_" + slug(c) for c in clima]
    assert len(columns) == 11 and set(columns) <= set(TIPOS)
    d["total_climatico"] = d[columns].sum(axis=1)
    assert int(d.total_climatico.sum()) == 37643 == int(tax.loc[tax.incluido_total_climatico, "registros"].sum())
    assert int(d[TIPOS].sum().sum()) == int(tax.registros.sum()) == 40339
    exposures = ["total_climatico"] + ["grupo_" + s for s in
                 ("climatologico", "hidrologico", "meteorologico", "outros")] + TIPOS
    assert len(exposures) == 21
    return d, exposures, columns


def support(d, key, months):
    q = d.loc[d.mes_ano.isin(months), ["uf", "mes_ano", key]]
    positive = q[key].gt(0)
    counts = q.groupby("uf")[key].sum().sort_values(ascending=False)
    tot = float(counts.sum())
    props = counts / tot if tot else counts.astype(float)
    return dict(registros=int(tot), uf_mes_positivos=int(positive.sum()),
                ufs_expostas=int(q.loc[positive, "uf"].nunique()),
                meses_expostos=int(q.loc[positive, "mes_ano"].nunique()),
                share_top1=float(props.iloc[0]), share_top2=float(props.iloc[:2].sum()),
                N_eff=float(1 / (props @ props)) if tot else 0,
                elegivel=(tot >= 24 and positive.sum() >= 12 and
                          q.loc[positive, "uf"].nunique() >= 5 and
                          q.loc[positive, "mes_ano"].nunique() >= 8))


def one_fit(y, x, idx, k, G, T):
    lags = list(range(3, k + 1))
    xx = np.stack([x[:, idx - lag] for lag in lags], axis=2)
    X = dm(xx).reshape(G*T, len(lags))
    Y = dm(y[:, idx, None]).reshape(G*T)
    p = X.shape[1]
    rank = int(np.linalg.matrix_rank(X))
    if rank < p:
        return None, "posto incompleto"
    sd = X.std(axis=0)
    if np.any(sd <= 1e-12):
        return None, "variação nula após TWFE"
    cond = float(np.linalg.cond(X / sd))
    if not np.isfinite(cond) or cond >= 1e8:
        return None, "condicionamento extremo"
    beta = np.linalg.lstsq(X, Y, rcond=None)[0]
    resid = Y - X @ beta
    rss = float(resid @ resid)
    n = len(Y)
    ptotal = G+T-1+p
    assert rss > 0 and n > ptotal
    aic = n*(np.log(2*np.pi)+1+np.log(rss/n))+2*ptotal
    bic = n*(np.log(2*np.pi)+1+np.log(rss/n))+np.log(n)*ptotal
    return dict(X=X, Y=Y, beta=beta, resid=resid, n=n, p=p,
                AIC=float(aic), BIC=float(bic), RSS=rss, cond=cond,
                ptotal=ptotal, T=T, G=G), "estimado"


def inference(f, band, lag_ids):
    b = f["beta"]
    V, dof = robust_cov(f["X"], f["resid"], f["p"]-1, f["G"], f["T"], band)
    rows = []
    tests = (("beta3", np.eye(f["p"])[0]), ("soma3K", np.ones(f["p"])))
    for name, c in tests:
        v = float(c @ V @ c)
        se = float(np.sqrt(v)) if v > 0 else np.nan
        est = float(c @ b)
        pval = float(2 * stats.t.sf(abs(est/se), dof)) if se > 0 else np.nan
        rows.append(dict(endpoint=name, estimativa=est, se=se, p=pval,
                         m_selecao=len(K_VALUES),
                         ic_inf=est-stats.t.ppf(.975,dof)*se if se>0 else np.nan,
                         ic_sup=est+stats.t.ppf(.975,dof)*se if se>0 else np.nan))
    for j, lag in enumerate(lag_ids):
        se = np.sqrt(V[j, j]) if V[j, j] > 0 else np.nan
        rows.append(dict(endpoint="coeficiente", lag=lag, estimativa=float(b[j]),
                         se=float(se), p=float(2*stats.t.sf(abs(b[j]/se),dof)) if se>0 else np.nan,
                         m_selecao=M_JOINT))
    candidates = [row["p"] for row in rows if row["endpoint"]=="coeficiente" and np.isfinite(row["p"])]
    rows.append(dict(endpoint="conjunto3K", estimativa=np.nan, se=np.nan,
                     p=float(min(candidates)) if candidates else np.nan,
                     m_selecao=M_JOINT,
                     metodo="união dos testes t entre todos os coeficientes candidatos"))
    return rows


def run():
    d, exposures, climate_types = read_panel()
    UFS = sorted(d.uf.unique())
    original = pd.read_csv(OLD, encoding="utf-8-sig")
    model_rows, candidate_rows, test_rows, coef_rows, support_rows = [], [], [], [], []
    for period, end in PERIODS.items():
        a = d[d.mes_ano <= end]
        dates = sorted(a.mes_ano.unique())
        months = dates[25:]
        TT, G = len(dates), len(UFS)
        idx = np.arange(25, TT)
        T = len(idx)
        y = np.stack([np.log(a.loc[a.uf.eq(u), "taxa_inadimplencia"].to_numpy(float)) for u in UFS])
        y[:, 1:] = np.diff(y, axis=1)
        for key in exposures:
            level = "Central" if key=="total_climatico" else "Grupo" if key.startswith("grupo_") else "Tipologia"
            meta = dict(periodo=period, exposicao=key, nivel=level)
            sup = support(a, key, months)
            support_rows.append({**meta, **sup})
            if not sup["elegivel"]:
                model_rows.append({**meta,"status":"suporte insuficiente"})
                continue
            orig_x = np.stack([a.loc[a.uf.eq(u), key].to_numpy(float) for u in UFS])
            x = np.log1p(orig_x)
            x[:, 1:] = np.diff(x, axis=1)
            fits = {}
            for K in K_VALUES:
                f, status = one_fit(y, x, idx, K, G, T)
                rec = {**meta,"K":K,"status":status,"N":G*T,"T":T}
                if f is not None:
                    fits[K] = f
                    rec.update(AIC=f["AIC"], BIC=f["BIC"], cond=f["cond"],
                               parametros_climaticos=f["p"], RSS=f["RSS"])
                candidate_rows.append(rec)
            if not fits:
                model_rows.append({**meta,"status":"sem candidato identificável"})
                continue
            chosen = min(fits, key=lambda K:(fits[K]["AIC"],K))
            f = fits[chosen]
            ordered = sorted(fits, key=lambda K:(fits[K]["AIC"],K))
            old = original.loc[original.periodo.eq(period)&original.exposicao.eq(key)]
            assert len(old)==1
            model_rows.append({**meta,"status":"estimado", "K":chosen,
                               "AIC":f["AIC"], "BIC":f["BIC"],"K_segundo":ordered[1],
                               "delta_AIC_segundo":fits[ordered[1]]["AIC"]-f["AIC"],
                               "K_antigo":int(old.K.iloc[0]) if pd.notna(old.K.iloc[0]) else np.nan,
                               "N":f["n"],"T":T,"banda_regra":min(T-1,int(np.floor(4*(T/100)**(2/9))))})
            for band in BANDS:
                results = inference(f, band, list(range(3,chosen+1)))
                for result in results:
                    r={**meta,"K":chosen,"banda_DK":band,**result}
                    if r["endpoint"]=="coeficiente":coef_rows.append(r)
                    else:test_rows.append(r)
            print(period,key,"K novo",chosen,"K antigo",old.K.iloc[0],flush=True)
    results=pd.DataFrame(test_rows)
    if not results.empty:
        results["p_selecao"]=(results.p*results.m_selecao).clip(upper=1)
        results["p_holm_familia"]=np.nan
        results["q_bh_familia"]=np.nan
        # Famílias por período / nível / endpoint / banda. Cada tipologia
        # disputou sua seleção K antes de entrar nesta correção.
        for _,group in results.groupby(["periodo","nivel","endpoint","banda_DK"]):
            idxs=group.index
            p=group.p_selecao.fillna(1).to_numpy(float)
            planned = {"Central": 1, "Grupo": 4, "Tipologia": 16}[group.nivel.iloc[0]]
            assert len(p) <= planned
            # Exposições sem suporte ocupam p=1 na família pré-definida.
            complete = np.r_[p, np.ones(planned-len(p))]
            results.loc[idxs,"p_holm_familia"]=multipletests(complete,method="holm")[1][:len(p)]
            results.loc[idxs,"q_bh_familia"]=multipletests(complete,method="fdr_bh")[1][:len(p)]
        results["rejeicao_nominal"]=results.p.lt(.05)
        results["rejeicao_apos_ajustes"]=results.p_holm_familia.lt(.05)
    OUT.mkdir(parents=True,exist_ok=True)
    for name,frame in (("modelos",model_rows),("candidatos",candidate_rows),
                       ("resultados",results),("coeficientes",coef_rows),
                       ("suporte",support_rows)):
        (frame if isinstance(frame,pd.DataFrame) else pd.DataFrame(frame)).to_csv(
            OUT/f"{name}.csv",index=False,encoding="utf-8-sig")
    mm=pd.DataFrame(model_rows)
    valid=mm[mm.status.eq("estimado")]
    summary=dict(base_sha256=HASH,periodos=list(PERIODS),K_candidatos=list(K_VALUES),
                 lags_incluidos="somente [3,..,K] (sem contemporâneo, lag1, lag2)",
                 resultado_historico_preservado=True,
                 reconciliacao_total_climatico=37643,tipologias_climaticas=climate_types,
                 n_aplicacoes=len(mm),estimaveis=len(valid),
                 K_selecionados={str(k):int(v) for k,v in valid.K.value_counts().items()},
                 rejeicoes_por_banda=results.groupby("banda_DK")["rejeicao_apos_ajustes"].sum().astype(int).to_dict(),
                 interpretacao="associação temporal exploratória, não causal; 90 dias de atraso é estoque, não data de início de inadimplência",
                 inferencia="Bonferroni x22 (escalar), união x253 (conjunto); Holm por nível/período/endpoint/banda. Não é inferência seletiva exata.")
    (OUT/"resumo.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    return summary


if __name__=="__main__":
    with threadpool_limits(limits=1):
        print(json.dumps(run(),ensure_ascii=False,indent=2))
