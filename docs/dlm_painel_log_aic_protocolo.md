# Referência atual: DLM em painel com K escolhido por AIC entre 1 e 24

Revisão solicitada em 06/10/2026, registrada antes desta execução. Substitui a escolha fixa K6 como referência; notebook 22 e suas saídas permanecem históricos, sem alteração. O pedido completo foi recuperado. Main de partida: ba0865e, versão K6 já publicada. Nenhum AGENTS.md foi encontrado em main ou nas quatro branches DLM listadas no histórico. Capítulo de metodologia preservado; não refazer Granger nem executar SARIMAX.

## Equação e seleção

y_it = Δlog(I_it), x_it = Δlog(1+D_it).

y_it = α_i + λ_t + Σ(k=0..K*) β_k x_i,t−k + ε_it.

K* = argmin(K=1,...,24) AIC(K), separadamente por exposição e período. Cada candidato inclui o contemporâneo e todos os lags de 1 até K; não seleciona lags isolados. Coeficientes livres, MQO não ponderado, 27 UFs, efeitos fixos de UF e mês-ano completos; sem defasagem de y, spline ou regimes. O mesmo K vale para as UFs de uma aplicação, mas pode mudar entre desastres e recortes. A seleção não deve produzir K distintos à força.

## Decisões prévias

| decisão | por que | implementação | consequência para interpretação |
|---|---|---|---|
| K candidato 1–24 | solicitação da autora; impactos podem ter horizontes distintos | 24 candidatos por exposição × período; incluir k0 | K é horizonte de ajuste nesse conjunto, não duração física comprovada |
| Seleção pelo menor AIC | critério solicitado, sem selecionar por significância | AIC = n[log(2π)+1+log(SQR/n)] + 2p_total; p_total=27+T−1+(K+1) | verossimilhança gaussiana de trabalho; dependência residual limita interpretação preditiva do AIC |
| Amostra comum e final mantida | comparar AIC na mesma variável resposta e calendário | diferença e 24 lags dentro de UF/recorte; primeira equação fev2015 em todos candidatos; não reexpandir final | N=1620 pré e 3213 total; perda de 675 UF-mês por recorte |
| Empates e incerteza | regra reproduzível, sem escolher pelo p | empate numérico até 1e−8: menor K; reportar todos ΔAIC e K com ΔAIC≤2 | modelos próximos não tornam K identificado com precisão |
| Candidatos não identificáveis | não mascarar falta de variação | rank completo, desvio TWFE>1e−12, condição padronizada<1e8; excluir só candidato falho, registrar razão | mínimo entre candidatos estimáveis; sem pseudoinversa silenciosa |
| Suporte na janela e amostra comum | não transferir suporte de meses retirados | mínimo 24 registros, 12 UF-mês positivos, 5 UFs, 8 meses positivos em ambas | aplicação insuficiente registrada sem inferência; UFs com zero ficam no painel |
| Inferência usual após seleção de K* | escopo clássico solicitado | CR1 UF, t26/F(r,26); DK6 Bartlett fixo independente de K, t(T−1)/F(r,T−1) | IC/p/q não incorporam seleção de K; resultados exploratórios, inclusive após BH |
| DK largura 6 | preservar única comparação de inferência e separar lag do modelo da banda de covariância | seis meses dos scores mensais para todos K | banda DK não é K; não escolher banda pelo menor p; aproximação em T grande |
| BH por família | exposições analisadas em paralelo | período × nível (central/grupo/tipologia) × covariância × endpoint | ajuste aplicado ao resultado escolhido, não corrige incerteza de seleção AIC |
| Fronteiras K1/K24 | intervalo finito solicitado | destacar limite inferior/superior | K24 pode indicar horizonte truncado; K1 não prova ausência após um mês |
| Modelos longos e 27 clusters | testes conjuntos podem ter muitas restrições | reportar rank da covariância e suporte efetivo | K24 usa 25 coeficientes frente a 27 clusters; Wald conjunto pode ser instável |

## Bases e interpretação preservadas

Recortes jan2013–jan2020 e jan2013–dez2024, sobrepostos. Primeira diferença feita após recortar; não buscar dados pré2013 nem concatenar estados. Todas UFs e meses presentes, crédito positivo, TI=100CI/CA. Contagem de linhas administrativas, identificador hash da fonte + linha; Data_Evento define o mês. Total climático diretamente de COBRADE 12/13/14, sem soma de grupos sobrepostos. Grupos e tipologias Atlas complementares, incluindo ambiguidades documentadas. Dados brutos não são publicados. Reconferir SHA256 das entradas e conciliação; não fabricar exposição central.

