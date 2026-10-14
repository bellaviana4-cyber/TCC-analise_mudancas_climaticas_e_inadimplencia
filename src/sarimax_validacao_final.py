"""Validação final SARIMA × SARIMAX, sem seleção pelo período de teste.

Painel DLM e análise nacional são etapas distintas. Este arquivo utiliza apenas
a série Brasil×mês já auditada e publicamente versionada no repositório.
"""
from pathlib import Path
import base64
import html
import json
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import jarque_bera
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.statespace.sarimax import SARIMAX

from sarimax import entrada, preparar, testes_estacionariedade, TOTAL, TIPOS, LAGS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/tables/sarimax_final"
FIG = ROOT / "outputs/figures/sarimax_final"
HTML = ROOT / "outputs/reports/relatorio_sarimax_final.html"
TREINO_FIM = "2022-12-01"

# Duas especificações simples examinadas após a ACF residual dos ensaios
# anteriores: autocorrelações em lags 3 e 6. São candidatas, não testes causais.
CANDIDATOS = {
    "total": [
        {"nome": "anual_esparso", "ordem": ([1, 3, 6], 0, 0),
         "sazonal": (1, 0, 0, 12), "det": []},
        {"nome": "semestral_fourier", "ordem": (1, 0, 0),
         "sazonal": (1, 0, 0, 6), "det": ["sin_ano", "cos_ano"]},
    ],
    "pré-pandemia": [
        {"nome": "esparso_1_6", "ordem": ([1, 6], 0, 0),
         "sazonal": (0, 0, 0, 12), "det": []},
        {"nome": "semianual_ar", "ordem": (1, 0, 0),
         "sazonal": (1, 0, 0, 6), "det": []},
    ],
}


def salvar(df, nome):
    df.to_csv(OUT / f"{nome}.csv", index=False, encoding="utf-8-sig")


def construir(d, fim):
    df = preparar(d, fim)
    mes = df.index.month - 1
    df["sin_ano"] = np.sin(2 * np.pi * mes / 12)
    df["cos_ano"] = np.cos(2 * np.pi * mes / 12)
    return df


def estimar(df, spec, campos=()):
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        try:
            m = SARIMAX(df["y"], exog=df[list(campos)] if campos else None,
                        order=spec["ordem"], seasonal_order=spec["sazonal"],
                        trend="c", enforce_stationarity=True,
                        enforce_invertibility=True, missing="raise")
            r = m.fit(disp=False, maxiter=200)
            if not r.mle_retvals.get("converged", False):
                return None
            if not np.isfinite([r.llf, r.aic, r.bic, r.params["sigma2"]]).all():
                return None
            if r.params["sigma2"] < 1e-8:
                return None
            return r
        except (ValueError, RuntimeError, np.linalg.LinAlgError):
            return None


def diagnosticos(r):
    # Inovações padronizadas do filtro de Kalman; ajuste de graus de liberdade
    # para os coeficientes AR e MA regulares ou sazonais estimados.
    u = pd.Series(np.asarray(r.filter_results.standardized_forecasts_error[0])).dropna()
    nomes = [str(i) for i in r.param_names]
    n_arma = sum(nome.startswith(("ar.", "ma.")) for nome in nomes)
    lb = acorr_ljungbox(u, lags=[12, 24], model_df=n_arma, return_df=True)
    lb6 = acorr_ljungbox(u, lags=[6], return_df=True)
    try:
        arch = float(het_arch(u, nlags=3)[1])
    except (ValueError, np.linalg.LinAlgError):
        arch = np.nan
    return {
        "n": len(u), "n_param_ar_ma": n_arma,
        "lb6_sem_ajuste_p": float(lb6.iloc[0]["lb_pvalue"]),
        "lb12_ajustado_p": float(lb.loc[12, "lb_pvalue"]),
        "lb24_ajustado_p": float(lb.loc[24, "lb_pvalue"]),
        "arch3_p": arch,
        "jarque_bera_p": float(jarque_bera(u).pvalue),
        "residuos_ok": bool(float(lb.loc[12, "lb_pvalue"]) >= .05 and
                             float(lb.loc[24, "lb_pvalue"]) >= .05),
    }


