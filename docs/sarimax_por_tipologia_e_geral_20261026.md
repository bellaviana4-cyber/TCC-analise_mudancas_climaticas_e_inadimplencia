# SARIMAX por tipologia e modelo geral com defasagens escolhidas

## Pergunta e motivação

O teste anterior adicionava várias tipologias simultaneamente, até quatro
no pré e seis no total, e comparava lags até três meses. Essa seleção
favorecia especificações com poucas exógenas; a tentativa de impor todas
as 16 simultaneamente mostrou-se não identificável na maioria das UFs.

Na revisão posterior, adotou-se a seguinte sequência:

1. **Um SARIMAX por tipologia**, UF e período, em vez de começar com as 16
   exposições simultâneas. São auditadas todas as 16, sem escolher somente
   categorias frequentes. Quando não há informação suficiente, a
   impossibilidade é registrada.
2. **Busca de K individual por tipologia**: comparar os blocos completos
   [0], [0,1], ..., [0,1,...,24] em uma amostra comum e escolher o menor
   BIC de treinamento entre candidatos identificáveis e convergidos.
3. **SARIMAX geral por UF e período**: reunir as tipologias estimáveis com
   as defasagens selecionadas em seus modelos individuais. Auditar a
   matriz concatenada; se necessário, selecionar um subconjunto com
   justificativa de suporte e posto, deixando explícito quais foram
   excluídas. A seleção desse subconjunto usa meses positivos, sem
   consultar valores-p do ajuste conjunto.
4. **Complemento nacional**: repetir a seleção individual das tipologias
   e o modelo geral no agregado nacional ponderado por saldo de crédito.
   O agregado não é a média simples das taxas estaduais.
5. Comparar o SARIMAX e o SARIMA de referência em cada UF/período, com
   mesma ordem temporal, treino e teste cronológico.

## Como as séries são construídas

- `y_t = 100Δlog(I_t)`; 100 é só escala, não altera a pergunta temporal.
- `x_{j,t} = Δlog(1+D_{j,t})` para a tipologia `j`.
- Dois recortes: até jan/2020 (pré) e até dez/2024 (total).
- Para manter os BIC dos 25 candidatos comparáveis, excluem-se os primeiros
  24 meses **em todos os modelos**, inclusive o SARIMA e K=0.
- Pré: 48 meses de treino e 12 de teste. Total: 95 meses de treino e
  24 de teste. Os recortes se sobrepõem.
- Cada bloco K usa K+1 coeficientes climáticos. K=0 inclui somente
  a exposição do mesmo mês; K=24 inclui os meses 0,1,...,24.
- Cinco ordens candidatas simples de SARIMA sazonal anual (`s=12`) são
  comparadas por BIC de treino e a vencedora fica **fixa** para todos os
  SARIMAX de uma mesma UF/período. Isso torna a comparação pareada.
- O BIC seleciona especificações **somente no treino**. A melhora no RMSE
  e no MAE é calculada no teste, não é usada para selecionar K.
- Quando K=0, o teste mede a previsão condicional de um passo **com a
  exposição climática contemporânea já conhecida**, e não previsão antes
  de observar os desastres do mês.

## Estimabilidade

Cada combinação UF × período × tipologia × K é registrada. Um candidato
é considerado elegível quando apresenta pelo menos três meses positivos
no treino para a tipologia, todas as regressoras do bloco variam, a matriz
tem posto completo, número de condição da matriz padronizada ≤1.000 e
observações suficientes para os coeficientes climáticos mais uma reserva
de cinco parâmetros temporais. Os demais são identificados como bloqueados
e não recebem BIC nem valores-p.

**A regra é por candidato**, não exige que o maior K=24 seja identificável
para que o K=0 possa ser estimado. Assim as 16 tipologias são auditadas em
todas as UFs, sem um teto fixo de quatro ou seis tipos.

