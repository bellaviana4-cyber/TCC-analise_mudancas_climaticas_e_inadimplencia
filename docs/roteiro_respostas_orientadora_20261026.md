# Revisão para orientação — defasagens, DLM e SARIMAX

**TCC:** Mudanças Climáticas e Inadimplência: uma análise do impacto de desastres naturais no sistema de crédito brasileiro.  
**Atualizado em:** 26/10/2026.  
**Status:** o registro original abaixo foi preservado como histórico; a sensibilidade SARIMAX sistemática foi executada e auditada posteriormente no mesmo dia.

## Atualização complementar — tentativa com todas as 16 tipologias

A busca sistemática anterior utilizava subconjuntos de até quatro tipologias no pré e seis no total. Para verificar a exigência de **16 tipologias simultâneas, sem exclusões**, foi auditado um conjunto de **216 matrizes estaduais** (54 aplicações × quatro blocos 0–3), conferindo constância, posto, condicionamento e tamanho amostral.

- **212/216 matrizes não identificáveis** com as 16 tipologias completas; não é possível atribuir BIC a essas especificações.
- **4/216 identificáveis**, todas em MG no período completo; os quatro SARIMAX convergiram.
- Em MG/total, o bloco contemporâneo teve menor BIC entre os SARIMAX, mas **nenhum superou SARIMA em BIC**. O contemporâneo melhorou RMSE em 4,57%, enquanto os blocos defasados apresentaram piora forte.
- A inviabilidade das outras UFs não é evidência de ausência de associação, mas de colunas sem variação e dependência linear no treino.
- A escolha entre SARIMAX estadual com tipos elegíveis, análises por tipologia, agrupamentos COBRADE ou abordagem nacional continua como **questão para a orientação**.

Ver [método e resultados completos](sarimax_16_tipologias_estimabilidade_20261026.md), o script de estimação e [as tabelas auditáveis](../outputs/tables/sarimax_todas_tipologias_20261026/). O DLM permanece inalterado.

---

## Atualização executada — seleção sistemática de lags SARIMAX

A seção histórica sobre os blocos `[0]`, `[0,1]` e `[0,1,3]` documenta **a primeira revisão, agora substituída como sensibilidade de referência**. Sua limitação era não testar sistematicamente o lag 2. A revisão executada usou:

1. **Horizonte curto pré-fixado: 0 a 3 meses**, com os quatro blocos consecutivos `[0]`, `[0,1]`, `[0,1,2]`, `[0,1,2,3]`.
2. **Mesmo treino** (69 meses pré, 116 total), **mesma ordem SARIMA** e **mesmo conjunto de tipos climáticos para cada UF/recorte** em todos os blocos; ordem SARIMA do menor BIC entre cinco opções, reajustada e verificada.
3. **Limite de parâmetros climáticos** do maior bloco: ao menos quatro observações de treino por coeficiente, com reserva de cinco para a dinâmica temporal. Máximo de 4 tipologias no pré e 6 no completo; suporte, posto e condicionamento auditados só no treino.
4. **Seleção por BIC de treino** e avaliação RMSE/MAE exclusivamente nos testes cronológicos. Ainda é previsão condicional de um passo com exposição `X_t` conhecida.

**Resultados auditados:** 54 aplicações, 53 estimáveis, **212 ajustes SARIMAX convergidos**; todos os 53 selecionaram `[0]`, 0/53 melhor BIC que SARIMA, **19/53** melhor RMSE, mediana da melhora **−2,34%**. A diferença entre primeiro e segundo BIC climático variou **2,68–26,77** (mediana 14,80). Testes conjuntos BH a 5%: 0; coeficientes individuais BH global: 2 (Enxurradas/PE, pré e total, exploratórios).

**Limitação importante:** o Ljung–Box de 12 meses aplicado às **inovações padronizadas**, ajustando graus de liberdade ARMA, rejeitou em **39/53** SARIMAX selecionados. O número anterior (9/53) veio de outra definição de resíduos/teste; não são diretamente comparáveis. Antes de defender inferência dos coeficientes, essa inadequação residual precisa ser discutida e auditada.

