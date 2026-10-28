# Metodologia e análises de sensibilidade

## Dados e medidas

O painel combina os registros mensais do SCR/Banco Central do Brasil e do Atlas Digital de Desastres do Brasil, agregados por UF e mês de 2013 a 2024. São 27 UFs observadas por 144 meses (3.888 registros). A taxa de inadimplência é calculada como 100 vezes o saldo de crédito inadimplente dividido pela carteira ativa. O Brasil é calculado pela razão entre as somas dos saldos, não pela média simples das taxas estaduais.

O conjunto operacional tem 16 tipologias. A exposição climática central do DLM é um subconjunto auditado por códigos COBRADE (11 tipologias, 37.643 registros), distinto do total de 40.339 registros das 16 tipologias. Grupos e tipologias são analisados separadamente no DLM, sem atribuir a todas elas a mesma interpretação climática.

São usados dois recortes: pré-pandemia (até janeiro de 2020) e período completo (até dezembro de 2024). Como o primeiro está contido no segundo, os resultados não são independentes nem constituem, por si, teste de mudança estrutural.

## 1. Precedência temporal: Granger

A primeira etapa verifica se os valores passados de uma tipologia acrescentam informação sobre a variação da inadimplência, além do histórico da própria resposta. As séries passam por transformações e verificações de estacionariedade; a grade de 1 a 6 defasagens é comparada por BIC na mesma amostra. O teste de hipótese é conjunto, com correção BH nas famílias planejadas e avaliação de autocorrelação residual.

A execução principal contabilizou 864 aplicações, das quais 627 foram estimáveis; 14 rejeições permaneceram após BH local, com ressalvas diagnósticas em dois casos. O termo *causalidade de Granger* se refere a precedência preditiva, não identificação causal.

## 2. DLM em painel

A equação estimada, em diferenças logarítmicas, é:

```text
Δlog(I_it) = α_i + λ_t + Σ β_k Δlog(1 + D_i,t-k) + ε_it
```

`I` é a taxa de inadimplência e `D` é uma medida de registros de desastres. `α_i` e `λ_t` representam efeitos fixos de UF e mês-ano. O uso de diferenças logarítmicas distingue a implementação da formulação genérica em níveis: os coeficientes não são diretamente mudanças em pontos percentuais da taxa.

**Especificação de referência:** inclui as exposições de `t` a `t−K`, escolhe K entre 1 e 24 por menor AIC, usa a mesma amostra para todos os K e admite comparação com BIC. Foram 29 aplicações estimáveis na seleção principal, com K=1 em 21. A comparação adicional com K=0 mostra que o limite inferior influencia a seleção, sem anular a análise original.

**Sensibilidade de três meses:** inclui somente `t−3, ..., t−K` com K de 3 a 24, também selecionado por AIC e com amostra comum. Foram 39 aplicações estimáveis de 42 (21 exposições × dois períodos). O AIC selecionou K=3 em 27. O total climático ficou em K=3 nos dois períodos, com soma estimada de −0,000035 no pré e −0,000313 no total, sem rejeição pela banda DK principal (p≈0,937 e p≈0,303).

A inferência usa covariância Driscoll–Kraay (DK) com banda por regra como análise principal, e bandas 6 e 12 como sensibilidade. DK corrige a estimativa da covariância sob certas formas de dependência, mas não altera os coeficientes, o AIC ou a escolha de K. Foram aplicadas proteções conservadoras para a busca de K e ajustes para famílias de hipóteses.

| Banda | Rejeições ajustadas nos DLMs 3–K |
| --- | ---: |
| Regra (L=3 pré; L=4 total) | 0 |
| DK6 | 0 |
| DK12 | 2 |

As duas rejeições sob DK12 ocorreram em Tornado no pré, K=4 (soma dos coeficientes e teste da união de coeficientes); a categoria tem ocorrência concentrada em poucas UFs. A divergência entre bandas impede tratar essas rejeições como conclusão estável.

A regra de 90 dias não impõe matematicamente um lag climático de três meses. A taxa de inadimplência é uma medida de estoque: as exposições podem afetar o fluxo de novas entradas com horizontes distintos. O corte em `t−3` é uma hipótese substantiva submetida a análise de sensibilidade, não uma nova definição da variável.

## 3. SARIMA e SARIMAX

A resposta é `y_t = 100 Δlog(I_t)`; cada tipologia de desastres entra como `x_j,t = Δlog(1 + D_j,t)`. A multiplicação por 100 é apenas uma mudança de escala da resposta. Para cada UF e período, cinco ordens SARIMA sazonais com periodicidade 12 são avaliadas pelo BIC do treinamento. A ordem vencedora é mantida em cada par SARIMA/SARIMAX.

São feitos dois exercícios complementares, com uma amostra comum que reserva os primeiros 24 meses mesmo para candidatos curtos:

1. **Referência 0–K:** um SARIMAX individual por tipologia, com blocos `[0]`, `[0,1]`, ... `[0,...,24]` e K escolhido por BIC no treino.
2. **Sensibilidade 3–K:** os mesmos modelos individuais e unidades, mas somente os blocos `[3]`, `[3,4]`, ... `[3,...,24]`, também por BIC no treino.

Depois da seleção individual, o **SARIMAX geral** de cada UF/período reúne as tipologias com seus K selecionados, com exclusões documentadas quando a matriz conjunta não tem suporte, posto ou graus de liberdade. Não se limita de antemão o número a quatro ou seis tipologias. No agregado Brasil, as 16 tipologias são incluídas nos dois recortes.

