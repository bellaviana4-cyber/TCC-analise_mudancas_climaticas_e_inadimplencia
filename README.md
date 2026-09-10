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

* **Modelos SARIMAX (Seasonal Autoregressive Integrated Moving Average with Exogenous Variables)**, utilizados para modelar a dinâmica temporal e sazonal da inadimplência incorporando indicadores de desastres naturais como variáveis exógenas.

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
    └── Modelos SARIMAX
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
