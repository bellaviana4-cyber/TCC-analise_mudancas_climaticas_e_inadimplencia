# Metodologia e análises de sensibilidade

Esta página descreve as especificações utilizadas na versão final do trabalho. Os [resultados](resultados.md) e o [guia de reprodução](reproducao.md) complementam a descrição.

## Dados, recortes e transformações

O painel contém 27 UFs e 144 meses, de janeiro de 2013 a dezembro de 2024. As operações de pessoas físicas são filtradas para excluir financiamentos imobiliários, financiamentos de títulos e valores mobiliários e outros créditos antes da agregação dos dois saldos. A [descrição dos dados](../data/README.md) detalha a construção.

A análise é realizada para janeiro de 2013 a janeiro de 2020 (pré-pandemia) e janeiro de 2013 a dezembro de 2024 (completo). A inclusão dos anos da pandemia e posteriores motiva essa comparação; os recortes são sobrepostos e não isolam, por si, mudanças causadas pela pandemia.

Nas aplicações de Granger e DLM, usam-se:

```text
Y_it = Δlog(I_it)
X_it = Δlog(1 + D_it)
```

`I` é a taxa de inadimplência e `D` é a contagem da exposição examinada. A adição de uma unidade permite aplicar o logaritmo nos meses sem registros. A primeira diferença é calculada entre meses consecutivos dentro de cada UF e busca favorecer a estacionariedade.

ADF com intercepto e seleção de defasagens pelo BIC e KPSS com intercepto e banda automática avaliam as séries por UF e recorte. A banda do KPSS determina as defasagens usadas na estimação da variância de longo prazo. Os avisos, limites dos valores-p e séries constantes permanecem registrados. Os testes são diagnósticos complementares e podem produzir resultados inconclusivos ou divergentes.

## Testes de Granger

Cada regressão examina uma tipologia em uma UF e um recorte. O modelo inclui intercepto, onze indicadores mensais, defasagens da própria resposta e defasagens da exposição. Janeiro é o mês de referência para os indicadores sazonais.

A ordem `p` é selecionada pelo BIC entre um e seis meses. Os candidatos usam amostra comum, com 78 observações no pré-pandemia e 137 no completo, após a transformação e a reserva das seis defasagens. Candidatos sem posto completo são descartados; exposições transformadas constantes não recebem teste.

O teste F compara o modelo completo ao modelo que retira apenas as defasagens de X:

```text
H0: β_1 = ... = β_p = 0
```

A rejeição indica que o bloco acrescenta informação preditiva ao histórico da própria inadimplência e aos indicadores mensais. O nível nominal é 5%. Aplica-se Benjamini–Hochberg nas famílias planejadas de 16 tipologias por UF e recorte. Aplicações não estimáveis recebem valor um apenas na composição do ajuste; isso não significa um teste observado sem associação.

O Ljung–Box até a defasagem 12 avalia a autocorrelação residual. O ajuste BH é local às famílias e não controla conjuntamente todas as 864 aplicações nem incorpora formalmente a seleção de p pelo BIC.

## Modelos de defasagens distribuídas em painel

O DLM estima uma exposição por vez, com efeitos fixos de UF e mês-ano:

```text
Y_it = α_i + λ_t + Σ(k=a,...,K) β_k X_i,t-k + ε_it
```

Os efeitos de UF controlam diferenças permanentes; os de mês-ano controlam variações compartilhadas pelas UFs em cada mês. As defasagens recebem coeficientes livres, sem a restrição polinomial de Almon.

| Exercício | Termos incluídos | Horizontes máximos candidatos |
| --- | --- | --- |
| Referência | Contemporâneo e defasagens de 1 a K | K de 1 a 24 |
| Sensibilidade | Somente defasagens de 3 a K | K de 3 a 24 |

O início na terceira defasagem é motivado pela definição de inadimplência com atraso superior a 90 dias. A base mensal registra estoques e não informa o início do atraso de cada contrato; três meses são uma aproximação desse intervalo.

A reserva de 24 defasagens permite comparar os candidatos na mesma amostra: 60 meses por UF no pré-pandemia e 119 no completo. As aplicações por tipologia comparam AIC e BIC. O exercício ampliado utiliza AIC e reúne 16 tipologias, quatro grupos e o total climático COBRADE 12/13/14, avaliados separadamente.

