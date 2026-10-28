# SARIMAX estadual — busca sistemática de defasagens climáticas (26/10/2026)

> **Escopo desta nota:** a busca dos quatro blocos foi executada com **subconjuntos de tipologias elegíveis** (até 4 no pré e 6 no total). O resultado de 53 aplicações selecionando o bloco contemporâneo não corresponde a modelos com as 16 tipologias simultâneas. Uma [auditoria complementar](sarimax_16_tipologias_estimabilidade_20261026.md) tentou incluir as 16 obrigatoriamente: apenas quatro das 216 matrizes estaduais foram identificáveis, todas de MG/total. As análises são complementares e nenhuma substitui automaticamente a outra.

## 1. Por que revisar a escolha dos atrasos?

Na sensibilidade anterior, os três conjuntos `[0]`, `[0,1]` e `[0,1,3]`
foram escolhidos manualmente. Em particular, a ausência de `t−2` impedia
afirmar que uma busca por blocos consecutivos havia sido feita. A presente
revisão **substitui essa comparação como sensibilidade de lags de referência**,
mas preserva o script e os CSVs antigos para auditoria. A etapa principal
SARIMA/SARIMAX e os DLMs não foram reestimados nesta revisão.

Esta é uma busca sistemática **condicional a um horizonte curto e à grade
explicitada abaixo**. Não se afirma ter encontrado o conjunto globalmente
ótimo de atrasos nem o melhor atraso de cada tipologia isoladamente.

## 2. Pergunta, séries e grade

Cada UF/período recebe **um único SARIMAX multivariado** com as tipologias
climáticas elegíveis simultaneamente; não se estimam 16 modelos separados.

- Resposta: `Y_it = 100 · Δlog(I_it)`, sendo `I` a taxa de inadimplência.
- Regressoras: `X_ijt = Δlog(1 + D_ijt)` para cada tipologia `j` elegível.
- SARIMA de referência: uma das cinco ordens sazonais parcimoniosas (s=12),
  escolhida por menor **BIC no treinamento comum**.
- Horizonte máximo **previamente fixado em três meses**. Trata-se de uma
  sensibilidade de curto prazo, interpretável diante da amostra estadual:
  ampliar K aumenta várias regressoras de uma vez e reduz a precisão.

| Nome no código | Regressoras **por tipologia** | Nº de coeficientes climáticos com `m` tipologias |
|---|---|---:|
| `l0` | `X_t` | `m` |
| `l0_1` | `X_t, X_(t−1)` | `2m` |
| `l0_1_2` | `X_t, X_(t−1), X_(t−2)` | `3m` |
| `l0_1_2_3` | `X_t, X_(t−1), X_(t−2), X_(t−3)` | `4m` |

Os quatro modelos são **aninhados e consecutivos**. Todos usam os mesmos
meses de treino, a mesma ordem SARIMA de base e as mesmas tipologias, para
que a comparação de BIC tenha fundamento. O modelo selecionado é o
**SARIMAX convergido com menor BIC de treino**; empate é resolvido pelo
menor K. O BIC é `−2 logLik + p log(n)`, portanto cada lag adicionado
para `m` tipologias custa aproximadamente `m log(n)` pontos de penalidade
antes de considerar o ganho de verossimilhança.

### Amostra e proteção contra uso do teste na escolha

| Recorte | Treino comum, após reservar três meses | Teste cronológico |
|---|---:|---:|
| Pré-pandemia | 69 meses | 12 meses (fev/2019–jan/2020) |
| Completo | 116 meses | 24 meses (jan/2023–dez/2024) |

Os primeiros três meses são reservados **até mesmo para o candidato `l0`**;
assim não há comparação artificialmente favorável aos blocos curtos por
terem mais observações. Os testes só avaliam o modelo **após a escolha**;
nem o RMSE, nem seus desfechos, nem os valores-p são usados para selecionar
a ordem temporal, as tipologias ou K.

## 3. Controle de parâmetros e estimabilidade

As 16 tipologias são avaliadas em cada treino. Um subconjunto *único* de
tipologias é definido antes de ajustar os quatro blocos:

1. Ordenar tipologias pela quantidade de meses com registros positivos no
   treinamento comum (desempate pela ordem original das colunas).
2. Exigir pelo menos **três meses com registros positivos** no treinamento.
3. Verificar a matriz do **maior bloco (0 a 3)**: colunas não constantes,
   posto completo e número de condição após padronização até **1.000**.
4. Aplicar um limite explícito de complexidade, sem usar a inadimplência:

   `m ≤ min(limite anterior, floor((n_treino − 5)/(4 × 4)))`.

   A heurística reserva cinco observações para termos temporais e exige
   **no mínimo quatro observações de treino por coeficiente climático do
   bloco máximo**. Portanto, o limite é de **quatro tipologias no pré** e
   **seis no período completo**; pode haver menos por falta de suporte.

Essa regra é uma **restrição prática de parcimônia**, não um teorema que
garante tamanho amostral ideal, precisão, inferência seletiva nem ausência
de sobreajuste. Uma tipologia rara pode não entrar; isso limita o alcance
dos resultados e deve ser dito explicitamente. Como se mantém **o mesmo
subconjunto para todos os K**, o BIC compara efeitos de lags, não mudanças
simultâneas na composição de tipologias. Sem observação elegível, a
aplicação é registrada como não estimável.

Após a auditoria, as séries X são padronizadas com média/desvio apenas do
treino para melhorar a otimização; coeficientes são devolvidos à escala
original na saída. A seleção da ordem temporal toma como referência as
cinco tentativas SARIMA previamente auditadas na **mesma amostra**,
reajusta a vencedora e **confere numericamente seu BIC** antes de ajustar
os quatro SARIMAX, todos por máxima verossimilhança (`statsmodels`).

## 4. Resultados verificados

| Indicador | Pré | Completo | Total |
|---|---:|---:|---:|
| Aplicações UF × período | 27 | 27 | 54 |
| SARIMAX estimáveis | 26 | 27 | **53** |
| Candidatos SARIMAX convergidos (4 por aplicação) | 104 | 108 | **212** |
| BIC escolheu `l0` | 26 | 27 | **53** |
| BIC escolheu algum lag positivo | 0 | 0 | **0** |
| SARIMAX escolhido com BIC menor que SARIMA | 0 | 0 | **0** |
| SARIMAX com RMSE condicional menor que SARIMA | 9 | 10 | **19** |
| Mediana da melhora de RMSE | −1,97% | −3,44% | **−2,34%** |

O único caso sem tipologia elegível no treino foi **DF, pré-pandemia**.
Cada um dos **212 ajustes** SARIMAX convergiu. Em todos os 53 casos, o BIC
selecionou `l0` com coeficientes apenas contemporâneos. A diferença de
BIC entre o primeiro e o segundo colocados climáticos variou de **2,68 a
26,77** pontos (mediana **14,80**). Assim, a escolha por `l0` não decorreu
da ausência de `t−2` na grade anterior, de amostras desiguais ou de
falhas de convergência dos blocos mais longos.

**Em comparação ao SARIMA sem X:** nenhum dos 53 SARIMAX selecionados
ganhou em BIC (diferença `BIC_SARIMAX − BIC_SARIMA` sempre positiva, de
**2,11 a 26,97**). A melhora de RMSE foi favorável ao SARIMAX em 19/53
testes, mas **a mediana geral de −2,34%** indica piora típica do erro
de previsão condicional. O ganho em 19 testes não reverte a conclusão
do BIC, que considera ajuste e complexidade *dentro do treino*.

Os modelos selecionados preservaram **dois coeficientes individuais** de
Enxurradas em Pernambuco com `q<0,05` após BH global das 240 estimativas
climáticas: `β_0≈1,195` (pré, `q≈0,019`) e `β_0≈0,791` (total,
`q≈0,019`). **Nenhum teste climático conjunto** permaneceu rejeitado
após BH (`q` mínimo ≈ 0,657). Os dois recortes são sobrepostos e a
inferência individual continua **exploratória após seleção**; BH não
corrige a busca adaptativa da ordem, das tipologias e da defasagem.

### Ressalva indispensável: autocorrelação dos resíduos

