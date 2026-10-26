# Documentação — TCC

Este índice distingue **o material da análise corrente** das notas de versões anteriores. O histórico foi preservado para permitir rastrear decisões e reproduzir os resultados anteriores.

## Leitura recomendada

1. [DLM complementar com defasagens 3–24 (26/10/2026)](dlm_defasagens_3a24_20261026.md) — justificativa dos 90 dias, busca AIC, dois menores AICs, DK e tabelas.
2. [SARIMAX por tipologia e geral, K=0–24 (26/10/2026)](sarimax_por_tipologia_e_geral_20261026.md) — nova análise principal da revisão, todos os tipos e UFs, seleção individual, composição do geral e resultados por período.
3. [Notebooks principais](../notebooks/README.md) — execução e resultados anteriores de Granger, DLM e SARIMA/SARIMAX.
4. [Auditoria anterior das 16 tipologias simultâneas (26/10/2026)](sarimax_16_tipologias_estimabilidade_20261026.md) — 216 matrizes, motivos de não estimabilidade e quatro ajustes possíveis em MG/total.
5. [Busca anterior de lags SARIMAX (26/10/2026)](sarimax_busca_sistematica_lags_20261026.md) — quatro blocos consecutivos e limite amostral de parâmetros.
6. [Roteiro das respostas à orientação (26/10/2026)](roteiro_respostas_orientadora_20261026.md) — comparações históricas, Driscoll–Kraay e limitações.
7. [Revisão técnica das defasagens (24/10/2026)](nota_defasagens_20261024.md) — decisões, inferência e comandos de reprodução.
8. [Auditoria metodológica dos notebooks (20/10/2026)](auditoria_metodologica_20261020.md) — dados, modelagem e validações.
9. [SARIMA/SARIMAX estadual e nacional (19/10/2026)](sarimax_revisao_estadual_nacional_20261019.md) — versão histórica.

## Princípios da análise corrente

- DLM de painel TWFE original com `K=1,...,24` por **AIC**, preservado. Nova sensibilidade com regressoras **somente de 3 a K**, onde `K=3,...,24`, também por AIC. DK com banda por regra e sensibilidades 6/12; não usar horizontes fixos.
- SARIMAX individual por tipologia e UF/período, com busca sistemática de **25 blocos consecutivos K=0,...,24**. Na sequência, SARIMAX geral com defasagens individuais selecionadas e inclusão de todos os tipos identificáveis; sem limite pré-definido de 4/6 tipologias.
- SARIMAX nacional geral inclui **as 16 tipologias** com os K selecionados: 18 regressoras climáticas no pré e 16 no total. Não se confunde com as tentativas anteriores de impor blocos longos simultaneamente às 16 tipologias estaduais.
- Os resultados históricos com quatro blocos `[0]`, `[0,1]`, `[0,1,2]`, `[0,1,2,3]` e com as 16 tipologias obrigatórias foram preservados como experimentos anteriores.
- Interpretação de associações e previsão **condicional**, sem alegações causais.

## Resultados e navegação

- [Painel interativo de defasagens](../outputs/reports/defasagens_metodos.html).
- [Comparação dos dois menores AICs](../outputs/reports/dlm_aic_duas_melhores_defasagens.html).
- [Tabelas do DLM revisado](../outputs/tables/revisao_defasagens_20261024/).
- [DLM complementar 3 a K: todos os AICs, coeficientes e testes](../outputs/tables/dlm_lags_3a24_20261026/).
- [SARIMAX individual e geral: 22.400 candidatos, coeficientes e resultados](../outputs/tables/sarimax_por_tipologia_k0_24_20261026/).
- [Auditoria e ajustes com as 16 tipologias](../outputs/tables/sarimax_todas_tipologias_20261026/).
- [Tabelas da sensibilidade sistemática com subconjuntos](../outputs/tables/sarimax_lags_sistematicos_20261026/).
- [Tabelas do SARIMAX defasado anterior, preservadas](../outputs/tables/sarimax_defasagens_20261024/).
- [Notebooks exploratórios e versões anteriores](../notebooks/historico/).

As notas antigas em `docs/` e os notebooks em `notebooks/historico/` são mantidos como histórico, não como especificação principal da monografia. Resultados metodológicos ainda sob revisão estão identificados no roteiro mais recente.
