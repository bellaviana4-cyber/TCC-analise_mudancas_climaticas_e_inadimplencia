# Documentação

Os documentos detalham os procedimentos de estimação, as análises de sensibilidade e os resultados disponíveis. A leitura pode começar pelos [cinco notebooks](../notebooks/README.md), que apresentam a sequência descritiva, estacionariedade, Granger, DLM e SARIMAX.

## Metodologia e resultados

1. [Metodologia e sensibilidades](metodologia_e_sensibilidades.md): variáveis, transformações, recortes, especificações e limitações.
2. [DLM com exposições de 3 a K meses](dlm_defasagens_3a24_20261026.md): amostra comum, seleção AIC, covariância Driscoll-Kraay e inferência.
3. [SARIMAX com exposições de 3 a K meses](sarimax_sensibilidade_3a24_20261026.md): seleção individual, composição dos modelos gerais e comparação com o SARIMA.
4. [SARIMAX com exposições de 0 a K meses](sarimax_por_tipologia_e_geral_20261026.md): especificação comparativa e resultados por UF e tipologia.

## Tabelas disponíveis

| Etapa | Tabelas |
| --- | --- |
| Descritiva | [Distribuições por tipologia](../outputs/tables/desastres_por_tipologia_2013_2024.csv), [região e ano](../outputs/tables/tabela_regiao_ano_2013_2024.csv) e [UF e ano](../outputs/tables/tabela_uf_ano_2013_2024.csv) |
| Estacionariedade | [Séries mensais nacionais](../outputs/tables/segunda_etapa/series_nacionais_agregadas.csv), [ADF/KPSS nacionais](../outputs/tables/testes_adf_kpss_series_granger_2013_2024.csv) e [diagnósticos estaduais](../outputs/tables/revisao_estadual_20261019/estacionariedade_adf_kpss.csv) |
| Granger | [Testes e diagnósticos](../outputs/tables/revisao_estadual_20261019/) |
| DLM por AIC/BIC | [Modelos de painel](../outputs/tables/dlm_painel_log_aic/) |
| DLM de 3 a K | [Candidatos e inferência](../outputs/tables/dlm_lags_3a24_20261026/) |
| SARIMAX de 0 a K | [Modelos individuais e gerais](../outputs/tables/sarimax_por_tipologia_k0_24_20261026/) |
| SARIMAX de 3 a K | [Modelos e comparações](../outputs/tables/sarimax_por_tipologia_k3_24_20261026/) |

## Análises complementares

O desenvolvimento também incluiu [busca sistemática de defasagens](sarimax_busca_sistematica_lags_20261026.md), [viabilidade de 16 exógenas simultâneas](sarimax_16_tipologias_estimabilidade_20261026.md), [revisão estadual](sarimax_revisao_estadual_nacional_20261019.md) e [auditoria metodológica](auditoria_metodologica_20261020.md). Esses documentos identificam os recortes e as especificações de cada exercício, permitindo comparar os resultados sem somar testes de diferentes famílias.

Os recortes pré-pandemia e completo se sobrepõem. Resultados não estimáveis são identificados nas tabelas, e os valores-p individuais de modelos com escolha prévia de ordens e defasagens devem ser interpretados com cautela.
