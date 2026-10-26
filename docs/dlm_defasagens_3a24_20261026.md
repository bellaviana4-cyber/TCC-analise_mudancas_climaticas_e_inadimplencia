# DLM com desastres defasados entre 3 e 24 meses

## Motivação e pergunta

O indicador de inadimplência do Banco Central corresponde ao saldo de operações
com parcelas vencidas há mais de 90 dias, incorporando o arrasto do restante
da operação. A sugestão da orientação foi investigar apenas a exposição
climática ocorrida três ou mais meses antes da referência da inadimplência.

**Ressalva:** mais de 90 dias de atraso é um critério de classificação de um
*estoque* de operações, não a data conhecida de início de cada inadimplemento.
Logo, excluir os meses contemporâneo, t−1 e t−2 é uma hipótese de sensibilidade,
não exigência algébrica do indicador ou demonstração de causalidade.

Fonte: Nota metodológica de operações de crédito, Banco Central do Brasil,
item “Atraso até 90 dias e inadimplência”:
https://www.bcb.gov.br/content/estatisticas/Documents/notas_metodologicas/emprestimos-sfn/notaempr.pdf

## Modelo e alterações

Foi preservada **integralmente** a análise anterior que escolhe K entre 1 e 24
e ajusta regressoras contemporâneas e defasadas entre 0 e K. Este novo
experimento é separado; nenhum arquivo anterior foi substituído.

Em cada exposição e período, ajusta-se o painel UF×mês, com efeitos fixos
de UF e mês-ano:

    Δlog(I_{i,t}) = α_i + λ_t + Σ_{k=3}^{K} β_k Δlog(1+D_{i,t-k}) + ε_{i,t}

- Intervalo candidato: **K=3,...,24**; K=3 tem somente x_{t−3}.
- Estimação: MQO TWFE na mesma amostra comum de 24 lags para todos K.
- Treino/recortes do DLM anterior preservados: 60 meses efetivos no pré,
  fev/2015–jan/2020, e 119 meses efetivos no total,
  fev/2015–dez/2024; 27 UFs em ambos (N=1.620 e 3.213).
- Mesmas transformações: y=Δlog(I) e x=Δlog(1+D).
- Mesmas regras de suporte: ≥24 registros, ≥12 células UF-mês positivas,
  ≥5 UFs e ≥8 meses expostos na janela efetiva.
- Mesmo domínio: total climático pela classificação COBRADE 12/13/14,
  quatro grupos e 16 tipologias. Todos os modelos são separados por exposição;
  não são 21 efeitos parciais simultâneos.
- Seleção por AIC na amostra comum, sem escolher K pelos valores-p.
- DK por regra (L=3 no pré, L=4 no total) é a covariância principal;
  DK6 e DK12 são verificações de sensibilidade, não alternativas escolhidas
  posteriormente para obter rejeições.
- Endpoints coerentes com a nova especificação: β₃, soma β₃+…+β_K,
  e teste exploratório conjunto dos coeficientes de 3 a K.
- Proteção conservadora da seleção: Bonferroni 22 para endpoints escalares;
  união de testes individuais sobre 253 coeficientes na grade para o
  conjunto. Holm por período, nível (central/grupo/tipologia), endpoint
  e banda, incluindo com p=1 as categorias indisponíveis em cada família
  planejada. Também há BH exploratório na tabela.

### Auditoria da exposição central sem Atlas bruto

O CSV processado, de SHA256
`46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36`,
contém as 16 tipologias e cada registro do Atlas pertence a uma tipologia
única. A taxonomia histórica auditada demonstra que 11 delas pertencem
integralmente ao recorte COBRADE 12/13/14. Somá-las produz exatamente
**37.643** registros climáticos, comparados a **40.339** registros gerais.
Com essa reconstrução, o AIC histórico do total climático em K=1 foi
recalculado com erro numérico zero: −7060,9658108 (pré) e −15035,5964583
(total). A fonte Atlas original não foi substituída silenciosamente por uma
classificação baseada no nome; a classificação auditada por código foi usada.

## Resultados da busca por AIC

Foram consideradas 42 aplicações (21 exposições × 2 períodos), com **39
estimáveis** (18 pré; 21 total). O mínimo foi K=3 em **27/39**. Alguns
horizontes longos permaneceram selecionados, mas os coeficientes dos novos
modelos diferem porque os lags 0–2 foram removidos.