Exige-se suporte da exposição em pelo menos cinco UFs no recorte e dez células UF–mês positivas na amostra comum. As tabelas registram os casos sem suporte ou sem candidato estimável.

A inferência de referência usa covariância Driscoll–Kraay com kernel de Bartlett e banda `floor(4 × (T/100)^(2/9))`, resultando em três e quatro meses nos dois recortes. Bandas de seis e doze meses são examinadas como sensibilidade. A banda se refere à dependência considerada no erro padrão e é distinta de K.

São examinados coeficientes individuais, somas e testes conjuntos. A soma de 0 a K testa `H0: β_0 + ... + β_K = 0`; o teste conjunto examina se todos os coeficientes do intervalo são zero. O erro padrão da soma incorpora variâncias e covariâncias entre os coeficientes.

A busca entre horizontes recebe ajuste de Bonferroni nos contrastes escalares e uma correção por união de testes nos conjuntos. Em seguida aplica-se Holm por recorte, contraste, banda e família planejada: 16 tipologias, quatro grupos ou uma exposição central. Os dois menores AICs são examinados em posições separadas. Esses ajustes dependem da calibração dos testes pontuais e não equivalem a inferência seletiva exata.

## Modelos SARIMA e SARIMAX

As aplicações abrangem cada UF e o Brasil, nos dois recortes. A resposta é `100 × Δlog(I_t)` e a exposição é `Δlog(1 + D_t)`. Para o Brasil, somam-se os saldos e as contagens antes do cálculo da taxa e das transformações.

Cinco estruturas sazonais, com periodicidade 12 e intercepto, concorrem pelo BIC no treino. Como a resposta já foi diferenciada, d e D são zero:

| Ordem regular | Ordem sazonal |
| --- | --- |
| (0,0,0) | (1,0,0)[12] |
| (1,0,0) | (1,0,0)[12] |
| (0,0,1) | (1,0,0)[12] |
| (1,0,1) | (1,0,0)[12] |
| (1,0,0) | (0,0,1)[12] |

O SARIMAX mantém as ordens do SARIMA selecionado e reestima os parâmetros com as exposições. Os modelos **individuais** acrescentam uma tipologia por vez; os **gerais** reúnem as tipologias admitidas a partir dos ajustes individuais, com suas defasagens selecionadas.

| Grade | Termos incluídos | Seleção de K |
| --- | --- | --- |
| 0 a K | Contemporâneo até K | BIC no treino, K de 0 a 24 |
| 3 a K | Terceira defasagem até K | BIC no treino, K de 3 a 24 |

As regressoras são padronizadas com a média e o desvio padrão do treino, usados também no teste. Exigem-se suporte e variação da exposição, posto completo, número de condição até 1.000 e mais de cinco observações de treino além do número de regressoras. Os ajustes usam máxima verossimilhança com L-BFGS, impondo estacionariedade autorregressiva e invertibilidade.

| Recorte | Treino | Teste |
| --- | --- | --- |
| Pré-pandemia | Fev./2015–jan./2019, 48 meses | Fev./2019–jan./2020, 12 meses |
| Completo | Fev./2015–dez./2022, 95 meses | Jan./2023–dez./2024, 24 meses |

A reserva inicial mantém a amostra comum aos candidatos. A avaliação é de **um passo condicional**, com parâmetros fixos do treino e atualização mensal do estado pela resposta observada. A grade de 0 a K admite os registros realizados do próprio mês; a de 3 a K utiliza exposições anteriores.

BIC menor indica melhor ajuste penalizado no treino. RMSE menor indica menor erro no teste. Na convenção das tabelas, `ΔBIC = BIC(SARIMAX) − BIC(SARIMA)` e a melhora percentual do RMSE é positiva quando o erro diminui.

## Interpretação

Granger examina contribuição preditiva das defasagens; o DLM estima associações no painel após os efeitos fixos; SARIMAX avalia previsão condicional fora da amostra. Os resultados não são diretamente intercambiáveis.

As contagens administrativas não medem intensidade dos desastres e a inadimplência é um estoque. Seleção de modelos, dependência residual e possíveis fatores não observados delimitam a interpretação. Erros padrão robustos não eliminam endogeneidade ou não estacionariedade. Os resultados são apresentados como associações temporais e evidência preditiva.
