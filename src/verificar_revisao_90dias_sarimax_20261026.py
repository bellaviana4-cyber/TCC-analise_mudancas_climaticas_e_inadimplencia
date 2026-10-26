"""Validação cruzada das novas saídas DLM e SARIMAX, sem reestimá-las."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analise_estadual import TIPOS
from dlm_lags_3a24_20261026 import read_panel

ROOT=Path(__file__).resolve().parents[1]
DLM=ROOT/"outputs/tables/dlm_lags_3a24_20261026"
SAR=ROOT/"outputs/tables/sarimax_por_tipologia_k0_24_20261026"


def read(folder,name):
    return pd.read_csv(folder/(name+".csv"),encoding="utf-8-sig")


def main():
    df,exposures,clima=read_panel()
    mods=read(DLM,"modelos")
    cand=read(DLM,"candidatos")
    outcomes=read(DLM,"resultados")
    assert len(mods)==42 and len(exposures)==21
    estimated=mods[mods.status=="estimado"]
    assert len(estimated)==39 and len(cand)==39*22
    assert estimated.K.ge(3).all() and estimated.K.le(24).all()
    assert outcomes.endpoint.isin(["beta3","soma3K","conjunto3K"]).all()
    assert len(outcomes)==39*3*3
    assert not outcomes.rejeicao_apos_ajustes.gt(outcomes.rejeicao_nominal).any()
    check=outcomes.groupby("banda_DK").rejeicao_apos_ajustes.sum().to_dict()
    assert check=={"dk_regra":0,"dk6":0,"dk12":2},check
    first=cand.loc[cand.groupby(["periodo","exposicao"]).AIC.idxmin()]
    compared=estimated.merge(first,on=["periodo","exposicao"],suffixes=("","_min"))
    assert np.array_equal(compared.K.to_numpy(int),compared.K_min.to_numpy(int))
    assert np.allclose(compared.AIC,compared.AIC_min,atol=1e-8)
    original=ROOT/"outputs/tables/dlm_painel_log_aic/candidatos_AIC.csv"
    assert original.exists() and len(pd.read_csv(original))>0
    print("DLM: 42 aplicações, 39 estimáveis, 858 candidatos e multiplicidade conferida")

    individual=read(SAR,"resumo")
    allc=read(SAR,"candidatos")
    baseline=read(SAR,"bases")
    gen=read(SAR,"geral")
    assert len(individual)==28*2*16==896,len(individual)
    assert len(allc)==896*25==22400,len(allc)
    assert len(gen)==28*2==56,len(gen)
    assert len(baseline)==56*5==280,len(baseline)
    assert not individual.duplicated(["periodo","unidade","tipologia"]).any()
    assert not allc.duplicated(["periodo","unidade","tipologia","K"]).any()
    assert not gen.duplicated(["periodo","unidade"]).any()
    assert len(set(individual.tipologia))==16 and len(set(individual.unidade))==28
    assert set(allc.K)==set(range(25))
    fitted=individual[individual.status=="estimado"]
    assert fitted.K.ge(0).all() and fitted.K.le(24).all()
    assert np.allclose(fitted.delta_BIC,fitted.bic_sarimax-fitted.bic_sarima,atol=1e-7)
    assert np.allclose(fitted.melhora_rmse_pct,
                       100*(1-fitted.rmse_sarimax/fitted.rmse_sarima),atol=1e-7)
    climate=allc[allc.status=="estimado"]
    best=climate.loc[climate.groupby(["periodo","unidade","tipologia"]).BIC.idxmin()]
    matched=fitted.merge(best,on=["periodo","unidade","tipologia"],suffixes=("","_best"))
    assert len(matched)==len(fitted),(len(matched),len(fitted))
    assert (matched.K==matched.K_best).all()
    assert np.allclose(matched.bic_sarimax,matched.BIC,atol=1e-6)
    assert set(gen.n_tipologias_incluidas.dropna().astype(int)).issubset(set(range(17)))
    if "numero_regressoras" in gen:
        for row in gen[gen.status=="estimado"].itertuples():
            parts=[p for p in str(row.defasagens_incluidas).split(";") if p]
            predicted=int(sum(int(p.rsplit(":",1)[1])+1 for p in parts))
            assert predicted==int(row.numero_regressoras),(row.unidade,row.periodo,predicted,row.numero_regressoras)
            assert len(parts)==int(row.n_tipologias_incluidas)
    checks={"dlm_modelos":len(estimated),"dlm_candidatos":len(cand),
            "dlm_rejeicoes_DK":check,"sarimax_univariados":len(fitted),
            "sarimax_candidatos":len(allc),"sarimax_gerais_estatuto":gen.status.value_counts().to_dict(),
            "sarimax_BIC_vence":int(fitted.delta_BIC.lt(0).sum()),
            "sarimax_RMSE_melhora":int(fitted.melhora_rmse_pct.gt(0).sum())}
    print("Validação final:\n"+json.dumps(checks,ensure_ascii=False,indent=2))
    return checks


if __name__=="__main__":main()
