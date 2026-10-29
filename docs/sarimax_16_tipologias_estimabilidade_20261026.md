# SARIMAX com as 16 tipologias simultâneas — auditoria de estimabilidade

**Data:** 26/10/2026. **Escopo:** análise estadual por UF e período, comparando
SARIMA e SARIMAX sazonal com defasagens climáticas consecutivas.

## 1. Objetivo e condições de estimabilidade

O objetivo é verificar se é possível **incluir as 16 tipologias de desastres
simultaneamente, sem nenhuma exclusão**, em cada SARIMAX estadual. Isso não
equivale a "testar as 16 candidatas e usar um subconjunto", como na análise
anterior. Esta execução não seleciona tipologias por frequência, não fixa um
teto de 4/6 ou 9/12 e não substitui tipos raros por zeros artificiais.

Antes de ajustar um SARIMAX é indispensável verificar se as regressoras
podem ser identificadas separadamente. Quando uma tipologia não varia no
treino, a coluna correspondente é constante; quando existe dependência
linear, combinações distintas de coeficientes geram a mesma contribuição.
Nesses casos, não existe uma estimativa única e interpretável dos
coeficientes das 16 tipologias na especificação avaliada. A rotina
**registra a impossibilidade** em vez de excluir silenciosamente colunas
ou interpretar um ajuste singular como evidência estatística.

## 2. Transformações, períodos e quatro blocos

Mantiveram-se exatamente as variáveis das etapas anteriores:

- Resposta estadual: `100·Δlog(I_t)`.
- Exposição `j`: `X_jt=Δlog(1+D_jt)`.
- Sazonalidade anual SARIMA (12 meses); a ordem temporal de referência é
  selecionada entre cinco candidatas auditadas pelo BIC do treino comum.
- Treino comum com os três primeiros meses reservados: **69** observações
  no pré e **116** no período completo; testes cronológicos de **12** e
  **24** meses, respectivamente.
- O mesmo conjunto **completo de 16 tipologias** entra em cada candidato,
  quando o ajuste é identificável.

| Bloco de lags para cada uma das 16 tipologias | Coeficientes climáticos |
|---|---:|
| `[0]` | 16 |
| `[0,1]` | 32 |
| `[0,1,2]` | 48 |
| `[0,1,2,3]` | 64 |

Além desses coeficientes climáticos, o SARIMAX estima parâmetros temporais
e de variância. Em particular, **64 regressoras climáticas e 69 meses de
treino** seria uma especificação muito carregada, ainda que a matriz tivesse
posto completo. A tentativa de inclusão conjunta é feita apenas quando
há observações suficientes para identificar os parâmetros.

## 3. Auditoria de todas as UF × período × bloco

Para cada uma das **216 matrizes candidatas** (27 UFs × 2 períodos ×
4 blocos), o script construiu as 16×(K+1) colunas e conferiu no treino:

1. colunas com desvio-padrão praticamente nulo;
2. posto completo do conjunto de regressoras;
3. condicionamento da matriz padronizada até 1.000;
4. quantidade de observações superior ao número de regressoras, com uma
   reserva de cinco observações para a dinâmica temporal.

Não houve triagem pela resposta, valor-p, RMSE ou BIC. **O BIC só é calculado
quando é possível estimar o modelo.**

| Bloco | Viáveis no pré (27) | Viáveis no completo (27) | Total viável (54) |
|---|---:|---:|---:|
| `[0]` | 0 | 1 | 1 |
| `[0,1]` | 0 | 1 | 1 |
| `[0,1,2]` | 0 | 1 | 1 |
| `[0,1,2,3]` | 0 | 1 | 1 |
| **Total** | **0/108** | **4/108** | **4/216** |

**Resultado:** somente **Minas Gerais no período completo** apresentou
as 16 tipologias conjuntamente identificáveis em todos os quatro blocos.
Em **53 de 54 aplicações** não foi possível estimar a grade completa com
as 16 tipologias simultâneas. Nas demais **212 matrizes**, a falta de
variação e/ou de posto completo impede a estimação conforme proposta.

