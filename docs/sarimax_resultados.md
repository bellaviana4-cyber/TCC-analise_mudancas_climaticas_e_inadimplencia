# SARIMAX — resultados e interpretação

Data de referência: 14/10/2026. Fonte: `outputs/tables/segunda_etapa/series_nacionais_agregadas.csv`. Tabelas completas: `outputs/tables/sarimax/`.

## Síntese

**Nenhum SARIMA de referência da grade pequena apresentou, simultaneamente, p≥0,05 em Ljung–Box 6 e 12 meses, tanto no período total como no pré-pandemia. Portanto, nenhum candidato deve ser comunicado como modelo final estatisticamente adequado.** A execução produziu estimativas e avaliações condicionais, que permanecem exploratórias e exigem ressalva diagnóstica. A grade ampliada incluiu quinze estruturas no total e onze no pré, evitando hiperparametrização.

## Transformações e estacionariedade

Variável dependente `100Δlog(I)`. Exógena `Δlog(1+D)` para cada categoria. A diferença é externa; SARIMAX usa d=D=0. Taxa I foi construída previamente como 100×ΣCI/ΣCA, não média das UFs. Para I nacional no período total, ADF de log(I): p=0,19576; KPSS: p=0,01703, resultado compatível com não estacionariedade em nível. Na primeira diferença de log(I), ADF p=0,02081 e KPSS p≥0,10: evidência compatível com estacionariedade. Exposição central em nível: ADF p=0,50600 e KPSS p≤0,01; em diferença: ADF p≈2×10⁻⁹ e KPSS p≥0,10.

Pré-pandemia: log(I) em nível ADF p=0,12208 e KPSS p≤0,01. Na primeira diferença, ADF p=0,34287 e KPSS p≥0,10: os testes divergem; **não há comprovação de estacionariedade**. Esses resultados reforçam a condição exploratória das estimativas pré-pandemia.

## Modelo SARIMA de referência e total climático

| Item | Total (treino mai/2013–dez/2022, n=116) | Pré-pandemia (mai/2013–jan/2020, n=81) |
|---|---:|---:|
| Ordem SARIMA candidata de menor BIC | (1,0,1)×(1,0,0)₁₂ | (1,0,0)×(1,0,0)₁₂ |
| BIC SARIMA | 554,2083 | 362,1183 |
| BIC SARIMAX total climático | 555,8297 | 362,9214 |
| Diferença BIC (com − sem clima) | +1,6214 | +0,8031 |
| Lag escolhido para total climático | 0 | 0 |
| Ljung–Box SARIMA, lag 6 (p) | 0,00990 | 0,00240 |
| Ljung–Box SARIMA, lag 12 (p) | 0,05195 | 0,03373 |
| Ljung–Box SARIMAX climático, lag 6 (p) | 0,00723 | 0,00039 |
| Ljung–Box SARIMAX climático, lag 12 (p) | 0,01705 | 0,00386 |

A série nacional total não obteve melhora de BIC com a exposição climática. A autocorrelação residual remanescente torna inadequada uma conclusão confirmatória sobre os coeficientes. Os modelos reportados são **melhores candidatos dentro da grade**, não modelos aprovados.

## Coeficientes e multiplicidade

Na amostra completa de 140 meses efetivos, o total climático apresentou estimativa β=0,41744, IC95% [−0,06446;0,89933], p usual=0,08955, q BH=0,35819. No pré-pandemia, β=0,56255, IC95% [−0,00465;1,12974], p=0,05191, q BH=0,31659. Assim, não houve rejeição a 5% nesses modelos; além disso, os testes não incorporam incerteza da seleção por BIC e os resíduos reprovam a triagem de autocorrelação.

Nenhuma tipologia apresentou q BH inferior a 0,05 no período total ou no pré. Há exceções nominais em grades preliminares e mudanças sensíveis à ordem ARMA, razão adicional para não identificar efeitos robustos. Coeficientes não devem ser descritos em pontos percentuais da taxa nem como causalidade.

## Avaliação temporal 2023–2024

Origem móvel de um passo, com coeficientes fixos, 24 observações e treino apenas até dez/2022. Medida: variação logarítmica mensal da inadimplência ×100.

