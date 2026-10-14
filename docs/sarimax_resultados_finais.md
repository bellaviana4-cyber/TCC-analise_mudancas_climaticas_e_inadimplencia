# Etapa SARIMAX — resultados finais da análise e roteiro de interpretação

**Data:** 14/10/2026. **Branch:** `analise/sarimax-nacional`. **Fonte pública auditada:** `outputs/tables/segunda_etapa/series_nacionais_agregadas.csv`. **Implementação válida:** `src/sarimax_validacao_final.py` e notebook 25. **Relatório:** `outputs/reports/relatorio_sarimax_final.html`. Notebooks 24 e `src/sarimax.py` são históricos e não devem ser citados como especificação final.

## 1. Resposta à pergunta central

**Não houve ganho consistente, relevante e robusto do SARIMAX sobre a referência sem desastres climáticos.** No modelo principal, a adição do total climático piorou o BIC em 2,5105 pontos, embora MAE e RMSE tenham melhorado numericamente, ambos em cerca de 0,2%. Essa diferença preditiva é pequena demais para sustentar superioridade substantiva. Na alternativa com sazonalidade anual, o BIC também piorou e o RMSE aumentou, invertendo a direção do resultado. Não foi realizado teste confirmatório de superioridade preditiva com apenas 24 erros mensais. Portanto, os resultados não sustentam a conclusão geral de que incluir desastres melhora o modelo.

A etapa está **executada, publicada e documentada**, mas não se considera que tenha demonstrado associação causal ou produzido inferência robusta sobre desastres: o treino não rejeitou autocorrelação residual em 12/24 meses no modelo principal, porém a versão completa apresentou autocorrelação em 12 meses e heterocedasticidade condicional, além de não normalidade. Essa limitação permanece explícita, em vez de buscar mais parâmetros até obter resultados convenientes.

## 2. Dados, unidade e preparo

A unidade de análise é **Brasil × mês**. A taxa nacional foi construída na etapa de integração BACEN/SCR como

\[
 I_t =100\frac{\sum_{i=1}^{27} CI_{it}}{\sum_{i=1}^{27} CA_{it}},
\]

não como média das taxas estaduais. Foram utilizados janeiro/2013–dezembro/2024 (144 meses) e janeiro/2013–janeiro/2020 no pré-pandemia (85 meses). A resposta foi transformada em \(y_t=100\Delta\log(I_t)\). Para cada exposição, \(x_t=\Delta\log(1+D_t)\), em que \(D_t\) é uma contagem mensal auditada. Aplicaram-se a diferença e, no máximo, três lags da exposição antes de estimar; assim, a amostra comum começa em maio/2013: **116 meses de treino** (maio/2013–dezembro/2022), **24 meses de teste** (janeiro/2023–dezembro/2024), **140 meses na estimação completa** e **81 meses pré-pandemia**.

A diferenciação é externa aos modelos: os parâmetros internos são \(d=D=0\). No período completo, ADF de \(\log(I)\) teve p=0,1958 e KPSS p=0,0170; em \(\Delta\log(I)\), ADF p=0,0208 e KPSS p≥0,10, compatíveis com estacionariedade. No pré-pandemia, ADF da série diferenciada teve p=0,3429 e KPSS p≥0,10: conclusão **inconclusiva**, não uma comprovação de estacionariedade.

O total climático respeita os códigos COBRADE iniciados em 12/13/14, conforme auditoria anterior. As tipologias do Atlas são analisadas individualmente, sujeitas a suporte mínimo de 18 meses positivos e 30 registros no treino. Onda de calor e onda de frio no pré-pandemia não alcançaram esse mínimo. Os grupos **naturais COBRADE exatos não estão disponíveis** nesta tabela agregada; para reconstruí-los sem mistura administrativa, é necessário o Atlas bruto (não versionado). Não se inventou a desagregação faltante.

## 3. O que é cada modelo e como foi escolhido

ARIMA usa termos autorregressivos AR(\(p\)), diferenciação (\(d\)) e médias móveis MA(\(q\)). SARIMA acrescenta dependência sazonal (\(P,D,Q,s\)). SARIMAX incorpora regressores externos. Em `statsmodels`, a formulação aplicada é **regressão com erros SARIMA**, coerente com a equação revisada no capítulo 3:

\[
y_t = c + \boldsymbol{\gamma}' \mathbf{z}_t + \beta x_{t-\ell} + u_t,\qquad
\Phi(B)\tilde{\Phi}(B^s)u_t=\Theta(B)\tilde{\Theta}(B^s)\varepsilon_t.
\]

\(\mathbf z_t\) é o conjunto de controles de calendário conhecidos; o modelo sem clima omite \(\beta x_{t-\ell}\). Coeficientes não são efeito causal nem pontos percentuais da taxa I.

Nos ensaios iniciais (notebook 24), modelos simples mantinham autocorrelação em múltiplos meses. Uma primeira triagem (`triagem_residual.csv`) avaliou alternativas com harmônicos anuais e intervenções predefinidas para a pandemia; nenhuma delas isoladamente resolveu os diagnósticos de autocorrelação no período completo. A ACF residual indicava concentração nos lags 3 e 6. Em uma segunda triagem controlada (`triagem_lags_especificos.csv`), foram testadas poucas estruturas que representavam dependência trimestral/semestral, além da anual.

Os candidatos finais para o total foram: **anual esparso** com AR nos lags 1, 3, 6 e sazonal AR(1) em 12 meses, sem controles determinísticos; e **semestral com harmônicos anuais** com AR(1), sazonal AR(1) em seis meses e um par \(\sin/\cos\) de período 12. Ambos apresentaram teste Ljung–Box ajustado não significativo em 12/24 meses no treino. O segundo obteve BIC menor (550,8255 ante 553,7072), sendo selecionado **somente pelo treino**, não pelo teste. Não equivale a um SARIMA puramente univariado: a referência contém dois regressores determinísticos anuais, comuns ao modelo com clima, e erros SARIMA semestrais. Ainda é um modelo pequeno (2 coeficientes AR, 2 harmônicos, constante e variância).

No pré-pandemia, escolheu-se AR esparso nos lags 1 e 6, sem termos harmônicos, com BIC 347,9981. A alternativa AR(1)×SAR(1) semestral obteve BIC 348,0235: diferença mínima. A seleção foi parcimoniosa e feita dentro dos 81 meses disponíveis.

Com a dinâmica escolhida, cada SARIMAX recebe **uma única categoria** climática e uma das defasagens 0, 1 ou 3, selecionada por BIC no treino entre candidatas com diagnóstico residual favorável, quando disponíveis. O baseline e o SARIMAX usam exatamente a mesma estrutura temporal e os mesmos controles de calendário; a única diferença é a exposição ao desastre. Defasagens isoladas não representam soma de efeitos acumulados.

## 4. Resultados principais e avaliação preditiva

| Métrica | Sem desastres (referência) | Com total climático (SARIMAX) | Diferença (com − sem) |
|---|---:|---:|---:|
| BIC no treinamento | 550,8255 | 553,3359 | +2,5105 |
| MAE no teste | 1,3385 | 1,3356 | −0,0028 |
| RMSE no teste | 1,7294 | 1,7260 | −0,0033 |

O BIC favorece a especificação **sem** o total de desastres. MAE e RMSE favoreceram numericamente o SARIMAX em aproximadamente **0,2%**, mudança marginal. Não é correto concluir que o modelo climático foi globalmente superior.

A avaliação é cronológica, com coeficientes estimados até dezembro de 2022. São 24 previsões de um mês à frente (2023–2024), atualizando apenas o estado filtrado com o novo mês, sem reajustar parâmetros. Como o melhor lag do total climático foi \(\ell=0\), a previsão utiliza **D do mês observado**: é condicional a esse conhecimento, não uma previsão operacional que antecipe desastres.

**Sensibilidade estrutural:** com o candidato anual esparso, BIC sem clima=553,7072 e com clima=553,7998 (diferença +0,0926). O RMSE também aumentou, de 1,3773 para 1,4224 (diferença +0,0451). Assim, o minúsculo ganho preditivo do SARIMAX principal não é robusto à especificação sazonal escolhida. Importante: o candidato anual esparso teve RMSE inferior à referência semestral selecionada por BIC no treino; isso demonstra que minimizar BIC não assegura menor erro fora da amostra. Não se deve utilizar o teste para trocar retrospectivamente o modelo, pois haveria seleção sobre a avaliação.