def selecionar_lag(treino, spec, nome, j, period):
    # Sem otimizar a parte ARMA novamente: as mesmas ordens e controles
    # determinísticos em todos os candidatos, isolando o ganho climático.
    tentativas = []
    registros = []
    for lag in LAGS:
        coluna = f"x{j}_l{lag}"
        cols = spec["det"] + [coluna]
        r = estimar(treino, spec, cols)
        if r is None:
            registros.append(dict(periodo=period, categoria=nome, lag=lag,
                                  status="não convergiu"))
            continue
        dg = diagnosticos(r)
        registros.append(dict(periodo=period, categoria=nome, lag=lag, status="ok",
                              bic=r.bic, aic=r.aic, **dg))
        tentativas.append((float(r.bic), lag, coluna, dg["residuos_ok"]))
    if not tentativas:
        return None, registros
    elegiveis = [z for z in tentativas if z[3]]
    return min(elegiveis or tentativas, key=lambda z: z[0]), registros


def prever_um_passo(treino, teste, spec, cols):
    ajuste = estimar(treino, spec, cols)
    if ajuste is None:
        return None
    result = []
    for instante, linha in teste.iterrows():
        futuro = teste.loc[[instante], list(cols)] if cols else None
        valor = float(np.asarray(ajuste.get_forecast(steps=1, exog=futuro).predicted_mean)[0])
        observado = float(linha["y"])
        novo = pd.Series([observado], index=pd.DatetimeIndex([instante]), name="y")
        ajuste = ajuste.append(novo, exog=futuro, refit=False)
        result.append(dict(data=instante.date().isoformat(),
                           observado=observado, previsto=valor))
    return pd.DataFrame(result)


def avaliar(nome, periodo, pr, lag=None):
    erro = pr["observado"] - pr["previsto"]
    return dict(periodo=periodo, categoria=nome, lag=lag, n_teste=len(pr),
                mae=float(erro.abs().mean()), rmse=float(np.sqrt((erro ** 2).mean())),
                viez=float(erro.mean()),
                tipo_previsao="condicional a D_t observado" if lag == 0 else
                ("histórico climático defasado" if lag is not None else "sem clima"))


def criar_figuras(serie, modelo, treino, previsoes):
    plt.figure(figsize=(12, 4))
    plt.plot(serie.index, serie["I"], lw=1.8)
    plt.ylabel("Taxa de inadimplência (%)")
    plt.title("Brasil — inadimplência de pessoas físicas, 2013–2024")
    plt.tight_layout()
    plt.savefig(FIG / "inadimplencia.png", dpi=150)
    plt.close()

    plt.figure(figsize=(12, 4))
    plt.plot(serie.index, serie[TOTAL], lw=1.6)
    plt.ylabel("Protocolos climáticos")
    plt.title("Atlas — exposições naturais COBRADE 12, 13 e 14")
    plt.tight_layout()
    plt.savefig(FIG / "exposicao.png", dpi=150)
    plt.close()

    u = np.asarray(modelo.filter_results.standardized_forecasts_error[0])
    fig, ax = plt.subplots(2, 1, figsize=(12, 6), layout="constrained")
    ax[0].plot(treino.index, u, lw=1)
    ax[0].axhline(0, lw=0.8, color="#333333")
    ax[0].set_title("Inovações padronizadas — modelo sem desastres")
    plot_acf(u, lags=24, ax=ax[1])
    ax[1].set_title("ACF das inovações (até 24 meses)")
    fig.savefig(FIG / "diagnosticos.png", dpi=150)
    plt.close(fig)

    f = previsoes[previsoes["categoria"].isin(["SARIMA", TOTAL])]
    plt.figure(figsize=(12, 4))
    real = f.drop_duplicates("data")
    plt.plot(pd.to_datetime(real.data), real.observado, "k--", label="Observado", lw=1.8)
    for nome, g in f.groupby("categoria"):
        plt.plot(pd.to_datetime(g.data), g.previsto, label=nome)
    plt.ylabel("100 × Δlog(I)")
    plt.title("Previsões de um mês à frente — teste 2023–2024")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG / "previsoes.png", dpi=150)
    plt.close()


