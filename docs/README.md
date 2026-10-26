# Documentação — TCC

Este índice distingue **o material da análise corrente** das notas de versões anteriores. O histórico foi preservado para permitir rastrear decisões e reproduzir os resultados anteriores.

## Leitura recomendada

1. [Notebooks principais](../notebooks/README.md) — execução e resultados de Granger, DLM e SARIMA/SARIMAX.
2. [Roteiro das respostas à orientação (26/10/2026)](roteiro_respostas_orientadora_20261026.md) — etapas, comparações, Driscoll–Kraay, SARIMAX com defasagens, tabelas e limitações.
3. [Revisão técnica das defasagens (24/10/2026)](nota_defasagens_20261024.md) — decisões, inferência e comandos de reprodução.
4. [Auditoria metodológica dos notebooks (20/10/2026)](auditoria_metodologica_20261020.md) — dados, modelagem e validações.
5. [SARIMA/SARIMAX estadual e nacional (19/10/2026)](sarimax_revisao_estadual_nacional_20261019.md) — **versão anterior** à extensão estadual com lags climáticos.

## Princípios da análise corrente

- DLM de painel TWFE com `K=1,...,24` selecionado por **AIC**, com segunda escolha auditada e Driscoll–Kraay. Não usar horizontes fixos.
- SARIMAX estadual multivariado com seleção de tipologias elegíveis no treino; extensão comparativa de lags climáticos `[0]`, `[0,1]` e `[0,1,3]`.
- SARIMAX nacional complementar com 16 tipologias contemporâneas, sem extensão de lags nesta etapa.
- Interpretação de associações e previsão **condicional**, sem alegações causais.

## Resultados e navegação

- [Painel interativo de defasagens](../outputs/reports/defasagens_metodos.html).
- [Comparação dos dois menores AICs](../outputs/reports/dlm_aic_duas_melhores_defasagens.html).
- [Tabelas do DLM revisado](../outputs/tables/revisao_defasagens_20261024/).
- [Tabelas do SARIMAX defasado](../outputs/tables/sarimax_defasagens_20261024/).
- [Notebooks exploratórios e versões anteriores](../notebooks/historico/).

As notas antigas em `docs/` e os notebooks em `notebooks/historico/` são mantidos como histórico, não como especificação principal da monografia. Resultados metodológicos ainda sob revisão estão identificados no roteiro mais recente.
