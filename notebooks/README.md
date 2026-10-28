# Notebooks do TCC

Os três cadernos abaixo organizam as metodologias efetivamente utilizadas. Os resultados completos estão nos CSVs versionados em `outputs/tables/`.

1. [Granger — UFs e tipologias](01_granger_ufs_tipologias.ipynb): seleção de lags, testes de precedência temporal e diagnósticos.
2. [DLM — painel com efeitos fixos](02_dlm_painel_aic_bic.ipynb): comparação AIC/BIC, inferência robusta e sensibilidade com exposições somente de 3 a K.
3. [SARIMA × SARIMAX — análise por tipologia e geral](03_sarima_sarimax_estadual_nacional.ipynb): seleção dos blocos 0–K e 3–K, comparações com o SARIMA e resultados nacional e estaduais. **Este é o notebook vigente da etapa SARIMAX.**

O notebook 03 lê os resultados auditados das execuções por scripts. Suas células de consulta podem ser executadas sem a base bruta. Para reestimar os modelos, é necessário preparar `data/processed/df_tcc_2013_2024.csv` e executar os comandos do [README principal](../README.md). Não confundir leitura das tabelas já produzidas com reestimação.

As extensões principais são documentadas em [metodologia e sensibilidades](../docs/metodologia_e_sensibilidades.md). A pasta [`historico/`](historico/) conserva cadernos de outras etapas e a versão anterior do notebook SARIMA/SARIMAX, que trabalhava com seleção de regressores e blocos de defasagem diferentes.
