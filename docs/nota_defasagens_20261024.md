# Revisão de defasagens — 24/10/2026

## Objetivo

Esta nota registra três desdobramentos da revisão do TCC:

1. Examinar a segunda escolha de \(K\) pelo AIC nos DLMs de painel.
2. Estimar SARIMAX com blocos explícitos de exposições climáticas defasadas.
3. Distinguir a defasagem do modelo (\(K\)) da banda de Driscoll–Kraay (\(L\)).

As análises usam o painel de 27 UFs, 2013–2024, com as 16 tipologias originais. A
base processada não é versionada; seu SHA-256 auditado é
`46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36`.

## 1. Primeiro e segundo AIC no DLM

O DLM mantém os efeitos fixos de UF e de mês-ano, resposta
\(\Delta\log(I)\), exposição \(\Delta\log(1+D)\), e grade \(K=1,\ldots,24\).
Cada tipologia/período tem uma **amostra comum para os 24 valores de K**.

- Houve 29 combinações estimáveis das 32 possíveis.
- Em todas as 29, o segundo menor AIC ficou a menos de 2 unidades do primeiro.
- A diferença variou entre 0,0618 e 1,9966.
- A seleção principal permanece o menor AIC; o segundo K é apresentado como
  alternativa próxima, sem tratar dois K como estimativas independentes.

**Ressalva de interpretação:** como todos os modelos são aninhados e usam a
mesma amostra, adicionar um único coeficiente leva a
\(AIC(K+1)-AIC(K)=2-2[\ell(K+1)-\ell(K)]\leq2\). Portanto, para todo
vencedor \(K<24\), existe necessariamente o candidato \(K+1\) com diferença
de AIC menor ou igual a 2. A proximidade observada é, em grande parte,
consequência matemática da grade aninhada; **não** é evidência independente
de que os dois horizontes tenham importância substantiva ou que os lags
sejam significativos. Por isso, a comparação de inferência também foi feita.

Exemplos: Tornados/pré \(K_1=1,K_2=2,\Delta AIC=0,062\);
Chuvas Intensas/pré \(K_1=15,K_2=16,\Delta AIC=0,306\);
Incêndios Florestais/total \(K_1=6,K_2=1,\Delta AIC=0,757\).

Foi refeita a inferência sob ambos os K, usando DK pela regra, DK6 e DK12,
proteção de Bonferroni para a busca em 24 K dos contrastes escalares,
famílias de 324/300 coeficientes para os testes conjuntos e Holm entre as
16 tipologias planejadas. Os números de hipóteses rejeitadas a 5% foram:

| Escolha | DK por regra | DK6 | DK12 |
|---|---:|---:|---:|
| Menor AIC | 0 | 0 | 7 |
| Segundo AIC | 0 | 2 | 4 |

As rejeições adicionais com DK6/DK12 **não são estáveis à banda de referência**.
Nenhuma rejeição sobreviveu à proteção adotada sob DK por regra, em qualquer
das duas escolhas de K. A inclusão do segundo menor AIC não modifica a
conclusão principal. Estes resultados permanecem exploratórios e não
equivalem a inferência seletiva exata.

## 2. O que o Driscoll–Kraay altera

O DLM é estimado por MQO e efeitos fixos. A matriz robusta de Driscoll–Kraay
ajusta **erros-padrão, intervalos e valores-p**, mantendo iguais os
coeficientes estimados e o AIC. A implementação agrega os escores
\(s_t=\sum_i\tilde X_{it}\hat\varepsilon_{it}\) ao longo das UFs e utiliza
autocovariâncias temporais ponderadas por uma janela Bartlett até \(L\)
meses. Assim, acomoda dependência transversal contemporânea e dependência
temporal de curta/média duração, sob condições assintóticas apropriadas.

Os erros-padrão clássicos tratam a matriz de covariância de maneira mais
restritiva. Em presença de resíduos temporalmente ou transversalmente
dependentes, valores-p clássicos podem estar mal calibrados. O DK pode
**aumentar ou diminuir** os erros-padrão, porque a soma ponderada de
autocovariâncias pode acrescentar termos positivos ou negativos; não é um
ajuste unilateral para tornar testes conservadores.

Na amostra comum do DLM, a regra
\(L=\lfloor 4(T/100)^{2/9}\rfloor\) resulta em **L=3** no pré-pandemia
(T=60 meses) e **L=4** no período completo (T=119 meses). DK6 e DK12 são
análises de sensibilidade. **K**, por sua vez, define quantos coeficientes
climáticos entram no modelo; **L** define até onde se calcula a
autocovariância dos resíduos para inferência. DK não é uma variável
explicativa adicional nem resolve causalidade, viés de especificação ou a
seleção de K por si só.

