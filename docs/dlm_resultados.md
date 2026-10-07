# DLM — resultados executados

## Escopo e validação

Etapa 2 do TCC, sem reexecução de Granger. O painel consolidado foi validado em 27 UFs × 144 meses (jan/2013–dez/2024), totalizando 3.888 UF-mês, sem duplicidades UF-mês. A taxa de inadimplência reproduz `100 × carteira_inadimplencia_total / carteira_ativa_total`. O CSV bruto do Atlas foi reaberto e reconciliado: 40.339 registros em 2013–2024, com igualdade exata para total, quatro grupos e 16 tipologias.

Foram executados separadamente o período total 2013–2024 e o pré-pandemia jan/2013–jan/2020.

## Mudança justificada em relação ao PDF

O desenho antigo do PDF usa a taxa de inadimplência em nível. A evidência específica do painel não sustentou essa escolha. No período total, a concordância ADF rejeita raiz unitária + KPSS não rejeita estacionariedade ocorreu em 22,2% das UFs para I em nível e 0% após a transformação TWFE; no pré, 7,4% em ambos os casos. Para ΔI, a concordância foi 85,2% no total e 51,9% no pré, com Fisher-ADF fortemente contrário à raiz unitária em ambos.

Por isso, antes da interpretação, a especificação principal foi definida como:

`ΔI_it = α_i + λ_t + Σ(k=0..K) β_k log(1 + X_i,t-k) + ε_it`.

A mudança altera o estimando e foi registrada explicitamente. Para um pulso de exposição em um mês, `Σβ_k` resume a mudança acumulada da taxa de inadimplência ao longo do horizonte K; por isso a terminologia recomendada é **efeito acumulado no horizonte K**, não “efeito de longo prazo”.

## K, multicolinearidade e Almon

A grade ex ante foi K ∈ {3,6,9,12}, sempre comparada em amostra comum. O BIC selecionou K=3 em todos os 40 modelos estimados. A maior correlação absoluta entre lags foi 0,461 e os condition numbers permaneceram muito abaixo do gatilho 30. Portanto, nenhum cenário acionou o PDL de Almon pelo protocolo. Almon permanece metodologicamente relevante como solução condicional, mas não foi necessário na execução final. Koyck não foi utilizado.

## Estimabilidade

Foram planejados 42 cenários: 21 exposições × 2 períodos. Quarenta foram estimados. No total, 18 exposições foram classificadas como “estimáveis” e 3 como “estimáveis com ressalvas”. No pré, 17 foram “estimáveis”, 2 “estimáveis com ressalvas” e 2 “não estimáveis”. Onda de Calor/Baixa Umidade e Rompimento/Colapso de barragens não foram estimadas no pré por não atenderem ao critério ex ante.

## Resultado geral e grupos

O total de desastres não apresentou efeito acumulado nem teste conjunto significativo em nenhum período. Nenhum dos quatro grupos apresentou efeito acumulado significativo após FDR. Hidrológico no período total apresentou teste conjunto nominal p=0,0306, mas q=0,1224 após BH/FDR.

Período total — total de desastres: efeito acumulado=0,000705 pp, IC95% [-0,006015; 0,007424], p=0,8310; teste conjunto p=0,1417.

Pré-pandemia — total de desastres: efeito acumulado=-0,000704 pp, IC95% [-0,011804; 0,010395], p=0,8972; teste conjunto p=0,9624.

## Tipologias: efeito acumulado

O único efeito acumulado que permaneceu significativo após BH/FDR foi **Onda de Frio no pré-pandemia**:

- K=3;
- efeito acumulado=0,047964 pp por unidade de `log1p(X)`;
- IC95% cluster-UF=[0,022756; 0,073172];
- p=0,0005893; q=0,009428;
- Driscoll–Kraay p=0,01839;
- teste conjunto p=0,0001246; q=0,001993;
- mesma direção em todas as cinco especificações da robustez limitada.

A ressalva é substantiva: no pré-pandemia há apenas 60 registros dessa tipologia, 21 UF-mês positivos e ocorrência em 6 UFs. Portanto, trata-se de um sinal específico em exposição esparsa, não de evidência geral de impacto climático no crédito.

Como ilustração de escala, uma mudança de 0 para 10 ocorrências corresponde a `log(11)` unidades de `log1p`; multiplicando pelo efeito acumulado, a associação estimada é aproximadamente 0,1150 pp, IC95% [0,0546; 0,1755]. Dez ocorrências é uma mudança grande relativamente à distribuição pré-pandemia e essa ilustração não deve ser tratada como elasticidade nem efeito causal.

