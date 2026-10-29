# Notebooks

Os cinco notebooks organizam as análises do trabalho na ordem de apresentação. O processamento dos dados está em `src/`; as tabelas e figuras correspondentes estão em `outputs/`.

1. [Análise descritiva](01_analise_descritiva.ipynb): cobertura, evolução temporal, distribuição de desastres e inadimplência por região e UF.
2. [Estacionariedade](02_estacionariedade.ipynb): séries em nível, decomposições, transformações, testes ADF/KPSS e gráficos ACF/PACF.
3. [Causalidade de Granger](03_granger_ufs_tipologias.ipynb): testes de precedência temporal por UF e tipologia, seleção de defasagens e diagnósticos.
4. [DLM em painel](04_dlm_painel_aic_bic.ipynb): efeitos fixos, seleção por AIC e BIC, inferência robusta e defasagens de 3 a K.
5. [SARIMA e SARIMAX](05_sarima_sarimax_estadual_nacional.ipynb): modelos por tipologia e geral, blocos de 0 a K e de 3 a K, comparação de ajuste e previsão.

Os dois primeiros notebooks utilizam as tabelas descritivas e as séries nacionais disponíveis no repositório. Para reestimar os modelos dos demais notebooks é necessário preparar a base UF-mês indicada em [dados e reprodução](../data/README.md). As tabelas de resultados já obtidos podem ser consultadas sem refazer a estimação.

Os demais cadernos de desenvolvimento e as análises complementares estão em [historico/](historico/), com as respectivas especificações e resultados preservados.

Detalhes de metodologia, correções para testes múltiplos e análise das defasagens estão em [metodologia e sensibilidades](../docs/metodologia_e_sensibilidades.md).
