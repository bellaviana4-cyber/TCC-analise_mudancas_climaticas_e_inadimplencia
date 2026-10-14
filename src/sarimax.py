"""SARIMAX nacional: séries publicadas, seleção enxuta e avaliação cronológica."""
from pathlib import Path
import base64
import io
import json
import warnings
import html

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import jarque_bera
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller, kpss

ROOT = Path(__file__).resolve().parents[1]
ENTRADA = ROOT / "outputs/tables/segunda_etapa/series_nacionais_agregadas.csv"
TABELAS = ROOT / "outputs/tables/sarimax"
FIGURAS = ROOT / "outputs/figures/sarimax"
RELATORIO = ROOT / "outputs/reports/relatorio_sarimax.html"
TOTAL = "Clima | Protocolos"
TIPOS = [
    "Tipologia | Alagamentos", "Tipologia | Chuvas Intensas",
    "Tipologia | Enxurradas", "Tipologia | Estiagem e Seca",
    "Tipologia | Granizo", "Tipologia | Incêndio Florestal",
    "Tipologia | Inundações", "Tipologia | Onda de Calor e Baixa Umidade",
    "Tipologia | Onda de Frio", "Tipologia | Tornado",
    "Tipologia | Vendavais e Ciclones",
]
ORDENS = [
    ((0, 0, 0), (0, 0, 0, 12)),
    ((1, 0, 0), (0, 0, 0, 12)),
    ((0, 0, 1), (0, 0, 0, 12)),
    ((1, 0, 1), (0, 0, 0, 12)),
    ((2, 0, 0), (0, 0, 0, 12)),
    ((1, 0, 0), (1, 0, 0, 12)),
    ((0, 0, 1), (1, 0, 0, 12)),
]
LAGS = [0, 1, 3]
CORTE_TESTE = pd.Timestamp("2023-01-01")


def salvar(df, nome):
    df.to_csv(TABELAS / (nome + ".csv"), index=False, encoding="utf-8-sig")


def entrada():
    if not ENTRADA.exists():
        raise FileNotFoundError("Série agregada não encontrada: " + str(ENTRADA))
    d = pd.read_csv(ENTRADA, encoding="utf-8-sig", parse_dates=["data"])
    d = d.set_index("data").sort_index()
    calendario = pd.date_range("2013-01-01", "2024-12-01", freq="MS")
    assert d.index.equals(calendario), "Calendário nacional incompleto ou duplicado"
    assert (d["I"] > 0).all(), "Taxa nacional deve ser positiva"
    assert d[["I", TOTAL] + TIPOS].notna().all().all(), "Valores ausentes"
    assert (d[[TOTAL] + TIPOS] >= 0).all().all(), "Contagens negativas"
    assert (d[[TOTAL] + TIPOS].apply(lambda x: x % 1 == 0)).all().all(), "Contagens não inteiras"
    return d


def preparar(d, fim):
    x = d.loc[:fim, ["I", TOTAL] + TIPOS].copy()
    # y é variação percentual logarítmica, não a taxa em pontos percentuais.
    x["y"] = 100 * np.log(x["I"]).diff()
    for j, nome in enumerate([TOTAL] + TIPOS):
        z = np.log1p(x[nome]).diff()
        for lag in LAGS:
            x["x%d_l%d" % (j, lag)] = z.shift(lag)
    # Amostra comum entre todos os lags; também aplicada ao baseline.
    return x.iloc[max(LAGS) + 1:].copy()


def ajustar(y, exog, ordem, sazonal):
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always")
        try:
            m = SARIMAX(y, exog=exog, order=ordem, seasonal_order=sazonal,
                        trend="c", enforce_stationarity=True,
                        enforce_invertibility=True, missing="raise")
            r = m.fit(disp=False, maxiter=150)
            convergiu = bool(r.mle_retvals.get("converged", False))
            aceitavel = convergiu and np.isfinite([r.aic, r.bic]).all()
            return (r if aceitavel else None), ("ok" if aceitavel else "não convergiu")
        except (ValueError, np.linalg.LinAlgError, RuntimeError) as exc:
            return None, type(exc).__name__ + ": " + str(exc)[:90]