No SARIMAX geral, o conjunto final de exógenas pode ter menos de 16
tipologias, pois os K individuais escolhidos podem, ao serem reunidos,
formar uma matriz com dependência linear, sem variação ou poucos graus de
liberdade. A ausência de estimabilidade não é interpretada como efeito nulo.

## O que significa dizer qual tipologia está mais associada?

Os modelos individuais permitem comparar **associação preditiva** de cada
tipo, e não estabelecer um ranking causal de impacto. Para cada
UF/período, são disponibilizados:

1. **ΔBIC = BIC(SARIMAX) − BIC(SARIMA)**: valores negativos favorecem a
   inclusão da tipologia segundo o critério penalizado no treino.
2. **Melhora percentual no RMSE** no teste: positivo indica menor erro
   de previsão condicional, negativo indica piora.
3. **Soma dos coeficientes estimados** no horizonte selecionado, na escala
   dos regressores Δlog(1+D); não são pontos percentuais simples.
4. **Associação acumulada para um pulso padronizado** de uma unidade de
   desvio-padrão de x, calculada na escala de Δlog(I), com interpretação
   condicional à transformação e ao modelo.
5. Diagnóstico de autocorrelação residual e incerteza dos parâmetros.

O sinal, a magnitude e o ranking de coeficientes variam com a frequência
dos desastres, correlação com outras exposições, escolha de K, parâmetros
do SARIMA e recorte. Um SARIMAX com uma única tipologia não controla as
outras quinze. Não confundir associação preditiva com efeito causal.

## Limitações da seleção e da inferência

- A grade até 24 meses é sistemática, mas **bastante grande em relação ao
  treino pré de 48 meses**. Candidatos longos podem ser não identificáveis
  ou instáveis; a penalização BIC cresce a cada lag acrescentado.
- O menor BIC entre candidatos convergidos não prova que o K é o verdadeiro
  horizonte físico; também não prova ausência de atrasos individuais.
- O conjunto de tipologias e os lags do modelo geral foram determinados
  usando a resposta nas etapas individuais. Portanto, coeficientes e
  testes do geral são *pós-seleção exploratória*, não inferência seletiva.
- BH de p-valores exploratórios não resolve seleção por BIC, múltiplos
  horizontes, endogeneidade nem autocorrelação residual.
- Pré e total se sobrepõem, e não constituem teste formal de mudança
  estrutural entre períodos.
- Acesso à exposição contemporânea do mês atual significa que a previsão
  avaliada é condicional, não previsão ex ante.
- O ranking de tipos não identifica um efeito causal dos desastres sobre
  a inadimplência, nem controla automaticamente por outras tipologias.

## Execução e organização

```bash
python src/executar_sarimax_tipologias_20261026.py --workers 4
python src/sarimax_por_tipologia_k0_24_20261026.py --fase gerais
python src/sarimax_por_tipologia_k0_24_20261026.py --fase consolidar
```

`--uf MG --periodo Total` permite repetir uma unidade. O lançador usa
checkpoints por UF/período e pode ser reexecutado com segurança.

As tabelas ficam em
`outputs/tables/sarimax_por_tipologia_k0_24_20261026/`:

- `resumo.csv`: um resultado por tipologia × UF/período, com K, BIC, RMSE,
  suporte, perfil resumido e associação padronizada.
- `candidatos.csv`: todos os candidatos da grade 0..24, inclusive os
  bloqueados, com razão de não estimabilidade.
- `coeficientes.csv`: coeficientes por lag do modelo individual escolhido.
- `bases.csv`: cinco SARIMA candidatos por UF/período.
- `geral.csv`: SARIMAX geral por UF/período, tipologias incluídas e excluídas,
  defasagens atribuídas e comparação pareada com SARIMA.
- `resumo.json`: métricas do processo e restrições de interpretação.

## Resultados

### Cobertura e seleção das defasagens

