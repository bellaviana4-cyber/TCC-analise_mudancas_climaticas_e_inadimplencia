"""Validação de integridade e consistência dos resultados SARIMAX."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "outputs/tables/sarimax_final"
P = ROOT / "outputs/tables/segunda_etapa/series_nacionais_agregadas.csv"
HTML = ROOT / "outputs/reports/relatorio_sarimax_final.html"
NB = ROOT / "notebooks/25_sarimax_validacao_final.ipynb"


def ok(condicao, descricao):
    if not condicao:
        raise AssertionError(descricao)
    print("passou:", descricao)


def main():
    d = pd.read_csv(P, encoding="utf-8-sig", parse_dates=["data"])
    ok(len(d) == 144 and d.data.min() == pd.Timestamp("2013-01-01") and
       d.data.max() == pd.Timestamp("2024-12-01"), "calendário completo de 144 meses")
    dados = {}
    for nome in ["baselines", "modelos", "coeficientes", "diagnosticos", "metricas",
                 "previsoes", "sensibilidade", "suporte", "estacionariedade", "candidatos"]:
        dados[nome] = pd.read_csv(T / f"{nome}.csv")
        ok(len(dados[nome]) > 0, "tabela " + nome + " não vazia")
    m = dados["modelos"]
    base = m[(m.periodo == "total") & (m.categoria == "SARIMA")]
    clima = m[(m.periodo == "total") & (m.categoria == "Clima | Protocolos")]
    ok(len(base) == len(clima) == 1, "modelos comparáveis do total climático")
    ok(base.iloc[0]["especificacao"] == clima.iloc[0]["especificacao"],
       "mesma estrutura temporal e calendário no par principal")
    ok(base.iloc[0]["n"] == clima.iloc[0]["n"] == 116,
       "amostra idêntica no treinamento")
    ok(abs(float(clima.iloc[0].delta_bic) -
           (float(clima.iloc[0].bic_treino) - float(base.iloc[0].bic_treino))) < 1e-6,
       "diferença do BIC calculada sobre a mesma base")
    p = dados["previsoes"]
    ok(p["data"].nunique() == 24 and p["data"].min() == "2023-01-01" and
       p["data"].max() == "2024-12-01", "24 meses de avaliação estritamente futura")
    ok(not p[["observado", "previsto"]].isna().any().any(), "previsões completas")
    for _, linha in dados["metricas"].iterrows():
        q = p[p.categoria == linha.categoria]
        erro = q["observado"] - q["previsto"]
        ok(len(q) == 24 and np.isclose(np.abs(erro).mean(), linha.mae) and
           np.isclose(np.sqrt(np.mean(erro ** 2)), linha.rmse),
           "reprodução das métricas para " + str(linha.categoria))
    coef = dados["coeficientes"]
    for periodo, f in coef.groupby("periodo"):
        q = multipletests(f["p"].to_numpy(), method="fdr_bh")[1]
        ok(np.allclose(q, f["q_bh"].to_numpy()),
           "BH recalculado para " + str(periodo))
    support = dados["suporte"]
    ok(not support.duplicated(["periodo", "categoria"]).any(),
       "categorias únicas por período")
    ok(not coef.duplicated(["periodo", "categoria"]).any(),
       "coeficientes únicos por período e categoria")
    ok(coef.p.between(0, 1).all() and coef.q_bh.between(0, 1).all(),
       "valores-p e q no intervalo [0,1]")
    diag = dados["diagnosticos"]
    ok(diag.lb12_ajustado_p.between(0,1).all() and
       diag.lb24_ajustado_p.between(0,1).all(), "diagnósticos válidos")
    ok(len(HTML.read_bytes()) > 100000 and "<nav>" in HTML.read_text(encoding="utf-8"),
       "relatório HTML standalone com menu lateral")
    notebook = json.loads(NB.read_text(encoding="utf-8"))
    ok(notebook.get("nbformat") == 4 and len(notebook["cells"]) >= 6,
       "notebook 25 com estrutura JSON válida")
    resumo = json.loads((T / "resumo.json").read_text(encoding="utf-8"))
    cc = resumo["comparacao"]
    ok(np.isclose(cc["delta_bic"], clima.iloc[0].delta_bic),
       "resumo conciliado com tabelas de estimação")
    manifesto = {
        "entrada_sha256": hashlib.sha256(P.read_bytes()).hexdigest(),
        "codigo_sha256": hashlib.sha256(
            (ROOT / "src/sarimax_validacao_final.py").read_bytes()).hexdigest(),
        "n_meses": int(len(d)), "teste_meses": int(p.data.nunique()),
        "q_bh": "auditado", "resumo": "conciliado",
        "resultado": "etapa reproduzida; limitações inferenciais documentadas",
    }
    (T / "manifest.json").write_text(json.dumps(manifesto,indent=2,ensure_ascii=False),
                                      encoding="utf-8")
    print(json.dumps(manifesto,indent=2,ensure_ascii=False))


if __name__ == "__main__":
    main()