No pré-pandemia, o total climático apresentou BIC 348,8455 contra 347,9981 da referência (ΔBIC +0,8473): a inclusão do desastre não foi favorecida pelo BIC também nesse recorte. Não foi possível testar previsão fora da amostra do pré-pandemia sem alterar os recortes estabelecidos; a comparação é descritiva/in-sample, não equivalente ao teste 2023–2024.

## 5. Hipóteses, coeficientes e multiplicidade

A hipótese nula pontual por categoria é \(H_0:\beta=0\) (associação condicional contemporânea ou em lag isolado, a depender do modelo). Rejeitá-la **não** implicaria identificação causal. Para o total climático:

| Período | \(\hat\beta\) | IC95% | p nominal | q BH |
|---|---:|---|---:|---:|
| Completo (reajuste de 140 meses) | 0,3657 | [−0,1181; 0,8495] | 0,1384 | 0,2888 |
| Pré-pandemia (81 meses) | 0,5321 | [0,0071; 1,0571] | 0,0470 | 0,1646 |

A rejeição nominal a 5% no pré-pandemia **não permanece após BH**. Nenhuma das tipologias também apresentou q BH inferior a 0,05 na família respectiva. Mesmo com BH, os p-valores são condicionados à estrutura e à defasagem selecionadas; BH não corrige incerteza pós-seleção.

A tipologia Onda de Calor e Baixa Umidade teve o menor RMSE entre as categorias climáticas avaliadas na especificação principal (1,6440, contra 1,7294 sem clima), mas isso **não estabelece associação robusta**: o coeficiente teve p nominal 0,0954 e q BH 0,2888, além de cobertura temporal rarefeita. Essa comparação envolve seleção entre muitas categorias e não constitui recomendação operacional.

## 6. Diagnóstico e limitações inferenciais

No treino de 116 meses do período completo, a referência teve Ljung–Box **ajustado pelo número de parâmetros ARMA**: p12=0,1827 e p24=0,4989; o SARIMAX com total climático apresentou p12=0,1132 e p24=0,4015. Não houve rejeição da hipótese de ausência de autocorrelação linear nesses horizontes no treino.

**Isso não basta para declarar todos os pressupostos satisfeitos.** Houve ARCH(3) muito significativo na referência (p≈0,0000087) e no SARIMAX central (p≈0,000031), bem como rejeição de normalidade pelo teste Jarque–Bera. Na estimação completa de 140 meses, o SARIMA sem clima também voltou a apresentar Ljung–Box ajustado p12=0,0234; o SARIMAX central, p12=0,0114 e p24=0,0457. Portanto, a correlação residual não permaneceu controlada na extensão da série.

O objetivo foi atingir um compromisso entre simplicidade, avaliação previsível e transparência. Acrescentar intervenções e novas defasagens indefinidamente para eliminar rejeições ou encontrar coeficientes significativos seria inadequado. Os erros-padrão usuais, intervalos e p-valores devem ser interpretados como **descritivos/exploratórios**; não há validação confirmatória da hipótese climática. A heterocedasticidade sinaliza que os intervalos de previsão baseados em variância constante também exigem cautela.

## 7. Comparação com Granger e DLM

A etapa de **Granger** avaliou precedência preditiva e não manteve rejeições após BH. O **DLM de painel UF×mês** examinou associações distribuídas em um horizonte K por categoria e não encontrou evidência robusta para o total climático na inferência principal. O **SARIMAX nacional** controla a dinâmica temporal agregada, mas também não apresentou evidência robusta de associação do total climático e não trouxe melhora relevante/estável de previsão. As conclusões se complementam, mas não são testes equivalentes: unidades, controles e estimandos diferem.

## 8. O que faz cada parte do código

