# Resumo numérico da execução

Esta página é gerada por [gerar_sintese_base_corrigida.py](../src/gerar_sintese_base_corrigida.py) a partir das tabelas publicadas. A interpretação está em [Resultados](resultados.md).

Painel: 3.888 observações; 27 UFs e 144 meses. Registros do Atlas: 40.339.

| Análise | Resumo |
| --- | --- |
| Granger | 627/864 estimáveis; 56 rejeições nominais e 16 após BH |
| Granger: diagnóstico residual | 3 aplicações com rejeição BH também rejeitaram no Ljung–Box |
| DLM ampliado, 0 a K | 39/42 estimáveis; 5 contrastes com rejeição após ajustes na banda de referência |
| DLM por tipologia | 29/32 estimáveis por AIC; 29/32 por BIC |
| DLM ampliado, 3 a K | 39/42 estimáveis; rejeições ajustadas por banda: dk12: 0; dk6: 0; dk_regra: 0 |
| SARIMAX individual, 0 a K | 452/896 estimáveis; 22 com BIC menor; 173 com RMSE menor; 5 com ambos menores |
| SARIMAX geral, 0 a K | 54/56 estimados; 0 com BIC e RMSE menores |
| SARIMAX individual, 3 a K | 452/896 estimáveis; 29 com BIC menor; 170 com RMSE menor; 6 com ambos menores |
| SARIMAX geral, 3 a K | 55/56 estimados; 1 com BIC e RMSE menores |

O BH de Granger é por UF e recorte. Os contrastes DLM usam os ajustes da grade e de família. No SARIMAX, a comparação é com o SARIMA da mesma unidade e recorte.

SHA-256 do painel: `d795e0ed176cc4628e1b02a81bc32ecab449f24aefc3e9be91d291479f46c043`.

[Índice das tabelas](../outputs/tables/modalidades_excluidas_20261104/README.md) · [Reprodução](reproducao.md)
