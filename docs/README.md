# Documentação da análise

Este índice reúne as especificações e os resultados considerados na leitura principal. As notas de experimentos anteriores permanecem disponíveis para reconstituir a evolução das análises, mas não substituem as especificações apresentadas aqui.

## Metodologia e resultados atuais

1. [Metodologia e sensibilidades](metodologia_e_sensibilidades.md) — comparação integrada das três etapas, escolhas de defasagem e limites de interpretação.
2. [DLM com defasagens de 3 a K](dlm_defasagens_3a24_20261026.md) — amostra comum, AIC, seleção K=3–24, covariância DK e rejeições.
3. [SARIMAX por tipologia e geral com lags 3 a K](sarimax_sensibilidade_3a24_20261026.md) — seleção individual, composição dos gerais e comparação pareada.
4. [SARIMAX por tipologia e geral com lags 0 a K](sarimax_por_tipologia_e_geral_20261026.md) — referência necessária para avaliar a mudança de janela.
5. [Notebooks principais](../notebooks/README.md) — código e sínteses de Granger, DLM e SARIMAX.

## Tabelas de resultados

| Análise | Arquivos |
| --- | --- |
| Granger | [Testes e diagnósticos](../outputs/tables/granger_fechamento/) |
| DLM por AIC/BIC | [Modelos de painel](../outputs/tables/dlm_painel_log_aic/) |
| DLM somente 3 a K | [Candidatos, modelos e inferência](../outputs/tables/dlm_lags_3a24_20261026/) |
| SARIMAX individual e geral, 0 a K | [Candidatos, coeficientes e métricas](../outputs/tables/sarimax_por_tipologia_k0_24_20261026/) |
| SARIMAX individual e geral, 3 a K | [Candidatos, métricas e comparações pareadas](../outputs/tables/sarimax_por_tipologia_k3_24_20261026/) |

Os dois recortes analisados são sobrepostos. Os modelos não estimáveis permanecem identificados nas tabelas, e os valores-p dos coeficientes SARIMAX devem ser lidos como exploratórios após seleção.

## Experimentos e auditorias anteriores

As seguintes notas registram etapas anteriores e não compõem a especificação principal de defasagens SARIMAX: [busca de blocos curtos](sarimax_busca_sistematica_lags_20261026.md), [tentativa com 16 tipologias simultâneas](sarimax_16_tipologias_estimabilidade_20261026.md), [revisão de defasagens de 24/10](nota_defasagens_20261024.md) e [análise estadual anterior](sarimax_revisao_estadual_nacional_20261019.md).

A [auditoria metodológica](auditoria_metodologica_20261020.md) e as [versões históricas dos notebooks](../notebooks/historico/) registram diagnósticos e decisões das etapas anteriores. Os painéis HTML antigos são documentos históricos, não a referência para a seleção atual de defasagens.