As 56 aplicações correspondem a 27 UFs mais Brasil agregado, em dois
períodos sobrepostos. Houve **896 tentativas de modelos individuais**
(56 × 16 tipologias). Para cada uma delas foram auditados os **25 blocos**
de defasagens consecutivas K=0,...,24, totalizando **22.400 candidatos**.
Destes, **11.180 chegaram a ser estimados**; os demais tiveram impedimentos
de suporte, regressora constante, convergência ou condicionamento, todos
registrados em `candidatos.csv`. Portanto, não se deve afirmar que 22.400
SARIMAX foram ajustados com sucesso.

| Indicador | Pré-pandemia | Período total | Total |
|---|---:|---:|---:|
| Modelos individuais possíveis | 448 | 448 | 896 |
| Modelos individuais estimáveis | **194** | **258** | **452** |
| Melhor BIC que SARIMA | 11 | 11 | **22** |
| Menor RMSE de teste que SARIMA | 71 | 96 | **167** |
| K=0 escolhido | 178 | 242 | **420** |
| K=1 escolhido | 10 | 12 | 22 |
| K=2 escolhido | 3 | 2 | 5 |
| K=3 escolhido | 2 | 2 | 4 |
| K=17 escolhido | 1 | 0 | 1 |

**Leitura da seleção:** 420 de 452 modelos individuais estimáveis
selecionaram a exposição do próprio mês sem defasagens adicionais. Isso
não significa que atrasos climáticos não existam. O BIC penaliza cada
coeficiente adicional; há 48 meses de treino no recorte pré e 95 no
total, e blocos longos têm baixa relação observações/parâmetros.
Também não é uma busca livre por atrasos isolados: o bloco K=17 inclui
**todos** os lags de 0 a 17, e não apenas o lag17.

### Comparação por tipologia

Os números abaixo mostram **quantas aplicações UF/período** favoreceram
cada tipo pelo BIC de treino. Trata-se de uma comparação descritiva de
ganhos relativos ao SARIMA, e não um ranking de efeito/causalidade.

| Tipologia | Modelos estimáveis | Casos com ΔBIC negativo | Casos com RMSE melhor |
|---|---:|---:|---:|
| Enxurradas | 41 | **5** | 14 |
| Estiagem e seca | 49 | **4** | 14 |
| Chuvas intensas | 45 | **3** | 15 |
| Inundações | 44 | 2 | 19 |
| Erosão | 36 | 2 | 18 |
| Movimento de massa | 36 | 2 | 14 |
| Doenças infecciosas | 13 | 2 | 8 |
| Vendavais e ciclones | 38 | 1 | 15 |
| Alagamentos | 46 | 1 | 12 |
| Outras tipologias (cada uma) | 3 a 29 | 0 | variável |

As demais sete tipologias são: outros, granizo, incêndio florestal,
tornado, onda de frio, onda de calor/baixa umidade e rompimento de
barragens. A quantidade de modelos estimáveis varia muito; comparar
somente contagens sem denominadores pode induzir interpretações
incorretas.

Entre os 22 casos com BIC favorável, **apenas quatro também diminuíram
o RMSE de teste**. Exemplos: enxurradas em PE selecionou K=0 nos dois
períodos e melhorou o BIC (ΔBIC −4,44 no pré; −2,87 no total), mas
piorou o RMSE em 4,76% e 1,85%, respectivamente. Já inundações em RR
pré selecionou K=17, com forte ganho aparente de BIC (−41,13), porém
**RMSE 184,32% pior**, ilustrando a instabilidade de um bloco longo.

Seis somas de coeficientes individuais apresentaram q-BH exploratório
menor que 0,05: PE/enxurradas no pré; AL/chuvas intensas,
AP/doenças infecciosas, PE/enxurradas, RN/chuvas intensas e
RS/incêndio florestal no total. Porém RN e RS não tiveram ΔBIC
favorável e nenhum desses seis resultados constitui uma conclusão
causal ou uma inferência que incorpore a seleção de K. Residual de
alguns ajustes também indica autocorrelação, o que reforça a cautela.

### Modelo geral por UF/período

