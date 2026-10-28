# Mudanças climáticas e inadimplência

Repositório do trabalho de conclusão de curso de **Isabella Viana Bambirra**, do curso de Estatística da Universidade Federal de São Carlos (UFSCar).

O estudo investiga a relação temporal entre registros de desastres e inadimplência no crédito bancário brasileiro. As análises usam dados mensais de **2013 a 2024**, com **27 unidades da federação**, **16 tipologias de desastres** e dois recortes: até janeiro de 2020 (pré-pandemia) e até dezembro de 2024 (período completo). Os recortes são sobrepostos.

## Por onde começar

| Etapa | Notebook | Pergunta |
| --- | --- | --- |
| 1. Granger | [Causalidade de Granger por UF e tipologia](notebooks/01_granger_ufs_tipologias.ipynb) | O histórico dos desastres acrescenta informação para prever a variação da inadimplência? |
| 2. DLM | [Modelos de defasagens distribuídas em painel](notebooks/02_dlm_painel_aic_bic.ipynb) | Como as associações mudam ao distribuir a exposição climática no tempo? |
| 3. SARIMAX | [SARIMA × SARIMAX por tipologia e geral](notebooks/03_sarima_sarimax_estadual_nacional.ipynb) | As variáveis climáticas melhoram o ajuste e a previsão condicional em relação ao SARIMA? |

A [descrição metodológica](docs/metodologia_e_sensibilidades.md) apresenta as especificações vigentes, as decisões de estimação e os cuidados de interpretação. O [índice técnico](docs/README.md) aponta para as tabelas completas. Os cadernos exploratórios e as abordagens anteriores de defasagem continuam disponíveis em `notebooks/historico/` e na documentação histórica, mas **não são a versão principal do SARIMAX**.

## Metodologia em uso

- **Granger:** séries transformadas, escolha de 1 a 6 defasagens por BIC, testes conjuntos e ajuste de múltiplas comparações. O teste investiga precedência preditiva, não causalidade estrutural.
- **DLM:** regressão em painel com efeitos fixos de UF e mês-ano, resposta `Δlog(taxa de inadimplência)` e exposição `Δlog(1+desastres)`. A especificação original examina lags **0 a K**, com K escolhido de 1 a 24 por AIC. A sensibilidade exclui os lags 0, 1 e 2 e testa **somente 3 a K**, escolhendo K de 3 a 24. A inferência principal usa covariância Driscoll–Kraay pela banda definida antes dos testes; bandas de 6 e 12 meses são verificações adicionais.
- **SARIMAX:** um modelo individual por tipologia, UF e período; o modelo geral reúne as tipologias individuais estimáveis com seus horizontes escolhidos. São comparados blocos consecutivos **0 a K** e **3 a K**, até 24 meses, com escolha por BIC no treino e avaliação do RMSE/MAE no teste cronológico. Cada comparação usa o mesmo SARIMA de referência, a mesma ordem temporal e uma amostra comum. A série Brasil é agregada pelos saldos de crédito, não pela média das taxas estaduais.

A restrição aos lags a partir de três meses é uma **sensibilidade** motivada pela medida de inadimplência acima de 90 dias. O indicador representa um estoque de operações em atraso: não permite conhecer a data individual de entrada em inadimplência. A escolha de K=3, por si só, não comprova um mecanismo com início no terceiro mês.

## Resultados da execução de 26/10/2026

| Exercício | Cobertura e resultado |
| --- | --- |
| Granger | 627 das 864 aplicações estimáveis; 14 rejeições após BH local, das quais duas com diagnóstico residual desfavorável |
| DLM, grade original | 29 aplicações estimáveis; AIC selecionou K=1 em 21 e K maior em oito |
| DLM, somente 3 a K | 39 de 42 aplicações estimáveis; K=3 em 27; **nenhuma rejeição** após os ajustes com a banda DK principal |
| SARIMAX individual, 0 a K | 452 de 896 modelos estimáveis; 22 com BIC melhor, 167 com RMSE menor e **4 com ambos** melhores que o SARIMA |
| SARIMAX individual, 3 a K | 452 de 896 modelos estimáveis; 29 com BIC melhor, 179 com RMSE menor e **5 com ambos** |
| SARIMAX geral, 3 a K | 55 de 56 estimados; três melhoraram o BIC, nove o RMSE, **nenhum os dois simultaneamente** |
| Brasil, geral 3 a K | Todas as 16 tipologias incluídas; BIC e RMSE piores que no SARIMA nos dois recortes |

Os resultados individuais variam conforme a tipologia, o estado e o período. O predomínio do menor K permitido na grade — K=0 na comparação original e K=3 na nova — também recomenda cautela. Em conjunto, as análises não sustentam uma melhora preditiva robusta e generalizada pela inclusão dos registros de desastres.

Resultados, critérios e limitações em detalhe: [DLM 3–24](docs/dlm_defasagens_3a24_20261026.md), [SARIMAX 3–24](docs/sarimax_sensibilidade_3a24_20261026.md) e [SARIMAX 0–24](docs/sarimax_por_tipologia_e_geral_20261026.md).

## Dados e reprodução

Os arquivos brutos e a base analítica não são distribuídos neste repositório. As tabelas de resultados e os notebooks estão disponíveis para leitura; **reestimar os modelos exige reconstruir a base**. Veja [origem, estrutura e preparação dos dados](data/README.md).

A versão auditada de `data/processed/df_tcc_2013_2024.csv` possui **3.888 linhas (27 UFs × 144 meses)** e SHA-256:

```text
46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36
```

Na raiz do projeto:

```bash
python -m pip install -r requirements-revisao-estadual.txt

# Preparação, após obter os arquivos de origem conforme data/README.md
python src/01_consolidar_scr.py
python src/02_preparar_atlas.py
python src/03_integrar_bases.py

# Sensibilidade DLM, lags 3 a K
python src/dlm_lags_3a24_20261026.py

# SARIMAX por tipologia e geral, lags 0 a K (referência comparativa)
python src/executar_sarimax_tipologias_20261026.py --workers 4
python src/sarimax_por_tipologia_k0_24_20261026.py --fase gerais
python src/sarimax_por_tipologia_k0_24_20261026.py --fase consolidar

# SARIMAX com exposições somente de 3 a K
python src/executar_sarimax_tipologias_20261026.py --workers 4 --inicio-lags 3
python src/sarimax_por_tipologia_lags3_24_20261026.py --fase gerais
python src/sarimax_por_tipologia_lags3_24_20261026.py --fase consolidar
python src/comparar_sarimax_lags3_24_20261026.py
python src/verificar_sarimax_lags3_24_20261026.py
```

A execução integral do SARIMAX percorre muitos candidatos e pode demorar. Para **consultar os resultados já produzidos**, não é necessário reestimar: as tabelas estão em `outputs/tables/` e o notebook 03 oferece uma leitura resumida dos CSVs. Os modelos SARIMAX individuais verificam 22.400 candidatos na grade 0–24 e 19.712 na grade 3–24; nem todos são estimáveis ou convergem.

## Limites de interpretação

Os testes dos coeficientes SARIMAX são exploratórios após seleção de ordens e defasagens. A avaliação fora da amostra usa previsões **condicionais de um passo**, atualizadas com a inadimplência anterior observada; na especificação 0–K, também se conhece a exposição climática contemporânea. O diagnóstico de autocorrelação residual é desfavorável em parte dos ajustes. Por essas razões, nem os valores-p isolados nem as melhorias de ajuste podem ser interpretados como efeitos causais dos desastres.

O histórico de experimentos permanece acessível para auditoria, separado da sequência principal de leitura.