def diagnosticar(r, periodo, categoria, amostra):
    residuos = pd.Series(np.asarray(r.resid)).dropna()
    lb = acorr_ljungbox(residuos, lags=[6, 12], return_df=True)
    try:
        arch_p = float(het_arch(residuos, nlags=3)[1])
    except ValueError:
        arch_p = np.nan
    return {
        "periodo": periodo, "categoria": categoria, "amostra": amostra,
        "n": len(residuos), "lb6_p": float(lb.loc[6, "lb_pvalue"]),
        "lb12_p": float(lb.loc[12, "lb_pvalue"]),
        "arch3_p": arch_p, "jarque_bera_p": float(jarque_bera(residuos).pvalue),
        "convergiu": True,
    }


def testes_estacionariedade(s, periodo, variavel):
    r = []
    for nome, z in [("nível", s), ("primeira diferença", s.diff().dropna())]:
        try:
            adf = float(adfuller(z, regression="c", autolag="AIC")[1])
        except ValueError:
            adf = np.nan
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                kp = float(kpss(z, regression="c", nlags="auto")[1])
        except (ValueError, OverflowError):
            kp = np.nan
        r.append(dict(periodo=periodo, variavel=variavel, transformacao=nome,
                      adf_p=adf, kpss_p=kp))
    return r


def prever_um_passo(modelo, treino, teste, coluna):
    x_treino = treino[[coluna]] if coluna else None
    r, status = ajustar(treino["y"], x_treino, modelo[0], modelo[1])
    if r is None:
        return None, status
    linhas = []
    for data, linha in teste.iterrows():
        futuro = pd.DataFrame({coluna: [linha[coluna]]}, index=[data]) if coluna else None
        p = r.get_forecast(steps=1, exog=futuro)
        previsto = float(np.asarray(p.predicted_mean)[0])
        # Atualiza com a informação já observada; coeficientes não são reajustados.
        real = pd.Series([linha["y"]], index=pd.DatetimeIndex([data]), name="y")
        r = r.append(real, exog=futuro, refit=False)
        linhas.append(dict(data=data.date().isoformat(), observado=float(real.iloc[0]),
                           previsto=previsto))
    return pd.DataFrame(linhas), "ok"


def salvar_figura(d, previsoes):
    plt.figure(figsize=(12, 4))
    plt.plot(d.index, d["I"], label="taxa nacional (%)")
    plt.ylabel("Taxa de inadimplência (%)")
    plt.title("Inadimplência nacional — crédito PF")
    plt.grid(alpha=.2)
    plt.tight_layout()
    plt.savefig(FIGURAS / "inadimplencia.png", dpi=145)
    plt.close()
    plt.figure(figsize=(12, 4))
    plt.plot(d.index, d[TOTAL], label="protocolos climáticos")
    plt.ylabel("Registros mensais")
    plt.title("Exposição nacional — COBRADE 12/13/14")
    plt.grid(alpha=.2)
    plt.tight_layout()
    plt.savefig(FIGURAS / "exposicao.png", dpi=145)
    plt.close()
    if len(previsoes):
        f = previsoes[previsoes["categoria"].isin(["SARIMA", TOTAL])]
        plt.figure(figsize=(12, 4))
        for nome, g in f.groupby("categoria"):
            plt.plot(pd.to_datetime(g["data"]), g["previsto"], label=nome)
        real = f.drop_duplicates("data")
        plt.plot(pd.to_datetime(real["data"]), real["observado"], "k--", label="observado")
        plt.title("Previsão de um passo: variação mensal 100×Δlog(I)")
        plt.ylabel("Variação logarítmica mensal ×100")
        plt.legend()
        plt.grid(alpha=.2)
        plt.tight_layout()
        plt.savefig(FIGURAS / "previsao.png", dpi=145)
        plt.close()