A amostra de treino/teste usada nessa etapa contém 48/12 meses no pré e 95/24 meses no recorte completo. Os erros RMSE/MAE são calculados na parte cronológica de teste, sem participação na escolha dos modelos. A validação é **condicional de um passo**, atualizando o estado com `y_(t−1)` realizado. A referência 0–K também conhece `x_t` realizado; a sensibilidade 3–K usa apenas exposições mais antigas. Essas previsões não devem ser descritas como previsão de múltiplos passos feita na origem do teste.

### Comparação dos modelos individuais

| Indicador | 0–K | 3–K |
| --- | ---: | ---: |
| Combinações possíveis (28 unidades × dois períodos × 16 tipos) | 896 | 896 |
| Modelos estimáveis | 452 | 452 |
| K no limite inferior da grade | 420 em K=0 | 424 em K=3 |
| BIC menor que SARIMA | 22 | 29 |
| RMSE menor que SARIMA | 167 | 179 |
| BIC e RMSE menores conjuntamente | **4** | **5** |

Entre os 452 pares, a estratégia 3–K teve BIC menor que 0–K em 236 e RMSE menor em 236; em 91, ambos os indicadores melhoraram. A mediana da diferença entre estratégias foi pequena. Não há superioridade geral e uniforme de uma janela sobre a outra.

As cinco combinações com BIC e RMSE favoráveis ao SARIMAX na sensibilidade 3–K foram:

| Recorte | UF | Tipologia | K | ΔBIC SARIMAX − SARIMA | Redução de RMSE |
| --- | --- | --- | ---: | ---: | ---: |
| Pré | MG | Chuvas intensas | 3 | −1,49 | 5,56% |
| Pré | MS | Granizo | 3 | −4,26 | 7,41% |
| Pré | RN | Estiagem e seca | 3 | −2,96 | 12,42% |
| Total | AP | Doenças infecciosas | 3 | −0,13 | 0,05% |
| Total | RN | Estiagem e seca | 3 | −9,81 | 0,86% |

São resultados pontuais e alguns ganhos muito pequenos. Na tabela 3–K, 115/452 modelos individuais tiveram Ljung–Box com p<0,05 sobre inovações padronizadas, ajustado pelos graus de liberdade ARMA. Isso reduz a confiança em inferências condicionadas aos ajustes.

### Modelos gerais e agregado Brasil

Foram estimados 55 SARIMAX gerais de 56 possíveis; o DF no pré não teve tipologia individual estimável. Na estratégia 3–K, **três** gerais melhoraram o BIC e **nove** tiveram RMSE menor que o SARIMA, mas **nenhum** melhorou os dois. Os três BICs favoráveis — AC/pré (−0,61), PI/pré (−3,05) e RR/pré (−51,92) — vieram acompanhados de piora de RMSE de 40,42%, 145,22% e 186,54%, respectivamente.

No Brasil, a análise geral inclui as 16 tipologias em ambos os recortes:

| Brasil | Pré 0–K | Pré 3–K | Total 0–K | Total 3–K |
| --- | ---: | ---: | ---: | ---: |
| BIC do SARIMA | 214,69 | 214,69 | 459,74 | 459,74 |
| ΔBIC (SARIMAX − SARIMA) | +47,04 | +51,04 | +58,90 | +45,89 |
| Melhora do RMSE frente ao SARIMA | −64,43% | −36,87% | −26,78% | −51,86% |

Em todos os casos nacionais, o BIC foi maior e o RMSE pior no SARIMAX. Assim, o acréscimo de variáveis de desastres não mostrou vantagem consistente para a previsão condicional da inadimplência no agregado.

## 4. Cuidados de leitura

- **Associação não é causalidade.** Choques macroeconômicos não observados, mudança de composição do crédito e outras fontes de confundimento permanecem possíveis.
- **Seleção e inferência são etapas diferentes.** Os valores-p individuais do SARIMAX e BH exploratório não incorporam plenamente a escolha prévia da ordem, do conjunto de tipologias e de K. Eles não são inferência seletiva exata.
- **Suporte não é efeito zero.** Modelos impedidos por baixa variação, posto ou convergência ficam não estimáveis. Não são substituídos por coeficientes nulos.
- **Predomínio da borda.** A escolha frequente de K mínimo muda de zero para três quando a própria grade muda. Isso não identifica a duração física do efeito.
- **Transformação e escala.** A resposta principal é variação logarítmica da taxa, não a taxa em nível. A soma dos betas não equivale automaticamente a pontos percentuais nem ao impacto de um único evento.
- **Diagnóstico temporal.** Rejeições no Ljung–Box de inovações padronizadas pedem cautela ao interpretar os coeficientes.
- **Escopo do teste.** A avaliação mostra previsão condicional de um passo e ganho preditivo relativo ao SARIMA; não mede causalidade nem previsão antes de conhecer todas as informações usadas.

## 5. Arquivos para conferência

- [Notebook de Granger](../notebooks/01_granger_ufs_tipologias.ipynb) e [tabelas](../outputs/tables/granger_fechamento/).
- [Notebook DLM](../notebooks/02_dlm_painel_aic_bic.ipynb), [protocolo 3–K](dlm_defasagens_3a24_20261026.md) e [tabelas](../outputs/tables/dlm_lags_3a24_20261026/).
- [Notebook SARIMAX](../notebooks/03_sarima_sarimax_estadual_nacional.ipynb), [referência 0–K](sarimax_por_tipologia_e_geral_20261026.md), [sensibilidade 3–K](sarimax_sensibilidade_3a24_20261026.md) e [comparações pareadas](../outputs/tables/sarimax_por_tipologia_k3_24_20261026/).

A execução está vinculada ao hash da base processada informado no README. As saídas publicadas permitem conferir as contagens e as comparações, mesmo sem distribuir os arquivos brutos do SCR e do Atlas.