| Modelo | MAE | RMSE | Nota |
|---|---:|---:|---|
| SARIMA | 1,0921 | 1,3548 | baseline univariado |
| SARIMAX total climático, lag 0 | 1,0628 | 1,3850 | condicional ao total de desastres no próprio mês |
| SARIMAX granizo, lag 1 | 1,0498 | 1,3247 | pequena melhora numérica de RMSE; BIC superior ao baseline e resíduos com autocorrelação |
| SARIMAX chuvas intensas, lag 1 | 0,9921 | 1,3590 | menor MAE isolado; RMSE maior que baseline |

Para o total climático, o MAE melhorou numericamente, mas o RMSE piorou. Não houve melhora preditiva uniforme. Comparações por tipologia são exploratórias e não constituem validação de superioridade sem testes e diagnósticos adequados. No lag zero, as exposições futuras são dadas como observadas; a previsão é condicional, não ex ante. Além disso, disponibilidade tempestiva do registro Atlas para lags positivos não foi auditada.

## Suporte e categorias

Foram consideradas as onze tipologias climáticas disponíveis na série agregada, além do total climático. Onda de calor e onda de frio pré-pandemia não atingiram a triagem mínima de 18 meses positivos e 30 registros: não receberam inferência nesse recorte. Não é possível recompor com exatidão os grupos naturais COBRADE 12/13/14 a partir das colunas agregadas do repositório. O Atlas bruto precisa ser recuperado para esse desdobramento, e grupos administrativos não são substitutos sem ressalva.

## Relação com etapas anteriores

A etapa de Granger testou precedência preditiva, mas não manteve rejeições após BH. O DLM de painel avalia associação distribuída por UF×mês e, para o total climático, não exibiu evidência robusta sob inferências conservadoras. O SARIMAX nacional não acrescentou suporte forte à relação total no ajuste ou nos testes usuais. As três etapas têm alvos estatísticos e condições de identificação distintos; não rejeição não demonstra ausência de efeito.

## Limitações e próximos ajustes técnicos

1. **Autocorrelação residual persistente:** ampliar a busca de ordens arbitrariamente seria inadequado. Antes de encerrar formalmente a modelagem, deve-se investigar intervenções e possíveis mudanças estruturais na pandemia, modelos com componentes determinísticos fundamentados, inspeção de ACF residual e estabilidade; revalidar em janela temporal.
2. **Inferência pós-seleção:** p e q condicionados à especificação; não confundir BH com correção seletiva.
3. **Exposição e агрегação:** grupos COBRADE não recuperáveis sem registros brutos; agregação Brasil mascara respostas estaduais heterogêneas.
4. **Previsão condicional e regressores:** lag zero usa exposição conhecida contemporânea; não informa diretamente previsão operacional.
5. **Pré-pandemia:** pequena amostra, testes de estacionariedade divergentes e Ljung–Box desfavorável.

## Redação acadêmica sugerida

> Na etapa de séries temporais, foram estimadas especificações SARIMA e SARIMAX para a variação logarítmica mensal da inadimplência nacional, utilizando a exposição aos desastres climáticos como regressora externa. A seleção foi realizada com uma grade reduzida de estruturas autorregressivas e de médias móveis, sob critério de informação de Schwarz, complementado pelo diagnóstico de autocorrelação residual. Os resultados exploratórios não indicaram melhora do BIC após a inclusão do total de registros climáticos. No horizonte de previsão de janeiro de 2023 a dezembro de 2024, a inclusão dessa variável reduziu o erro absoluto médio, mas elevou a raiz do erro quadrático médio em comparação ao SARIMA sem regressoras climáticas. Os modelos conservaram autocorrelação residual estatisticamente detectável, motivo pelo qual suas estimativas não foram interpretadas como evidência confirmatória de associação. A análise, de caráter observacional, tampouco fornece identificação causal dos efeitos de desastres sobre a inadimplência.

## Documentação e reprodução

Executar `python src/sarimax.py` na raiz. Relatório offline: `outputs/reports/relatorio_sarimax.html`; figuras `outputs/figures/sarimax/`; resultados CSV `outputs/tables/sarimax/`. Conferir o manifesto `resumo.json` e o workflow GitHub Actions. Todos os números acima correspondem à grade de quinze candidatos e devem ser conferidos após a última execução de geração do relatório.