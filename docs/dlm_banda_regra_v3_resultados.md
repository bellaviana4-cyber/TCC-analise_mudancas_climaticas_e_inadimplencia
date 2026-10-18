# resultados com banda dk definida por regra — versão 3

Regra principal: L=floor[4(T/100)^(2/9)], com T da amostra comum das equações. Pré: T60/L3; total: T119/L4. K_AIC, amostra e coeficientes preservados. Proteção da seleção e Holm mantidos. 42 aplicações planejadas, 39 elegíveis, 936 candidatos conferidos; 840 linhas de cinco endpoints/quatro covariâncias, 780 calculadas.

Na leitura principal DK_regra/Holm por família: nenhuma rejeição a 5% nos cinco endpoints em ambos períodos. Não prova associação zero. DK6/DK12/CR1 e resultados v2 preservados. A regra é independente dos p, mas adotada após observar o histórico; análise continua exploratória e a referência não garante ótimo desempenho no painel.

## soma acumulada no total — categorias com sensibilidade histórica

| Exposição | K | L | Soma | SE | p seleção | Holm família |
|---|---:|---:|---:|---:|---:|---:|
| Movimento de Massa | 5 | 4 | 0.020125 | 0.005235 | 0.004715 | 0.075439 |
| Rompimento/Colapso de barragens | 4 | 4 | 0.073092 | 0.020384 | 0.011763 | 0.176442 |

Sensibilidades L3/4/6/12/18/24 continuam reportadas. Movimento de Massa e Barragens rejeitam apenas em algumas bandas mais longas no total; isso não justifica selecionar essas bandas como principais. São categorias fora do total climático/hidrometeorológico.

## verificações

Conferidas bandas derivadas de T60/T119, preservação K/beta, resultados v2 de DK6/DK12/CR1, proteção de seleção, Holm/BH/BY e variâncias DK contra statsmodels. A validação de programação não certifica estacionariedade, exogeneidade, cobertura finita ou banda ótima. A regra simples não modela explicitamente a persistência dos scores.
