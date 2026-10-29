# Mudanças Climáticas e Inadimplência

Este repositório contém os códigos, análises e materiais desenvolvidos para o Trabalho de Conclusão de Curso **“Mudanças Climáticas e Inadimplência: uma análise do impacto de desastres naturais no sistema de crédito brasileiro”**.

## Revisão estatística de 20/10/2026

A execução foi revisada sobre a base mensal de 27 UFs × 144 meses, usando **exclusivamente as 16 tipologias originais do Atlas**. Não foram criados grupos nem reclassificadas tipologias. A atualização não altera os capítulos de texto da monografia, que serão fechados depois da validação do código.

**Notebooks com execução conferida:** [Granger UF × tipologia (34)](notebooks/34_granger_ufs_tipologias_validacao.ipynb) · [DLM painel AIC × BIC e curvas de coeficientes (35)](notebooks/35_dlm_painel_aic_bic_validacao.ipynb) · [SARIMA/SARIMAX estadual e nacional (36)](notebooks/36_sarima_sarimax_estadual_nacional_validacao.ipynb).

- **Granger:** 627 estimados de 864 aplicações; 14 rejeições após BH local; dois resultados de Alagamentos/RR rejeitam Ljung–Box e permanecem com ressalva de inferência.
- **DLM:** 29 tipologia×período estimáveis, duas escolhas de K (AIC e BIC); todos BIC K=1, oito diferenças AIC/BIC. Nenhuma rejeição protegida sob BIC + DK regra, quatro sob AIC + DK regra. Auditoria numérica dos 58 modelos selecionados não detectou matrizes de regressores com cond>1000 nem covariâncias com cond>10⁶. [Perfis β por defasagem e curvas acumuladas](outputs/tables/auditoria_metodologica_20261020/).
- **SARIMAX corrigido:** statsmodels não possui seleção automática de ordens. A busca por BIC foi implementada sobre **cinco candidatos sazonais em separado para SARIMA e SARIMAX**, preservando também a comparação com ordens pareadas. As 16 exógenas simultâneas **não são identificáveis em treino em 53/54 aplicações estaduais**; a alternativa estadual reduz as exógenas exclusivamente por suporte, posto e parcimônia predefinida. **53 modelos comparáveis, 16 com melhora de RMSE e nenhum com melhora de BIC**. No Brasil, as 16 tipologias são identificáveis, mas o SARIMAX aumenta o RMSE em 15,02% no pré e em 10,58% no total; não melhora BIC.
- **Significância SARIMAX:** dois coeficientes individuais de Enxurradas/PE sobreviveram BH global (395 testes). Nenhum conjunto de exógenas sobreviveu à correção BH.
- **Warnings:** os 550 candidatos sazonais foram ajustados com registro de avisos; 41 candidatos emitiram warnings de inicialização ou primeira tentativa. Não houve candidatos finais sem convergência após repetição. Residual Ljung–Box rejeitado em 13 dos 53 SARIMAX estaduais e ambos SARIMAX nacionais.

**Resultados e diagnósticos:** [checkpoint metodológico](docs/auditoria_metodologica_20261020.md) · [todas as 58 rejeições corrigidas por método e cenário](outputs/tables/auditoria_metodologica_20261020/rejeicoes_significativas_consolidadas.csv) · [candidatos SARIMA/SARIMAX, q-valores e warnings](outputs/tables/sarimax_criterios_independentes_20261020/).

Reprodução com base original em `data/processed/df_tcc_2013_2024.csv` (não versionada):
```bash
python src/analise_estadual.py granger
python src/analise_estadual.py dlm
python src/auditoria_dlm_granger.py
python src/selecionar_sarima_sarimax_statsmodels.py estadual Pré
python src/selecionar_sarima_sarimax_statsmodels.py estadual Total
python src/selecionar_sarima_sarimax_statsmodels.py nacional Pré
python src/selecionar_sarima_sarimax_statsmodels.py nacional Total
python src/consolidar_analises_finais.py
python src/gerar_notebooks_revisionados.py
```

**Histórico:** as revisões de 19/10 abaixo permanecem para rastreabilidade, mas a seleção SARIMA/SARIMAX que forçava ordens iguais foi substituída, na comparação de modelos independentemente selecionados, pela busca individual por BIC descrita acima.

## Histórico — comparação SARIMA/SARIMAX (19/10/2026)