| Exposição | Pré: novo K | Pré: antigo K | Total: novo K | Total: antigo K |
|---|---:|---:|---:|---:|
| Total climático | 3 | 1 | 3 | 1 |
| Grupo Climatológico | 3 | 1 | 3 | 1 |
| Grupo Hidrológico | 5 | 1 | 9 | 1 |
| Grupo Meteorológico | 14 | 1 | 9 | 9 |
| Grupo Outros | 3 | 1 | 3 | 1 |
| Alagamentos | 3 | 1 | 3 | 1 |
| Chuvas Intensas | 15 | 15 | 16 | 16 |
| Doenças infecciosas | 3 | 1 | 3 | 1 |
| Enxurradas | 3 | 1 | 3 | 1 |
| Erosão | 3 | 1 | 3 | 1 |
| Estiagem e Seca | 3 | 1 | 3 | 1 |
| Granizo | 3 | 1 | 3 | 1 |
| Incêndio Florestal | 3 | 1 | 6 | 6 |
| Inundações | 3 | 1 | 3 | 1 |
| Movimento de Massa | 4 | 1 | 3 | 5 |
| Onda de Calor e Baixa Umidade | — | — | 14 | 14 |
| Onda de Frio | — | — | 3 | 1 |
| Tipologia Outros | 3 | 1 | 3 | 1 |
| Rompimento/Colapso de barragens | — | — | 3 | 4 |
| Tornado | 4 | 1 | 3 | 1 |
| Vendavais e Ciclones | 14 | 14 | 9 | 9 |

As três tipologias sem inferência no pré não atendem à regra original
de suporte: Onda de Calor e Baixa Umidade, Onda de Frio e Barragens.

O primeiro e segundo AIC continuam próximos (ΔAIC de 0,01875 a 2,00,
mediana ≈1,56). Os candidatos são aninhados com mesma amostra, e adicionar
um lag não aumenta a soma de quadrados dos resíduos; diferenças pequenas
são parcialmente consequência da penalização AIC de dois pontos.

### Evidência estatística

| Covariância | Rejeições após correção para seleção e Holm |
|---|---:|
| DK por regra (principal) | **0** |
| DK6 | **0** |
| DK12 | **2** |

As duas rejeições de DK12 são de **Tornado no pré-pandemia, K=4**:

- soma β₃+β₄: p ajustado Holm = **0,009106**;
- conjunto dos lags 3–4: p ajustado Holm = **0,000565**.

São resultados **sensíveis à banda** e à exposição concentrada: Tornado
no pré teve 33 registros em 25 células UF-mês, oito UFs expostas,
N_efetivo ≈3,82, top-1 42,42% e top-2 66,67%.

O total climático escolheu K=3 em ambos recortes. A soma β₃ foi
**−0,000035** no pré (p DK-regra≈0,937) e **−0,000313** no total
(p DK-regra≈0,303); não houve rejeições principais.

## Limitações importantes

1. Como 27/39 escolhas estão em K=3, o limite inferior da grade pode estar
   influenciando a concentração das escolhas, assim como K=1 influenciava
   a apresentação antiga. K=3 selecionado **não prova** que o efeito começa
   necessariamente no terceiro mês.
2. Excluir lags 0–2 testa uma hipótese temporal mais restrita; se houver
   associação contemporânea verdadeira, omiti-la pode mudar os coeficientes
   de lags mais longos. Uma relação causal não foi identificada.
3. A transformação da variável dependente é diferença logarítmica da
   inadimplência, e a exposição é diferença logarítmica de (1+D).
   Coeficientes e somas não são automaticamente pontos percentuais nem
   impactos de um único desastre físico.
4. A amostra comum remove os 24 meses iniciais de referência, mesmo nos
   modelos mais curtos, garantindo comparabilidade dos AICs sem recuperar
   informação histórica anterior.
5. Bonferroni+Holm são conservadores e não são inferência seletiva exata.
   DK não corrige confundimento, omissões do modelo nem dependência da
   escolha de bandas nos resultados.
6. As regras de suporte e o domínio incluem grupos/tipos não estritamente
   hidrometeorológicos nas análises secundárias, separados da medida central.

## Reproduzir

```bash
PYTHONPATH=/tmp/tcc_sarimax_deps OPENBLAS_NUM_THREADS=1 python src/dlm_lags_3a24_20261026.py
```

No ambiente usual basta instalar `requirements-dlm-painel-log.lock.txt`
e usar `python src/dlm_lags_3a24_20261026.py`.

Arquivos: `outputs/tables/dlm_lags_3a24_20261026/`:
`candidatos.csv` (toda a grade), `modelos.csv` (escolhas e K anterior),
`resultados.csv` (testes e multiplicidade), `coeficientes.csv` (perfil),
`suporte.csv` (auditoria) e `resumo.json` (metadados).
