# Notebooks da análise

Os cinco notebooks apresentam a investigação na ordem utilizada no trabalho. Eles leem o painel e as tabelas da versão final e contêm saídas salvas para consulta pelo GitHub.

| Ordem | Notebook | Conteúdo |
| --- | --- | --- |
| 1 | [Análise descritiva](01_analise_descritiva.ipynb) | Cobertura, distribuição dos registros e evolução da inadimplência |
| 2 | [Estacionariedade](02_estacionariedade.ipynb) | ADF e KPSS por UF e recorte nas séries transformadas |
| 3 | [Granger por UF e tipologia](03_granger_ufs_tipologias.ipynb) | Defasagens, testes conjuntos, ajuste BH e diagnóstico residual |
| 4 | [DLM em painel](04_dlm_painel_aic_bic.ipynb) | Efeitos fixos, escolha de K, associações acumuladas e sensibilidade |
| 5 | [SARIMA e SARIMAX](05_sarima_sarimax_estadual_nacional.ipynb) | Modelos individuais e gerais, treino e teste, BIC e RMSE |

## Como ler e executar

A leitura das saídas salvas não exige os arquivos brutos. Para executar as células, utilize o ambiente do [guia de reprodução](../docs/reproducao.md) e abra o notebook na raiz do repositório ou na pasta `notebooks/`. As células localizam as tabelas em `outputs/tables/modalidades_excluidas_20261104/`.

Os cadernos organizam e apresentam os resultados exportados. A reconstrução dos dados, a estimação dos modelos e as validações são executadas pelos scripts em `src/`, na sequência descrita no guia.

Todos os notebooks principais se referem ao crédito a pessoas físicas após as três exclusões de modalidade aplicadas antes da agregação dos saldos. Consulte [Dados](../data/README.md), [Metodologia](../docs/metodologia_e_sensibilidades.md) e [Resultados](../docs/resultados.md).

Os cadernos de etapas anteriores permanecem em [historico/](historico/README.md), separados do percurso principal.