A auditoria da especificação **16 tipologias simultâneas por UF** confirmou deficiência de posto no treino em **53 de 54** aplicações (27 UFs × 2 períodos). O componente sazonal anual não elimina dependência linear dos regressores. A especificação nacional, entretanto, tem **posto 16/16** no treino em ambos os períodos e foi efetivamente ajustada.

- **Principal (estadual):** SARIMA sazonal versus SARIMAX sazonal com tipologias selecionadas *apenas no treino* por meses positivos, posto, condicionamento e limites de parcimônia previamente declarados. **53 modelos pareados**, com **14 melhorias de RMSE** e **nenhuma melhoria de BIC** frente ao SARIMA.
- **Complementar (Brasil):** SARIMAX sazonal com **16 tipologias simultâneas**, com regressoras obtidas ao agregar os registros nacionais antes de aplicar Δlog(1+D). Posto 16/16, mas RMSE piorou no pré (+29,01%) e no completo (+10,58%), sem melhora de BIC.
- **Inferência:** não houve rejeição dos testes conjuntos após BH; dois coeficientes estaduais individuais (Enxurradas/PE, pré e total) permaneceram abaixo de q=0,05 global, mas sem superioridade preditiva nem conjunta; resultados exploratórios.
- **Previsão:** condicional de um passo com exposição contemporânea observada, não previsão de desastres futuros. SARIMA e SARIMAX são comparados com a mesma ordem sazonal em cada par.

**Arquivos:** [relatório HTML offline](outputs/reports/relatorio_sarimax_revisao_20261019.html) · [documentação e limites](docs/sarimax_revisao_estadual_nacional_20261019.md) · [tabelas e auditorias](outputs/tables/sarimax_revisao_20261019/) · [notebook estadual](notebooks/32_sarimax_estadual_tipologias_estimaveis.ipynb) · [notebook nacional](notebooks/33_sarimax_nacional_16_tipologias.ipynb) · [script de estimação](src/sarimax_revisao_final.py).

Para reproduzir, disponibilize localmente a base mensal consolidada e execute `python src/sarimax_revisao_final.py estadual` e `python src/sarimax_revisao_final.py nacional`. A base bruta não é publicada no repositório.

## Revisão estadual das três metodologias — outubro de 2026

Esta revisão amplia a aplicação para as **27 UFs** e os períodos **jan/2013–jan/2020** (pré-pandemia) e **jan/2013–dez/2024** (completo), com **16 tipologias** separadas nos DLMs/Granger e **16 variáveis exógenas simultâneas** em cada SARIMAX estadual. Mantém intactos os notebooks e os resultados históricos.

**Notebooks executados:** [27 — Granger UF × tipologia](notebooks/27_granger_por_uf_tipologia.ipynb), [28 — DLM AIC/BIC, FE/RE](notebooks/28_dlm_painel_aic_bic_fe_re.ipynb), [29 — SARIMA por UF](notebooks/29_sarima_por_uf.ipynb), [30 — SARIMAX de 16 exógenas](notebooks/30_sarimax_16_exogenas_por_uf.ipynb), [31 — comparação integrada](notebooks/31_comparacao_final_modelos.ipynb).

**Relatório:** [HTML standalone interativo](outputs/reports/relatorio_tcc_analises_estaduais_20261019.html), com menu lateral, filtros, tabelas e comparação dos resultados. O HTML contém dados de modelos derivados do painel consolidado, não bases brutas completas.

**Tabelas:** [revisão estadual](outputs/tables/revisao_estadual_20261019/), com Granger (864 status, 45 rejeições nominais, 14 BH), seleção de DLM (29/32 estimáveis, BIC K=1 em todas), candidatos, testes F/LM/Hausman, indicadores SARIMA/SARIMAX e rejeições nominais/BH. As tabelas completas maiores `dlm_hipoteses.csv` e `consolidado_mestre.csv` são reconstruídas localmente por `src/finalizar_entrega.py`; as famílias e rejeições principais estão disponíveis nos CSVs menores versionados.

**Interpretação principal:** com BIC, proteção da grade e DK pela regra, nenhum dos cinco endpoints DLM rejeitou após BH. Dos 54 SARIMAX estaduais planejados, os dados identificam 16 coeficientes contemporâneos no período completo somente para MG, MS, RS, SC e SP; nenhuma UF no pré-pandemia. Nenhum teste conjunto dos cinco rejeitou H0 e nenhum coeficiente individual sobreviveu ao BH. Somente MG tem matriz de treino com posto 16, permitindo comparar previsões condicionais: RMSE SARIMA ≈1,3563 e SARIMAX ≈1,2861. Melhora de RMSE **não prova superioridade geral ou causalidade**.