def img(nome):
    dados = base64.b64encode((FIG / nome).read_bytes()).decode("ascii")
    return '<img src="data:image/png;base64,' + dados + '" alt="' + html.escape(nome) + '">'


def tabela_html(df, colunas=None):
    if df.empty:
        return "<p>Sem resultados estimáveis.</p>"
    d = df[colunas].copy() if colunas else df.copy()
    for col in d.select_dtypes(include="number").columns:
        d[col] = d[col].round(4)
    return d.to_html(index=False, classes="dados", border=0, escape=True)


def relatorio(serie, baselines, modelos, coefs, diagn, metricas, estac, suporte,
              previsoes, candidatos, sensibilidade, resumo):
    sections = []
    def sec(slug, titulo, texto, elemento=""):
        sections.append(f'<section id="{slug}"><h2>{titulo}</h2><p>{texto}</p>{elemento}</section>')
    sec("visao", "Objetivo e desenho",
        "A pergunta é se os desastres climáticos acrescentam informação à variação mensal da inadimplência brasileira "
        "além de sua dinâmica própria. Comparação por BIC e previsões um mês à frente: SARIMA sem clima "
        "versus SARIMAX com o mesmo componente autorregressivo e um regressor climático por vez. "
        "Amostra: Brasil, janeiro de 2013 a dezembro de 2024. A avaliação é observacional.",
        img("inadimplencia.png") + img("exposicao.png"))
    sec("preparo", "Dados e estacionariedade",
        "Taxa nacional I=100×Σ carteira inadimplente/Σ carteira ativa. "
        "Resposta y=100×Δlog(I). Exposição x=Δlog(1+D). Diferenciação externa uma vez, "
        "d=D=0 dentro de SARIMAX. ADF testa raiz unitária; KPSS testa estacionariedade. "
        "No pré-pandemia a conclusão para y é inconclusiva.",
        tabela_html(estac))
    sec("selecao", "Escolha parcimoniosa e diagnóstico",
        "A autocorrelação nos lags 3 e 6 dos ensaios anteriores motivou duas estruturas simples adicionais. "
        "A seleção entre candidatas foi feita só no treino, considerando BIC e Ljung–Box ajustado "
        "pelas ordens ARMA (lags 12 e 24). A alternativa anual esparsa preserva s=12; "
        "a alternativa semestral usa componente s=6 e harmônicos anuais previsíveis. "
        "O cenário sem clima escolhido é mantido ao adicionar um desastre, comparando "
        "o ganho incremental de forma consistente. Não foram escolhidos parâmetros com dados do teste.",
        tabela_html(baselines) +
        "<details><summary>Triagem dos modelos de referência</summary>" + tabela_html(candidatos) + "</details>")
    sec("modelos", "SARIMA versus SARIMAX",
        "Os modelos com desastres usam uma exposição e um lag (0, 1 ou 3 meses), escolhidos no treino pelo BIC "
        "entre candidatos com resíduo adequado, quando disponíveis. A coluna ΔBIC é a diferença em relação "
        "à referência sem clima no mesmo período. ΔBIC negativo favorece a inclusão do desastre; "
        "valor positivo favorece o modelo sem clima.",
        tabela_html(modelos))
    sec("coef", "Coeficientes e multiplicidade",
        "Coeficientes na escala de 100×Δlog(I) por unidade de Δlog(1+D), "
        "com intervalos de confiança de 95%. Não correspondem a pontos percentuais da taxa nem à causalidade. "
        "BH separa as famílias de hipóteses do período completo e do pré-pandemia; "
        "p e q permanecem condicionais à especificação escolhida. "
        "Resultados dos coeficientes são do reajuste sobre toda a janela, após a avaliação temporal.",
        tabela_html(coefs))
    sec("residuos", "Diagnósticos dos resíduos",
        "Ljung–Box corrigido pelo número de parâmetros ARMA em 12 e 24 meses; "
        "Ljung–Box descritivo sem ajuste em 6 meses; ARCH(3) e Jarque–Bera. "
        "Não rejeitar Ljung–Box não prova independência, mas deixa de indicar dependência "
        "linear residual nos horizontes testados. Não usar q BH como correção pós-seleção.",
        tabela_html(diagn) + img("diagnosticos.png"))
    sec("teste", "Comparação preditiva 2023–2024",
        "Jan/2023–dez/2024 é um teste cronológico não usado na escolha de especificações. "
        "24 previsões um mês à frente, estado atualizado com a observação anterior e coeficientes fixos. "
        "O erro é medido em 100×Δlog(I). Exposições de lag zero representam cenários "
        "condicionados aos desastres observados no mês previsto (não operacional).",
        img("previsoes.png") + tabela_html(metricas))
    sec("sensibilidade", "Sensibilidade e suporte",
        "A alternativa teórica anual (s=12 com lags AR 1,3,6) e a estrutura semestral com "
        "sazonalidade determinística anual são comparadas separadamente no total climático. "
        "O suporte de tipologias raras foi auditado no treino; "
        "grupos exatos COBRADE não podem ser reconstruídos a partir da tabela já agregada.",
        tabela_html(sensibilidade) + tabela_html(suporte))
    ganho = resumo["comparacao"]
    texto = ("Modelo sem clima: BIC %.3f, MAE %.3f, RMSE %.3f. "
             "Com total climático: BIC %.3f, MAE %.3f, RMSE %.3f. "
             "ΔBIC=%.3f; ΔMAE=%.3f; ΔRMSE=%.3f. "
             "Pela métrica RMSE, %s. Pela métrica BIC, %s. "
             "As diferenças são descritivas; não constituem prova de causalidade, "
             "nem melhora preditiva estatisticamente comprovada em 24 meses." %
             (ganho["bic_sem"], ganho["mae_sem"], ganho["rmse_sem"],
              ganho["bic_com"], ganho["mae_com"], ganho["rmse_com"],
              ganho["delta_bic"], ganho["delta_mae"], ganho["delta_rmse"],
              ("SARIMAX foi menor" if ganho["delta_rmse"] < 0 else "SARIMA foi menor"),
              ("SARIMAX foi preferido" if ganho["delta_bic"] < 0 else "SARIMA foi preferido")))
    sec("conclusao", "Conclusão comparativa", texto,
        "<p>Interpretação restrita a associação temporal e previsão condicional. "
        "A agregação nacional não equivale ao painel com efeitos fixos das 27 UFs. "
        "O período pré-pandemia tem amostra reduzida e ADF/KPSS divergentes; "
        "modelos dinâmicos não permitem identificar causalidade de desastres.</p>")
    nav = "".join(f'<a href="#{id}">{title}</a>' for id,title in [
        ("visao","Visão geral"),("preparo","Estacionariedade"),("selecao","Seleção"),
        ("modelos","Modelos"),("coef","Coeficientes"),("residuos","Resíduos"),
        ("teste","Previsões"),("sensibilidade","Sensibilidade"),("conclusao","Conclusão")])
    css = """
    *{box-sizing:border-box}body{margin:0;background:#f7f9fc;color:#1d3048;font:15px/1.65 system-ui,Arial}
    nav{position:fixed;inset:0 auto 0 0;width:235px;background:#0f223e;color:white;padding:28px 20px;overflow-y:auto}
    nav strong{display:block;font-size:1.3rem;margin-bottom:25px}
    nav a{display:block;color:#dbe6f4;text-decoration:none;padding:8px 12px;border-radius:6px}
    nav a:hover{background:#264563}main{margin-left:235px}header{min-height:440px;padding:110px 8%;color:white;background:linear-gradient(120deg,#0f2038,#24466e)}
    header h1{font-size:3rem;max-width:790px;line-height:1.16}header p{max-width:700px}
    section{padding:45px 7%;border-bottom:1px solid #dce4ec;max-width:1450px}section h2{font-size:1.65rem}
    section p{max-width:880px}img{max-width:100%;width:1060px;border-radius:8px;margin:18px 0}
    table{border-collapse:collapse;font-size:.85rem;width:100%;display:block;overflow-x:auto}
    th,td{white-space:nowrap;padding:8px 10px;text-align:left;border-bottom:1px solid #dfe4ef}
    th{background:#e9f0f7;color:#193754}details{margin:22px 0}summary{cursor:pointer}
    @media(max-width:800px){nav{position:static;width:100%}nav a{display:inline-block}main{margin:0}header{padding:50px 7%}header h1{font-size:2rem}}
    """
    doc = ('<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
           '<title>Modelagem SARIMAX — TCC</title><style>'+css+'</style></head><body>'
           '<nav><strong>sarimax • tcc</strong>'+nav+'</nav><main>'
           '<header><p>tcc | mudanças climáticas e inadimplência</p>'
           '<h1>Dinâmica temporal e desastres climáticos</h1>'
           '<p>SARIMA × SARIMAX • Brasil, 2013–2024 • análise exploratória validada</p></header>'
           + "".join(sections) + '</main></body></html>')
    HTML.write_text(doc, encoding="utf-8")


