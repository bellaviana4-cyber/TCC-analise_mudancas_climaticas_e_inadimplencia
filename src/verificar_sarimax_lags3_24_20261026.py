"""Conferências da sensibilidade SARIMAX 3..K versus a análise 0..K."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "outputs/tables/sarimax_por_tipologia_k0_24_20261026"
NEW = ROOT / "outputs/tables/sarimax_por_tipologia_k3_24_20261026"


def read(root, name):
    return pd.read_csv(root / f"{name}.csv", encoding="utf-8-sig")


def main():
    old = read(OLD, "resumo")
    new = read(NEW, "resumo")
    old_gen = read(OLD, "geral")
    gen = read(NEW, "geral")
    candidates = read(NEW, "candidatos")
    coefficients = read(NEW, "coeficientes")
    old_bases = read(OLD, "bases")
    new_bases = read(NEW, "bases")

    assert len(old) == len(new) == 56 * 16 == 896
    assert len(gen) == len(old_gen) == 56
    assert len(candidates) == 56 * 16 * 22 == 19712
    assert set(candidates.K.dropna().astype(int)) == set(range(3, 25))

    modeled = new.loc[new.status.eq("estimado")]
    assert modeled.K.ge(3).all() and modeled.K.le(24).all()
    assert np.all(modeled.n_exog.to_numpy() == modeled.K.to_numpy() - 2)
    assert (coefficients.lag >= 3).all()
    assert (coefficients.lag <= 24).all()
    for item in ("n_exog", "K", "bic_sarimax"):
        assert modeled[item].notna().all()
    protocol = json.loads((NEW / "resumo.json").read_text(encoding="utf-8"))
    assert protocol["lag_inicial"] == 3 and "[3..K]" in protocol["regra"]

    # O baseline e o horizonte amostral permaneceram idênticos ao 0..K.
    keys = ["periodo", "unidade", "ordem", "sazonal"]
    a = old_bases.sort_values(keys).reset_index(drop=True)
    b = new_bases.sort_values(keys).reset_index(drop=True)
    assert len(a) == len(b) == 56 * 5
    assert a[keys].equals(b[keys])
    assert np.allclose(a.BIC, b.BIC, equal_nan=True, atol=1e-5)
    assert np.allclose(a.AIC, b.AIC, equal_nan=True, atol=1e-5)

    matched = old.merge(new, on=["periodo", "unidade", "tipologia"], suffixes=("_0", "_3"), validate="one_to_one")
    assert len(matched) == 896
    assert np.allclose(matched.bic_sarima_0, matched.bic_sarima_3, equal_nan=True, atol=1e-5)
    assert np.allclose(matched.rmse_sarima_0, matched.rmse_sarima_3, equal_nan=True, atol=1e-5)

    report = {
        "modelos_individuais_planejados": len(new),
        "modelos_individuais_estimados": int(len(modeled)),
        "candidatos_lags_3_24": len(candidates),
        "candidatos_estimados": int(candidates.status.eq("estimado").sum()),
        "k_escolhidos": {str(int(k)): int(v) for k, v in modeled.K.value_counts().sort_index().items()},
        "gerais_estimados": int(gen.status.eq("estimado").sum()),
        "gerais_BIC_favoravel": int(gen.delta_BIC.lt(0).sum()),
        "individuais_BIC_favoravel": int(modeled.delta_BIC.lt(0).sum()),
        "individuais_RMSE_favoravel": int(modeled.melhora_rmse_pct.gt(0).sum()),
        "individuais_ambos_favoraveis": int((modeled.delta_BIC.lt(0) & modeled.melhora_rmse_pct.gt(0)).sum()),
        "baseline_equivalente": True,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