No período total, Onda de Calor/Baixa Umidade (p=0,0367) e Outros (p=0,0230) apresentaram efeitos acumulados apenas nominalmente significativos; ambos perderam significância após FDR (q=0,2646).

Nenhum coeficiente de lag individual permaneceu significativo após a correção FDR da família de lags.

## Testes conjuntos das defasagens

Após BH/FDR, seis cenários apresentaram teste conjunto significativo. Cinco são do período total e um do pré:

| período | tipologia | p conjunto | q conjunto | efeito acumulado FDR? |
|---|---|---:|---:|---|
| Total | Alagamentos | 0,015009 | 0,048030 | não |
| Total | Chuvas Intensas | 0,004051 | 0,016317 | não |
| Total | Inundações | 0,000856 | 0,006850 | não |
| Total | Onda de Calor e Baixa Umidade | 0,000089 | 0,001430 | não |
| Total | Onda de Frio | 0,004079 | 0,016317 | não |
| Pré-pandemia | Onda de Frio | 0,000125 | 0,001993 | sim |

Nos cinco cenários do período total, a rejeição conjunta sem efeito acumulado FDR indica um perfil temporal detectável com possível compensação entre lags; não deve ser resumida como aumento ou redução acumulada persistente.

## Granizo e relação com Granger

Granizo no período total, que no fechamento de Granger apareceu como sinal exploratório sensível à covariância/especificação, não se reproduziu no DLM como efeito acumulado robusto: efeito acumulado=0,008965 pp, IC95% [-0,000642; 0,018572], p=0,06615, q=0,26458; teste conjunto p=0,10755, q=0,21510.

Isso não constitui contradição entre métodos. Granger testa informação temporal precedente em uma dinâmica nacional transformada; o DLM em painel estima um perfil de associação contemporânea/defasada condicionado a FE de UF e mês-ano.

## Diagnósticos e inferência

A inferência principal usa cluster por UF, com 27 clusters, correção de pequena amostra e referência t/F com 26 graus de liberdade. Como robustez, foram mantidos resultados Driscoll–Kraay com bandwidth 12. O teste conjunto de autocorrelação residual não rejeitou em nenhum dos 40 modelos. Houve sinal de dependência transversal residual em 19 modelos, justificando manter a inferência DK visível.

Onze modelos foram classificados como “adequados” e 29 como “adequados com ressalvas”; nenhum atingiu o critério pré-definido de “inadequado para inferência substantiva”. Leave-one-UF-out foi usado como diagnóstico de influência, não para excluir estados.

## Robustez

A multiverse foi limitada, conforme protocolo, a transformação `log1p` versus contagem, controles temporais alternativos, K vizinho e Almon apenas se acionado. Onda de Frio pré foi a associação acumulada mais estável: principal, contagem, FE sazonal, tendência e K=6 mantiveram sinal positivo e p nominal <0,05. Os testes conjuntos do período total foram menos estáveis em sinal/magnitude e devem ser tratados principalmente como evidência sobre a forma do perfil de lags.

## Multiplicidade

BH/FDR foi aplicado em famílias planejadas por período × nível (Total, Grupo, Tipologia). Os dois cenários pré não estimáveis permanecem implicitamente na família de tipologias como p=1 para não encolher post hoc o conjunto de hipóteses. Resumo:

- 42 cenários planejados;
- 40 estimados;
- 1 efeito acumulado após FDR;
- 6 testes conjuntos após FDR;
- 0 lags individuais após FDR.

## Implicações para SARIMAX

SARIMAX não foi executado. A etapa seguinte deve preservar a transformação da inadimplência compatível com a estacionariedade, usar horizontes parcimoniosos sem selecionar regressoras por significância do DLM, tratar tipologias esparsas com cautela, modelar sazonalidade/choques comuns e enfatizar validação fora da amostra.

## Recomendações para atualizar o texto do TCC

1. Atualizar a cobertura temporal do painel em relação ao PDF desatualizado.
2. Explicitar que o DLM final usa ΔI e por quê.
3. Substituir “efeito de longo prazo” por “efeito acumulado no horizonte K”.
4. Explicar que FE mês-ano identifica β pela heterogeneidade de exposição entre UFs dentro de cada mês.
5. Registrar a limitação de 27 clusters e a robustez DK.
6. Manter Almon como solução metodológica condicional e registrar que ele não foi acionado nos dados finais.
7. Não usar linguagem causal forte: os coeficientes são associações condicionais.