- `entrada()` recupera a série nacional e valida calendário, números positivos e contagens.
- `preparar()` constrói a transformação, as defasagens 0,1,3 e a amostra comum.
- `construir()` adiciona harmônicos anuais determinísticos, conhecidos em qualquer mês previsto.
- `estimar()` ajusta SARIMAX por máxima verossimilhança, exige convergência e parâmetros finitos.
- `diagnosticos()` usa inovações padronizadas do filtro de Kalman, Ljung–Box 12/24 ajustado por parâmetros ARMA, Ljung–Box 6 descritivo, ARCH(3) e Jarque–Bera.
- `selecionar_lag()` compara apenas defasagens predeterminadas no treinamento, sem buscar significância.
- `prever_um_passo()` produz avaliação temporal sem reajuste de coeficientes, atualizando observações já realizadas.
- `avaliar()` calcula MAE, RMSE e viés na escala da variável dependente.
- `relatorio()` cria HTML standalone offline com menu lateral, gráficos, tabelas, diagnósticos e explicações.
- `main()` integra períodos, mantém o mesmo modelo-base sem/com clima, estima categorias elegíveis, faz BH por recorte e salva os resultados.

## 9. Redação para a monografia — metodologia

> Na etapa final de modelagem de séries temporais, a taxa mensal nacional de inadimplência foi construída pela razão entre a soma das carteiras inadimplentes e a soma das carteiras ativas das unidades federativas. A série foi transformada por primeira diferença logarítmica, enquanto as medidas de exposição aos desastres foram expressas pela primeira diferença de logaritmo de um mais a contagem de ocorrências. Foram comparados modelos sem e com a exposição climática, mantendo-se idêntica a estrutura temporal de erros e, quando utilizados, os termos determinísticos de calendário. A identificação partiu de modelos parsimoniosos, examinados pelos critérios de informação e pelos diagnósticos de autocorrelação. Diante da persistência de dependência nos lags três e seis, foram consideradas especificações compactas com estrutura semestral e alternativa anual esparsa. A seleção utilizou exclusivamente observações até dezembro de 2022; janeiro de 2023 a dezembro de 2024 foi reservado para a avaliação cronológica de previsões de um passo à frente.

## 10. Redação para a monografia — resultados e discussão

> A inclusão do total climático não foi favorecida pelo BIC no período principal: o modelo sem desastres apresentou BIC igual a 550,83, contra 553,34 no modelo com essa exposição. No conjunto de 24 meses destinado à avaliação preditiva, a inclusão da variável climática reduziu marginalmente o MAE de 1,3385 para 1,3356 e o RMSE de 1,7294 para 1,7260, diferenças próximas de 0,2%. Entretanto, na especificação alternativa com componente sazonal anual, a introdução do total climático elevou tanto o BIC quanto o RMSE, indicando que o pequeno ganho preditivo não foi robusto à estrutura temporal escolhida. Na estimação completa, não houve rejeição da hipótese de coeficiente nulo para o total climático ao nível de 5%, tampouco rejeições após a correção de Benjamini–Hochberg para as famílias de exposições analisadas. Apesar da melhora dos diagnósticos de autocorrelação no treinamento com as especificações revisadas, persistiram indícios de heterocedasticidade condicional e, após a inclusão dos últimos meses, de autocorrelação residual. Dessa forma, os resultados são interpretados como exploratórios e não sustentam a conclusão de ganho preditivo relevante ou associação causal dos desastres com a inadimplência nacional.

## 11. Entregáveis e reprodução

- Notebook: `notebooks/25_sarimax_validacao_final.ipynb`.
- Código: `src/sarimax_validacao_final.py`.
- Protocolo: `docs/sarimax_protocolo.md`.
- Tabelas: `outputs/tables/sarimax_final/` (modelo, baseline, estimativas, diagnósticos, estacionariedade, suporte, previsão e sensibilidade).
- Figuras: `outputs/figures/sarimax_final/`.
- Relatório standalone: `outputs/reports/relatorio_sarimax_final.html`.
- Reprodução: `python src/sarimax_validacao_final.py` com Python 3.11, numpy, pandas, scipy, statsmodels, matplotlib. O GitHub Actions executou a rotina e validou arquivos e 24 meses de teste; dados brutos não versionados não foram reaproveitados.
