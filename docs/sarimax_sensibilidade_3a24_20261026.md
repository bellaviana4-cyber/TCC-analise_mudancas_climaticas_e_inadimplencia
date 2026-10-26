# Sensibilidade SARIMAX: exposições climáticas apenas a partir do terceiro mês

## Pergunta da análise

O indicador de inadimplência de pessoas físicas do Banco Central é calculado
com operações que apresentam atraso superior a 90 dias. Para investigar
possíveis associações entre desastres anteriores ao início do atraso e a
inadimplência observada, reestimamos os SARIMAX com **somente as exposições
climáticas defasadas de 3 a K meses**, onde K pode variar entre 3 e 24.

Essa hipótese **não implica que o início do atraso seja observado**: a
inadimplência da carteira é uma medida de estoque, e a ocorrência de
desastres não identifica automaticamente a data do primeiro pagamento
descumprido. Em particular, alguns contratos podem estar em atraso há
mais de 90 dias e continuar contabilizados no indicador. A regra de
arrasto do Bacen considera o saldo da operação, não só a parcela vencida.

**Fonte primária:** Banco Central do Brasil, [Nota Metodológica — Nova
estrutura de dados de crédito](https://www.bcb.gov.br/content/estatisticas/Documents/notas_metodologicas/emprestimos-sfn/notaempr.pdf),
item 9, "Atraso até 90 dias e inadimplência".

## O que mudou e o que foi preservado

| Componente | Análise anterior | Sensibilidade atual |
|---|---|---|
| Exógenas de uma tipologia | Bloco [0,...,K] | **Bloco [3,...,K]** |
| K candidatos | 0 a 24 (25) | **3 a 24 (22)** |
| Variáveis de desastres | Δlog(1+registros) | A mesma transformação |
| Resposta | 100Δlog(inadimplência) | A mesma transformação |
| Janela histórica | 24 meses iguais para todos os candidatos | **Inalterada** |
| Períodos | Pré-pandemia e 2013–2024 | **Inalterados** |
| Unidades | 27 UFs + Brasil | **Inalteradas** |
| Estimação do SARIMA | Cinco ordens candidatas e seleção por BIC do treino | **Inalterada** |
| Seleção de K climático | Menor BIC convergido e identificável | **Mesmo critério** |
| Avaliação | Previsão um passo, RMSE e MAE fora do treino | **Inalterada** |
| Modelo geral | Tipologias com K escolhido individualmente | **Mesma construção, com novos K** |

Não é um modelo que inclui defasagens 0, 1, 2 e seleciona K a partir de
3: **essas três regressoras foram efetivamente removidas**. Por exemplo,
K=3 contém *somente* o desastre observado três meses antes; K=5 contém
apenas os lags 3, 4 e 5. Também não se fixa K em 3; a busca prossegue até
24 e audita suporte, variação, posto e condicionamento para cada bloco.

A variável climática é a **variação logarítmica do número de registros**,
e não diretamente a contagem de desastres. Um coeficiente associado ao
lag 3 não deve ser interpretado como o efeito causal de um desastre
ocorrido exatamente três meses antes.

## Amostra, comparabilidade e informação disponível na previsão

O começo da série é o mesmo para os 25 candidatos anteriores e os 22
atuais: descartar 24 meses de histórico da resposta mantém a amostra
de treino e teste comparável. O pré tem 48 observações de treino e
12 de teste; o período completo tem 95 e 24, respectivamente.

No modelo anterior, os modelos escolhidos com K=0 exigem conhecer a
exposição climática do próprio mês t para uma previsão condicional de
inadimplência nesse mês; isso não é previsão antecipada do mesmo mês sem
cenário externo. Na sensibilidade atual, as exógenas referem-se aos
meses t−3 e anteriores e já podem estar disponíveis na origem de
previsão de um passo, desde que não haja atraso na divulgação da base.
Por esse motivo, a comparação de RMSE é útil, mas as duas especificações
**não usam exatamente o mesmo conjunto de informações disponíveis no
momento da previsão**.

## Limitações e recomendações para discussão

1. **Indicador de estoque versus início do atraso:** começar em 3 meses
   é plausível para sensibilidade, mas não separa operações que passaram
   pela primeira vez dos 90 dias das que permanecem inadimplentes.
2. **Blocos consecutivos:** K=24 implica 22 coeficientes climáticos por
   tipologia, um número grande para 48 meses de treino no pré. A
   penalização do BIC e o condicionamento podem preferir o limite
   inferior K=3 por razão estatística, não econômica.
3. **SARIMAX individuais e modelo geral:** um SARIMAX de uma só tipologia
   não controla as demais; reunir apenas os modelos identificáveis e
   selecionados no treino torna a inferência pós-seleção exploratória.
4. **Desastres são registros administrativos:** o número de registros
   não mede necessariamente a intensidade econômica nem os clientes
   efetivamente atingidos.
5. **Seleção por BIC versus previsão:** melhora no BIC de treino não
   implica RMSE menor no teste. São resultados diferentes.
6. **Possíveis extensões, ainda não aplicadas:** avaliar desfecho de
   *entrada em inadimplência* se o SCR permitir; comparar lags isolados
   pré-especificados, em vez de forçar blocos sucessivos; e usar
   validação temporal por múltiplas origens, com a mesma informação
   disponível na previsão.

## Reprodução

```bash
# Apenas lags 3..K, com 6 processos e checkpoints independentes
python src/executar_sarimax_tipologias_20261026.py --workers 6 --inicio-lags 3
python src/sarimax_por_tipologia_lags3_24_20261026.py --fase gerais
python src/sarimax_por_tipologia_lags3_24_20261026.py --fase consolidar
python src/comparar_sarimax_lags3_24_20261026.py
python src/verificar_sarimax_lags3_24_20261026.py
```

As análises originais permanecem intactas em
`outputs/tables/sarimax_por_tipologia_k0_24_20261026/` e os novos
resultados, inclusive os 19.712 candidatos, ficam em
`outputs/tables/sarimax_por_tipologia_k3_24_20261026/`.

## Resultados auditados

### 1. Cobertura das aplicações e horizontes escolhidos

Auditamos **896 aplicações possíveis** (16 tipologias × 28 unidades,
incluindo Brasil, × dois períodos) e **19.712 blocos candidatos**
(22 por aplicação). Desses candidatos, **9.861 foram efetivamente
estimados**. Outros 9.680 ficaram impedidos por menos de três meses
positivos de suporte, 156 por regressoras sem variação, 12 por falha de
convergência e três por condicionamento elevado.

Foram **452 SARIMAX individuais estimáveis**, exatamente as mesmas
combinações da análise 0..K: 194 pré e 258 total. Não interpretar as
outras 444 como coeficientes zero ou ausência de associação.

| K escolhido pelo BIC | Pré-pandemia | Total | Soma |
|---|---:|---:|---:|
| **3** | **180** | **244** | **424** |
| 4 | 9 | 12 | 21 |
| 5 | 2 | 1 | 3 |
| 7 | 0 | 1 | 1 |
| 8 | 1 | 0 | 1 |
| 11 | 1 | 0 | 1 |
| 17 | 1 | 0 | 1 |
| **Total** | **194** | **258** | **452** |

Assim, **424/452 (93,8%) escolheram o novo limite inferior K=3**.
Na análise original, **420/452 (92,9%) escolheram K=0**. Isso é um
alerta metodológico relevante: o predomínio do limite inferior **não
desapareceu**, apenas se deslocou junto com a grade. A presença de
um lag 3 na regressão não comprova que o mecanismo atua aos 90 dias.

### 2. SARIMAX individual versus SARIMA de referência

ΔBIC negativo significa SARIMAX favorecido pelo BIC do treino;
melhora percentual de RMSE positiva significa erro menor no teste.

| Critério | Original [0..K] | Novo [3..K] |
|---|---:|---:|
| Modelos individuais estimáveis | 452 | 452 |
| Melhor BIC que SARIMA | **22** | **29** |
| Menor RMSE que SARIMA | **167** | **179** |
| **BIC e RMSE melhores simultaneamente** | **4** | **5** |

No novo modelo, as 29 melhorias por BIC dividem-se em 14 no pré e
15 no total; os 179 ganhos de RMSE dividem-se em 85 e 94. Os ganhos
simultâneos são três no pré e dois no total.

As cinco aplicações com os dois critérios favoráveis foram:

| Período | UF | Tipologia | K | ΔBIC | Melhora no RMSE |
|---|---|---|---:|---:|---:|
| Pré | MG | Chuvas intensas | 3 | −1,49 | +5,56% |
| Pré | MS | Granizo | 3 | −4,26 | +7,41% |
| Pré | RN | Estiagem e seca | 3 | −2,96 | +12,42% |
| Total | AP | Doenças infecciosas | 3 | −0,13 | +0,05% |
| Total | RN | Estiagem e seca | 3 | −9,81 | +0,86% |

Os ganhos podem ser pequenos, especialmente os dois do período total.
No teste da soma de coeficientes individuais, após BH exploratório por
período, houve apenas duas rejeições: movimento de massa/CE no pré
(q≈2,68×10⁻⁸) e estiagem e seca/RN no total (q≈8,03×10⁻⁵).
O primeiro tem **RMSE 46,26% pior que SARIMA**, ilustrando por que
valores-p pós-seleção não devem ser tomados como ganho preditivo.
Nenhuma dessas rejeições é inferência causal ou seletiva formal.

### 3. Comparação direta de cada aplicação 0..K versus 3..K

Os **452 pares** tinham as mesmas ordens SARIMA, resposta, janela,
treino, teste e baseline. A única mudança sistemática foi o intervalo
de defasagens climáticas, além da nova seleção K pelo BIC.

| Indicador pareado | Pré: 194 pares | Total: 258 pares | Soma |
|---|---:|---:|---:|
| [3..K] teve BIC menor que [0..K] | 100 | 136 | **236** |
| [3..K] teve RMSE menor que [0..K] | 110 | 126 | **236** |
| [3..K] melhor em ambos critérios | 40 | 51 | **91** |
| Mediana de BIC novo menos antigo | −0,016 | −0,046 | — |
| Mediana de RMSE novo menos antigo | −0,008 | +0,001 | — |

Há vantagens individuais nos dois sentidos, e as **diferenças medianas
de BIC e RMSE foram pequenas**. Portanto, o resultado não sustenta que
uma janela seja uniformemente superior. A versão 3..K permite usar
somente exposições históricas em uma previsão de um passo, o que pode
ser operacionalmente preferível ao acesso a X contemporâneo exigido
por muitos modelos da análise 0..K.

### 4. Modelos gerais por UF/período

Estimamos **55 dos 56 modelos gerais**; como antes, DF no pré não
apresentou nenhuma tipologia individual estimável. Nenhum limite de
quatro ou seis tipologias foi imposto. Os conjuntos finais variaram
com suporte e posto, com média 7,19 tipos no pré e 9,21 no total.

| Indicador | Geral [0..K] | Geral [3..K] |
|---|---:|---:|
| Modelos estimados | 55 | 55 |
| Melhor BIC que SARIMA | 1 | **3** |
| Menor RMSE que SARIMA | 10 | **9** |
| Melhorou **ambos** | **0** | **0** |

Os três gerais que melhoraram o BIC foram **AC/pré**
(ΔBIC=−0,61; RMSE 40,42% pior), **PI/pré** (−3,05;
RMSE 145,22% pior) e **RR/pré** (−51,92; RMSE 186,54%
pior). Portanto, **nenhum modelo geral demonstrou benefício
simultâneo de ajuste penalizado e previsão fora do treino**.

Nos 55 pares de gerais, a sensibilidade 3..K teve BIC menor que 0..K
em 35 casos (16 no pré, 19 no total), RMSE menor em 27 (14 pré, 13
total), e ambos melhores em 12 (quatro pré, oito total). Ainda assim,
as duas estratégias gerais continuaram sem superar conjuntamente
o SARIMA de referência.

### 5. Modelo geral nacional: 16 tipologias simultâneas

**Todas as 16 tipologias foram incluídas no Brasil**, nos dois
períodos, com **19 coeficientes climáticos** em cada geral. O K=3
prevaleceu; no pré, onda de calor/baixa umidade recebeu K=4 e onda
de frio K=5. No total, estiagem e seca recebeu K=5 e movimento de
massa K=4. Os demais tipos receberam K=3.

| Brasil, SARIMAX geral | Pré 0..K | Pré 3..K | Total 0..K | Total 3..K |
|---|---:|---:|---:|---:|
| BIC SARIMA | 214,69 | 214,69 | 459,74 | 459,74 |
| BIC SARIMAX | 261,74 | 265,73 | 518,63 | 505,63 |
| ΔBIC vs SARIMA | +47,04 | **+51,04** | +58,90 | **+45,89** |
| Melhora RMSE vs SARIMA | −64,43% | **−36,87%** | −26,78% | **−51,86%** |

No **pré**, restringir aos lags 3..K reduziu a piora do RMSE, mas
aumentou a desvantagem de BIC. No **total**, reduziu a desvantagem de
BIC, mas piorou o RMSE. Portanto, o modelo geral nacional com lags
a partir de três meses **ainda não supera o SARIMA**.

### 6. Conclusão da sensibilidade

Restringir os regressores climáticos a 3..K é uma hipótese temporal
defensável e torna os preditores potencialmente conhecidos antes de
prever o mês t. A verificação reproduziu as 56 referências SARIMA
e manteve as 452 aplicações individuais estimáveis.

Houve um pequeno aumento nas contagens de ganhos individuais de BIC
e RMSE, **mas o ganho simultâneo permanece raro (5/452)**, a escolha
de K voltou a se concentrar no limite inferior (424/452) e nenhum
modelo geral teve melhora de BIC e RMSE ao mesmo tempo. Isso não
confirma um impacto climático robusto sobre a inadimplência.

**Recomendação metodológica:** manter as duas especificações como
análises de sensibilidade, deixando clara a diferença entre informação
contemporânea e histórica. Antes de ampliar ainda mais a grade,
avaliar a possibilidade de um indicador de *novas entradas* em
inadimplência (em vez de estoque) e, se viável, testar um pequeno
conjunto pré-especificado de atrasos individuais com validação
temporal de múltiplas origens. Isso exigiria nova decisão metodológica
e não foi aplicado automaticamente.
