"""SARIMA vs SARIMAX sazonal com exposições climáticas defasadas.

Compara três estruturas pré-definidas (t), (t,t-1) e (t,t-1,t-3).
O mesmo recorte temporal, as mesmas tipologias estimáveis e a mesma ordem
SARIMA são usados em cada comparação. A escolha é feita exclusivamente pelo
BIC do treino, nunca pelo RMSE do teste ou pelo valor-p dos coeficientes.

Cada UF/período tem um único SARIMAX multivariado: não são 16 modelos separados.
As 16 tipologias são verificadas; apenas blocos de regressoras com suporte,
posto completo e condicionamento aceitável entram simultaneamente no modelo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.statespace.sarimax import SARIMAX

from analise_estadual import TIPOS, load
from sarimax_revisao_final import MODELS, MAX_COND, MAX_EXOG, MIN_MESES_COM_OCORRENCIA, PERIODS, series_for_unit, predicted_1step

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/tables/sarimax_defasagens_20261024"
EXPECTED_HASH = "46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36"
LAG_SETS = {"l0": (0,), "l0_1": (0, 1), "l0_1_3": (0, 1, 3)}
MAX_LAG = 3


def lag_design(x: np.ndarray, indices: list[int], start: int, lags: tuple[int, ...]) -> np.ndarray:
    """Linhas a partir de `start`, colunas organizadas por tipo e defasagem."""
    if not indices:
        return np.empty((len(x) - start, 0))
    return np.column_stack([x[start - lag:len(x) - lag, j]
                            for j in indices for lag in lags])


def choose_types(x: np.ndarray, d: np.ndarray, ntrain: int, period: str):
    """Audita as 16 tipologias exclusivamente no treino comum a três lags."""
    counts = (d[MAX_LAG:ntrain] > 0).sum(axis=0)
    priority = sorted(range(len(TIPOS)), key=lambda j: (-counts[j], j))
    indices: list[int] = []
    exclusions: dict[str, str] = {}
    for j in priority:
        name = TIPOS[j]
        if counts[j] < MIN_MESES_COM_OCORRENCIA:
            exclusions[name] = "menos de 3 meses de exposição no treino comum"
            continue
        if len(indices) >= MAX_EXOG[period]:
            exclusions[name] = "limite pré-definido de tipologias por modelo"
            continue
        trial = indices + [j]
        # Um conjunto fixo de tipos para os três candidatos: o maior bloco
        # determina a estimabilidade, não o desempenho da resposta y.
        design = lag_design(x[:ntrain], trial, MAX_LAG, LAG_SETS["l0_1_3"])
        dev = design.std(axis=0)
        if np.any(dev < 1e-12):
            exclusions[name] = "regressora constante em alguma defasagem"
            continue
        z = (design - design.mean(axis=0)) / dev
        if np.linalg.matrix_rank(z) != z.shape[1]:
            exclusions[name] = "posto incompleto do bloco de defasagens"
            continue
        if np.linalg.cond(z) > MAX_COND:
            exclusions[name] = "condicionamento elevado do bloco de defasagens"
            continue
        if z.shape[1] + 6 >= z.shape[0]:
            exclusions[name] = "graus de liberdade insuficientes"
            continue
        indices.append(j)
    indices.sort()
    return indices, exclusions, counts


def fit_one(y: np.ndarray, order, seasonal, x: np.ndarray | None = None):
    last = None
    notes: list[str] = []
    for maxiter in (85, 170):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with np.errstate(all="ignore"):
                model = SARIMAX(y, exog=x, order=order, seasonal_order=seasonal,
                                trend="c", enforce_stationarity=True,
                                enforce_invertibility=True)
                last = model.fit(disp=False, method="lbfgs", maxiter=maxiter)
        notes += [f"{w.category.__name__}: {str(w.message)[:110]}" for w in caught]
        if last.mle_retvals.get("converged", False):
            break
    return last, bool(last.mle_retvals.get("converged", False)), sorted(set(notes))


def one_unit(df: pd.DataFrame, period: str, uf: str):
    y, x, d, dates = series_for_unit(df, uf, period)
    ntrain = PERIODS[period][2]
    assert ntrain + PERIODS[period][3] == len(y)
    indices, excluded, support = choose_types(x, d, ntrain, period)
    yy = y[MAX_LAG:]
    train = ntrain - MAX_LAG
    assert dates[ntrain - 1] == PERIODS[period][1]
    row = dict(periodo=period, unidade=uf, n_treino_comum=train,
               n_teste=len(yy) - train, n_tipologias_originais=16,
               n_tipologias_elegiveis=len(indices),
               tipologias=";".join(TIPOS[j] for j in indices),
               excluidas=json.dumps(excluded, ensure_ascii=False),
               rank_original_treino=int(np.linalg.matrix_rank(x[MAX_LAG:ntrain])),
               escolha_lags="BIC treino, grade [0], [0,1], [0,1,3]",
               transformacao_y="100 Delta log inadimplencia",
               transformacao_x="Delta log(1+registros climáticos)")
    candidates = []
    coefficients = []
    # A ordem temporal é escolhida por BIC apenas no mesmo treinamento comum.
    baseline_fits = []
    for order, seasonal in MODELS:
        rec = {"periodo": period, "unidade": uf, "modelo": "SARIMA",
               "lags": "nenhum", "ordem": str(order), "sazonal": str(seasonal),
               "n_exog": 0, "n_treino": train}
        try:
            fitted, ok, notes = fit_one(yy[:train], order, seasonal)
            rec.update(BIC=float(fitted.bic), AIC=float(fitted.aic), convergiu=ok,
                       warnings=" | ".join(notes), n_warnings=len(notes),
                       lb12_p=float(acorr_ljungbox(fitted.resid, lags=[12], return_df=True).lb_pvalue.iloc[0]))
            if ok and np.isfinite(fitted.bic):
                baseline_fits.append((rec, fitted))
        except Exception as exc:
            rec.update(convergiu=False, erro=repr(exc)[:200])
        candidates.append(rec)
    if not baseline_fits:
        row["status"] = "sem SARIMA convergido no treino comum"
        return row, candidates, coefficients
    base_rec, baseline = min(baseline_fits, key=lambda pair: pair[0]["BIC"])
    order, seasonal = baseline.model.order, baseline.model.seasonal_order
    base_pred = predicted_1step(baseline, yy, None, train)
    row.update(ordem=str(order), sazonal=str(seasonal), bic_sarima=float(baseline.bic),
               rmse_sarima=base_pred["rmse"], mae_sarima=base_pred["mae"],
               lb12_sarima=float(base_rec["lb12_p"]))
    if not indices:
        row["status"] = "nenhuma tipologia estimável para todos os lags"
        return row, candidates, coefficients
    climate_fits = []
    for label, lags in LAG_SETS.items():
        matrix = lag_design(x, indices, MAX_LAG, lags)
        center = matrix[:train].mean(axis=0)
        scale = matrix[:train].std(axis=0)
        assert np.all(scale > 0)
        standardized = (matrix - center) / scale
        assert np.linalg.matrix_rank(standardized[:train]) == standardized.shape[1]
        rec = {"periodo": period, "unidade": uf, "modelo": "SARIMAX",
               "lags": label, "n_exog": standardized.shape[1],
               "n_tipologias": len(indices), "n_treino": train,
               "ordem": str(order), "sazonal": str(seasonal),
               "cond_exog": float(np.linalg.cond(standardized[:train]))}
        try:
            fitted, ok, notes = fit_one(yy[:train], order, seasonal, standardized[:train])
            rec.update(BIC=float(fitted.bic), AIC=float(fitted.aic), convergiu=ok,
                       warnings=" | ".join(notes), n_warnings=len(notes),
                       lb12_p=float(acorr_ljungbox(fitted.resid, lags=[12], return_df=True).lb_pvalue.iloc[0]))
            if ok and np.isfinite(fitted.bic):
                climate_fits.append((rec, fitted, standardized, scale, lags))
        except Exception as exc:
            rec.update(convergiu=False, erro=repr(exc)[:200])
        candidates.append(rec)
    if not climate_fits:
        row["status"] = "SARIMAX sem candidato convergido"
        return row, candidates, coefficients
    chosen, fit, matrix, scale, lags = min(climate_fits, key=lambda pair: pair[0]["BIC"])
    pred = predicted_1step(fit, yy, matrix, train)
    likelihood_ratio = max(0., 2 * (fit.llf - baseline.llf))
    row.update(status="estimado", lag_escolhido=chosen["lags"],
               max_defasagem=max(lags), numero_regressoras=chosen["n_exog"],
               bic_sarimax=float(fit.bic), delta_BIC=float(fit.bic - baseline.bic),
               rmse_sarimax=pred["rmse"], mae_sarimax=pred["mae"],
               melhora_rmse_pct=100 * (1 - pred["rmse"] / base_pred["rmse"]),
               lb12_sarimax=float(chosen["lb12_p"]),
               LR_condicional=float(likelihood_ratio),
               p_conjunto_condicional=float(chi2.sf(likelihood_ratio, chosen["n_exog"])),
               selecao_condicional="testes exploratorios apos selecao de BIC")
    for j, tip in enumerate(indices):
        for q, lag in enumerate(lags):
            pos = j * len(lags) + q
            key = "x" + str(pos + 1)
            if key not in fit.param_names:
                raise ValueError(f"Parâmetro {key} ausente em {uf} {period}")
            k = fit.param_names.index(key)
            coefficients.append(dict(periodo=period, unidade=uf, tipologia=TIPOS[tip],
                                     lag=lag, lag_escolhido=chosen["lags"],
                                     coef_original=float(fit.params[k] / scale[pos]),
                                     se_original=float(fit.bse[k] / scale[pos]),
                                     p_condicional=float(fit.pvalues[k])))
    return row, candidates, coefficients


def write_outputs(models, candidates, coefficients):
    OUT.mkdir(parents=True, exist_ok=True)
    a = pd.DataFrame(models)
    b = pd.DataFrame(candidates)
    c = pd.DataFrame(coefficients)
    for frame, name in [(a, "comparacao.csv"), (b, "candidatos.csv"), (c, "coeficientes.csv")]:
        frame.to_csv(OUT / name, index=False, encoding="utf-8-sig")
    if not a.empty and "p_conjunto_condicional" in a:
        p = a.p_conjunto_condicional.dropna()
        a["q_conjunto_BH"] = np.nan
        if len(p):
            a.loc[p.index, "q_conjunto_BH"] = multipletests(p, method="fdr_bh")[1]
        a.to_csv(OUT / "comparacao.csv", index=False, encoding="utf-8-sig")
    if not c.empty:
        c["q_global_BH"] = multipletests(c.p_condicional.fillna(1).clip(0, 1), method="fdr_bh")[1]
        c.to_csv(OUT / "coeficientes.csv", index=False, encoding="utf-8-sig")
    summary = dict(aplicacoes=len(a), estimadas=int(a.status.eq("estimado").sum()),
                   grade_lags={label: list(lags) for label, lags in LAG_SETS.items()},
                   selecao="BIC no treino cronológico em amostra comum; ordens temporais fixadas pelo melhor SARIMA BIC",
                   previsao="um passo condicional, com x contemporânea observada quando lag 0 está presente",
                   inferencia="valores-p exploratórios condicionais à seleção, BH não corrige busca de lags/ordens",
                   base_sha256=EXPECTED_HASH)
    if "lag_escolhido" in a:
        summary["lags_escolhidos"] = a.lag_escolhido.value_counts().to_dict()
        sub = a[a.status.eq("estimado")]
        summary["melhor_bic_que_sarima"] = int(sub.delta_BIC.lt(0).sum())
        summary["melhor_rmse_que_sarima"] = int(sub.melhora_rmse_pct.gt(0).sum())
        summary["mediana_melhora_rmse_pct"] = float(sub.melhora_rmse_pct.median())
        summary["conjuntos_BH_05"] = int(sub.q_conjunto_BH.lt(.05).sum())
    (OUT / "resumo.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--periodo", choices=["Pré", "Total", "ambos"], default="ambos")
    parser.add_argument("--uf", default="todas")
    args = parser.parse_args()
    src = ROOT / "data/processed/df_tcc_2013_2024.csv"
    assert hashlib.sha256(src.read_bytes()).hexdigest() == EXPECTED_HASH
    df = load()
    periods = PERIODS if args.periodo == "ambos" else [args.periodo]
    units = sorted(df.uf.unique()) if args.uf == "todas" else [args.uf]
    if args.uf != "todas" and args.uf not in df.uf.unique():
        parser.error("UF desconhecida")
    existing = {}
    file = OUT / "comparacao.csv"
    if file.exists():
        for rec in pd.read_csv(file).to_dict("records"):
            existing[(rec["periodo"], rec["unidade"])] = rec
    candidates = pd.read_csv(OUT / "candidatos.csv").to_dict("records") if (OUT / "candidatos.csv").exists() else []
    coefficients = pd.read_csv(OUT / "coeficientes.csv").to_dict("records") if (OUT / "coeficientes.csv").exists() else []
    for period in periods:
        for uf in units:
            if (period, uf) in existing:
                print(f"mantido {period} {uf}", flush=True)
                continue
            rec, ca, co = one_unit(df, period, uf)
            existing[(period, uf)] = rec
            candidates.extend(ca)
            coefficients.extend(co)
            write_outputs(list(existing.values()), candidates, coefficients)
            print(f"{period} {uf}: {rec['status']} | lags={rec.get('lag_escolhido')} | "
                  f"ΔBIC={rec.get('delta_BIC', float('nan')):.2f} | "
                  f"ganho RMSE={rec.get('melhora_rmse_pct', float('nan')):.2f}%", flush=True)


if __name__ == "__main__":
    main()