O processo e suas limitações estão descritos detalhadamente em [SARIMAX — busca sistemática de lags](sarimax_busca_sistematica_lags_20261026.md), código `src/sarimax_lags_sistematicos.py` e [tabelas de saída](../outputs/tables/sarimax_lags_sistematicos_20261026/). **O DLM permanece com K=1,...,24 por AIC**, e incluir K=0 segue apenas como pergunta para a orientadora; os horizontes fixos de DLM não foram adotados.

---

## 1. Contexto e decisões adotadas

O painel mensal reúne 27 UFs e 144 meses (2013–2024; 3.888 observações).
A base auditada tem SHA-256 `46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36`.
Foram consideradas 16 tipologias operacionais de desastres. Analisamos
um recorte pré-pandemia (até janeiro de 2020) e o período completo
(até dezembro de 2024); **os recortes são sobrepostos**.

Etapas complementares:
- **Granger:** precedência preditiva das exposições em relação à variação da inadimplência.
- **DLM em painel:** associação contemporânea e defasada, com efeitos fixos de UF e mês-ano (TWFE).
- **SARIMA/SARIMAX:** acréscimo de informação climática ao ajuste e à previsão condicional.

Não se deve atribuir interpretação causal às três etapas isoladamente.
O DLM principal permanece com seleção de `K=1,...,24` por **AIC**,
incluindo comparação dos dois primeiros colocados. **Não adotamos
horizontes fixos de 6 ou 12 meses**. A comparação `K=0` é somente
uma auditoria da restrição inferior da grade, sem substituição automática
do modelo principal.

## 2. DLM: seleção de K e comparação dos dois menores AICs

Para uma tipologia e período, estimamos o DLM:

`Δlog(I_it) = α_i + λ_t + Σ[k=0..K] β_k Δlog(1+D_i,t−k) + ε_it`.

`α_i` representa o efeito fixo de UF; `λ_t` representa o efeito fixo
de mês-ano. Todos os K de 1 a 24 foram estimados **na mesma amostra**
para tornar os AICs comparáveis (60 meses úteis no pré e 119 no total).

**O que encontramos:**
- 29 das 32 combinações de tipologia × período tiveram suporte suficiente.
- O menor AIC escolheu `K=1` em 21/29 casos; nos outros oito escolheu K maior.
- Os 29 segundos menores AICs ficaram a `ΔAIC < 2` do primeiro
  (mínimo 0,0618; máximo 1,9966).
- A escolha principal continua sendo o primeiro K, e o segundo é
  uma análise da sensibilidade de especificação.

**Por que a proximidade não é prova de dois K equivalentes?**
Com a mesma amostra e modelos aninhados, acrescentar um único coeficiente
nunca reduz a máxima verossimilhança. Logo:

`AIC(K+1) − AIC(K) = 2 − 2[logLik(K+1) − logLik(K)] ≤ 2`.

Quando o mínimo está em K menor que 24, seu vizinho K+1 necessariamente
terá uma diferença de AIC de até 2. A proximidade é em parte
**consequência algébrica da grade**, e não teste de significância
da defasagem acrescentada.

### AIC vencedor e segundo menor por tipologia

