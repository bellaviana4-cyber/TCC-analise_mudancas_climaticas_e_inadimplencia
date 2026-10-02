# Mudanças Climáticas e Inadimplência

Este repositório contém os códigos, análises e materiais desenvolvidos para o Trabalho de Conclusão de Curso **“Mudanças Climáticas e Inadimplência: uma análise do impacto de desastres naturais no sistema de crédito brasileiro”**.

## Objetivo

O trabalho tem como objetivo avaliar o impacto da ocorrência de desastres naturais sobre a inadimplência de pessoas físicas no sistema de crédito brasileiro no período de **2013 a 2024**.

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

* **Painel dinâmico UF × mês**, para relacionar a exposição de cada estado à sua inadimplência;

* **Projeções locais, Toda–Yamamoto e previsão temporal**, como análises complementares, conforme os critérios de viabilidade documentados. SARIMAX não foi estimado nesta segunda etapa.

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
| `11_exposicao_gravidade_segunda_etapa.ipynb` | Auditoria de frequência, municípios, deslocamento e habitações; foco COBRADE12/13/14; modelos e BH da família nacional completa |
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
# O HTML final e seu gerador são entregues separadamente no chat.
```

O executor usa processosPython novos e captura tabelas/Markdown/PNG sem depender de socketsJupyter. `--recalcular` substitui apenas as saídas da segunda etapa; para retomar trabalho validado, leia tabelas/checkpoints antes de executar novamente. Checkpoints registram hashes de entradas, código, protocolo e tabelas; etapas futuras só podem reutilizá-los após conferir diferenças de código/entradas. Não certificar equivalência de código modificado por mera presença deCSV.

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