Exemplos concretos no bloco `[0]`:

- No pré, a mediana estadual foi de **6 tipologias sem variação** e o
  posto mediano da matriz foi **10**, em vez dos 16 necessários.
- No período completo, as medianas foram **4 tipologias sem variação** e
  **posto 12**.
- No DF, pré-pandemia, **14 das 16** exposições contemporâneas não
  apresentaram variação no treino (posto 2).
- MG, no período completo, teve posto **16 de 16** no contemporâneo e
  **64 de 64** no bloco de até três meses, com números de condição
  aproximadamente 4,14 e 20,38.

Não é correto preencher com zeros novas observações onde a exposição já
é genuinamente zero, remover colunas sem explicar ou usar inversa
generalizada para afirmar que todas as 16 contribuições individuais
foram identificadas. A ausência de estimabilidade **não equivale à
ausência de associação climática**.

## 4. Ajustes completos possíveis: Minas Gerais, período completo

Foram estimados por máxima verossimilhança os quatro SARIMAX com **todas
as 16 tipologias** e, como controle, o SARIMA com a mesma ordem temporal
e amostra comum. Os quatro modelos SARIMAX obtiveram convergência final;
nos blocos maiores, a otimização precisou de nova tentativa, reforçando
a necessidade de cautela sobre estabilidade numérica.

| Modelo | Nº de coeficientes climáticos | BIC de treino | ΔBIC contra SARIMA | RMSE de teste | Melhora de RMSE |
|---|---:|---:|---:|---:|---:|
| SARIMA (sem clima) | 0 | **560,43** | — | 1,355 | — |
| SARIMAX `[0]` | 16 | 625,27 | +64,84 | **1,293** | **+4,57%** |
| SARIMAX `[0,1]` | 32 | 658,82 | +98,39 | 5,779 | −326,47% |
| SARIMAX `[0,1,2]` | 48 | 701,84 | +141,41 | 6,400 | −372,35% |
| SARIMAX `[0,1,2,3]` | 64 | 724,53 | +164,10 | 9,207 | −579,46% |

O `[0]` foi o melhor SARIMAX pelo BIC, mas **nenhum dos quatro modelos
climáticos superou o SARIMA no BIC**. O `[0]` apresentou melhora de RMSE
de 4,57% na previsão condicional; os blocos longos tiveram grande piora
de RMSE. O BIC compara ajuste e penalização de complexidade no treino,
enquanto o RMSE avalia erro preditivo no teste. A seleção de K não usa
informação do teste.

### Diagnóstico residual

O Ljung–Box no lag 12 foi aplicado às inovações padronizadas, com ajuste
de graus de liberdade **apenas para termos ARMA (`p+q+P+Q`)**. Descontar
os 16–64 coeficientes exógenos de 12 graus de liberdade tornaria o
teste indefinido; por isso a definição do diagnóstico é explícita.

| Modelo | p do Ljung–Box (lag 12) |
|---|---:|
| SARIMA | 0,0068 |
| SARIMAX `[0]` | 0,0727 |
| SARIMAX `[0,1]` | 0,0943 |
| SARIMAX `[0,1,2]` | 0,0159 |
| SARIMAX `[0,1,2,3]` | 0,0053 |

A 5%, o teste rejeita ausência de autocorrelação no SARIMA e nos dois
SARIMAX mais longos. Isso é uma limitação adicional de adequação residual.
O conjunto completo de diagnósticos e warnings está disponível nos CSVs.
Todos esses resultados correspondem **somente a MG no período completo**;
não podem ser generalizados para o país ou para os demais estados.

## 5. Relação com as análises anteriores