| Período | Tipologia | Primeiro K | Segundo K | ΔAIC |
|---|---|---:|---:|---:|
| Pré-pandemia | Alagamentos | 1 | 2 | 1,787 |
| Pré-pandemia | Chuvas intensas | 15 | 16 | 0,306 |
| Pré-pandemia | Doenças infecciosas | 1 | 2 | 1,925 |
| Pré-pandemia | Enxurradas | 1 | 2 | 1,721 |
| Pré-pandemia | Erosao | 1 | 2 | 1,983 |
| Pré-pandemia | Estiagem e seca | 1 | 2 | 1,968 |
| Pré-pandemia | Granizo | 1 | 2 | 1,997 |
| Pré-pandemia | Incêndio florestal | 1 | 2 | 1,370 |
| Pré-pandemia | Inundacoes | 1 | 2 | 1,672 |
| Pré-pandemia | Movimento de massa | 1 | 2 | 1,909 |
| Pré-pandemia | Outros | 1 | 2 | 1,680 |
| Pré-pandemia | Tornados | 1 | 2 | 0,062 |
| Pré-pandemia | Vendavais e ciclones | 14 | 9 | 1,942 |
| Completo | Alagamentos | 1 | 3 | 0,589 |
| Completo | Chuvas intensas | 16 | 15 | 0,978 |
| Completo | Doenças infecciosas | 1 | 2 | 1,913 |
| Completo | Enxurradas | 1 | 2 | 1,370 |
| Completo | Erosao | 1 | 2 | 1,932 |
| Completo | Estiagem e seca | 1 | 2 | 1,947 |
| Completo | Granizo | 1 | 2 | 1,986 |
| Completo | Incêndio florestal | 6 | 1 | 0,757 |
| Completo | Inundacoes | 1 | 2 | 0,656 |
| Completo | Movimento de massa | 5 | 4 | 1,478 |
| Completo | Onda de calor e baixa umidade | 14 | 15 | 1,167 |
| Completo | Onda de frio | 1 | 2 | 1,547 |
| Completo | Outros | 1 | 2 | 1,991 |
| Completo | Rompimento/colapso de barragens | 4 | 2 | 0,500 |
| Completo | Tornados | 1 | 2 | 0,904 |
| Completo | Vendavais e ciclones | 9 | 10 | 1,989 |

O código e a tabela auditada estão em
[`src/auditar_dlm_aic_top2.py`](../src/auditar_dlm_aic_top2.py) e
[`outputs/tables/revisao_defasagens_20261024/dlm_dois_menores_aic.csv`](../outputs/tables/revisao_defasagens_20261024/dlm_dois_menores_aic.csv).

### A limitação de começar a grade em K=1

O limite inferior obrigava todos os modelos selecionados a incluir pelo
menos um mês de atraso. Uma auditoria posterior calculou o AIC de K=0
na mesma amostra dos demais candidatos e verificou que o contemporâneo
sozinho teria menor AIC em **18/29** combinações, incluindo **17/21**
que originalmente escolheram K=1.

Isso ajuda a explicar a frequência de K=1. **Não** implica que
vamos escolher K=0 automaticamente, nem demonstra ausência de associação
defasada. A auditoria está isolada em
[`src/auditar_dlm_k0.py`](../src/auditar_dlm_k0.py).

## 3. Por que usamos Driscoll–Kraay (DK) no DLM?

Os coeficientes do DLM são estimados por mínimos quadrados com efeitos
fixos. Entretanto, os resíduos podem apresentar dependência:

1. **Serial:** o erro de uma UF em um mês pode estar relacionado ao
   erro da mesma UF em outro mês.
2. **Transversal:** os erros de UFs distintas no mesmo mês podem
   compartilhar choques nacionais não capturados pela especificação.

A correlação residual absoluta média entre UFs foi aproximadamente
**0,1914 no pré** e **0,1852 no completo**. A magnitude é moderada,
mas não constitui um teste formal de independência; por isso, adotamos
uma covariância robusta a essas formas de dependência.

**O que DK faz:** usa uma estimativa robusta da matriz de covariância
dos coeficientes, agregando contribuições das UFs por mês e ponderando
autocovariâncias temporais por uma janela Bartlett. Essa opção segue
a proposta de Driscoll e Kraay (1998), cuja validade depende de
condições assintóticas, especialmente na dimensão temporal.

- **DK não muda** a equação, os coeficientes MQO, os valores ajustados,
  o AIC nem o K escolhido.
- **DK muda** os erros-padrão, intervalos de confiança, estatísticas
  de teste e valores-p.