**Reprodução:** são necessárias as bases mensais originais, que não são versionadas no Git. A aplicação sobre a base consolidada usa o SHA-256 `46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36`. Salve o CSV em `data/processed/df_tcc_2013_2024.csv`; instale `requirements-revisao-estadual.txt` e execute:

```bash
python src/analise_estadual.py granger
python src/analise_estadual.py dlm
python src/estacionariedade_estadual.py
python src/sarimax_estadual.py Pré
python src/sarimax_estadual.py Total
python src/finalizar_entrega.py
```

A reexecução dos scripts foi conferida sobre o painel com hash idêntico ao histórico. O Atlas bruto foi localizado na Biblioteca do projeto, mas a leitura integral de seus registros não foi reproduzida nesta revisão; códigos classificação original do Atlas e taxonomia permanecem conforme auditoria anterior, com essa ressalva. O estudo observa associações e precedência preditiva, não identifica causalidade.

[Resultados e limitações detalhadas](docs/revisao_estadual_resultados_20261019.md).

## Referência histórica da etapa DLM — seleção AIC de 1 a 24 meses

O notebook [23 — DLM em painel com seleção do horizonte por AIC](notebooks/23_dlm_painel_selecao_aic_1a24.ipynb) é a referência atual: 27 UFs, Δlog(I), Δlog(1+D), efeitos fixos de UF e mês-ano completos, coeficientes livres de k=0 a K, sem lags de Y. **K escolhido pelo menor AIC entre 1 e 24, separadamente por exposição e período**, com amostra comum desde fev/2015 (N=1620 pré/3213 total), mantida no modelo final.

O total climático (classificação original do Atlas 12/13/14) escolheu K1 nos dois recortes e não apresentou rejeição acumulada a 5% em CR1 ou DK6. Algumas categorias complementares rejeitam após BH, com limitações de classificação, suporte e inferência. **Análise exploratória: estacionariedade estadual não uniforme; IC/p/q usuais ignoram a incerteza da seleção de K; não houve inferência seletiva formal.** K escolhido não comprova duração física dos impactos.

- [Protocolo e decisões](docs/dlm_painel_log_aic_protocolo.md) · [Resultados, horizontes e limites](docs/dlm_painel_log_aic_resultados.md).
- Visualização interativa: o HTML é gerado somente para consulta local, a partir dos CSVs em `outputs/tables/dlm_painel_log_aic/`, com filtros de período, exposição, covariância, seleção de K, diagnósticos e cenários. O arquivo HTML não é versionado.
- Código: `src/dlm_painel_log_aic.py`; tabelas/manifesto: `outputs/tables/dlm_painel_log_aic/`; figuras: `outputs/figures/dlm_painel_log_aic/`.
- Reprodução: instalar `requirements-dlm-painel-log.lock.txt`, colocar entradas nos caminhos do manifesto, executar `python src/executar_notebook_painel_log.py notebooks/23_dlm_painel_selecao_aic_1a24.ipynb`; depois `python src/relatorio_dlm_painel_log_aic.py`, `python src/verificar_dlm_painel_log_aic.py` e `node src/verificar_relatorio_dlm_painel_log_aic.cjs`.

A versão [22 — K6 fixo](notebooks/22_dlm_painel_diferencas_logaritmicas.ipynb), seu [protocolo](docs/dlm_painel_log_protocolo.md), [resultados](docs/dlm_painel_log_resultados.md), relatório e saídas permanecem históricos, sem alteração. Versões 16–21 continuam nas branches documentadas no [histórico e SHAs](docs/dlm_painel_log_historico.json). O capítulo foi corrigido em `tcc/capitulos/c3_metodologias_tg_referencia.tex`, com a versão anterior preservada no histórico Git. Granger não foi reestimado; SARIMAX continua para etapa posterior.

## Objetivo

O trabalho tem como objetivo investigar associações temporais entre registros de desastres e a inadimplência de pessoas físicas no sistema de crédito brasileiro no período de **2013 a 2024**.

Para isso, são combinadas informações sobre crédito e inadimplência provenientes do **Sistema de Informações de Crédito do Banco Central do Brasil (SCR/BACEN)** com dados de ocorrências de desastres naturais disponibilizados pelo **Atlas Digital de Desastres no Brasil**.

