# Código da análise

Os scripts abaixo são os pontos de entrada da versão final. Execute-os na raiz do repositório, seguindo o [guia de reprodução](../docs/reproducao.md).

| Etapa | Script | Função |
| --- | --- | --- |
| SCR | [01_consolidar_scr.py](01_consolidar_scr.py) | Seleção PF, exclusão das três modalidades e soma dos saldos por UF–mês |
| Atlas | [02_preparar_atlas.py](02_preparar_atlas.py) | Restrição temporal e agregação dos registros |
| Integração | [03_integrar_bases.py](03_integrar_bases.py) | Construção do painel e preenchimento das contagens sem registros |
| Validação dos dados | [auditar_base_com_exclusoes.py](auditar_base_com_exclusoes.py) | Cobertura, taxa, filtros e conferência dos saldos nos extremos |
| Descritiva | [analise_descritiva_base_corrigida.py](analise_descritiva_base_corrigida.py) | Tabelas e figuras a partir do painel |
| Granger, estacionariedade e DLM | [reestimar_com_exclusoes.py](reestimar_com_exclusoes.py) | Coordenação das rotinas sobre a base identificada no manifesto |
| SARIMA/SARIMAX | [executar_reestimacao_sarimax.py](executar_reestimacao_sarimax.py) | Execução das duas grades por unidade e recorte |
| Verificação Granger | [verificar_granger_com_exclusoes.py](verificar_granger_com_exclusoes.py) | Conferência independente dos testes e do ajuste BH |
| Verificação SARIMAX | [verificar_sarimax_com_exclusoes.py](verificar_sarimax_com_exclusoes.py) | Conferência de cobertura, seleção e métricas |
| Síntese | [gerar_sintese_base_corrigida.py](gerar_sintese_base_corrigida.py) | Exportação do resumo numérico da execução |

Os nomes `com_exclusoes` e `base_corrigida` identificam o recorte de crédito adotado na versão final. As exclusões integram a definição dos dados e não uma seleção posterior de resultados.

Os executores utilizam módulos auxiliares de Granger, DLM e SARIMAX mantidos nesta pasta. Alguns módulos também foram usados em versões anteriores e têm datas ou caminhos históricos próprios. Para reproduzir a versão final, utilize os pontos de entrada acima, que definem os caminhos e a proveniência das saídas.