Recalcular ADF/KPSS nas séries transformadas completas dentro dos recortes, independentes de K; não declarar esses diagnósticos como testes específicos da subamostra fev2015 em diante. ADF intercepto/AIC: H0 γ=0, H1 γ<0. KPSS intercepto/banda auto: H0 Var(η)=0, H1 Var(η)>0. Ambos não rejeitar: inconclusivo. Preservar desfavoráveis, constantes e limites tabulares. Testes estaduais não corrigem dependência transversal nem certificam painel; FE e covariância robusta não corrigem raiz unitária.

Inferência com covariâncias completas das somas, IC95% pontuais e cinco endpoints: β0, soma0K, soma1K, conjunto0K, conjunto1K. BH mantém 1/4/16 hipóteses nas famílias central/grupos/tipologias por período; indisponíveis recebem 1 apenas no cálculo conservador, seus p observados permanecem ausentes.

β tem unidade logarítmica; não pontos percentuais ou elasticidade simples na contagem. Cenários preservam convolução da mudança persistente/pulso de um mês em D com β e acumulam Δlog(I); traduzir por 100[exp(resposta acumulada)−1]. Soma β é associação acumulada no horizonte K escolhido, condicional ao modelo. Horizontes diferentes implicam somas sobre intervalos diferentes; não comparar diretamente como o mesmo estimando.

Exogeneidade estrita condiciona todo histórico de x e efeitos fixos. Origem natural não garante causalidade. Não rejeição não prova ausência. Diferentes p nas janelas sobrepostas não demonstram mudança temporal. Almon não obrigatório; fórmulas corrigidas e pressupostos discutidos no protocolo histórico do notebook 22, com correções incorporadas ao capítulo e histórico preservado no Git.

## Validação e reprodução

Exportar 1008 linhas de candidatos planejados (42×24), incluindo inelegíveis, e uma seleção por aplicação. Conferir mesma amostra, minimum AIC, aninhamento dos regressores, contagem dos FE, dummies explícitas nas centrais e candidatos extremos, CR1, DK contra statsmodels, covariância completa da soma, convolução e lags até 24 por UF.

Notebook 23 executado com explicação antes e interpretação depois; tabelas/figuras em dlm_painel_log_aic, HTML standalone com filtros e curva ΔAIC, documentação e README atualizados. Publicar diretamente na main sem PR/force push, conforme autorização expressa do pedido anterior; confirmar SHA remoto.

Referências de implementação: https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.aic.html e https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_nw_groupsum.html . AIC gaussiano com variância estimada pode incluir mais 2 pela contagem da escala: constante comum a todos candidatos, não altera K; usamos a convenção OLSResults (coeficientes de regressão).


## Correções metodológicas de 07/10/2026

A inferência usual ignora a escolha de K por AIC; não houve inferência seletiva formal. IC95% não têm cobertura pós-seleção demonstrada, e BH não fornece garantia de FDR global nem corrige p-valores pós-seleção. As rejeições são exploratórias.

A regra original de suporte contemporâneo foi mantida. Onda de Frio no pré está **bloqueada pela regra de suporte**, não demonstrada como impossível de estimar: com K24 há regressoras não nulas em seis UFs, posto 25/25 e condição da matriz de regressoras de aproximadamente 10,24. Quatro UFs referem-se à exposição contemporânea nas datas das equações. A auditoria distingue essas medidas em `outputs/tables/dlm_painel_log_aic_revisao/suporte_regressores_auditoria.csv`.

O condicionamento da covariância padronizada CR1 dos testes conjuntos é aproximadamente 37.463 em Calor/Baixa Umidade total (K14), 13.312 em Chuvas Intensas total (K16) e 8.627 em Chuvas Intensas pré (K15). Isso não demonstra erro algébrico na implementação, mas sinaliza fragilidade da aproximação Wald. 27 UFs não equivalem a 27 clusters igualmente informativos; p-valores muito pequenos desses testes não são evidência conclusiva. Ver `condicionamento_covariancias.csv` na mesma pasta de revisão.

Mantém-se a especificação diante dos casos inconclusivos com não rejeição KPSS, conforme decisão da autora, sem reclassificá-los como favoráveis; preservam-se também os casos desfavoráveis. A ressalva deve acompanhar as conclusões.

O capítulo recebeu correções das expansões quadrática/cúbica de Almon, das variáveis auxiliares e da afirmação sobre colinearidade. Almon continua apenas alternativa teórica. A aplicação e os cenários são descritos em Δlog(I)/Δlog(1+D), com associação acumulada para cenário definido, em unidades logarítmicas ou variação relativa percentual, nunca automaticamente pontos percentuais ou impacto total de um desastre.

Nenhuma regra de seleção, estimativa, exclusão ou p-valor foi alterada nesta revisão editorial e metodológica. Publicação na main autorizada explicitamente pela autora nesta conversa, preservando histórico e sem force push.
