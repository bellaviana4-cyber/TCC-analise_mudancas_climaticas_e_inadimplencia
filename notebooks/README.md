# Notebooks

Os cinco notebooks principais usam a base PF com as três exclusões de modalidade, identificada em [manifesto](../outputs/tables/modalidades_excluidas_20261104/manifesto.json). Os resultados anteriores foram preservados em `historico/antes_exclusoes_modalidades/` e não representam a base corrigida. O status das reestimações está no [índice principal](../README.md).

Os cinco notebooks organizam as análises do trabalho na ordem de apresentação. O processamento dos dados está em `src/`; as tabelas e figuras correspondentes estão em `outputs/`.

1. [Análise descritiva](01_analise_descritiva.ipynb): cobertura, evolução temporal, distribuição de desastres e inadimplência por região e UF.
2. [Estacionariedade](02_estacionariedade.ipynb): ADF e KPSS por UF e período nas séries transformadas, incluindo avisos e aplicações não testáveis.
3. [Causalidade de Granger](03_granger_ufs_tipologias.ipynb): testes de precedência temporal por UF e tipologia, seleção de defasagens e diagnósticos.
4. [DLM em painel](04_dlm_painel_aic_bic.ipynb): efeitos fixos, seleção por AIC e BIC, inferência robusta e defasagens de 3 a K.
5. [SARIMA e SARIMAX](05_sarima_sarimax_estadual_nacional.ipynb): modelos por tipologia e geral, blocos de 0 a K e de 3 a K, comparação de ajuste e previsão.

Os notebooks leem as tabelas corrigidas e conferidas. O painel agregado corrigido é disponibilizado em `data/processed/df_tcc_2013_2024.csv`; os comandos de reestimação e auditoria estão no índice principal. As tabelas podem ser consultadas sem repetir os ajustes.

Os demais cadernos de desenvolvimento e as análises complementares estão em [historico/](historico/), com as respectivas especificações e resultados preservados.

Detalhes de metodologia, correções para testes múltiplos e análise das defasagens estão em [metodologia e sensibilidades](../docs/metodologia_e_sensibilidades.md).
