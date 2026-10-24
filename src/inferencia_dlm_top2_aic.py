"""Sensibilidade da inferência DK aos dois menores AICs de cada DLM.

A análise principal continua sendo o K de menor AIC. O segundo K é uma
especificação alternativa próxima, não uma nova hipótese selecionada por p.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t
from statsmodels.stats.multitest import multipletests

from analise_estadual import load, design_panel, robust_cov, wald

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/tables/revisao_defasagens_20261024"
ENDPOINTS = ("beta0", "soma0K", "soma1K", "conjunto0K", "conjunto1K")
BANDS = ("dk_regra", "dk6", "dk12")


def run():
    selections = pd.read_csv(OUT / "dlm_dois_menores_aic.csv", encoding="utf-8-sig")
    orig = pd.read_csv(ROOT / "outputs/tables/revisao_estadual_20261019/dlm_candidatos.csv", encoding="utf-8-sig")
    df = load()
    rows = []
    for (period, tip), choice in selections.groupby(["periodo", "tipologia"]):
        sel = choice.iloc[0]
        d = df[df.mes_ano <= ("2020-01" if period == "Pré" else "2024-12")]
        ufs = sorted(d.uf.unique())
        nmonth = d.mes_ano.nunique()
        x = np.stack([d.loc[d.uf.eq(u), "x_" + tip].to_numpy(float) for u in ufs])
        y = np.stack([d.loc[d.uf.eq(u), "y"].to_numpy(float) for u in ufs])
        for rank, k in [(1, int(sel.K_menor_AIC)), (2, int(sel.K_segundo_AIC))]:
            X, Y, T = design_panel(x, y, k, nmonth, len(ufs))
            assert np.linalg.matrix_rank(X) == X.shape[1]
            beta = np.linalg.lstsq(X, Y, rcond=None)[0]
            resid = Y - X @ beta
            rss = float(resid @ resid)
            ptotal = len(ufs) + T - 1 + k + 1
            aic = len(Y) * (np.log(2*np.pi) + 1 + np.log(rss/len(Y))) + 2*ptotal
            ref = orig.loc[orig.periodo.eq(period) & orig.tipologia.eq(tip) & orig.K.eq(k), "AIC"].iloc[0]
            assert np.isclose(aic, ref, atol=1e-7), (period, tip, k, aic, ref)
            for band in BANDS:
                cov, df_res = robust_cov(X, resid, k, len(ufs), T, band)
                for ep in ENDPOINTS:
                    if ep in ("conjunto0K", "conjunto1K"):
                        # Uma seleção entre K=1..24 torna a distribuição F usual
                        # inadequada como correção simultânea simples. Conforme
                        # o fechamento anterior, testa-se a família de todos os
                        # coeficientes candidatos via min(p) e união de Bonferroni.
                        start = 0 if ep == "conjunto0K" else 1
                        individual = [2 * student_t.sf(abs(beta[j] / np.sqrt(cov[j, j])), df_res)
                                      for j in range(start, k + 1) if cov[j, j] > 0]
                        z = dict(p=float(min(individual)) if individual else np.nan,
                                 status="união dos testes t por coeficiente")
                        m = 324 if ep == "conjunto0K" else 300
                    else:
                        z = wald(beta, cov, df_res, ep)
                        m = 24
                    rows.append(dict(periodo=period, tipologia=tip, posicao_AIC=rank,
                                     K=k, AIC=aic, banda_DK=band, banda_meses=(
                                         int(np.floor(4*(T/100)**(2/9))) if band == "dk_regra" else int(band.removeprefix("dk"))),
                                     endpoint=ep, N=len(Y), m_selecao=m, **z))
    result = pd.DataFrame(rows)
    result["p_selecao"] = (result.p * result.m_selecao).clip(upper=1)
    result["p_holm_familia"] = np.nan
    for keys, group in result.groupby(["periodo", "posicao_AIC", "banda_DK", "endpoint"]):
        p = group.p_selecao.fillna(1).to_numpy(float)
        padded = np.r_[p, np.ones(16 - len(group))]
        result.loc[group.index, "p_holm_familia"] = multipletests(padded, method="holm")[1][:len(group)]
    result["rejeicao_nominal"] = result.p.lt(.05)
    result["rejeicao_apos_ajustes"] = result.p_holm_familia.lt(.05)
    OUT.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT / "dlm_inferencia_top2.csv", index=False, encoding="utf-8-sig")
    groups = result.groupby(["posicao_AIC", "banda_DK"]).agg(
        hipoteses=("p", "count"), nominal=("rejeicao_nominal", "sum"),
        com_ajustes=("rejeicao_apos_ajustes", "sum")).reset_index()
    groups.to_csv(OUT / "resumo_inferencia_top2.csv", index=False, encoding="utf-8-sig")
    (OUT / "metodologia_inferencia_top2.json").write_text(json.dumps({
        "metodo": "painel TWFE em amostra comum; coeficientes MQO; matriz de covariância DK",
        "comparacao": "K melhor e segundo menor AIC da mesma grade K=1..24",
        "multiplicidade": "Bonferroni x24 para contrastes escalares; união com x324 (todos lags) ou x300 (lags 1..K) para conjuntos; Holm por família planejada de 16 tipologias, por período/covariância/endpoint/rank",
        "ressalva": "Correção conservadora por grade; validade requer testes individuais bem calibrados, não corresponde a inferência seletiva exata. Os dois K não constituem dois efeitos independentes.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(groups.to_string(index=False))
    return result


if __name__ == "__main__":
    run()
