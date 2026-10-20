# Notebooks principais — TCC

Este diretório mantém **um notebook principal por metodologia**, com código de estimação, verificações de entrada, diagnósticos, saídas e interpretação no mesmo arquivo.

1. [`01_granger_ufs_tipologias.ipynb`](01_granger_ufs_tipologias.ipynb) — Granger por UF e tipologia, seleção BIC entre 1 e 6 meses, correção BH e análise residual.
2. [`02_dlm_painel_aic_bic.ipynb`](02_dlm_painel_aic_bic.ipynb) — DLM TWFE por MQO, com AIC e BIC no mesmo notebook; cinco hipóteses, covariâncias, auditorias e curvas de efeitos por lag.
3. [`03_sarima_sarimax_estadual_nacional.ipynb`](03_sarima_sarimax_estadual_nacional.ipynb) — busca independente SARIMA/SARIMAX por BIC e comparação com ordens pareadas; séries estaduais e nacional.

**Ordem de leitura:** 01 → 02 → 03. Cada notebook pode ser executado isoladamente, desde que a base mensal auditada esteja em `../data/processed/df_tcc_2013_2024.csv` ou apontada por `TCC_BASE_CSV` e as dependências estejam instaladas.

Em SARIMAX, `FORCAR_REESTIMACAO=True` por padrão força a reestimação integral dos candidatos; use `False` se estiver retomando uma execução interrompida. Os notebooks escrevem tabelas em `outputs/tables/` e não devem ser executados em paralelo.

A pasta [`historico/`](historico/) contém as versões antigas, mantidas sem alterações. Os notebooks atuais substituem os anteriores como **fonte principal de execução**; os scripts em `src/` permanecem como material complementar e histórico.