## 3. SARIMAX com desastres defasados

Uma extensão dos modelos estaduais foi estimada com três estruturas de
exposição, definidas antes da comparação:

| Candidato | Regressoras climáticas de cada tipologia elegível |
|---|---|
| `l0` | \(X_t\) |
| `l0_1` | \(X_t, X_{t-1}\) |
| `l0_1_3` | \(X_t, X_{t-1}, X_{t-3}\) |

Em todos os candidatos, \(X=\Delta\log(1+D)\) e a resposta é
\(100\Delta\log(I)\). Os 16 tipos são auditados por UF e período;
tipologias sem suporte, posto completo ou condicionamento adequado são
excluídas **com critérios exclusivamente do treino**. Uma mesma seleção de
tipologias é usada para os três candidatos. Isso mantém um modelo
SARIMAX multivariado por UF/período, e não 16 ajustes separados.

A busca entre cinco ordens sazonais do SARIMA foi refeita por BIC sobre o
treinamento comum, após reservar os primeiros três meses para os lags.
Os três SARIMAX usam essa ordem temporal, a mesma seleção de tipologias e
a mesma amostra. Seleciona-se por BIC do treino; a avaliação por RMSE/MAE
é feita apenas no teste cronológico, por previsão condicional de um passo
com \(y_{t-1}\) observado. Quando se utiliza \(X_t\), a exposição climática
do mês \(t\) também é observada: **não se trata de previsão ex ante de
desastres**.

Resultados:

| Indicador | Resultado |
|---|---:|
| Aplicações UF × período | 54 |
| SARIMAX estimáveis | 53 |
| Sem bloco climático elegível | 1 (DF, pré) |
| Candidatos vencedores pelo BIC com apenas `l0` | 53/53 |
| BIC do SARIMAX melhor que SARIMA | 0/53 |
| SARIMAX com menor RMSE que SARIMA no teste | 16/53 |
| Mediana da melhora percentual de RMSE | −7,59% |
| Testes conjuntos com BH a 5% | 0 |
| Coeficientes individuais com BH global a 5% | 2 |

Os dois coeficientes individuais com BH global foram de Enxurradas em
Pernambuco, pré-pandemia e período completo, ambos contemporâneos; são
exploratórios, pois a inferência não corrige formalmente a seleção de
ordens/defasagens e o modelo SARIMAX não melhorou o SARIMA pelo BIC.

O aumento da complexidade com os termos climáticos defasados não foi
compensado por melhora consistente do ajuste penalizado ou da previsão.
Isso não prova inexistência de efeitos, mas restringe a evidência empírica
na especificação e na amostra utilizadas.

## 4. Reprodução e saídas

Na raiz do repositório, depois de instalar as dependências e disponibilizar
a base auditada:

```bash
python src/auditar_dlm_aic_top2.py
python src/inferencia_dlm_top2_aic.py
python src/sarimax_com_defasagens.py
python src/gerar_painel_defasagens.py
```

As tabelas estão em `outputs/tables/revisao_defasagens_20261024/` e
`outputs/tables/sarimax_defasagens_20261024/`. O painel interativo é
`outputs/reports/defasagens_metodos.html`.

**Nota:** este complemento é uma análise de sensibilidade sobre os três
notebooks unificados já existentes; a comparação prévia com SARIMAX
independentemente selecionados e o SARIMAX nacional permanecem preservados.

## 5. Auditoria da exclusão de K=0 da grade do DLM

A grade por AIC começa em K=1 e, portanto, sempre inclui pelo menos um
mês de atraso. Um cálculo auxiliar avaliou **K=0** na mesma amostra comum
dos demais modelos e observou AIC menor em **18 das 29 combinações**,
inclusive em **17 das 21** escolhas originais de K=1.

Isso indica que a restrição inferior pode explicar parte da frequência
de K=1. A auditoria não equivale a selecionar K=0 automaticamente nem
estabelece ausência de efeitos defasados; é uma comparação de especificação
à luz do mesmo AIC. O DLM principal continua com a seleção por AIC
original, aguardando a definição metodológica com a orientadora.

Reprodução: `python src/auditar_dlm_k0.py`. Tabela:
`outputs/tables/revisao_defasagens_20261024/dlm_k0_comparacao_aic.csv`.
Não são utilizados horizontes fixos de seis ou doze meses.

## 6. Consolidação posterior

O [roteiro de revisão de 26/10/2026](roteiro_respostas_orientadora_20261026.md) reúne os resultados das perguntas da orientação em ordem de interpretação, incluindo o efeito das três bandas DK nos erros-padrão e a ressalva de penalização do BIC ao adicionar blocos climáticos no SARIMAX. Essa consolidação **não envolve novas estimações** nem adota DLMs com horizonte fixo.
