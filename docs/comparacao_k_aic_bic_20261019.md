# comparação aic versus bic dos dlms de painel — 19/10/2026

## origem e método

Esta auditoria não reestima DLMs. Utiliza o CSV versionado de candidatos já ajustados: outputs/tables/dlm_painel_log_aic/candidatos_AIC.csv (blob SHA 3ccbf9d6c9d884e48bc917e9dc4637ac9f130073), que contém AIC, BIC, N, número de parâmetros, status e outros campos para a grade K=1 a K=24.

A auditoria verificou, para cada exposição e período, uma grade completa de 24 candidatos, amostra constante (N, T, número de UFs e datas de início/fim) e a identidade BIC = AIC + [ln(N) − 2] × número de parâmetros, com tolerância 0,000001. Selecionou o mínimo de AIC e o mínimo de BIC na mesma exposição e recorte. A família de comparação não mistura diferentes verossimilhanças. Não selecionou especificações por p-valor.

O CSV principal de resultados está em outputs/tables/dlm_comparacao_aic_bic/comparacao_k_aic_bic.csv. Contém as 16 tipologias solicitadas e também o total e os quatro grupos históricos para rastreabilidade, sem promover esses agregados a novas exposições principais.

## resultados

- 42 aplicações históricas candidatas: 2 períodos × (1 total + 4 grupos + 16 tipologias).
- 39 estimáveis, 3 sem suporte suficiente no pré-pandemia.
- BIC selecionou K=1 para todas as 39 aplicações estimáveis.
- Das 32 aplicações por tipologia, 29 foram estimáveis e 8 mudaram de K entre AIC e BIC.
- Uma nona mudança ocorreu no grupo Meteorológico total (AIC K=9, BIC K=1).

| tipologia | período | k por aic | k por bic |
| --- | --- | ---: | ---: |
| Chuvas Intensas | Pré | 15 | 1 |
| Vendavais e Ciclones | Pré | 14 | 1 |
| Chuvas Intensas | Total | 16 | 1 |
| Incêndio Florestal | Total | 6 | 1 |
| Movimento de Massa | Total | 5 | 1 |
| Onda de Calor e Baixa Umidade | Total | 14 | 1 |
| Rompimento/Colapso de barragens | Total | 4 | 1 |
| Vendavais e Ciclones | Total | 9 | 1 |

As três aplicações pré-pandemia sem suporte são Onda de Frio, Onda de Calor e Baixa Umidade e Rompimento/Colapso de barragens. A tabela as preserva sem K/p artificial. O campo vantagem_BIC é BIC do K escolhido por AIC menos BIC do K escolhido por BIC; valores positivos favorecem o último. delta_BIC_2 é a diferença entre os dois menores BICs.

## interpretação e escopo da execução

K=1 representa contemporâneo (beta_0) e um mês defasado (beta_1). Como K=1 é a borda inferior da grade, a seleção não exclui modelos K=0 (não testados) nem demonstra que efeitos físicos mais longos sejam ausentes.

Esta é uma nova SELEÇÃO aplicada a ajustes históricos, não uma reestimação dos DLMs, nem novos testes de hipótese. As covariâncias e os cinco contrastes associados ao novo K selecionado por BIC não foram recalculados. Não é possível afirmar que a significância mudou (ou não mudou) a partir da seleção isolada.

As bases mensais e o Atlas bruto não estão versionados no GitHub, conforme data/README.md. Não estão disponíveis nesta execução. Não foram realizados novos Granger estaduais, testes F/LM/Hausman nem SARIMA/SARIMAX estaduais. Nenhum novo p/q-valor ou rejeição de H0 é reivindicado nesta auditoria. Sem as entradas originais conferidas, não se deve apresentar como concluído o projeto integral de 864 Granger, 32 DLMs, 54 SARIMA e 54 SARIMAX.

Os resultados e arquivos históricos não foram alterados; esta branch contém somente o novo CSV derivado e a documentação da sua proveniência. Este resultado parcial deve ser revisado antes de ser integrado à main.