A análise busca investigar tanto relações contemporâneas quanto efeitos temporalmente defasados entre a ocorrência de desastres naturais e o comportamento da inadimplência.

## Dados

O trabalho utiliza duas principais fontes de dados:

### Sistema de Informações de Crédito — SCR/BACEN

Dados do Sistema de Informações de Crédito do Banco Central do Brasil utilizados para construção dos indicadores relacionados ao mercado de crédito e à inadimplência de pessoas físicas.

### Atlas Digital de Desastres no Brasil

Dados municipais de ocorrências de desastres naturais, contendo informações como tipo de desastre, localização e período de ocorrência.

O período analisado compreende os anos de **2013 a 2024**.

Os arquivos brutos não são armazenados neste repositório devido ao volume dos dados. As bases devem ser inseridas localmente nos diretórios indicados na seção de estrutura do projeto.

## Metodologia

A análise empírica utiliza métodos de séries temporais para investigar a relação entre desastres naturais e inadimplência.

As principais técnicas consideradas são:

* **Causalidade de Granger**, utilizada para avaliar se informações passadas sobre a ocorrência de desastres contribuem para prever o comportamento futuro da inadimplência;

* **Modelos de Defasagens Distribuídas (Distributed Lag Models)**, utilizados para estimar como o efeito associado aos desastres se distribui ao longo dos períodos subsequentes;

* **Painel dinâmico UF × mês (histórico)**, para relacionar a exposição de cada estado à sua inadimplência;

* **Projeções locais, Toda–Yamamoto e previsão temporal (histórico)**, como análises complementares, conforme os critérios de viabilidade documentados. SARIMAX não foi estimado nesta segunda etapa.

Também são realizados procedimentos de diagnóstico e tratamento das séries temporais, incluindo testes de estacionariedade e análise da estrutura de autocorrelação.

## Estrutura do repositório

```text
.
├── data/
│   ├── raw/
│   │   ├── bacen/
│   │   └── atlas_desastres/
│   ├── interim/
│   └── processed/
│
├── notebooks/
├── src/
│
├── outputs/
│   ├── figures/
│   └── tables/
│
├── docs/
│
└── tcc/
    ├── capitulos/
    ├── figuras/
    └── bibliografia/
```

### `data/raw`

Contém os arquivos originais obtidos diretamente das fontes de dados.

Os arquivos armazenados neste diretório não devem ser alterados manualmente.

### `data/interim`

Contém bases intermediárias resultantes das etapas de limpeza, padronização, agregação e transformação dos dados.

### `data/processed`

Contém as bases finais utilizadas nas análises estatísticas e nos modelos.

### `notebooks`

Contém os notebooks responsáveis pelas análises exploratórias, procedimentos estatísticos e estimação dos modelos.

Os notebooks são organizados de forma sequencial de acordo com as etapas da análise.

### `src`

Contém os scripts responsáveis pelas etapas de preparação, transformação e integração das bases de dados, além de funções e rotinas reutilizáveis ao longo do projeto.

### `outputs`

Contém os principais resultados produzidos pelas análises:

* `figures/`: gráficos utilizados nas análises e na monografia;
* `tables/`: tabelas e resultados estatísticos.

### `docs`

Contém documentação complementar do projeto, como dicionário de variáveis, decisões metodológicas e descrição do processamento das bases.

### `tcc`

Contém os arquivos relacionados ao texto final da monografia, incluindo capítulos, figuras e referências bibliográficas.

## Fluxo de processamento

O projeto segue, de forma geral, o seguinte fluxo:

```text
Dados brutos
    │
    ├── SCR / BACEN
    │
    └── Atlas Digital de Desastres
    │
    ▼
Limpeza e padronização
    │
    ▼
Construção das bases intermediárias
    │
    ▼
Integração das fontes
    │
    ▼
Base final de análise
    │
    ├── Análise descritiva
    ├── Testes de estacionariedade
    ├── Causalidade de Granger
    ├── Modelos de defasagens distribuídas
    └── Painel, resposta temporal e previsão
```

## Reprodutibilidade

Os dados brutos e bases processadas de grande volume não são versionados pelo Git.

Para reproduzir as análises, os arquivos das fontes originais devem ser armazenados localmente nas seguintes pastas:

```text
data/raw/bacen/
data/raw/atlas_desastres/
```