def figura_html(nome):
    p = FIGURAS / nome
    if not p.exists():
        return ""
    im = base64.b64encode(p.read_bytes()).decode("ascii")
    return '<img loading="lazy" src="data:image/png;base64,' + im + '" alt="' + html.escape(nome) + '">'


def secao(id_, titulo, texto, conteudo=""):
    return '<section id="' + id_ + '"><h2>' + titulo + '</h2><p>' + texto + '</p>' + conteudo + '</section>'


def tabela(df, colunas=None):
    if df is None or df.empty:
        return "<p>Nenhum resultado disponível nesta etapa.</p>"
    a = df[colunas].copy() if colunas else df.copy()
    return a.round(5).to_html(index=False, escape=True, classes="dados", border=0)


def relatorio(d, candidatos, modelos, coefs, diagnosticos, metricas, previsoes, testes, suporte):
    intro = ("A inadimplência nacional é calculada como 100 × soma da carteira inadimplente / "
             "soma da carteira ativa, conforme auditoria anterior. A entrada é a série nacional "
             "já publicada no repositório. y = 100×Δlog(I); x = Δlog(1+D). As diferenças foram "
             "feitas uma única vez fora do modelo e, portanto, d=D=0. A escolha entre termos "
             "sazonais AR/MA permanece empírica. Não se aplica outra diferenciação interna.")
    blocos = []
    blocos.append(secao("metodo", "Objetivo e metodologia", intro,
        "<p>Comparamos SARIMA sem exógenas e SARIMAX com uma exposição e um lag por vez. "
        "A grade é deliberadamente pequena, a escolha usa BIC no treino e as inferências "
        "após seleção são exploratórias. Selecionar um lag isolado não estima efeito acumulado.</p>"))
    blocos.append(secao("dados", "Séries nacionais",
        "São 144 meses (jan/2013–dez/2024). O total climático usa COBRADE 12/13/14; "
        "categorias por tipologia são publicadas na série agregada. Grupos COBRADE exatos "
        "não podem ser reconstituídos sem os registros brutos, que não estão versionados.",
        figura_html("inadimplencia.png") + figura_html("exposicao.png")))
    blocos.append(secao("estacionariedade", "ADF e KPSS",
        "ADF: hipótese nula de raiz unitária. KPSS: hipótese nula de estacionariedade. "
        "Divergência entre testes não autoriza afirmar estacionariedade.",
        tabela(testes)))
    blocos.append(secao("selecao", "Seleção parcimoniosa",
        "Treino até dez/2022; teste jan/2023–dez/2024. Pré-pandemia até jan/2020. "
        "Mesma amostra dentro de cada período, iniciada em mai/2013 devido às diferenças e ao lag 3. "
        "Modelos selecionados por menor BIC; reportamos também AIC e convergência.",
        tabela(modelos) + "<details><summary>Ver todas as especificações</summary>" +
        tabela(candidatos) + "</details>"))
    blocos.append(secao("suporte", "Suporte das exposições",
        "Triagem descritiva: pelo menos 18 meses positivos no treino e 30 registros. "
        "A baixa frequência impede inferência confiável para as categorias excluídas.",
        tabela(suporte)))
    blocos.append(secao("estimativas", "Estimativas e inferência",
        "Cada coeficiente é a associação condicional entre 100×Δlog(I) e uma unidade de "
        "Δlog(1+D) no lag indicado. Não são pontos percentuais da taxa I nem causalidade. "
        "P-valores usuais e BH não corrigem incerteza da seleção por BIC.",
        tabela(coefs)))
    blocos.append(secao("diagnosticos", "Diagnósticos de resíduos",
        "Ljung–Box verifica autocorrelação; ARCH avalia heterocedasticidade condicional; "
        "Jarque–Bera avalia normalidade. Valores p pequenos sinalizam ressalvas, "
        "sem que a normalidade isoladamente determine a validade do modelo.",
        tabela(diagnosticos)))
    blocos.append(secao("previsao", "Avaliação temporal",
        "Previsões um passo à frente com atualização do estado e parâmetros fixos. "
        "Quando o regressor é contemporâneo, a previsão utiliza o desastre observado "
        "no mesmo mês: é condicional, e não uma previsão operacional ex ante. "
        "MAE/RMSE referem-se a 100×Δlog(I), não à taxa em pontos percentuais.",
        figura_html("previsao.png") + tabela(metricas)))
    principal = modelos[(modelos["periodo"] == "total") & (modelos["categoria"] == TOTAL)]
    base = modelos[(modelos["periodo"] == "total") & (modelos["categoria"] == "SARIMA")]
    txt = ("O BIC dos candidatos é comparável apenas na mesma amostra. "
           "Um BIC menor não prova causalidade nem melhora preditiva. "
           "Uma não rejeição da hipótese nula não comprova ausência de associação. "
           "Sem grupos COBRADE reconstruídos exatamente, a comparação por grupo está pendente "
           "dos registros brutos. Resultados pré-pandemia são exploratórios pelo tamanho da amostra.")
    if not principal.empty and not base.empty:
        diff = float(principal["bic_treino"].iloc[0] - base["bic_treino"].iloc[0])
        txt += " Diferença BIC (total climático − SARIMA) no treino: %.3f." % diff
    blocos.append(secao("conclusao", "Conclusões e limitações", txt,
        "<p>A análise é observacional. O SARIMAX nacional não substitui o painel estadual "
        "dos DLMs: não representa heterogeneidade entre UFs. "
        "A escolha de termos ARMA e regressoras condiciona os erros-padrão. "
        "A classificação Atlas é administrativa e inclui ressalvas de taxonomia.</p>"))
    menu = "".join('<a href="#' + i + '">' + t + "</a>" for i, t in [
        ("metodo", "Metodologia"), ("dados", "Séries"), ("estacionariedade", "ADF/KPSS"),
        ("selecao", "Seleção"), ("suporte", "Suporte"), ("estimativas", "Coeficientes"),
        ("diagnosticos", "Diagnósticos"), ("previsao", "Previsão"),
        ("conclusao", "Conclusão")])
    css = """
    *{box-sizing:border-box}body{margin:0;background:#f7f9fc;color:#18243b;font-family:system-ui,Arial,sans-serif;line-height:1.55}
    nav{position:fixed;inset:0 auto 0 0;width:230px;background:#12213b;padding:34px 20px;overflow:auto}
    nav strong{color:white;display:block;margin-bottom:22px}nav a{display:block;color:#d8e3f3;padding:9px 10px;text-decoration:none;border-radius:6px}
    nav a:hover{background:#314665}main{margin-left:230px}header{padding:90px 8%;background:linear-gradient(135deg,#0d1b2f,#1e4166);color:white;min-height:350px}
    header h1{font-size:3rem;max-width:800px}section{padding:40px 7%;border-bottom:1px solid #d8e0ec;max-width:1300px}
    section h2{color:#183755}section img{width:100%;max-width:1000px;border-radius:12px;margin:12px 0}
    .dados{width:100%;border-collapse:collapse;font-size:.86rem;display:block;overflow:auto}
    .dados th,.dados td{border-bottom:1px solid #d7dee9;padding:8px;text-align:left;white-space:nowrap}
    .dados th{background:#e4ecf4}details{margin-top:25px}summary{cursor:pointer}
    @media(max-width:800px){nav{position:static;width:100%;height:auto;padding:15px}nav a{display:inline-block}main{margin:0}header{padding:35px}header h1{font-size:2rem}}
    """
    pag = ('<!doctype html><html lang="pt-br"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width, initial-scale=1">'
           '<title>SARIMAX | TCC</title><style>' + css + '</style></head><body>'
           '<nav><strong>sarimax • tcc</strong>' + menu + '</nav><main>'
           '<header><p>mudanças climáticas e inadimplência</p>'
           '<h1>SARIMAX: dinâmica temporal e exposição climática</h1>'
           '<p>Brasil | 2013–2024 | análise exploratória</p></header>'
           + "".join(blocos) + '</main></body></html>')
    RELATORIO.write_text(pag, encoding="utf-8")