- Sem DK, usar os erros-padrão clássicos sob dependência residual pode
  levar a inferência mal calibrada; o uso de DK não resolve endogeneidade
  nem confere interpretação causal.

A **banda L** indica quantos meses de autocovariância dos escores
entram no cálculo da inferência. A regra
`floor(4·(T/100)^(2/9))` resultou em L=3 meses no pré e L=4 no total.
Também avaliamos DK6 e DK12, **como sensibilidade**.

**K é a defasagem máxima da exposição climática no modelo; L é a banda
da covariância DK. São escolhas diferentes.** Não há necessidade de igualar
K e L; nem de escolher DK12 apenas porque as observações são mensais
e possuem sazonalidade anual.

As bandas DK6 e DK12 não aumentaram sempre os erros-padrão. Considerando
o coeficiente contemporâneo `β₀` no primeiro K por AIC, comparado à
banda por regra:
- DK6 apresentou erros-padrão menores em 22/29 casos e maiores em 7/29;
  a mediana da razão `EP(DK6)/EP(regra)` foi 0,975.
- DK12 apresentou erros-padrão menores em 22/29 e maiores em 7/29;
  a mediana da razão `EP(DK12)/EP(regra)` foi 0,958.

Logo, a banda pode **aumentar ou diminuir** o erro-padrão, conforme
a autocorrelação residual estimada. Os números acima dizem respeito
a `β₀` e não devem ser generalizados automaticamente a todos os
contrastes do modelo.

### A conclusão mudou no segundo K?

Refizemos os cinco testes de cada DLM com os dois K:

1. `β₀ = 0` (associação no próprio mês);
2. `Σ₀ᴷ β_k = 0` (soma contemporânea e defasada);
3. `Σ₁ᴷ β_k = 0` (soma apenas defasada);
4. `β₀ = ⋯ = β_K = 0` (conjunto completo);
5. `β₁ = ⋯ = β_K = 0` (conjunto defasado).

Aplicamos proteções conservadoras de multiplicidade para a grade de K
(Bonferroni; para testes conjuntos, união de testes individuais na
grade) e Holm nas famílias de 16 tipologias. Não é inferência seletiva
exata; rejeições são exploratórias.

| Escolha de K | DK por regra | DK6 | DK12 |
|---|---:|---:|---:|
| Menor AIC | 0 | 0 | 7 |
| Segundo menor AIC | 0 | 2 | 4 |

A tabela conta **hipóteses rejeitadas a 5% após os ajustes**,
não o número de tipologias independentes. Sob **DK por regra**, nenhum
dos dois K apresentou rejeições após os ajustes. As rejeições
encontradas sob outras bandas não foram estáveis à banda principal.
Portanto, **a conclusão central não mudou**.

O cálculo está em
[`src/inferencia_dlm_top2_aic.py`](../src/inferencia_dlm_top2_aic.py),
com resumo em
[`outputs/tables/revisao_defasagens_20261024/resumo_inferencia_top2.csv`](../outputs/tables/revisao_defasagens_20261024/resumo_inferencia_top2.csv).

## 4. SARIMAX: como construímos o modelo com defasagens

### Pergunta e transformações

O SARIMA usa somente a dinâmica temporal da resposta. O SARIMAX
acrescenta as exposições climáticas para avaliar informação
explicativa/preditiva incremental.

A resposta estadual foi `Y_it = 100·Δlog(I_it)`.
As exposições por tipologia foram `X_ijt = Δlog(1+D_ijt)`.
O fator 100 facilita a escala da resposta; não converte coeficientes
em pontos percentuais da taxa de inadimplência.

No nacional, calculamos primeiro a taxa a partir da **soma das carteiras**
e os registros de desastre pela **soma entre UFs**; depois aplicamos
as transformações. A análise nacional com todas as 16 tipologias foi
complementar e **não recebeu esta extensão de lags climáticos**.

### Divisão cronológica e modelos temporais