| Execução | O que significou "considerar 16 tipologias" | Limitação |
|---|---|---|
| SARIMAX estadual original | 16 candidatas, subconjunto simultâneo com máximo de 9 no pré/12 no completo | Nem todas entraram; triagem por suporte/condicionamento e teto |
| Sensibilidade sistemática anterior | 16 candidatas, subconjunto simultâneo com máximo de 4 no pré/6 no completo | Grade 0–3 estimável em 53 casos; recorte favorece tipologias mais frequentes |
| **Auditoria atual** | **Exige todas as 16 simultaneamente em todos os blocos, sem exclusões** | Identificável somente em MG/total; não se obtém painel de 54 resultados |
| Nacional complementar anterior | 16 exógenas simultâneas no agregado nacional, condicionadas a posto e condicionamento | Não substitui heterogeneidade estadual nem resolve defasagens por UF |

A regra de 4/6 tipologias da sensibilidade anterior era uma heurística
de parcimônia; não constitui número teoricamente obrigatório ou ótimo.
Porém, a análise restrita respondeu a uma pergunta **diferente** da
imposição das 16 tipologias. Não se deve afirmar que 53/53 modelos com
"todas as 16" selecionaram `[0]`: esse resultado vinha dos **subconjuntos
elegíveis**. Na execução com 16 obrigatórias, só existe um caso estadual
estimável.

## 6. Questões metodológicas

1. **Unidade de análise.** Diante da impossibilidade de identificar as
   16 tipologias simultaneamente na maioria das UFs, o SARIMAX estadual
   deve continuar multivariado com os subconjuntos estimáveis? Nesse caso,
   quais regras de exclusão e limites de complexidade são justificáveis?
2. **Tipologias raras.** Convém incluir uma análise complementar por
   tipologia, com as mesmas transformações e divisão temporal, para
   observar atrasos de eventos raros que ficam fora dos modelos conjuntos?
3. **Agregação prévia.** Faz sentido trabalhar com conjuntos de tipos
   definidos substantivamente pela classificação COBRADE, reduzindo
   a quantidade de exógenas, sem escolher grupos pelos valores-p?
4. **Escopo nacional e estadual.** O modelo nacional com 16 exógenas pode
   ser apresentado como análise multivariada completa e a análise
   estadual como heterogeneidade condicionada à estimabilidade?
5. **Adequação temporal.** Que revisão das ordens SARIMA e dos resíduos é
   necessária antes de interpretar testes de significância climática?
6. **Objetivo principal.** Queremos avaliação de ganho preditivo
   condicional (com `X_t` observado), associações temporais ou previsão
   genuinamente antecipada sem informação climática do próprio mês?

Não foi escolhida uma nova especificação definitiva nesta auditoria.
As alternativas mudariam a pergunta e/ou a inferência e devem ser
discutidas antes de serem incorporadas à análise principal.

## 7. Reprodução

Com a base auditada no caminho indicado, a partir da raiz do repositório:

```bash
python src/sarimax_todas_tipologias_20261026.py --somente-auditoria
python src/sarimax_todas_tipologias_20261026.py
```

Entradas: `data/processed/df_tcc_2013_2024.csv` (SHA-256
`46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36`)
e `outputs/tables/sarimax_defasagens_20261024/candidatos.csv` para recuperar
a seleção histórica da ordem SARIMA sobre exatamente a mesma amostra.

Saídas distintas, preservando integralmente os resultados anteriores:

- `outputs/tables/sarimax_todas_tipologias_20261026/auditoria.csv`:
  todas as 216 matrizes, posto, constância, condicionamento e motivos;
- `.../ajustes.csv`: SARIMA e os quatro SARIMAX estimados no caso viável;
- `.../coeficientes.csv`: coeficientes dos quatro modelos de MG,
  exploratórios e sem inferência pós-seleção;
- `.../resumo.json`: protocolo e contagens.

O DLM e sua grade principal `K=1..24` não foram alterados; incluir `K=0`
é discutida separadamente na auditoria de defasagens.
