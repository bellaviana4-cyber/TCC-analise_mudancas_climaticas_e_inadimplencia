"""Compara a sensibilidade SARIMAX [3..K] à referência [0..K].

Exige que ambas tenham sido executadas e consolidadas. Produz tabelas
pareadas para os modelos individuais e gerais, sem reestimar parâmetros.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "outputs/tables/sarimax_por_tipologia_k0_24_20261026"
NEW = ROOT / "outputs/tables/sarimax_por_tipologia_k3_24_20261026"
COLS = ["status", "K", "n_exog", "delta_BIC", "bic_sarimax",
        "melhora_rmse_pct", "rmse_sarimax", "p_soma_condicional",
        "q_soma_BH_exploratorio", "lb12_padronizado"]


def compare(name, keys):
    old = pd.read_csv(OLD / f"{name}.csv", encoding="utf-8-sig")
    new = pd.read_csv(NEW / f"{name}.csv", encoding="utf-8-sig")
    allowed = [c for c in COLS if c in old.columns and c in new.columns]
    selected = keys + allowed
    merged = old[selected].merge(new[selected], how="outer", on=keys,
                                 suffixes=("_0aK", "_3aK"), validate="one_to_one")
    merged["ambos_estimaveis"] = (merged.status_0aK.eq("estimado")
                                   & merged.status_3aK.eq("estimado"))
    merged["diferenca_BIC_3_menos_0"] = merged.bic_sarimax_3aK - merged.bic_sarimax_0aK
    merged["diferenca_RMSE_3_menos_0"] = merged.rmse_sarimax_3aK - merged.rmse_sarimax_0aK
    merged["BIC_melhor_3aK"] = merged.ambos_estimaveis & merged.diferenca_BIC_3_menos_0.lt(0)
    merged["RMSE_melhor_3aK"] = merged.ambos_estimaveis & merged.diferenca_RMSE_3_menos_0.lt(0)
    return merged


def main():
    NEW.mkdir(parents=True, exist_ok=True)
    individual = compare("resumo", ["periodo", "unidade", "tipologia"])
    general = compare("geral", ["periodo", "unidade"])
    assert len(individual) == 896 and len(general) == 56
    individual.to_csv(NEW / "comparacao_individuais.csv", index=False, encoding="utf-8-sig")
    general.to_csv(NEW / "comparacao_gerais.csv", index=False, encoding="utf-8-sig")
    sums = {}
    for name,df in (("individuais",individual),("gerais",general)):
        sums[name] = {}
        for period,part in df.groupby("periodo"):
            both = part[part.ambos_estimaveis]
            sums[name][period] = {
                "aplicacoes":int(len(part)),
                "estimaveis_0aK":int(part.status_0aK.eq("estimado").sum()),
                "estimaveis_3aK":int(part.status_3aK.eq("estimado").sum()),
                "estimaveis_em_ambos":int(len(both)),
                "BIC_3aK_melhor_em_pares":int(both.BIC_melhor_3aK.sum()),
                "RMSE_3aK_melhor_em_pares":int(both.RMSE_melhor_3aK.sum()),
                "ambos_criterios_melhores_3aK":int((both.BIC_melhor_3aK & both.RMSE_melhor_3aK).sum()),
                "delta_BIC_mediano_3_menos_0":float(both.diferenca_BIC_3_menos_0.median()) if len(both) else None,
                "delta_RMSE_mediano_3_menos_0":float(both.diferenca_RMSE_3_menos_0.median()) if len(both) else None,
            }
    (NEW / "comparacao_resumo.json").write_text(json.dumps(sums,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(sums,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
