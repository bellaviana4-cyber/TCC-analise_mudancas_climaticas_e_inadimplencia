# Tabelas da versão final

As tabelas correspondem ao painel de pessoas físicas com as três exclusões de modalidade, de janeiro de 2013 a dezembro de 2024. O [manifesto](manifesto.json) registra o filtro e os identificadores das fontes.

## Consultas por etapa

| Etapa | Arquivos principais |
| --- | --- |
| Descritiva | [Série nacional mensal](descritiva_nacional_mensal.csv), [agregação anual](descritiva_anual.csv), [registros por região](descritiva_regioes.csv) |
| Estacionariedade | [ADF e KPSS por UF, recorte e série](granger/estacionariedade_adf_kpss.csv) |
| Granger | [Todas as aplicações](granger/granger_aplicacoes.csv), [rejeições nominais](granger/granger_rejeicoes_nominais.csv), [rejeições após BH](granger/granger_rejeicoes_bh.csv) |
| DLM por AIC/BIC | [Seleção](dlm_aic_bic/dlm_selecao.csv), [candidatos](dlm_aic_bic/dlm_candidatos.csv) |
| DLM ampliado, 0 a K | [Seleção de K](dlm0/selecao_K.csv), [inferência ajustada](dlm0_inferencia/resultados.csv) |
| DLM, dois menores AICs | [Modelos](dlm_top2/dlm_dois_menores_aic.csv), [inferência](dlm_top2/dlm_inferencia_top2.csv) |
| DLM, 3 a K | [Resumo](dlm3/resumo.json), [resultados](dlm3/resultados.csv) |
| SARIMAX, 0 a K | [Individuais](sarimax0/resumo.csv), [gerais](sarimax0/geral.csv), [resumo da grade](sarimax0/resumo.json) |
| SARIMAX, 3 a K | [Individuais](sarimax3/resumo.csv), [gerais](sarimax3/geral.csv), [resumo da grade](sarimax3/resumo.json) |

## Validação e rastreabilidade

- [Hash, cobertura e recorte do painel](manifesto.json).
- [Hashes dos 144 arquivos mensais do SCR](fontes_scr_sha256.csv).
- [Agregação do primeiro e do último mês](validacao_agregacao_independente.csv).
- [Verificação independente de Granger](granger/validacao_independente.csv).
- [SARIMAX 0 a K](validacao_sarimax.csv) e [SARIMAX 3 a K](validacao_sarimax_lag3.csv).
- [Integridade SARIMAX 0 a K](integridade_sarimax.json) e [SARIMAX 3 a K](integridade_sarimax_lag3.json).

As pastas de cada método também contêm candidatos, coeficientes, diagnósticos e arquivos intermediários. `Pré` indica o recorte até janeiro de 2020 e `Total` indica o período até dezembro de 2024.

As definições das métricas e a interpretação dos ajustes estão em [Metodologia](../../../docs/metodologia_e_sensibilidades.md) e [Resultados](../../../docs/resultados.md).