As etapas de processamento foram estruturadas de forma que as bases utilizadas nas análises possam ser reconstruídas a partir dos dados originais por meio dos scripts disponíveis em `src/`.

## Status

Projeto em desenvolvimento.


## Ampliação: grupos e tipologias (2013–2024 e pré-pandemia)

A ampliação mantém os notebooks 05 e 06 e acrescenta:

- `notebooks/07_estacionariedade_grupos_tipologias.ipynb`: auditoria do Atlas/Parquet, reconciliação e estacionariedade por recorte;
- `notebooks/08_granger_grupos.ipynb`: execução conjunta das famílias de testes e interpretação de grupos/referência;
- `notebooks/09_granger_tipologias.ipynb`: resultados e interpretações por tipologia;
- `outputs/tables/ampliacao/`: resultados completos, incluindo não significativos;
- `docs/ampliacao_metodologia.md`: decisões, hipóteses, limitações e reprodução.

A unidade validada é protocolo municipal: 40.339 registros únicos em 2013–2024, com reconciliação integral ao Parquet. São 4 grupos e 16 tipologias. Pré-pandemia termina em **janeiro de 2020**, inclusive (85 meses).

Nesta execução, 29 das 235 hipóteses únicas na direção desastres → inadimplência têm significância nominal, mas nenhuma permanece após Benjamini–Hochberg. A estacionariedade da inadimplência transformada é inconclusiva no pré-pandemia; a inferência desse recorte é exploratória. Consulte os notebooks para as limitações e os resultados inversos. Não se trata de prova de ausência de efeitos causais.

Após instalar as dependências e disponibilizar localmente as duas bases:

```powershell
python -m pip install -r requirements.txt -r requirements-ampliacao.txt
python src/executar_notebooks_categorias.py
```

O HTML standalone é entregue separadamente, fora do GitHub. Seu gerador está em `src/relatorio_categorias.py`; o template textual é código-fonte, sem dados embutidos. Para gerar uma cópia fora do repositório:

```powershell
python src/relatorio_categorias.py --output ..\relatorio_grupos_tipologias_tcc.html
```

Os notebooks incluem os gráficos; a execução também produz PNGs locais em `outputs/figures/ampliacao/`. Não são versionadas as bases brutas nem as séries intermediárias.


## Segunda etapa: dinâmica, exposição e localização geográfica

Extensão informada pela análise anterior; protocolo registrado **antes dos novos testes**, commit `b667d451519711dc0fa2f48ad3d0138e360e86be`. Não é confirmação independente e não busca significância por alterações dos recortes.

| Notebook executado | Conteúdo |
|---|---|
| `10_dinamica_nacional_segunda_etapa.ipynb` | ADL com ordens próprias/cruzadas diferentes, amostra comum BIC, sazonalidade, quebras, diagnósticos e TY condicionado à viabilidade |
| `11_exposicao_gravidade_segunda_etapa.ipynb` | Auditoria de frequência, municípios, deslocamento e habitações; foco classificação original do Atlas12/13/14; modelos e BH da família nacional completa |
| `12_painel_uf_segunda_etapa.ipynb` | UF×mês, TWFE dinâmico, DK, sensibilidade SPJ e influência das UFs |
| `13_resposta_previsao_segunda_etapa.ipynb` | Projeções locais1/3/6/12 meses; previsão expansiva sem divisão aleatória; IC e limitações de disponibilidade |

**Conclusão:** nenhuma rejeição ajustada com todos os diagnósticos favoráveis. Vendavais/Ciclones tem rejeiçõesHAC apósBH, porém q0 é preferido e há limitações de RESET/estacionariedade; testes clássicos/HC3 não confirmam evidência ajustada. As quatro medidas climáticas, o painel e as projeções locais não dão confirmação robusta. Acrescentar desastres não melhora o RMSE nas72 previsões do período total. Pré-pandemia tem13 alvos: descrição, sem inferência qualificada. Ausência de evidência robusta não prova ausência de impactos.

Documentação: [protocolo](docs/segunda_etapa_protocolo.md), [resultados e interpretação](docs/segunda_etapa_resultados.md), [fontes](docs/segunda_etapa_fontes.md), [progresso/checkpoints](docs/segunda_etapa_progresso.md). Tabelas completas em `outputs/tables/segunda_etapa/`, com famílias fixas, p originais/ajustados, coeficientes/IC, amostras, diagnósticos e exclusões. Os notebooks05–09 e seus resultados ajustados permanecem preservados. O ajuste do10 era provisório com reservas p=1; o11 contém a família nacional final50, sem reduzir hipóteses.

