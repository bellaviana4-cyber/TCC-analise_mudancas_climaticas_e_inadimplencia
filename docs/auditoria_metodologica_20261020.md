# Auditoria metodológica e execução das três etapas — 20/10/2026

## Escopo e dados

As 16 tipologias são preservadas **literalmente conforme o painel consolidado proveniente do Atlas**, consideradas variáveis de desastres no recorte operacional do TCC. Não são construídos grupos nem efetuadas reclassificações. A série estadual tem 27 UFs × 144 meses, base CSV com SHA-256 `46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36`. Dados originais privados não são versionados.

## 1. Granger

Testes aplicados em UF × 2 períodos × 16 tipologias. Resposta `Δlog(I)`, exógena `Δlog(1+D)`, regressão restrita/irrestrita com defasagens 1–6 escolhidas por BIC em amostra comum, sazonalidade mensal com 11 dummies e teste conjunto F. 864 aplicações, **627 estimadas**, **227 com exposição constante**, **10 sem posto completo**. **45 rejeições nominais e 14 BH** (BH local UF × período). Duas rejeições BH, ambas Alagamentos/RR, também rejeitam Ljung–Box (p≈0,00389 pré e 0,00124 total); maior autocorrelação residual absoluta até 12 lags, respectivamente ≈0,347 e 0,325. Essas intensidades não podem ser automaticamente classificadas como desprezíveis; manter os modelos é possível, mas a inferência F clássica requer ressalva. Não confundir precedência preditiva de Granger com causalidade.

## 2. DLM em painel: estrutura conforme a monografia

O estimador é MQO após remoção dos efeitos fixos de UF e mês-ano:

`Δlog(I_it) = α_i + λ_t + Σ_{k=0}^{K} β_k Δlog(1+D_{tipo,i,t−k}) + ε_it`,

com uma tipologia por modelo, K=1..24, AIC e BIC escolhidos separadamente em amostra comum, 29 tipologia×período estimáveis (58 ajustes selecionados). Nos 29, BIC K=1; AIC escolhe K diferente em oito. Cinco hipóteses: beta0, soma0K, soma1K, conjunto0K, conjunto1K; erro-padrão cluster-UF, DK-regra, DK6, DK12; multiplicidade Bonferroni 24×p e BH em famílias por período×critério×covariância×hipótese. A proteção conservadora não substitui inferência seletiva.

Auditoria independente dos **58 ajustes**: posto completo em todos, **nenhum** com cond(X)>1000, nenhuma das 232 covariâncias com autovalor não positivo ou cond(V)>10⁶. Isso afasta instabilidade numérica extrema segundo os limiares adotados, não garante validade substantiva dos Wald. AIC + DK-regra: quatro rejeições (pré: Chuvas Intensas e Vendavais/Ciclones, teste conjunto completo e defasado); BIC + DK-regra: nenhuma; BIC + DK12: três testes para Movimento de Massa no total, não reproduzidos em DK-regra ou DK6.

Gerados perfis `β_k` e curvas acumuladas `C(h)=Σ_{k=0}^{h}β_k` com intervalos para quatro covariâncias, **764 linhas cada**. `Σβ` é a associação acumulada no horizonte do modelo transformado, não um impacto causal automaticamente identificado nem um efeito em pontos percentuais.

Não rejeitar KPSS significa **não encontrar evidência suficiente contra estacionariedade**; não equivale a provar estacionariedade. Mantida `Δlog` por coerência comparativa entre as aplicações.

## 3. SARIMA vs. SARIMAX: correção da seleção de ordens

**Importante:** a classe `statsmodels.tsa.statespace.SARIMAX` não escolhe ordens automaticamente. Implementou-se busca explícita por **BIC no treino**, com cinco especificações candidatas *todas com componente sazonal anual s=12*. SARIMA e SARIMAX são selecionados **independentemente**, não se impõe automaticamente a ordem do SARIMA ao SARIMAX. Também é registrada uma comparação pareada com a mesma ordem para isolar o acréscimo de exógenas.

