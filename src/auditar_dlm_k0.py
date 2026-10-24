"""Auditoria da inclusão de K=0 na seleção original por AIC.

Não altera a especificação principal nem fixa um horizonte para o DLM:
somente confronta o candidato contemporâneo (K=0) com o menor AIC
na grade histórica K=1,...,24, mantendo a mesma amostra comum.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/processed/df_tcc_2013_2024.csv"
EXPECTED_HASH = "46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36"
SELECT = ROOT / "outputs/tables/revisao_defasagens_20261024/dlm_dois_menores_aic.csv"
OUT = ROOT / "outputs/tables/revisao_defasagens_20261024/dlm_k0_comparacao_aic.csv"


def demean(a):
    return a - a.mean(axis=0, keepdims=True) - a.mean(axis=1, keepdims=True) + a.mean()


def fit_panel(x: np.ndarray, y: np.ndarray, k: int):
    G, TT = x.shape
    months = np.arange(25, TT)
    T = len(months)
    X = np.stack([x[:, months - lag] for lag in range(k + 1)], axis=2)
    X = (X - X.mean(axis=0, keepdims=True)
           - X.mean(axis=1, keepdims=True)
           + X.mean(axis=(0, 1), keepdims=True)).reshape(G*T, k+1)
    yy = demean(y[:, months]).reshape(G*T)
    if np.linalg.matrix_rank(X) != k+1:
        raise ValueError(f"Matriz singular no horizonte {k}")
    b = np.linalg.lstsq(X, yy, rcond=None)[0]
    e = yy - X @ b
    rss = float(e@e)
    n = len(yy)
    ptotal = G+T-1+(k+1)
    aic = n * (np.log(2*np.pi)+1+np.log(rss/n)) + 2*ptotal
    return dict(X=X, b=b, e=e, rss=rss, aic=float(aic), G=G, T=T, n=n, ptotal=ptotal)


def run() -> pd.DataFrame:
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == EXPECTED_HASH
    selected = pd.read_csv(SELECT, encoding="utf-8-sig")
    df = pd.read_csv(BASE, sep=";", encoding="utf-8-sig").sort_values(["uf", "mes_ano"])
    assert len(df) == 3888 and df.uf.nunique() == 27 and df.mes_ano.nunique() == 144
    df["y"] = df.groupby("uf").taxa_inadimplencia.transform(lambda s: np.log(s).diff())
    records = []
    for period in ("Pré", "Total"):
        d = df[df.mes_ano <= ("2020-01" if period == "Pré" else "2024-12")].copy()
        units = sorted(d.uf.unique())
        y = np.stack([d.loc[d.uf.eq(u), "y"].to_numpy(float) for u in units])
        for sel in selected.loc[selected.periodo.eq(period)].itertuples(index=False):
            d["x"] = d.groupby("uf")[sel.tipologia].transform(lambda s: np.log1p(s).diff())
            x = np.stack([d.loc[d.uf.eq(u), "x"].to_numpy(float) for u in units])
            model = fit_panel(x, y, 0)
            records.append({
                "periodo": period,
                "tipologia": sel.tipologia,
                "K_AIC_original": int(sel.K_menor_AIC),
                "AIC_K0": model["aic"],
                "AIC_K_original": float(sel.AIC_1),
                "delta_AIC_K0_menos_original": model["aic"] - float(sel.AIC_1),
                "K0_seria_preferido": bool(model["aic"] < float(sel.AIC_1)),
            })
    result = pd.DataFrame(records)
    assert len(result) == 29
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT, index=False, encoding="utf-8-sig")
    preferidos = int(result.K0_seria_preferido.sum())
    k1 = int((result.K_AIC_original.eq(1) & result.K0_seria_preferido).sum())
    print(f"K=0 teria menor AIC em {preferidos}/29 casos, incluindo {k1}/21 escolhas originais K=1.")
    return result


if __name__ == "__main__":
    run()
