"""Audita e tenta SARIMAX com TODAS as 16 tipologias simultaneamente.

Não remove, seleciona, preenche artificialmente nem regulariza regressoras.
As quatro especificações consecutivas de lags 0..3 utilizam treino comum;
candidatos não identificáveis são registrados, e não ajustados com matriz
singular. Somente os candidatos identificáveis recebem tentativa de MLE.

Esta execução é complementar ao SARIMAX estadual com subconjuntos elegíveis;
não substitui silenciosamente os resultados anteriores.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox

from analise_estadual import TIPOS, load
from sarimax_revisao_final import MAX_COND, PERIODS, predicted_1step, series_for_unit
from sarimax_com_defasagens import fit_one, lag_design
from sarimax_lags_sistematicos import baseline_for

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/df_tcc_2013_2024.csv"
EXPECTED_HASH = "46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36"
HISTORICAL = ROOT / "outputs/tables/sarimax_defasagens_20261024/candidatos.csv"
OUT = ROOT / "outputs/tables/sarimax_todas_tipologias_20261026"
MAX_LAG = 3
LAG_SETS = {"l0": (0,), "l0_1": (0, 1), "l0_1_2": (0, 1, 2), "l0_1_2_3": (0, 1, 2, 3)}
ALL_TYPES = list(range(16))
RESERVE_TEMPORAL_PARAMETERS = 5


def lb12_arma_inovacoes_padronizadas(fitted):
    """Ljung–Box comparável: inovações padronizadas, df ARMA (não exógenas).

    A API test_serial_correlation(df_adjust=True) desconta todos os parâmetros
    ajustados, incluindo exógenas. Com 16+ coeficientes, a defasagem 12 fica
    sem graus de liberdade e o valor-p é indefinido. Aqui a correção usa
    somente p+q+P+Q, explicitando esse critério no relatório.
    """
    arr = np.asarray(fitted.filter_results.standardized_forecasts_error[0], dtype=float)
    burn = int(fitted.loglikelihood_burn)
    arr = arr[burn:]
    arr = arr[np.isfinite(arr)]
    order = fitted.model.order
    seasonal = fitted.model.seasonal_order
    model_df = int(order[0] + order[2] + seasonal[0] + seasonal[2])
    if len(arr) <= 12 or model_df >= 12:
        return np.nan
    return float(acorr_ljungbox(arr, lags=[12], model_df=model_df,
                              return_df=True).lb_pvalue.iloc[0])


def audit_one(x: np.ndarray, ntrain: int, period: str, uf: str, label: str, lags):
    """Só álgebra e exposições do treino; nunca consulta y nem meses de teste."""
    A = lag_design(x[:ntrain], ALL_TYPES, MAX_LAG, lags)
    n, p = A.shape
    sd = A.std(axis=0)
    constant = np.flatnonzero(sd <= 1e-12)
    varying = np.flatnonzero(sd > 1e-12)
    Z = np.zeros_like(A)
    if len(varying):
        Z[:, varying] = (A[:, varying] - A[:, varying].mean(axis=0)) / sd[varying]
    rank = int(np.linalg.matrix_rank(Z))
    cond = float(np.linalg.cond(Z)) if p <= n and rank == p else np.inf
    no_variation = sorted({TIPOS[int(c // len(lags))] for c in constant})
    names = [f"{TIPOS[j]}_lag{k}" for j in ALL_TYPES for k in lags]
    full_rank = (rank == p) and len(constant) == 0
    degrees_ok = n > p + RESERVE_TEMPORAL_PARAMETERS
    well_conditioned = full_rank and np.isfinite(cond) and cond <= MAX_COND
    estimavel = full_rank and degrees_ok and well_conditioned
    reasons = []
    if constant.size:
        reasons.append(f"{len(constant)} regressor(es) constante(s) no treino")
    if rank < p:
        reasons.append(f"posto {rank} < {p}")
    if not degrees_ok:
        reasons.append(f"amostra {n} insuficiente frente a {p} regressoras + reserva temporal")
    if full_rank and not well_conditioned:
        reasons.append(f"condicionamento {cond:.1f} > {MAX_COND:.0f}")
    result = {
        "periodo": period, "unidade": uf, "bloco": label, "K": max(lags),
        "n_treino_comum": n, "n_teste": PERIODS[period][3],
        "n_tipologias_exigidas": len(ALL_TYPES), "n_exogenas": p,
        "n_regressoras_sem_variacao": len(constant),
        "tipologias_com_algum_lag_sem_variacao": ";".join(no_variation),
        "regressoras_sem_variacao": ";".join(names[c] for c in constant),
        "posto_matriz": rank, "deficiencia_posto": p - rank,
        "numero_condicao": cond if np.isfinite(cond) else np.nan,
        "reserva_parametros_temporais": RESERVE_TEMPORAL_PARAMETERS,
        "estimavel": bool(estimavel),
        "status": "matriz identificável" if estimavel else "não identificável",
        "motivos": "; ".join(reasons),
    }
    return result


def fit_eligible(df, historical, audit: pd.DataFrame):
    models = []
    coefficients = []
    # BIC entre SARIMAX exige amostra comum e que todos os K sejam identificáveis.
    for (period, uf), g in audit.groupby(["periodo", "unidade"], sort=True):
        viable = g.loc[g.estimavel.eq(True)]
        if viable.empty:
            continue
        y, x, D, dates = series_for_unit(df, uf, period)
        ntrain = PERIODS[period][2]
        yy = y[MAX_LAG:]
        n = ntrain - MAX_LAG
        order, seasonal, recorded_bic = baseline_for(historical, period, uf)
        baseline, converged, notes = fit_one(yy[:n], order, seasonal)
        if not converged:
            models.append(dict(periodo=period, unidade=uf, modelo="SARIMA",
                               status="baseline não convergiu"))
            continue
        assert abs(float(baseline.bic) - recorded_bic) < 0.1
        baseline_pred = predicted_1step(baseline, yy, None, n)
        models.append(dict(periodo=period, unidade=uf, modelo="SARIMA",
                           bloco="nenhum", n_exogenas=0,
                           status="estimado", convergiu=True,
                           BIC=float(baseline.bic), AIC=float(baseline.aic),
                           rmse=baseline_pred["rmse"], mae=baseline_pred["mae"],
                           lb12_padronizado=lb12_arma_inovacoes_padronizadas(baseline),
                           ordem=str(order), sazonal=str(seasonal),
                           avisos=" | ".join(notes)))
        for label, lags in LAG_SETS.items():
            if label not in viable.bloco.to_list():
                continue
            A = lag_design(x, ALL_TYPES, MAX_LAG, lags)
            center = A[:n].mean(axis=0)
            scale = A[:n].std(axis=0)
            assert np.all(scale > 0)
            Z = (A - center) / scale
            assert np.linalg.matrix_rank(Z[:n]) == Z.shape[1]
            result = dict(periodo=period, unidade=uf, modelo="SARIMAX",
                          bloco=label, K=max(lags), n_exogenas=Z.shape[1],
                          n_tipologias=16, ordem=str(order), sazonal=str(seasonal))
            print(f"ajustando {period}/{uf} {label} com {Z.shape[1]} exógenas...", flush=True)
            try:
                fitted, ok, notes = fit_one(yy[:n], order, seasonal, Z[:n])
                result.update(BIC=float(fitted.bic), AIC=float(fitted.aic),
                              convergiu=ok, status="estimado" if ok else "não convergiu",
                              lb12_padronizado=lb12_arma_inovacoes_padronizadas(fitted),
                              avisos=" | ".join(notes),
                              delta_BIC=float(fitted.bic-baseline.bic))
                if ok and np.isfinite(fitted.bic):
                    predicted = predicted_1step(fitted, yy, Z, n)
                    result.update(rmse=predicted["rmse"], mae=predicted["mae"],
                                  melhora_rmse_pct=100*(1-predicted["rmse"]/baseline_pred["rmse"]))
                    for j, typ in enumerate(TIPOS):
                        for a, lag in enumerate(lags):
                            idx = j * len(lags) + a
                            param = fitted.param_names.index(f"x{idx+1}")
                            coefficients.append(dict(periodo=period, unidade=uf,
                                                     bloco=label, tipologia=typ, lag=lag,
                                                     coef_original=float(fitted.params[param]/scale[idx]),
                                                     p_condicional=float(fitted.pvalues[param])))
            except Exception as exc:
                result.update(status="falha de estimação", convergiu=False, erro=repr(exc)[:250])
            models.append(result)
            print(f"{period}/{uf} {label}: {result['status']}", flush=True)
            pd.DataFrame(models).to_csv(OUT / "ajustes.csv", index=False, encoding="utf-8-sig")
            pd.DataFrame(coefficients).to_csv(OUT / "coeficientes.csv", index=False,
                                              encoding="utf-8-sig")
    return pd.DataFrame(models), pd.DataFrame(coefficients)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--somente-auditoria", action="store_true",
                        help="Gera auditoria de estimabilidade antes do ajuste numérico.")
    args = parser.parse_args()
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_HASH
    df = load()
    assert len(TIPOS) == 16
    audited = []
    for period in PERIODS:
        for uf in sorted(df.uf.unique()):
            y, x, D, dates = series_for_unit(df, uf, period)
            ntrain = PERIODS[period][2]
            for label, lags in LAG_SETS.items():
                audited.append(audit_one(x, ntrain, period, uf, label, lags))
    a = pd.DataFrame(audited)
    assert len(a) == 27 * 2 * 4
    OUT.mkdir(parents=True, exist_ok=True)
    a.to_csv(OUT / "auditoria.csv", index=False, encoding="utf-8-sig")
    summary = {
        "amostra_sha256": EXPECTED_HASH, "n_tipos_exigidos": len(TIPOS),
        "n_ufs": 27, "n_periodos": 2, "n_casos": 54,
        "n_candidatos": len(a), "n_matrizes_identificaveis": int(a.estimavel.sum()),
        "matrizes_identificaveis_por_K": a.groupby("bloco").estimavel.sum().astype(int).to_dict(),
        "casos_com_todos_os_quatro_blocos_identificaveis": [
            {"periodo":p,"uf":u} for (p,u),g in a.groupby(["periodo","unidade"])
            if g.estimavel.all()],
        "criterio": "16 tipologias sem exclusão; posto completo, condicionamento até 1000, reserva temporal de 5",
        "sem_cap_de_tipologias": True,
        "comparacao": "não confundir impossibilidade algébrica com resultado de BIC",
        "n_treino_comum": {"Pré":69,"Total":116},
    }
    print("auditoria concluída:", summary["matrizes_identificaveis_por_K"], flush=True)
    if not args.somente_auditoria:
        historical = pd.read_csv(HISTORICAL, encoding="utf-8-sig")
        fits, coefs = fit_eligible(df, historical, a)
        valid = fits.loc[fits.modelo.eq("SARIMAX") & fits.convergiu.eq(True)] if not fits.empty else fits
        summary.update(n_sarimax_convergidos=int(len(valid)),
                       bic_sarimax_vence_sarima=int(valid.delta_BIC.lt(0).sum()) if len(valid) else 0,
                       diagnostico_ljung_box="lag 12, inovações padronizadas, df ARMA p+q+P+Q (sem subtrair exógenas)",
                       diagnostico="estatísticas SARIMAX somente para casos estimáveis; não generalizáveis às 54 aplicações")
    (OUT / "resumo.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