Treino pré: 72 observações / teste 12; treino completo: 119 / teste 24. A resposta é `100 Δlog(I)`; exógenas `Δlog(1+D)`. Previsões de um passo à frente, **condicionais à exposição contemporânea observada**, não previsão genuína anterior ao desastre.

A matriz original 16×exógenas não tem posto completo no treino de **53 das 54** aplicações estaduais; apenas MG/período completo tem posto 16. Os 53 SARIMAX estaduais alternativos usam tipologias selecionadas **exclusivamente no treino**: ao menos três meses com registro, independência linear, cond≤1000, limite 9 exógenas no pré e 12 no total. DF/pré não tem exógena elegível. Os limites de parcimônia foram mantidos e não houve seleção por p-valor ou erro de teste.

**Resultados revisados com ordens selecionadas independentemente:** 53 comparações estaduais; **16** com melhora de RMSE, **nenhuma** com BIC menor. Mediana da melhora relativa no RMSE é **−5,10%** (sinal negativo representa piora). 14 coeficientes individuais com p<0,05, apenas **dois** após BH global dos 395 coeficientes: Enxurradas/PE no pré e no período completo, positivos. Nenhum teste conjunto de exógenas sobreviveu BH. No nacional as 16 exógenas têm posto completo; SARIMAX piorou RMSE e BIC nos dois períodos: pré (RMSE ≈2,147 vs SARIMA ≈1,866; +15,02% de erro), total (≈1,497 vs ≈1,354; +10,58% de erro). Nenhum coeficiente individual nacional nominalmente significativo.

**Warnings registrados (não suprimidos):** **550 candidatos** SARIMA/SARIMAX foram ajustados (530 estaduais e 20 nacionais); **41 candidatos** produziram algum warning na tentativa inicial ou repetição. Predominam mensagens `UserWarning` de parâmetros AR/MA iniciais não estacionários/não invertíveis, inicializados em zero; houve uma tentativa inicial sem convergência, repetida. Todos os candidatos terminaram com convergência válida na configuração final. Ao nível de 5%, Ljung–Box rejeita em **13 dos 53 SARIMAX estaduais** e **2 de 2 SARIMAX nacionais** escolhidos. Os modelos não são impedidos de serem ajustados por isso, porém o diagnóstico deve constar e a inferência em casos de autocorrelação remanescente deve ser tratada com cautela.

## Reprodutibilidade e arquivos

Scripts novos:

- `src/auditoria_dlm_granger.py`
- `src/consolidar_analises_finais.py`
- `src/selecionar_sarima_sarimax_statsmodels.py`
- `src/gerar_notebooks_revisionados.py`

Notebooks executados sem erros:

- `notebooks/34_granger_ufs_tipologias_validacao.ipynb`
- `notebooks/35_dlm_painel_aic_bic_validacao.ipynb`
- `notebooks/36_sarima_sarimax_estadual_nacional_validacao.ipynb`

Saídas (sem reclassificar tipologias):

- `outputs/tables/auditoria_metodologica_20261020/` — intensidade de autocorrelação, matrizes do DLM, curvas de coeficientes e 58 ajustes auditados; todas as 58 combinações AIC/BIC com quatro matrizes de covariância.
- `outputs/tables/sarimax_criterios_independentes_20261020/` — 550 candidatos com BIC, convergência e warnings; comparações estaduais e nacionais, significância e BH global.

As tabelas originais de 19/10 e seus notebooks históricos **foram preservados como histórico**. Quando houver divergência na comparação de SARIMA/SARIMAX, a revisão de 20/10 prevalece, pois permite seleção separada da ordem temporal e registra warnings.

Este checkpoint não reescreve o capítulo metodológico nem fixa quais resultados serão classificados como principais na monografia: essas decisões serão feitas após a validação do código, conforme a orientação atual.