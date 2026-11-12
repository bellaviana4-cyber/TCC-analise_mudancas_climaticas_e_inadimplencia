# Resultados da análise

Esta página corresponde ao [painel de 2013–2024](../data/README.md), com as três exclusões de modalidade aplicadas antes da agregação dos saldos. Os [cinco notebooks](../notebooks/README.md) apresentam as saídas; o [índice de tabelas e figuras](../outputs/README.md) identifica os arquivos de conferência.

## Análise descritiva

O período completo contém **40.339 registros municipais**. Climatológico e Hidrológico reúnem 19.518 e 15.409 registros, respectivamente, somando 86,58% do total. Estiagem e Seca (16.149), Chuvas Intensas (8.084) e Incêndio Florestal (3.081) concentram 67,71% dos registros.

A taxa nacional foi de 6,86% em janeiro de 2013, atingiu 4,10% em junho de 2021, subiu a 6,31% em maio de 2023 e encerrou dezembro de 2024 em 5,64%. O pico de registros ocorreu em janeiro de 2022, com 1.408 registros. A aproximação temporal das séries motiva a investigação das defasagens, considerando também os movimentos comuns da economia e as diferenças entre UFs.

## Granger

| Recorte | Planejadas | Estimáveis | Rejeições nominais | Após BH |
| --- | ---: | ---: | ---: | ---: |
| Pré-pandemia | 432 | 292 | 33 | 9 |
| Completo | 432 | 335 | 23 | 7 |
| Total | 864 | 627 | 56 | 16 |

As 16 rejeições ajustadas indicam contribuição preditiva das defasagens dos registros em combinações específicas de UF, recorte e tipologia. O ajuste de Benjamini–Hochberg foi aplicado entre as 16 tipologias de cada UF e recorte.

O Ljung–Box rejeitou a ausência de autocorrelação até a defasagem 12 em 54 dos 292 ajustes pré-pandemia e 102 dos 335 completos. Entre as 16 aplicações com rejeição após BH, três apresentaram esse diagnóstico: Chuvas Intensas no Rio Grande do Norte no pré-pandemia e Alagamentos em Roraima nos dois recortes. Os recortes têm tamanhos distintos e compartilham observações; essas proporções não constituem um teste de mudança da dependência residual.

## DLM

Foram estimáveis 29 das 32 aplicações por tipologia em cada critério e 39 das 42 aplicações no exercício ampliado. AIC e BIC selecionaram o mesmo horizonte em 18 das 29 comparações estimáveis pelos dois critérios. Nas 11 divergências, o BIC selecionou K=1 e o AIC selecionou horizontes maiores.

Nos modelos de menor AIC da grade de 0 a K, os 145 contrastes por tipologia apresentaram 54 rejeições nominais com a banda de referência. Após os ajustes pela grade e por família, permaneceram cinco:

| Tipologia | Recorte | K | Somas positivas significativas |
| --- | --- | ---: | --- |
| Granizo | Pré-pandemia | 1 | 0 a 1 |
| Movimento de Massa | Completo | 5 | 0 a 5 e 1 a 5 |
| Rompimento/Colapso de Barragens | Completo | 4 | 0 a 4 e 1 a 4 |

A rejeição da hipótese de soma igual a zero indica associação acumulada estatisticamente diferente de zero no intervalo, considerando os ajustes aplicados. No segundo menor AIC, uma rejeição permaneceu com a banda de referência: soma de 0 a 3 para Rompimento/Colapso de Barragens no período completo.

Com bandas fixas de seis e doze meses, os modelos de menor AIC apresentaram cinco e nove rejeições ajustadas; os de segundo menor AIC, duas e quatro. As contagens se referem a especificações alternativas e podem incluir a mesma exposição.

Na grade de 3 a K, foram estimáveis 39 das 42 aplicações e não houve rejeições após os ajustes nas três bandas. O total climático também não manteve significância ajustada em nenhum dos dois recortes ou grades.

| Total climático: recorte e grade | K | Soma estimada | p nominal | p ajustado |
| --- | ---: | ---: | ---: | ---: |
| Pré-pandemia, 0 a K | 1 | 0,00020 | 0,8057 | 1,0000 |
| Pré-pandemia, 3 a K | 3 | 0,00021 | 0,6155 | 1,0000 |
| Completo, 0 a K | 1 | 0,00128 | 0,0417 | 0,9998 |
| Completo, 3 a K | 3 | −0,00022 | 0,4473 | 1,0000 |

A estimativa é a soma dos coeficientes no intervalo indicado, na escala das variáveis transformadas. Na grade de 0 a K, K=1 corresponde a β₀+β₁; na de 3 a K, K=3 corresponde a β₃. A soma não representa diretamente pontos percentuais da taxa ou o efeito de um desastre adicional.

## Comparação SARIMA/SARIMAX

Os modelos individuais foram planejados para 16 tipologias, 28 unidades (27 UFs e Brasil) e dois recortes: 896 aplicações por grade. O BIC foi avaliado no treino e o RMSE nos meses de teste.

| Grade individual | Estimáveis | BIC menor | RMSE menor | Ambos menores |
| --- | ---: | ---: | ---: | ---: |
| 0 a K | 452/896 | 22 | 173 | 5 |
| 3 a K | 452/896 | 29 | 170 | 6 |

Os horizontes mínimos foram selecionados em 427 modelos na primeira grade (K=0) e 424 na segunda (K=3). A escolha reflete a comparação entre ajuste e penalização pelo número de parâmetros.

Os modelos gerais reúnem tipologias e suas defasagens em uma única especificação:

| Grade geral | Estimados | BIC menor | RMSE menor | Ambos menores |
| --- | ---: | ---: | ---: | ---: |
| 0 a K | 54/56 | 2 | 7 | 0 |
| 3 a K | 55/56 | 5 | 7 | 1 |

O ganho simultâneo ocorreu no Maranhão pré-pandemia, na grade de 3 a K. O modelo reuniu Estiagem e Seca, Alagamentos e Inundações na terceira defasagem e Enxurradas nas defasagens três e quatro. O BIC diminuiu 1,25 ponto e o RMSE passou de 2,79 para 2,35, uma redução de 15,93% calculada sobre as métricas não arredondadas.

No agregado Brasil, os modelos gerais incluíram as 16 tipologias:

| Recorte | Grade | ΔBIC | Melhora no RMSE |
| --- | --- | ---: | ---: |
| Pré-pandemia | 0 a K | 48,57 | −40,60% |
| Pré-pandemia | 3 a K | 53,36 | 3,04% |
| Completo | 0 a K | 62,06 | −8,97% |
| Completo | 3 a K | 53,95 | −34,96% |

ΔBIC é BIC(SARIMAX) menos BIC(SARIMA): valores positivos favorecem o SARIMA. Melhora negativa de RMSE significa aumento do erro. O ganho de 3,04% veio acompanhado de rejeição no Ljung–Box das inovações padronizadas (p=0,0011).

## Leitura conjunta

Granger identifica informação adicional em defasagens dos registros; o DLM identifica associações acumuladas positivas em algumas combinações; os SARIMAX apresentam ganhos preditivos em aplicações específicas. A contribuição depende do contexto estadual, da tipologia e do horizonte.

Os resultados devem ser lidos com os diagnósticos, os ajustes de significância e as condições da previsão. Eles permitem investigar a relação temporal entre desastres e inadimplência, sem atribuição causal das variações observadas. A ausência de rejeição em outras aplicações não demonstra inexistência de relação.