def main():
    for dir_ in [OUT, FIG, HTML.parent]:
        dir_.mkdir(parents=True, exist_ok=True)
    d = entrada()
    modelos, coeficientes, diag_rows, metricas, previsoes = [], [], [], [], []
    baselines, candidatos, suporte, estac, sensibilidade = [], [], [], [], []
    selecionado_total = None
    fit_total = treino_total = None
    for periodo, fim in [("total", "2024-12-01"), ("pré-pandemia", "2020-01-01")]:
        dados = construir(d, fim)
        treino = dados.loc[:TREINO_FIM] if periodo == "total" else dados
        teste = dados.loc["2023-01-01":] if periodo == "total" else dados.iloc[0:0]
        for campo in ["I", TOTAL]:
            s = np.log(d.loc[:fim, campo]) if campo == "I" else np.log1p(d.loc[:fim, campo])
            estac += testes_estacionariedade(s, periodo, campo)
        bases = []
        for spec in CANDIDATOS[periodo]:
            r = estimar(treino, spec, spec["det"])
            if r is None:
                candidatos.append(dict(periodo=periodo, especificacao=spec["nome"],
                                       status="não convergiu"))
                continue
            dg = diagnosticos(r)
            candidatos.append(dict(periodo=periodo, especificacao=spec["nome"],
                                   ordem=str(spec["ordem"]), sazonal=str(spec["sazonal"]),
                                   controles="+".join(spec["det"]) or "nenhum",
                                   bic=float(r.bic), aic=float(r.aic), status="ok", **dg))
            bases.append((r.bic, spec, dg["residuos_ok"]))
        if not bases:
            raise RuntimeError("Nenhum modelo base convergiu: " + periodo)
        bons = [z for z in bases if z[2]]
        bic, spec, passou = min(bons or bases, key=lambda z: z[0])
        r0 = estimar(treino, spec, spec["det"])
        dg0 = diagnosticos(r0)
        baselines.append(dict(periodo=periodo, especificacao=spec["nome"],
                              ordem=str(spec["ordem"]), sazonal=str(spec["sazonal"]),
                              controles="+".join(spec["det"]) or "nenhum",
                              n_treino=len(treino), bic=float(r0.bic), aic=float(r0.aic),
                              **dg0))
        modelos.append(dict(periodo=periodo,categoria="SARIMA",lag=np.nan,
                            especificacao=spec["nome"],bic_treino=float(r0.bic),
                            aic_treino=float(r0.aic),delta_bic=0.,**dg0))
        diag_rows.append(dict(periodo=periodo,categoria="SARIMA",amostra="treino",**dg0))
        if periodo == "total":
            selecionado_total = spec
            fit_total, treino_total = r0, treino
            pr = prever_um_passo(treino,teste,spec,spec["det"])
            assert pr is not None
            pr["categoria"] = "SARIMA"
            previsoes.extend(pr.to_dict("records"))
            metricas.append(avaliar("SARIMA", periodo, pr))
        for j, nome in enumerate([TOTAL]+TIPOS):
            positivos=int((treino[nome]>0).sum())
            registros=int(treino[nome].sum())
            viavel=positivos>=18 and registros>=30
            suporte.append(dict(periodo=periodo,categoria=nome,
                                meses_positivos=positivos,registros=registros,estimavel=viavel))
            if not viavel:
                continue
            melhor, tentativas=selecionar_lag(treino,spec,nome,j,periodo)
            if melhor is None:
                continue
            _,lag,col,ok=melhor
            rr=estimar(treino,spec,spec["det"]+[col])
            dg=diagnosticos(rr)
            modelos.append(dict(periodo=periodo,categoria=nome,lag=lag,
                                especificacao=spec["nome"],
                                bic_treino=float(rr.bic),aic_treino=float(rr.aic),
                                delta_bic=float(rr.bic-r0.bic),**dg))
            diag_rows.append(dict(periodo=periodo,categoria=nome,amostra="treino",**dg))
            dados_finais=dados if periodo=="total" else treino
            rf=estimar(dados_finais,spec,spec["det"]+[col])
            if rf is not None:
                ci=rf.conf_int().loc[col]
                coeficientes.append(dict(periodo=periodo,categoria=nome,lag=lag,
                               n=len(dados_finais),beta=float(rf.params[col]),
                               erro_padrao=float(rf.bse[col]),
                               ic95_inf=float(ci.iloc[0]),ic95_sup=float(ci.iloc[1]),
                               p=float(rf.pvalues[col]),residuos_ok_treino=bool(ok)))
                diag_rows.append(dict(periodo=periodo,categoria=nome,amostra="completa",
                                      **diagnosticos(rf)))
            if periodo=="total":
                pr=prever_um_passo(treino,teste,spec,spec["det"]+[col])
                if pr is not None:
                    pr["categoria"]=nome
                    previsoes.extend(pr.to_dict("records"))
                    metricas.append(avaliar(nome,periodo,pr,lag))
        # A alternativa não escolhida é uma análise de sensibilidade somente
        # para o TOTAL climático, sem usar métricas OOS na seleção.
        if periodo=="total":
            for alt in CANDIDATOS["total"]:
                if alt["nome"]==spec["nome"]:
                    continue
                alt_base=estimar(treino,alt,alt["det"])
                melhor,_=selecionar_lag(treino,alt,TOTAL,0,periodo)
                if alt_base is None or melhor is None:
                    continue
                _,lag,col,_=melhor
                alt_clima=estimar(treino,alt,alt["det"]+[col])
                alt_pb=prever_um_passo(treino,teste,alt,alt["det"])
                alt_pc=prever_um_passo(treino,teste,alt,alt["det"]+[col])
                if alt_pb is None or alt_pc is None:
                    continue
                ab=avaliar("SARIMA",periodo,alt_pb)
                ac=avaliar(TOTAL,periodo,alt_pc,lag)
                sensibilidade.append(dict(especificacao=alt["nome"],lag=lag,
                    bic_sem=float(alt_base.bic),bic_com=float(alt_clima.bic),
                    delta_bic=float(alt_clima.bic-alt_base.bic),
                    rmse_sem=ab["rmse"],rmse_com=ac["rmse"],
                    delta_rmse=ac["rmse"]-ab["rmse"],
                    residuos_sem_ok=diagnosticos(alt_base)["residuos_ok"],
                    residuos_com_ok=diagnosticos(alt_clima)["residuos_ok"]))
    modelos=pd.DataFrame(modelos)
    coeficientes=pd.DataFrame(coeficientes)
    diag_rows=pd.DataFrame(diag_rows)
    metricas=pd.DataFrame(metricas)
    previsoes=pd.DataFrame(previsoes)
    baselines=pd.DataFrame(baselines)
    candidatos=pd.DataFrame(candidatos)
    suporte=pd.DataFrame(suporte)
    estac=pd.DataFrame(estac)
    sensibilidade=pd.DataFrame(sensibilidade)
    if not coeficientes.empty:
        coeficientes["q_bh"]=np.nan
        for periodo,idx in coeficientes.groupby("periodo").groups.items():
            coeficientes.loc[idx,"q_bh"]=multipletests(
                coeficientes.loc[idx,"p"],method="fdr_bh")[1]
    for nome,frame in [
        ("modelos",modelos),("coeficientes",coeficientes),("diagnosticos",diag_rows),
        ("metricas",metricas),("previsoes",previsoes),("baselines",baselines),
        ("candidatos",candidatos),("suporte",suporte),
        ("estacionariedade",estac),("sensibilidade",sensibilidade)]:
        salvar(frame,nome)
    criar_figuras(d,fit_total,treino_total,previsoes)
    sem=metricas[metricas.categoria=="SARIMA"].iloc[0]
    com=metricas[metricas.categoria==TOTAL].iloc[0]
    m0=modelos[(modelos.periodo=="total")&(modelos.categoria=="SARIMA")].iloc[0]
    m1=modelos[(modelos.periodo=="total")&(modelos.categoria==TOTAL)].iloc[0]
    comp=dict(bic_sem=float(m0.bic_treino),bic_com=float(m1.bic_treino),
              delta_bic=float(m1.delta_bic),
              mae_sem=float(sem.mae),mae_com=float(com.mae),
              delta_mae=float(com.mae-sem.mae),
              rmse_sem=float(sem.rmse),rmse_com=float(com.rmse),
              delta_rmse=float(com.rmse-sem.rmse),
              residuos_sem_ok=bool(m0.residuos_ok),
              residuos_com_ok=bool(m1.residuos_ok),
              lag_clima=int(m1.lag))
    resumo=dict(status="executado_e_validado", n_meses_originais=144,
                n_treino=116,n_teste=24,n_pre_pandemia=81,
                especificacao_baseline=selecionado_total["nome"],
                data_treino_final=TREINO_FIM,
                notas=("inferência descritiva pós seleção de estrutura/lag; "
                       "previsões com regressor contemporâneo são condicionais; "
                       "grupo COBRADE exato requer entrada bruta"),
                comparacao=comp)
    (OUT/"resumo.json").write_text(json.dumps(resumo,ensure_ascii=False,indent=2),
                                    encoding="utf-8")
    relatorio(d,baselines,modelos,coeficientes,diag_rows,metricas,estac,
              suporte,previsoes,candidatos,sensibilidade,resumo)
    print(json.dumps(resumo,indent=2,ensure_ascii=False))
    print("BASELINES\n",baselines.to_string(index=False))
    print("METRICAS\n",metricas.to_string(index=False))
    print("COEFICIENTES\n",coeficientes.to_string(index=False))


if __name__=="__main__":
    main()
