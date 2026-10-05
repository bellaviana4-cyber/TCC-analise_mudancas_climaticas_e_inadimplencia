# Revisão integrada de Granger e DLMs clássicos — 05/10/2026

Auditoria após a seleção de K: conferir fontes, famílias BH, coeficientes, calendários e inferência sem alterar o principal. Conferência de dois painéis por OLS com dummies explícitas; reprodução dos 46 nacionais. Cook e correlação residual entre UFs são diagnósticos descritivos, não certificação nem exclusão automática.

## Sensibilidades adicionais finitas, registradas antes da execução

Os diagnósticos apontaram março/2020 como observação mais influente para Outros e maio/2020 para Tecnológico/antrópico. Para todos os 46 nacionais (sem filtrar pela significância): manter K/AR/controles, remover somente a contribuição da observação de maior Cook ao ajuste e conferir soma e teste conjunto. Não remover esse mês das variáveis defasadas nem comprimir o calendário. HAC usa scores zero na data omitida, mantendo a distância temporal correta; correção pequena amostra/GL usa N−1. BH48 separado por endpoint dessa sensibilidade. É diagnóstico de influência, não novo principal; séries e categorias originais permanecem.

No total, testar mudança a partir de março/2020 por indicador e interações com todos os termos AR e da exposição; tendência e sazonalidade mantidas comuns. Data fixada conforme protocolo Granger anterior, não escolhida pelo resultado. Testes HAC12 conjuntos de todos os termos adicionados e somente das interações de exposição; família BH24 separada por endpoint, três agregados analíticos incluídos. Pré não recebe essa sensibilidade, pois não inclui março/2020. Não atribuir eventual mudança especificamente à pandemia: o corte identifica diferença temporal, não mecanismo.

Inferência de todas essas sensibilidades continua condicional a K/AR. Não escolher novo principal pelo p-valor. Granger permanece sem reestimação; verificação de saídas/hash e famílias. Spline não é usado. SARIMAX não foi executado.

## Resultados da execução

Conferência numérica aprovada: fontes nacionais coincidem (taxa com diferença máxima 8,88e−16; 40.339 registros em ambas), BH48 dos cinco endpoints reproduzido; 46 Wald-F/HAC nacionais reproduzidos, todas covariâncias da exposição têm rank completo. OLS explícito concorda com FWL nos dois painéis conferidos (diferenças máximas de beta <1,6e−14). 40 verificações de saídas Granger e 469 de DLM selecionado aprovadas.

Influência: Outros total passa de C=46,836 e q=0,01848 a C=31,476 e q=0,08540 ao retirar a linha de março/2020. Meteorológico mantém BH (q=0,04693); Vendavais total mantém BH (q=0,00618). Tecnológico/antrópico, sem soma BH no principal, apresenta soma positiva BH nesta sensibilidade (q=0,03652); isso indica sensibilidade, não substitui o principal.

Mudança: 23/24 equações totais rejeitam mudança geral após BH24. Somente Vendavais/Ciclones (q=0,00823) e Tecnológico/antrópico (q≈1,65e−6) rejeitam interações específicas da exposição. Outros: mudança geral q=0,03963, exposição q=0,9110. Meteorológico: geral q=0,00317, exposição q=0,9223. Rejeição geral não demonstra mudança do desastre; pode envolver intercepto/dinâmica própria da taxa. Ausência de rejeição específica tampouco comprova constância.

Correlação residual média absoluta entre UFs nos dois ajustes conferidos: 0,203 e 0,166. É diagnóstico descritivo, afetado pelos FE, e não teste independente de dependência. Limita a leitura do bootstrap por UF.

## Avaliação e ajustes necessários

Não foi encontrado erro na seleção BIC, na escala, nas somas, na covariância ou nos ajustes BH conferidos. O principal permanece reproduzível e exploratório. O relatório passou a expor influência e mudança temporal ao lado dos sinais nacionais. Semente efetiva do bootstrap: 20261004, proveniente de `dlm_validacao_final.wcr`; a constante local 20261005 do pipeline selecionado não comandava os sorteios. Corrigir a rastreabilidade dessa constante não muda resultados.

Antes de alegações confirmatórias: definir inferência que contemple a seleção de K/AR; investigar dependência residual entre UFs com sensibilidade de covariância apropriada; considerar modelo nacional com dinâmica variável/regimes previamente definidos e controles econômicos com fontes/cobertura compatíveis. Não mudar transformação, janela ou inferência buscando menor p. Corrigir nomes interpretativos quando divergem do COBRADE sem reclassificar silenciosamente a fonte. Os dois períodos são sobrepostos; diferença de significância não testa diferença de associação.
