# Verificações da entrega

- Entradas efetivamente lidas: Atlas consolidado (71.929 linhas, 70 colunas) e Parquet (3.888 linhas, 33 colunas).
- Recorte Atlas 2013–2024: 40.339 protocolos distintos, nenhum ID ausente/repetido; 101 excedentes por município/data/COBRADE preservados.
- Reconciliação total, 4 grupos e 16 tipologias: nenhuma diferença nas 3.888 células UF × mês.
- Testes selecionados: 480 linhas AIC/BIC, representando 470 hipóteses distintas, 235 por direção.
- Direção principal: 29 hipóteses únicas com p<5%; zero após BH. Direção inversa: 52 nominais; 8 após BH. Nenhuma após BY.
- F restrito/irrestrito conferido numericamente contra Wald-F para a hipótese equivalente; 11 dummies preservadas no modelo restrito.
- Resultados nacionais BIC reproduzidos, direção principal: 0,292114 (dummies, lag 1), 0,356239 (sem dummies, lag 1), 0,326779 (sazonal, lag 2).
- Notebooks 07, 08 e 09 executados em processos Python novos. Nenhuma célula de código ficou sem execução; nenhuma saída de erro. O 07 inclui 44 figuras; 08 inclui 10; 09 inclui 30. PNGs embutidos foram otimizados em paleta para reduzir o tamanho, sem alterar os dados.
- HTML: scripts analisados sintaticamente; navegação de oito abas, filtros, busca, tabelas BH, cenários raros e comprimentos das transformações verificados em DOM local. Bibliotecas e dados incorporados; não há script ou stylesheet externo. Os gráficos individuais dos notebooks foram inspecionados visualmente. Não foi possível fazer renderização integral do HTML em Chromium neste runtime; a verificação de interface usou DOM com chamadas gráficas capturadas, não uma captura de tela do relatório completo.
- Os arquivos brutos do SCR não foram fornecidos: não foi certificada ausência de sobreposição de modalidades na origem. A ausência de multiplicação na agregação nacional atual foi verificada.