### Reprodução

As entradas continuam locais e ignoradas peloGit:

- `data/processed/df_tcc_2013_2024.parquet` — SHA256 `49991105866dc140e959bfd9200b780c76edae0b8c95c31040bcdbde7811afe5`.
- `data/raw/atlas_desastres/BD_Atlas_1991_2024_v1.0_2025.04.14_Consolidado.csv` — SHA256 `6ca29008a60a30e9f45d0f451da7750f850d8902704487798e1ef39ca3da44af`.

```powershell
python -m pip install -r requirements-segunda-etapa.txt
# Reestimar a segunda etapa integralmente, preservando05–09:
python src/executar_segunda_etapa.py --recalcular
# Verificar saídas publicadas, sem bases locais nem reestimação:
python src/verificar_saidas_publicadas.py
# Verificação original com os intermediários disponíveis:
# python src/verificar_segunda_etapa.py
# O relatório HTML foi mantido fora do controle de versão.
```

O executor usa processosPython novos e captura tabelas/Markdown/PNG sem depender de socketsJupyter. `--recalcular` é um alias de `--reproduzir` e preserva um backup local antes de reexecutar; para retomar trabalho validado, leia tabelas/checkpoints antes de executar novamente. Checkpoints registram hashes de entradas, código, protocolo e tabelas; etapas futuras só podem reutilizá-los após conferir diferenças de código/entradas. Não certificar equivalência de código modificado por mera presença deCSV.

Limitações centrais: p-valores condicionais à seleçãoBIC; dados administrativos e zeros de significado incompleto; nenhuma unicidade de pessoas/imóveis; monetários excluídos por mês-base não confirmado; SCRbruto não disponível; sem vintagesAtlas; confundimento econômico deUF não eliminado; dependência e viés dinâmico do painel. BootstrapH0 e simulação de poder não foram usados para resgatar modelos reprovados. HTML final e bases brutas não são publicados.


## Extensão 14: transformações e adequação

O notebook executado `notebooks/14_adequacao_transformacoes.ipynb` compara primeiras diferenças, variações relativas e suas versões com diferença sazonal. Utiliza datas comuns e famílias fixas de **200 hipóteses nacionais e 32 de painel**, sem escolher transformações pelo menor p-valor. [Protocolo prévio](docs/adequacao_protocolo.md), [resultados completos](docs/adequacao_resultados.md) e [verificação da retomada](docs/retomada_final_verificacao.md).

**Conclusão atual:** 41 cenários nacionais têm triagem diagnóstica favorável, todos no período total e nas versões sazonais. Há 44 rejeições nominais e 11 após BH/HAC; apenas Onda de Frio sazonal combina BH com triagem favorável (p=0,002176; BH=0,039558). Esse sinal é exploratório: BIC prefere q=0, BH clássico/HC3 e BY/Holm não confirmam significância. Os demais resultados ajustados têm limitações diagnósticas. No painel: 2 nominais, nenhuma após BH, autocorrelação persistente. As melhorias não estabelecem precedência robusta geral ou causalidade estrutural.

As análises 05–13 e seus ajustes foram preservados. A reprodução da extensão requer `data/processed/segunda_series_completas.parquet` e `segunda_painel.parquet`, produzidos pela etapa 11. Seus hashes estão em `outputs/tables/adequacao/checkpoint_14.json`. Esses intermediários e as bases brutas não são publicados.

```powershell
python -m pip install -r requirements-segunda-etapa.txt
# Apenas conferir as saídas entregues (sem reestimar):
python src/verificar_saidas_publicadas.py
# Reexecutar 14 somente com os intermediários e hashes conferidos:
python src/executar_notebooks_categorias.py notebooks/14_adequacao_transformacoes.ipynb
```

O HTML final permanece externo ao GitHub. Na retomada de 02/10/2026, foram recuperados e conferidos os resultados executados, sem recalcular análises anteriores. Ausência de evidência robusta não demonstra ausência de impactos econômicos dos desastres.


## Encerramento 15: mapa completo de Granger

[Notebook 15 executado](notebooks/15_fechamento_granger_grupos_tipologias.ipynb), [protocolo](docs/granger_fechamento_protocolo.md), [resultados e limitações](docs/granger_fechamento_resultados.md) e [matriz dos 42 cenários](outputs/tables/granger_fechamento/matriz42.csv).

