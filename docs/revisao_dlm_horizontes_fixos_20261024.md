# Sensibilidade do DLM com horizonte comum — 24/10/2026

## Por que rever a escolha do horizonte?

A seleção original por AIC compara modelos de defasagens distribuídas
aninhados, com horizontes de 1 a 24 meses e amostra comum. Ela escolheu K=1
em 21 das 29 combinações estimáveis. Isso não decorre da proximidade entre os
dois menores AICs: ao adicionar um coeficiente, o AIC penaliza em duas
unidades e a verossimilhança nunca diminui, de modo que
`AIC(K+1) - AIC(K) <= 2` é consequência da estrutura aninhada.

Há uma restrição mais relevante: o modelo K=0, apenas contemporâneo, não foi
incluído na grade. Ao calculá-lo na mesma amostra, **K=0 teve AIC menor que o
melhor K original em 18 das 29 combinações**, incluindo **17 das 21** que
originalmente escolheram K=1. A grade forçava, portanto, pelo menos um atraso
mensal. O resultado é uma verificação de especificação, não inferência sobre
ausência de efeitos climáticos.

## Estratégia complementar

Mantiveram-se a equação do DLM finito irrestrito, os efeitos fixos de UF e
mês-ano, a resposta `Δlog(I)`, a exposição `Δlog(1+D)` e a amostra comum
original, de 60 meses no pré-pandemia e 119 no período completo. Para as
mesmas 29 combinações estimáveis, compararam-se dois horizontes comuns:

- **K=12** como horizonte de referência, abrangendo um ano de defasagens;
- **K=6** como sensibilidade em um horizonte de meio ano.

Os coeficientes de cada lag continuam livres; não se impõe Almon, spline ou
restrição de perfil. A motivação é separar a escolha de um horizonte
substantivo da tentativa de encontrar o melhor K para cada tipologia.

Essa definição foi feita **após conhecer os resultados da seleção original**.
Consequentemente, trata-se de uma análise exploratória de sensibilidade, e
não de uma pré-especificação temporal genuína. Nenhum dos horizontes deve ser
selecionado posteriormente porque produziu menor valor-p.

## Inferência e resultados

Para cada horizonte, utilizaram-se Driscoll–Kraay por regra (principal), DK6
e DK12. Foram avaliados `β0`, `Σβ0..K`, `Σβ1..K`, conjunto completo e conjunto
defasado. Para os dois últimos, foi usado o menor valor-p individual, com
Bonferroni pelo número de coeficientes do conjunto, evitando inverter matrizes
de covariância potencialmente mal condicionadas. Por fim, aplicou-se Holm à
família planejada de 16 tipologias **em ambos os horizontes juntos** (32
posições por período, banda e hipótese).

| K | DK por regra | DK6 | DK12 |
|---|---:|---:|---:|
| 6 | 2 | 2 | 5 |
| 12 | 0 | 2 | 2 |

Os números são hipóteses rejeitadas a 5% **após os ajustes**, não quantidades
de tipologias diferentes.

- **DK por regra, K=6:** Movimento de Massa no período completo, nos dois
  testes conjuntos (completo e defasado).
- **DK por regra, K=12:** nenhuma rejeição.
- **DK6, K=12:** Vendavais e Ciclones no período pré-pandemia, nos dois
  testes conjuntos.
- **DK12, K=6:** Inundações e Movimento de Massa no período completo;
  aparecem cinco hipóteses rejeitadas no total.
- **DK12, K=12:** Vendavais e Ciclones no período pré-pandemia, nos dois
  testes conjuntos.

Os valores de AIC dos horizontes 6 e 12 foram recomputados e conferidos
numericamente contra a grade histórica. O novo cálculo não alterou a base,
os coeficientes históricos nem a definição das variáveis.

**Interpretação:** a leitura principal de K=12 com DK por regra não apresenta
rejeições após os ajustes. O K=6 revela sensibilidade em Movimento de Massa,
mas a evidência não permanece no horizonte anual. Portanto, o complemento
não sustenta uma conclusão generalizada e estável de associação climática.

## Arquivos e reprodução

```bash
python src/dlm_horizontes_predefinidos.py
```

Saídas:

- `outputs/tables/dlm_horizontes_fixos_20261024/inferencia.csv` — testes;
- `outputs/tables/dlm_horizontes_fixos_20261024/k0_comparacao_aic.csv` —
  sensibilidade à inclusão de K=0;
- `outputs/tables/dlm_horizontes_fixos_20261024/resumo_inferencia.csv` —
  síntese por horizonte e banda;
- `outputs/tables/dlm_horizontes_fixos_20261024/resumo.json` — protocolo.

O DLM original por AIC e os notebooks históricos foram preservados. Este
complemento não substitui automaticamente a especificação discutida com a
orientadora; permite avaliar explicitamente a estabilidade temporal.