| Período | Treino original | Teste | Treino comum após reservar 3 lags |
|---|---|---|---:|
| Pré | Fev/2013–jan/2019 | Fev/2019–jan/2020 | 69 meses |
| Completo | Fev/2013–dez/2022 | Jan/2023–dez/2024 | 116 meses |

Utilizamos cinco ordens parcimoniosas de SARIMA, com dinâmica sazonal
de 12 meses e d=D=0 após a diferença aplicada externamente.
Escolhemos a ordem de referência pelo BIC no **treino comum**.
Na extensão, mantivemos a mesma ordem temporal em todos os três
candidatos SARIMAX para que a comparação isolasse o acréscimo
das exposições.

### Triagem das 16 tipologias

Para cada UF e período, todas as 16 tipologias são consideradas,
mas só entram as que atendem às regras do treino:
pelo menos três meses positivos, variação, posto completo do maior
bloco de lags, número de condição até 1.000 e limite de 9 tipologias
no pré ou 12 no completo.

A seleção utiliza **apenas dados do treino** e não busca valores-p
pequenos nem melhor RMSE do teste. As tipologias elegíveis entram
simultaneamente em um único SARIMAX multivariado por UF/período.

### Estruturas de lags comparadas

| Nome | Exógenas por tipologia elegível |
|---|---|
| `l0` | `X_t` (contemporânea) |
| `l0_1` | `X_t, X_{t−1}` |
| `l0_1_3` | `X_t, X_{t−1}, X_{t−3}` |

Os lags se referem às séries **já transformadas**, não ao número
de meses desde um registro isolado de desastre. A última estrutura
**não inclui t−2**; não se deve apresentá-la como grade completa
de 0 a 3 meses.

Reservamos os três primeiros meses das séries transformadas para
que os três modelos usem a mesma amostra. Estimamos SARIMA e SARIMAX
com `statsmodels`, parâmetros do treino, intercepto e restrições
usuais de estacionariedade e invertibilidade dos componentes ARMA.
Todas as 159 estimações SARIMAX candidatas (53 casos × 3 blocos)
convergiram.

O bloco vencedor é o de menor BIC de treinamento. Para comparar
previsão, usamos RMSE e MAE no teste cronológico, com predição
**condicional de um passo**: atualiza-se o estado com inadimplência
observada em `t−1` e, quando há `X_t`, com a exposição
climática já observada no próprio mês `t`.
**Isso não representa previsão ex ante dos desastres**.

### Defasagens escolhidas e resultados

| Resultado | Pré | Completo | Total |
|---|---:|---:|---:|
| Aplicações planejadas | 27 | 27 | 54 |
| Estimáveis | 26 | 27 | 53 |
| BIC escolheu só `X_t` | 26 | 27 | **53** |
| SARIMAX com BIC inferior ao SARIMA | 0 | 0 | **0** |
| SARIMAX com RMSE inferior ao SARIMA | 8 | 8 | **16** |
| Mediana da melhora percentual do RMSE | −6,70% | −9,01% | **−7,59%** |

DF/pré não apresentou tipologia elegível. A mediana negativa significa
que, no caso típico, **o RMSE do SARIMAX foi maior**.
O SARIMAX não apresentou ganho consistente de parcimônia nem previsão
na extensão avaliada.

### Testes e diagnósticos

No modelo escolhido:
- Nenhum teste conjunto de exógenas resistiu à correção BH.
- Dois coeficientes individuais resistiram a BH global: Enxurradas em
  Pernambuco no pré (aprox. 1,195) e completo (aprox. 0,845), ambos
  contemporâneos e positivos, mas **os dois modelos pioraram BIC e RMSE**.
- O Ljung–Box nominal em 12 meses rejeitou ausência de autocorrelação
  em 9/53 SARIMAX com defasagens: AM, RJ, SE, SP (pré) e
  ES, MA, MS, RJ, SP (completo).

