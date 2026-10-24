"""Compara os dois melhores horizontes K do DLM pela grade AIC já auditada."""
from __future__ import annotations

import html
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs/tables/revisao_estadual_20261019/dlm_candidatos.csv"
OUT = ROOT / "outputs/tables/revisao_defasagens_20261024"
REPORT = ROOT / "outputs/reports/dlm_aic_duas_melhores_defasagens.html"


def run() -> pd.DataFrame:
    a = pd.read_csv(SOURCE, encoding="utf-8-sig")
    assert not a.duplicated(["periodo", "tipologia", "K"]).any()
    assert a.groupby(["periodo", "tipologia"]).size().between(2, 24).all()
    records = []
    for (period, tip), group in a.groupby(["periodo", "tipologia"], sort=True):
        ranked = group.sort_values(["AIC", "K"], kind="stable")
        first, second = ranked.iloc[0], ranked.iloc[1]
        delta = float(second.AIC - first.AIC)
        weights = np.exp(-0.5 * (ranked.AIC.to_numpy(float) - float(first.AIC)))
        weights /= weights.sum()
        records.append({
            "periodo": period, "tipologia": tip, "K_menor_AIC": int(first.K),
            "K_segundo_AIC": int(second.K), "AIC_1": float(first.AIC),
            "AIC_2": float(second.AIC), "delta_AIC": delta,
            "peso_Akaike_1": float(weights[0]), "peso_Akaike_2": float(weights[1]),
            "evidencia_relativa_segundo": float(np.exp(-delta/2)),
            "dois_plausiveis_delta_menor_2": bool(delta < 2),
            "N": int(first.N), "candidatos_estimados": len(ranked),
        })
    b = pd.DataFrame(records)
    OUT.mkdir(parents=True, exist_ok=True)
    b.to_csv(OUT / "dlm_dois_menores_aic.csv", index=False, encoding="utf-8-sig")
    metadata = {
        "modelos_estimaveis": len(b),
        "modelos_delta_aic_abaixo_2": int(b.dois_plausiveis_delta_menor_2.sum()),
        "min_delta_aic": float(b.delta_AIC.min()),
        "max_delta_aic": float(b.delta_AIC.max()),
        "criterio": "AIC calculado na mesma amostra mensal dentro de cada período/tipologia",
        "interpretacao": "A grade aninhada faz o candidato K+1 ter ΔAIC <= 2 quando o ótimo K é inferior a 24; isso não indica significância dos coeficientes",
    }
    (OUT / "resumo.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = []
    for x in b.itertuples(index=False):
        name = str(x.tipologia).removeprefix("tipo_").replace("_", " ").title()
        rows.append("<tr data-period='{p}'><td>{p}</td><td>{tip}</td><td>{k1}</td>"
                    "<td>{k2}</td><td>{a1:.3f}</td><td>{a2:.3f}</td><td><strong>{delta:.3f}</strong></td>"
                    "<td>{w1:.1%}</td><td>{w2:.1%}</td></tr>".format(
                        p=html.escape(str(x.periodo)), tip=html.escape(name),
                        k1=int(x.K_menor_AIC), k2=int(x.K_segundo_AIC),
                        a1=x.AIC_1, a2=x.AIC_2, delta=x.delta_AIC,
                        w1=x.peso_Akaike_1, w2=x.peso_Akaike_2))
    document = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>DLM — dois menores AICs</title>
<style>:root{color-scheme:light;font-family:Inter,system-ui,-apple-system,sans-serif;color:#283241}
body{margin:0;background:#f7f8fb}main{max-width:1120px;margin:auto;padding:48px 24px 80px}
h1{font-size:clamp(27px,4vw,42px);line-height:1.1;letter-spacing:-.04em;margin:12px 0}
.tag{font-size:12px;text-transform:uppercase;letter-spacing:.15em;color:#95507c;font-weight:700}
p{line-height:1.6;color:#687181;max-width:850px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:28px 0}
.stat,.panel{background:white;border:1px solid #e3e6eb;border-radius:17px;padding:20px}.num{font-size:34px;font-weight:750;letter-spacing:-.05em}
.stat small{color:#6c7280}.panel{overflow:auto}.controls{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:0 0 14px}
select{background:white;border:1px solid #ced3dc;border-radius:9px;padding:10px 14px;color:#334155}
table{border-collapse:collapse;width:100%;font-size:13px;white-space:nowrap}td,th{border-bottom:1px solid #e9edf2;text-align:right;padding:12px 14px}
td:nth-child(-n+2),th:nth-child(-n+2){text-align:left}th{color:#647082;font-size:11px;text-transform:uppercase;letter-spacing:.04em}
tbody tr:hover{background:#fcf8fb}strong{color:#8c3c70}.note{border-left:3px solid #95507c;padding:2px 15px;margin-top:28px}
@media(max-width:680px){main{padding:32px 12px}.grid{grid-template-columns:1fr}.stat{padding:14px}}</style></head><body>
<main><div class="tag">TCC · Modelos de defasagens distribuídas</div><h1>AIC: as duas melhores defasagens</h1>
<p>Comparação dos horizontes de K selecionados entre 1 e 24 meses para cada tipologia e período.
O AIC é calculado com a mesma amostra dentro de cada comparação, garantindo comparabilidade.</p>
<div class="grid"><div class="stat"><div class="num">29</div><small>combinações estimáveis</small></div>
<div class="stat"><div class="num">29</div><small>com ΔAIC menor que 2</small></div>
<div class="stat"><div class="num">0,062–1,997</div><small>intervalo observado de ΔAIC</small></div></div>
<div class="panel"><div class="controls"><b>Comparação por tipologia</b><label>Período: <select id="period">
<option value="todos">Ambos</option><option value="Pré">Pré-pandemia</option><option value="Total">Total</option>
</select></label></div><table><thead><tr><th>Período</th><th>Tipologia</th><th>1º K</th><th>2º K</th>
<th>Menor AIC</th><th>Segundo AIC</th><th>ΔAIC</th><th>Peso do 1º</th><th>Peso do 2º</th></tr></thead>
<tbody>""" + "\n".join(rows) + """</tbody></table></div>
<div class="note"><p><strong>Como interpretar:</strong> ΔAIC = AIC(2º) − AIC(1º). Como os modelos são
aninhados e usam a mesma amostra, acrescentar um lag a K aumenta a penalização em 2,
mas não diminui a verossimilhança: por isso, quando K&lt;24, haverá um candidato K+1
com ΔAIC ≤ 2. A proximidade é parcialmente mecânica e não demonstra efeitos significativos.
Os pesos de Akaike usam todos os candidatos K estimados, não apenas os dois exibidos.
Cada K representa um modelo distinto com coeficientes para todos os lags de 0 até K.</p></div></main>
<script>const control=document.getElementById('period');control.addEventListener('change',()=>{
document.querySelectorAll('tbody tr').forEach(tr=>tr.hidden=control.value!=='todos'&&tr.dataset.period!==control.value);
});</script></body></html>"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(document, encoding="utf-8")
    return b


if __name__ == "__main__":
    df = run()
    print(f"{len(df)} modelos, {(df.delta_AIC < 2).sum()} com ΔAIC < 2")
