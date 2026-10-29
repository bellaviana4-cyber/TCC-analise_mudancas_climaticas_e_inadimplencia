# Checkpoint de execução — DLM

Status: **executado e validado em 2026-10-03**.

Entradas locais usadas na execução:

- `df_tcc_2013_2024.csv`: SHA256 `46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36`, 3.888 linhas;
- `BD_Atlas_1991_2024_v1.0_2025.04.14_Consolidado.csv`: SHA256 `6ca29008a60a30e9f45d0f451da7750f850d8902704487798e1ef39ca3da44af`, 40.339 registros no recorte 2013–2024.

As bases permanecem fora do repositório. A análise é reproduzida localmente ao disponibilizar os arquivos nos caminhos documentados.

## Decisões confirmadas antes da interpretação

1. A dependente foi alterada de nível para `Δ taxa de inadimplência` devido à evidência de não estacionariedade em nível no painel. A alteração era permitida pelo protocolo e muda explicitamente o estimando.
2. A exposição principal é `log1p(contagem)` em nível.
3. K foi selecionado por BIC em amostra comum, na grade predefinida {3,6,9,12}; K=3 em todos os cenários estimados.
4. Almon não foi acionado porque nenhum cenário ultrapassou os gatilhos de multicolinearidade predefinidos.
5. BH/FDR usa famílias planejadas por período × nível. Cenários não estimáveis entram implicitamente como p=1 para preservar o tamanho planejado da família.
6. O shift de exposições é feito dentro da UF; o sanity check impede leakage entre estados.

## Validação final

- cenários planejados: 42;
- modelos estimados: 40;
- não estimáveis no pré-pandemia: 2;
- efeito acumulado significativo após FDR: 1;
- testes conjuntos significativos após FDR: 6;
- lags individuais significativos após FDR: 0;
- UFs: 27;
- período total: jan/2013–dez/2024;
- pré-pandemia: jan/2013–jan/2020;
- inferência principal: cluster UF, 27 clusters, referência t/F com 26 gl;
- robustez inferencial: Driscoll–Kraay, bandwidth 12.

Arquivos de resultados versionados nesta branch devem ser lidos em conjunto com `docs/dlm_resultados.md` e `docs/dlm_protocolo.md`. O HTML interativo final é deliberadamente entregue apenas no chat e não é versionado no GitHub.