Os testes condicionam-se à escolha anterior das ordens e dos regressores.
BH não torna a inferência seletiva exata; os achados individuais não
identificam efeitos causais.

O código integral e as saídas estão em
[`src/sarimax_com_defasagens.py`](../src/sarimax_com_defasagens.py) e
[`outputs/tables/sarimax_defasagens_20261024/`](../outputs/tables/sarimax_defasagens_20261024/).

### Por que todos os candidatos preferiram lag 0?

O BIC penaliza **todos os parâmetros novos**. Se houver nove tipologias
e acrescentarmos lag 1 para todas simultaneamente, surgem nove
coeficientes extras; com 69 meses de treino, só a penalização
adicional do BIC é aproximadamente `9·log(69) ≈ 38,1`.
É uma penalização legítima de parcimônia, mas significa que o teste
foi para um **bloco inteiro** de defasagens.

Portanto, a escolha universal de `l0` **não prova ausência de efeito
defasado em cada tipologia isoladamente**. Ela indica que os blocos
adicionados não ofereceram ganho suficiente de verossimilhança para
compensar sua complexidade.

## 5. O que foi acrescentado ou alterado nesta rodada

1. SARIMAX estaduais: extensão dos modelos contemporâneos para
   comparar três blocos de lags climáticos em amostra comum;
   nenhuma superioridade consistente foi encontrada.
2. DLM: comparação explícita dos dois menores AICs e reavaliação das
   cinco hipóteses com DK por regra, DK6 e DK12.
3. DLM: auditoria separada do candidato K=0, que não integrava
   a grade original.
4. Documentação: esclarecimento da finalidade do DK e distinção
   entre banda de inferência L e lag climático K.
5. O histórico e os modelos anteriores permanecem preservados;
   a análise com K fixado em 6 ou 12 meses foi retirada por decisão
   metodológica e não compõe os resultados atuais.

## 6. Pontos que exigem cuidado antes do fechamento

- **Resíduos SARIMAX:** a avaliação principal usa Ljung–Box de resíduos
  brutos com 12 lags. É recomendável validar com erros de previsão
  padronizados e graus de liberdade adequados às ordens ARMA, além
  de examinar os modelos que ainda têm autocorrelação.
- **Blocos de defasagens:** a grade omite o segundo atraso e
  adiciona muitas regressoras de uma vez; se a pergunta sobre atraso
  individual for essencial, uma análise complementar parcimoniosa
  deve ser definida antes de olhar novos valores-p.
- **Estrutura sazonal:** os cinco candidatos incluem um termo sazonal
  obrigatoriamente; ampliar de forma pequena a grade pode ajudar
  quando a adequação residual for insuficiente.
- **Prognóstico:** como há `X_t` observado, avaliar os resultados
  como previsão condicional, não prognóstico antecipado.
- **Inferência:** nem DK no DLM nem BH no SARIMAX resolvem
  confundimento ou seleção adaptativa de modelos.

**Esses pontos são verificações metodológicas pendentes, não resultados
de novas estimações.** Evitar modificar a especificação principal
apenas para obter rejeições de hipóteses.

## 7. Reprodução

Com a base auditada em `data/processed/df_tcc_2013_2024.csv`:

```bash
python src/auditar_dlm_aic_top2.py
python src/inferencia_dlm_top2_aic.py
python src/auditar_dlm_k0.py
python src/sarimax_com_defasagens.py
python src/gerar_painel_defasagens.py
```

Para ler a análise principal, seguir a sequência de
[notebooks 01, 02 e 03](../notebooks/README.md). Para a comparação
interativa das defasagens, abrir
[`outputs/reports/defasagens_metodos.html`](../outputs/reports/defasagens_metodos.html).

**Referência metodológica do DK:** Driscoll, J. C. e Kraay, A. C. (1998),
*Consistent Covariance Matrix Estimation with Spatially Dependent Panel Data*,
The Review of Economics and Statistics, 80(4), 549–560,
https://doi.org/10.1162/003465398557825.
