"""Busca sistemática e parcimoniosa de lags climáticos no SARIMAX estadual.

Grade aninhada, sobre uma mesma amostra e um mesmo conjunto de tipologias:
    l0       : X_t
    l0_1     : X_t, X_(t-1)
    l0_1_2   : X_t, X_(t-1), X_(t-2)
    l0_1_2_3 : X_t, X_(t-1), X_(t-2), X_(t-3)

As tipologias são escolhidas por suporte, posto e condicionamento somente no
treinamento do maior bloco. Uma regra explícita de tamanho amostral limita as
exógenas para evitar modelos muito parametrizados.

O SARIMA de referência foi selecionado por BIC numa execução auditada sobre
a mesma amostra comum. Reajustamos essa ordem no treino e validamos seu BIC
antes de comparar os quatro SARIMAX pareados. Nenhum valor de teste é usado
na escolha do modelo. A amostra/base original tem hash verificado.

A grade 0..3 é uma sensibilidade sistemática dentro desse alcance, não uma
seleção ótima irrestrita nem inferência seletiva formal.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2
from statsmodels.stats.multitest import multipletests

from analise_estadual import TIPOS, load
from sarimax_revisao_final import (
    MAX_COND, MAX_EXOG, MIN_MESES_COM_OCORRENCIA, PERIODS,
    predicted_1step, series_for_unit,
)
from sarimax_com_defasagens import fit_one, lag_design

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/processed/df_tcc_2013_2024.csv"
OUT = ROOT / "outputs/tables/sarimax_lags_sistematicos_20261026"
OLD = ROOT / "outputs/tables/sarimax_defasagens_20261024/candidatos.csv"
EXPECTED_HASH = "46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36"
LAGS = {
    "l0": (0,),
    "l0_1": (0, 1),
    "l0_1_2": (0, 1, 2),
    "l0_1_2_3": (0, 1, 2, 3),
}
MAX_LAG = 3
# Ao comparar o maior bloco, reservar >= 4 observações do treino por
# coeficiente climático e mais 5 observações para intercepto/ARMA/variância.
N_POR_PARAMETRO = 4
RESERVA_ARMA = 5


def eligible_types(x, d, ntrain, period):
    """Escolhe subconjunto idêntico para todos os blocos, sem consultar y."""
    n_eff = ntrain - MAX_LAG
    cap_amostral = max(0, (n_eff - RESERVA_ARMA) // (N_POR_PARAMETRO * (MAX_LAG + 1)))
    cap = min(MAX_EXOG[period], cap_amostral)
    counts = (d[MAX_LAG:ntrain] > 0).sum(axis=0)
    priority = sorted(range(len(TIPOS)), key=lambda j: (-counts[j], j))
    included = []
    exclusions = {}
    for j in priority:
        name = TIPOS[j]
        if counts[j] < MIN_MESES_COM_OCORRENCIA:
            exclusions[name] = "menos de 3 meses positivos no treino comum"
            continue
        if len(included) >= cap:
            exclusions[name] = "limite amostral de parâmetros climáticos"
            continue
        trial = included + [j]
        full = lag_design(x[:ntrain], trial, MAX_LAG, LAGS["l0_1_2_3"])
        sd = full.std(axis=0)
        if np.any(sd <= 1e-12):
            exclusions[name] = "algum lag com variação nula"
            continue
        z = (full - full.mean(axis=0)) / sd
        if np.linalg.matrix_rank(z) != z.shape[1]:
            exclusions[name] = "posto incompleto no bloco de 0 a 3"
            continue
        if np.linalg.cond(z) > MAX_COND:
            exclusions[name] = "condicionamento acima de 1000"
            continue
        included.append(j)
    included.sort()
    return included, exclusions, counts, cap


def baseline_for(cached, period, unit):
    """Recupera o menor BIC convergido dos cinco SARIMA auditados."""
    candidates = cached.loc[
        cached.periodo.eq(period) & cached.unidade.eq(unit)
        & cached.modelo.eq("SARIMA")
    ].copy()
    assert len(candidates) == 5, (period, unit, len(candidates))
    valid = candidates.loc[candidates.convergiu.eq(True) & candidates.BIC.notna()]
    assert not valid.empty, (period, unit)
    chosen = valid.sort_values(["BIC", "ordem", "sazonal"], kind="stable").iloc[0]
    return (ast.literal_eval(chosen.ordem),
            ast.literal_eval(chosen.sazonal),
            float(chosen.BIC))


def p_ljungbox_padronizado(fitted):
    """Inovações padronizadas, ajustando graus de liberdade ARMA."""
    try:
        result = fitted.test_serial_correlation(method="ljungbox", df_adjust=True, lags=[12])
        return float(result[0, 1, -1])
    except (ValueError, IndexError):
        return np.nan


def run_one(df, cached, period, unit):
    y, x, disaster_counts, dates = series_for_unit(df, unit, period)
    ntrain = PERIODS[period][2]
    assert dates[ntrain - 1] == PERIODS[period][1]
    indices, excluded, support, cap = eligible_types(x, disaster_counts, ntrain, period)
    yy = y[MAX_LAG:]
    train = ntrain - MAX_LAG
    assert len(yy) - train == PERIODS[period][3]

    order, seasonal, recorded_bic = baseline_for(cached, period, unit)
    baseline, ok, warnings = fit_one(yy[:train], order, seasonal)
    if not ok:
        return (dict(periodo=period, unidade=unit,
                     status="SARIMA de referência não convergiu",
                     n_tipologias_elegiveis=len(indices)), [], [])
    # Mesmo treino, ordem, transformação, versão de pacote e estimação anterior.
    assert abs(float(baseline.bic) - recorded_bic) < 0.1, (
        period, unit, baseline.bic, recorded_bic
    )
    bp = predicted_1step(baseline, yy, None, train)
    selected_types = ";".join(TIPOS[j] for j in indices)
    row = {
        "periodo": period, "unidade": unit, "status": "iniciado",
        "n_treino_comum": train, "n_teste": len(yy) - train,
        "n_tipologias_originais": len(TIPOS),
        "n_tipologias_elegiveis": len(indices),
        "limite_tipologias": cap, "tipologias": selected_types,
        "excluidas": json.dumps(excluded, ensure_ascii=False),
        "ordem": str(order), "sazonal": str(seasonal),
        "bic_sarima": float(baseline.bic),
        "rmse_sarima": bp["rmse"], "mae_sarima": bp["mae"],
        "lb12_padronizado_sarima": p_ljungbox_padronizado(baseline),
        "selecao": "menor BIC no treino; grade aninhada 0 a 3",
    }
    candidates = [{
        "periodo": period, "unidade": unit, "modelo": "SARIMA",
        "lags": "nenhum", "BIC": float(baseline.bic),
        "AIC": float(baseline.aic), "convergiu": True,
        "n_exog": 0, "n_treino": train,
        "ordem": str(order), "sazonal": str(seasonal),
        "lb12_padronizado": p_ljungbox_padronizado(baseline),
        "warnings": " | ".join(warnings),
    }]
    if not indices:
        row["status"] = "nenhuma tipologia elegível"
        return row, candidates, []

    climate_fits = []
    for label, lags in LAGS.items():
        design = lag_design(x, indices, MAX_LAG, lags)
        center = design[:train].mean(axis=0)
        scale = design[:train].std(axis=0)
        assert np.all(scale > 0)
        z = (design - center) / scale
        assert np.linalg.matrix_rank(z[:train]) == z.shape[1]
        candidate = {
            "periodo": period, "unidade": unit, "modelo": "SARIMAX",
            "lags": label, "K": max(lags), "n_exog": int(z.shape[1]),
            "n_tipologias": len(indices), "n_treino": train,
            "cond_exog": float(np.linalg.cond(z[:train])),
            "ordem": str(order), "sazonal": str(seasonal),
        }
        try:
            fitted, converged, notes = fit_one(yy[:train], order, seasonal, z[:train])
            candidate.update(BIC=float(fitted.bic), AIC=float(fitted.aic),
                             convergiu=converged,
                             lb12_padronizado=p_ljungbox_padronizado(fitted),
                             warnings=" | ".join(notes),
                             n_warnings=len(notes))
            if converged and np.isfinite(fitted.bic):
                climate_fits.append((candidate, fitted, z, scale, lags))
        except Exception as exc:
            candidate.update(convergiu=False, erro=repr(exc)[:180])
        candidates.append(candidate)

    if not climate_fits:
        row["status"] = "nenhum SARIMAX convergiu"
        return row, candidates, []

    best, fitted, z, scale, lags = min(
        climate_fits, key=lambda v: (v[0]["BIC"], v[0]["K"])
    )
    pred = predicted_1step(fitted, yy, z, train)
    LR = max(0.0, 2 * (float(fitted.llf) - float(baseline.llf)))
    row.update({
        "status": "estimado", "lag_escolhido": best["lags"],
        "max_defasagem": max(lags), "numero_regressoras": best["n_exog"],
        "bic_sarimax": float(fitted.bic),
        "delta_BIC": float(fitted.bic - baseline.bic),
        "rmse_sarimax": pred["rmse"], "mae_sarimax": pred["mae"],
        "melhora_rmse_pct": 100 * (1 - pred["rmse"] / bp["rmse"]),
        "lb12_padronizado_sarimax": best["lb12_padronizado"],
        "LR_condicional": LR,
        "p_conjunto_condicional": float(chi2.sf(LR, best["n_exog"])),
        "ressalva_inferencia": "testes condicionais à seleção da ordem, tipologias e K",
    })
    coefs = []
    for j, typ in enumerate(indices):
        for lag_idx, lag in enumerate(lags):
            col = j * len(lags) + lag_idx
            parameter = "x" + str(col + 1)
            k = fitted.param_names.index(parameter)
            coefs.append({
                "periodo": period, "unidade": unit, "tipologia": TIPOS[typ],
                "lag": lag, "lag_escolhido": best["lags"],
                "coef_original": float(fitted.params[k] / scale[col]),
                "se_original": float(fitted.bse[k] / scale[col]),
                "p_condicional": float(fitted.pvalues[k]),
            })
    return row, candidates, coefs


def save(models, candidates, coefs):
    OUT.mkdir(parents=True, exist_ok=True)
    a, b, c = pd.DataFrame(models), pd.DataFrame(candidates), pd.DataFrame(coefs)
    if "p_conjunto_condicional" in a:
        a["q_conjunto_BH"] = np.nan
        keep = a.p_conjunto_condicional.notna()
        if keep.any():
            a.loc[keep, "q_conjunto_BH"] = multipletests(
                a.loc[keep, "p_conjunto_condicional"], method="fdr_bh"
            )[1]
    if not c.empty:
        c["q_global_BH"] = multipletests(
            c.p_condicional.fillna(1).clip(0, 1), method="fdr_bh"
        )[1]
    a.to_csv(OUT / "comparacao.csv", index=False, encoding="utf-8-sig")
    b.to_csv(OUT / "candidatos.csv", index=False, encoding="utf-8-sig")
    c.to_csv(OUT / "coeficientes.csv", index=False, encoding="utf-8-sig")
    good = a.loc[a.status.eq("estimado")]
    summary = {
        "aplicacoes": len(a),
        "estimadas": len(good),
        "base_sha256": EXPECTED_HASH,
        "max_lag_testado": MAX_LAG,
        "grade_lags": {k: list(v) for k, v in LAGS.items()},
        "amostra_comum": {"Pré": 69, "Total": 116},
        "limite_parametros": {
            "regra": "4 observacoes de treino por parametro climatico, com reserva de 5 para termos temporais",
            "min_meses_positivos": MIN_MESES_COM_OCORRENCIA,
            "cond_maximo": MAX_COND,
        },
        "ordem_sarima": "menor BIC dos cinco modelos auditados na mesma amostra; refit verificado",
        "selecao_K": "menor BIC de treinamento entre 0,1,2,3, mesma amostra/ordem/tipologias",
        "avaliacao": "um passo condicional com X_t observado, parametros fixos no teste",
        "diagnostico": "Ljung-Box 12 sobre inovacoes padronizadas, graus de liberdade ajustados",
        "inferencia": "exploratoria apos selecao; BH nao corrige selecao adaptativa de K",
        "lags_escolhidos": good.lag_escolhido.value_counts().to_dict() if len(good) else {},
        "melhor_bic_que_sarima": int(good.delta_BIC.lt(0).sum()) if len(good) else 0,
        "melhor_rmse_que_sarima": int(good.melhora_rmse_pct.gt(0).sum()) if len(good) else 0,
        "mediana_melhora_rmse_pct": float(good.melhora_rmse_pct.median()) if len(good) else None,
        "conjuntos_BH_05": int(good.q_conjunto_BH.lt(.05).sum()) if len(good) else 0,
        "lb12_sarimax_rejeita": int(good.lb12_padronizado_sarimax.lt(.05).sum()) if len(good) else 0,
    }
    (OUT / "resumo.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--periodo", choices=["Pré", "Total", "ambos"], default="ambos")
    parser.add_argument("--uf", default="todas")
    parser.add_argument("--refazer", action="store_true",
                        help="Substitui apenas as unidades selecionadas na saída desta revisão.")
    args = parser.parse_args()
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == EXPECTED_HASH
    cached = pd.read_csv(OLD, encoding="utf-8-sig")
    df = load()
    periods = PERIODS if args.periodo == "ambos" else [args.periodo]
    units = sorted(df.uf.unique()) if args.uf == "todas" else [args.uf]
    if args.uf != "todas" and args.uf not in df.uf.unique():
        parser.error("UF desconhecida")
    a_path, b_path, c_path = [OUT / x for x in
                               ("comparacao.csv", "candidatos.csv", "coeficientes.csv")]
    existing = pd.read_csv(a_path).to_dict("records") if a_path.exists() else []
    candidates = pd.read_csv(b_path).to_dict("records") if b_path.exists() else []
    coefs = pd.read_csv(c_path).to_dict("records") if c_path.exists() and c_path.stat().st_size > 3 else []
    for period in periods:
        for unit in units:
            key = (period, unit)
            if any((r["periodo"], r["unidade"]) == key for r in existing):
                if not args.refazer:
                    print(f"mantido {period} {unit}", flush=True)
                    continue
                existing = [r for r in existing if (r["periodo"], r["unidade"]) != key]
                candidates = [r for r in candidates if (r["periodo"], r["unidade"]) != key]
                coefs = [r for r in coefs if (r["periodo"], r["unidade"]) != key]
            row, cand, coef = run_one(df, cached, period, unit)
            existing.append(row)
            candidates.extend(cand)
            coefs.extend(coef)
            save(existing, candidates, coefs)
            print(f"{period} {unit}: {row['status']} | "
                  f"tipologias={row.get('n_tipologias_elegiveis', 0)} | "
                  f"lags={row.get('lag_escolhido')} | "
                  f"delta BIC={row.get('delta_BIC', float('nan')):.2f} | "
                  f"ganho RMSE={row.get('melhora_rmse_pct', float('nan')):.2f}%",
                  flush=True)


if __name__ == "__main__":
    main()