O teste de Ljung–Box com **12 atrasos sobre inovações padronizadas e ajuste
dos graus de liberdade ARMA** rejeitou a hipótese de ausência de
autocorrelação em **39/53 SARIMAX selecionados** (`p<0,05`), contra
**25/53 SARIMA** no mesmo diagnóstico. Este não é o mesmo indicador da
revisão anterior, que usou resíduos brutos e não ajustou os graus de
liberdade (9/53 rejeições); **os dois números não são diretamente
comparáveis**. A sensibilidade ao diagnóstico exige cautela: os modelos
selecionados não devem ser apresentados como universalmente adequados,
e os testes dos coeficientes são ainda mais frágeis quando sobra
autocorrelação residual. Antes de sustentar inferência substantiva desses
coeficientes, é recomendável auditar a dinâmica temporal em casos com
Ljung–Box rejeitado. Essa ressalva não muda os BICs e RMSEs calculados.

## 5. O que a escolha por `l0` permite concluir — e o que não permite

**Permite concluir:** entre os quatro blocos consecutivos, para os
subconjuntos de tipologias elegíveis e ordens temporais pré-selecionadas,
o ganho de verossimilhança não compensou a penalização do BIC ao incluir
lags de 1, 2 ou 3 meses. Há pouco suporte para ampliar conjuntamente
todos os tipos elegíveis nesse alcance.

**Não permite concluir:** inexistência de efeitos atrasados por tipologia,
ausência de efeitos após o terceiro mês, ótimo global de lags nem efeito
causal nulo. Como um novo atraso adiciona um coeficiente **para cada
tipologia de uma vez**, um sinal esparso (por exemplo, de apenas uma
tipologia) pode não justificar o custo do bloco completo. Seleção
específica por tipo, regularização e validação temporal aninhada poderiam
responder a outras perguntas, mas mudariam a complexidade/metodologia;
não foram implementadas aqui.

O teste usa previsões condicionais de **um passo à frente com Y anterior
observado e X contemporâneo conhecido**. Portanto, não mede previsão
realizada antes de saber se houve desastres no próprio mês. A etapa
complementar nacional com 16 exposições contemporâneas não foi alterada.

## 6. Reprodução e arquivos

Na raiz do repositório, após instalar as dependências e disponibilizar a
base auditada, executar:

```bash
python src/sarimax_lags_sistematicos.py
```

Para uma UF/recorte: `python src/sarimax_lags_sistematicos.py --periodo Pré --uf AC`.
Por padrão, uma UF/período já registrada é mantida. Para **reestimar
explicitamente** os recortes escolhidos: acrescentar `--refazer`.

Entradas necessárias: a base
`data/processed/df_tcc_2013_2024.csv` com SHA-256
`46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36`
e a tabela de ordens SARIMA auditadas em
`outputs/tables/sarimax_defasagens_20261024/candidatos.csv`.

Arquivos desta revisão, separados dos históricos:

| Arquivo | Conteúdo |
|---|---|
| [`src/sarimax_lags_sistematicos.py`](../src/sarimax_lags_sistematicos.py) | Execução reproduzível e critérios |
| [`comparacao.csv`](../outputs/tables/sarimax_lags_sistematicos_20261026/comparacao.csv) | Um registro por UF/recorte, métricas e diagnóstico |
| [`candidatos.csv`](../outputs/tables/sarimax_lags_sistematicos_20261026/candidatos.csv) | SARIMA de referência e **quatro** SARIMAX por aplicação |
| [`coeficientes.csv`](../outputs/tables/sarimax_lags_sistematicos_20261026/coeficientes.csv) | Coeficientes, atrasos e BH global |
| [`resumo.json`](../outputs/tables/sarimax_lags_sistematicos_20261026/resumo.json) | Metadados da grade e síntese auditável |

O DLM **permanece na grade principal K=1,...,24 por AIC**; a inclusão de K=0 foi avaliada em auditoria separada, sem alterar a grade principal. O Driscoll–Kraay continua sendo
uma escolha de **covariância para inferência do DLM**, não uma correção ou
seleção de lags do SARIMAX.