O geral usa, em conjunto, as tipologias com seus **K individuais
selecionados**. Se não houver posto completo, suporte ou graus de
liberdade, são excluídas as combinações que impedem estimação;
as exclusões ficam explícitas em `geral.csv`. **Não foi aplicado um
limite arbitrário de quatro ou seis tipologias**. Foram feitas 56
tentativas, com **55 modelos gerais estimados**; somente DF no pré
não apresentou nenhuma tipologia individual estimável. Média de tipos
incluídos por geral estimado: 7,19 (pré) e 9,21 (total).

| Indicador geral | Pré-pandemia | Total |
|---|---:|---:|
| Modelos estimados | 27 de 28 | 28 de 28 |
| Geral com ΔBIC favorável | **1** | **0** |
| Geral com RMSE melhor em teste | 5 | 5 |
| Tipologias incluídas (mín.–máx.) | 2–16 | 1–16 |

O único caso com BIC favorável foi **RR pré**, reunindo inundações
(K=17) e estiagem e seca (K=0): ΔBIC=−42,49, mas RMSE de teste
**185,59% pior** que o SARIMA. Os dez casos com RMSE favorável
não tiveram BIC favorável. Logo, não houve ganho preditivo robusto,
simultaneamente sustentado por BIC e RMSE, para o modelo geral.

### Agregado nacional: as 16 tipologias simultâneas

No agregado Brasil, **todas as 16 tipologias puderam ser incluídas**
com seus K individuais; são 18 regressoras climáticas no pré
(alagamentos e estiagem/seca com K=1; outras 14 com K=0) e 16 no
período total (todos K=0). Essa estimabilidade não contradiz a
inviabilidade de impor blocos longos às 16 tipologias em muitas UFs:
o número de colunas aqui é muito menor.

| Brasil | Pré-pandemia | Período total |
|---|---:|---:|
| Tipologias no geral | 16 | 16 |
| BIC do SARIMA | 214,69 | 459,74 |
| BIC do SARIMAX | 261,74 | 518,63 |
| ΔBIC (SARIMAX − SARIMA) | **+47,04** | **+58,90** |
| Variação de RMSE (melhora %) | **−64,43%** | **−26,78%** |

O resultado agregado nacional **não favorece o SARIMAX geral**:
acrescentar as exposições piorou tanto o ajuste penalizado no treino
quanto o desempenho no teste nos dois recortes.

### Conclusão e cuidados para a monografia

1. O exercício sistemático ampliou a busca anterior, que usava apenas
   blocos até três lags e limitava tipologias. Agora a escolha é de
   K=0 a24 **individualmente** para todos os tipos possíveis e o
   geral incorpora os K selecionados, sem teto prévio de tipos.
2. Nos modelos individuais estimáveis, **K=0 predominou**. O resultado
   é compatível com a preferência penalizada por modelos curtos, mas
   não demonstra que os desastres só importam contemporaneamente.
3. Há ganhos pontuais por BIC e RMSE, mas raramente coincidentes. O
   SARIMAX geral, em especial o nacional, **não apresentou ganhos
   consistentes** sobre o SARIMA de referência.
4. A tipologia com mais casos favoráveis pelo BIC foi **enxurradas**
   (cinco), seguida por estiagem/seca (quatro), mas diferenças de
   suporte e preditores omitidos **impedem chamar qualquer uma delas
   de tipologia de maior impacto**.
5. As conclusões são associativas, condicionais aos modelos, à
   informação climática contemporânea disponível no teste e à
   seleção por BIC; pré/total se sobrepõem. A checagem de dependência
   residual e a validação fora da amostra limitam a interpretação de
   rejeições isoladas.

### Sensibilidade posterior: excluir os lags 0, 1 e 2

Foi acrescentada a análise com **somente as defasagens 3 a K**,
mantendo intactos os resultados deste documento. A comparação
pareada dos dois protocolos, incluindo os indicadores de BIC e RMSE
por UF, período e tipologia, está em
[`sarimax_sensibilidade_3a24_20261026.md`](sarimax_sensibilidade_3a24_20261026.md).