Total nacional, quatro grupos e 16 tipologias nos recortes jan/2013–jan/2020 (85 meses) e jan/2013–dez/2024 (144 meses). Principal sazonal com ordens fixas; três sensibilidades finitas, famílias BH/BY/Holm de 42 e 126 hipóteses e sensibilidade global de 168. Ajustes históricos preservados. Amostras efetivas comuns: 60 e 119 meses.

**Conclusão:** há dez rejeições BH na principal (cinco por período); nove têm limitações na triagem. Granizo no período total combina BH e triagem ampliada favorável na referência HAC, mas perde a rejeição nas inferências clássica/HC3 e no BIC. É um sinal exploratório sensível à especificação. Onda de Frio também não fornece confirmação robusta. A estacionariedade da inadimplência pré-pandemia permanece inconclusiva. Dois cenários pré são inelegíveis por escassez, preservados na matriz e na família. Podemos encerrar Granger com essas limitações documentadas; nenhum método seguinte foi executado.

```powershell
python -m pip install -r requirements-granger-fechamento.txt
# Reutilizar resultados após conferir entradas, código, protocolo e tabelas:
python src/executar_granger_fechamento.py --retomar
# Conferir saídas sem reestimar (não certifica pressupostos):
python src/verificar_granger_fechamento.py --somente-saidas
# Reprodução integral apenas da etapa 15, com agregados publicados:
python src/executar_granger_fechamento.py --reproduzir
# Etapas antigas: conferir sem recálculo; exige bases/hashes compatíveis:
python src/executar_segunda_etapa.py --retomar
# Reproduzir 10–13 exige bases originais; preserva backup local:
python src/executar_segunda_etapa.py --reproduzir
```

A etapa 15 usa agregados com hash validado, sem publicar bases brutas. A ausência das bases impede recuperar códigos numéricos originais do Atlas e reconstruir integralmente 10–13; os nomes e contagens foram preservados. A retomada distingue verificação de arquivos, reprodução e diagnósticos estatísticos. Checkpoints históricos divergentes ou entradas ausentes interrompem a retomada sem recálculo silencioso. O HTML final é entregue fora do repositório.

## Fechamento do DLM — versão 4 (outubro de 2026)

A referência metodológica atual do DLM de painel está em [docs/dlm_fechamento_v4_decisao.md](docs/dlm_fechamento_v4_decisao.md). A especificação é o DLM irrestrito UF×mês com efeitos fixos de UF e mês-ano, y=Δlog(I), x=Δlog(1+D) e K selecionado por AIC (1–24) em amostra comum. A inferência principal utiliza Driscoll–Kraay com banda de Bartlett definida pela regra L=⌊4(T/100)^(2/9)⌋ (pré L=3; total L=4), proteção Bonferroni dos 24 horizontes candidatos e ajuste Holm entre exposições nas famílias definidas. DK6 e DK12 são sensibilidades; BH é comparação, não a referência principal.

O [notebook 26](notebooks/26_dlm_fechamento_especificacao_inferencia_v4.ipynb), os scripts `src/dlm_inferencia_banda_regra_v3.py` e `src/dlm_fechamento_diagnosticos_v4.py`, os arquivos de [inferência](outputs/tables/dlm_inferencia_banda_regra_v3/resultados.csv) e as [tabelas da inferência final](outputs/tables/dlm_inferencia_banda_regra_v3/resultados.csv) documentam o fechamento. Com DK por regra + seleção protegida + Holm não houve rejeições a 5%; DK6 também não, ao passo que DK12 registrou sete rejeições complementares, não persistentes entre as bandas. Os achados são exploratórios e não estabelecem causalidade. A tentativa de calibração transversal que falhou foi preservada para auditoria; seus p-valores não fazem parte da inferência adotada.

Os [coeficientes de todos os K](outputs/tables/dlm_inferencia_banda_regra_v3/coeficientes_todos_K.csv), os resultados numéricos e as auditorias permanecem versionados na `main`. Relatórios e apresentações HTML são materiais de consulta local, não publicados no GitHub. Para reprodução integral, são necessárias as bases locais não versionadas. As implementações antigas (como o notebook 23 e os resultados CR1/DK6 sem proteção de seleção) permanecem no histórico e não substituem o fechamento v4.