def main():
    for p in (TABELAS, FIGURAS, RELATORIO.parent):
        p.mkdir(parents=True, exist_ok=True)
    d = entrada()
    nomes = [TOTAL] + TIPOS
    candidatos, escolhidos, coeficientes, diagnosticos = [], [], [], []
    metricas, previsoes, suporte, estacionariedade = [], [], [], []
    for periodo, fim in [("total", "2024-12-01"), ("pré-pandemia", "2020-01-01")]:
        dados = preparar(d, fim)
        treino = dados.loc[:("2022-12-01" if periodo == "total" else fim)]
        teste = dados.loc[CORTE_TESTE:] if periodo == "total" else pd.DataFrame()
        for campo in ["I", TOTAL]:
            z = np.log(d.loc[:fim, campo]) if campo == "I" else np.log1p(d.loc[:fim, campo])
            estacionariedade += testes_estacionariedade(z, periodo, campo)
        base = []
        for ordem, saz in ORDENS[:(7 if periodo == "total" else 5)]:
            r, status = ajustar(treino["y"], None, ordem, saz)
            candidatos.append(dict(periodo=periodo, categoria="SARIMA", lag=np.nan,
                                   ordem=str(ordem), sazonal=str(saz),
                                   bic=float(r.bic) if r is not None else np.nan,
                                   aic=float(r.aic) if r is not None else np.nan,
                                   status=status))
            if r is not None:
                base.append((r.bic, ordem, saz))
        if not base:
            raise RuntimeError("Nenhum modelo de referência convergiu em " + periodo)
        _, ordem, saz = min(base, key=lambda z: z[0])
        r0, _ = ajustar(treino["y"], None, ordem, saz)
        escolhidos.append(dict(periodo=periodo, categoria="SARIMA", lag=np.nan,
                               ordem=str(ordem), sazonal=str(saz), n_treino=len(treino),
                               bic_treino=float(r0.bic), aic_treino=float(r0.aic),
                               delta_bic_vs_baseline=0))
        diagnosticos.append(diagnosticar(r0, periodo, "SARIMA", "treino"))
        if periodo == "total":
            pr, status = prever_um_passo((ordem, saz), treino, teste, None)
            if pr is not None:
                pr["categoria"] = "SARIMA"
                previsoes.extend(pr.to_dict("records"))
                metricas.append(dict(categoria="SARIMA", lag=np.nan,
                                    n_teste=len(pr), mae=float(np.abs(pr.observado-pr.previsto).mean()),
                                    rmse=float(np.sqrt(((pr.observado-pr.previsto)**2).mean())),
                                    tipo="univariada"))
        for j, nome in enumerate(nomes):
            positivos = int((treino[nome] > 0).sum())
            registros = int(treino[nome].sum())
            viavel = positivos >= 18 and registros >= 30
            suporte.append(dict(periodo=periodo, categoria=nome, meses_positivos=positivos,
                                registros=registros, estimavel=viavel))
            if not viavel:
                continue
            tentativas = []
            for lag in LAGS:
                col = "x%d_l%d" % (j, lag)
                r, status = ajustar(treino["y"], treino[[col]], ordem, saz)
                candidatos.append(dict(periodo=periodo, categoria=nome, lag=lag,
                                       ordem=str(ordem), sazonal=str(saz),
                                       bic=float(r.bic) if r is not None else np.nan,
                                       aic=float(r.aic) if r is not None else np.nan,
                                       status=status))
                if r is not None:
                    tentativas.append((r.bic, lag, col))
            if not tentativas:
                continue
            _, lag, col = min(tentativas, key=lambda t: t[0])
            r, _ = ajustar(treino["y"], treino[[col]], ordem, saz)
            escolhidos.append(dict(periodo=periodo, categoria=nome, lag=lag,
                                   ordem=str(ordem), sazonal=str(saz),
                                   n_treino=len(treino), bic_treino=float(r.bic),
                                   aic_treino=float(r.aic),
                                   delta_bic_vs_baseline=float(r.bic-r0.bic)))
            diagnosticos.append(diagnosticar(r, periodo, nome, "treino"))
            # Coeficientes apresentados para a amostra integral, após avaliação OOS.
            completo = dados if periodo == "total" else treino
            rf, status = ajustar(completo["y"], completo[[col]], ordem, saz)
            if rf is not None:
                ci = rf.conf_int().loc[col]
                coeficientes.append(dict(periodo=periodo, categoria=nome, lag=lag,
                                         n=len(completo), beta=float(rf.params[col]),
                                         erro_padrao=float(rf.bse[col]),
                                         ic95_inf=float(ci.iloc[0]), ic95_sup=float(ci.iloc[1]),
                                         p=float(rf.pvalues[col]), bic_treino=float(r.bic)))
                diagnosticos.append(diagnosticar(rf, periodo, nome, "amostra completa"))
            if periodo == "total":
                pr, status = prever_um_passo((ordem, saz), treino, teste, col)
                if pr is not None:
                    pr["categoria"] = nome
                    previsoes.extend(pr.to_dict("records"))
                    metricas.append(dict(categoria=nome, lag=lag, n_teste=len(pr),
                                        mae=float(np.abs(pr.observado-pr.previsto).mean()),
                                        rmse=float(np.sqrt(((pr.observado-pr.previsto)**2).mean())),
                                        tipo=("condicional, D_t observado" if lag == 0
                                              else "lag conhecido no início do mês")))
    candidatos = pd.DataFrame(candidatos)
    escolhidos = pd.DataFrame(escolhidos)
    coeficientes = pd.DataFrame(coeficientes)
    diagnosticos = pd.DataFrame(diagnosticos)
    metricas = pd.DataFrame(metricas)
    previsoes = pd.DataFrame(previsoes)
    suporte = pd.DataFrame(suporte)
    estacionariedade = pd.DataFrame(estacionariedade)
    if not coeficientes.empty:
        coeficientes["q_bh"] = np.nan
        for periodo, indices in coeficientes.groupby("periodo").groups.items():
            coeficientes.loc[indices, "q_bh"] = multipletests(
                coeficientes.loc[indices, "p"].values, method="fdr_bh")[1]
    for nome, frame in [("candidatos", candidatos), ("modelos", escolhidos),
                        ("coeficientes", coeficientes), ("diagnosticos", diagnosticos),
                        ("metricas", metricas), ("previsoes", previsoes),
                        ("suporte", suporte), ("estacionariedade", estacionariedade)]:
        salvar(frame, nome)
    salvar_figura(d, previsoes)
    relatorio(d, candidatos, escolhidos, coeficientes, diagnosticos, metricas,
              previsoes, estacionariedade, suporte)
    resumo = dict(status="concluido", n_meses=144, treino_fim="2022-12-01",
                  teste_inicio="2023-01-01", teste_fim="2024-12-01",
                  modelos=len(escolhidos), exogenas_testadas=len(nomes),
                  ressalva="inferência exploratória condicionada à seleção por BIC")
    (TABELAS / "resumo.json").write_text(json.dumps(resumo, indent=2, ensure_ascii=False),
                                         encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False))
    print(escolhidos.to_string(index=False))
    print(metricas.to_string(index=False))
    print(coeficientes[["periodo", "categoria", "lag", "beta", "p", "q_bh"]].to_string(index=False))


if __name__ == "__main__":
    main()
