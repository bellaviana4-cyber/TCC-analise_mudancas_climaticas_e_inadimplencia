# Transformações e adequação — resultados executados

Protocolo: commit1e598373ca0d9b2ec796a5d7b031be30da3fe188, registrado antes dos novos testes. Extensão exploratória informada; notebook14 integralmente executado. Preservados05–13. Não foram escolhidas transformações ou períodos por p menor.

## O que melhorou

200 hipóteses nacionais planejadas,192 estimáveis e8 exclusões por raridade. Família BH/Holm fixa200. No total, diferença sazonal tem21 de25 triagens favoráveis; relativa+sazonal20 de25. Primeira diferença simples e relativa:0; pré-pandemia:0 nas quatro. Portanto41 cenários com triagem favorável, todos com BIC preferindo q=0. Separar pressupostos e utilidade evita chamar q0 de diagnóstico inadequado.

A referência Total nacional usa119 observações em todas transformações e60 no pré, em datas comuns. Na diferença simples total, RESETp0,01114; na sazonal RESETp0,58755, BG1p0,79515 eBG12p0,10135, CUSUMp0,64625. A forma funcional e resíduos melhoraram. Total sazonal tem pHAC0,039265 eBH0,185514: nominal apenas. Total relativa+sazonal p0,061496/BH0,244833. No pré, estacionariedade de I continua inconclusiva; não forçar novas diferenças até aprovar.

Comparação das novas referências simples com notebook10 envolve redução para datas comuns após25 meses; não atribuir mudanças de p somente à transformação. BIC não é comparável entre escalas de desfecho distintas. Δ12 muda o estimando e pode introduzir dependência MA/sobrediferenciação; ACF e variância constam nas tabelas, sem solução automática.

## Significância e diagnóstico separados

44 rejeições nominais e11BH/HAC na família nacional de200; só1 delas tem triagem favorável: Onda de Frio, total, diferença sazonal. F_HAC9,8336, p0,002176, BH0,039558; soma0,013698pp por unidade de Δ12Δlog exposição, IC95%HAC[0,005046;0,022351]. Não é resposta estrutural acumulada, nem efeito causal. q0 preferido, ΔBIC1,12850. Clássico p0,060902 eHC3p0,044401, masBHclássico0,451127 eBHHC30,535693. Holm não confirma significância ajustada. Resultado exploratório sensível à inferência; não confirma precedência robusta.

Outras10 rejeiçõesBH/HAC têm falhas/inconclusões: Vendavais/Ciclones em diferenças simples/relativas, Alagamentos, grupoOutros, grupoClimatológico eHabitações climáticas, conforme cenário/período. Todos permanecem nas tabelas sem filtragem antes do ajuste. Nenhuma rejeição ajustada foi confirmada pelo BH de clássico/HC3. Não reduzir famílias para recuperar significância. RejeiçõesBH/HAC anteriores são preservadas em suas famílias originais50/25, não substituídas pelas novas200.

## Painel UF × mês

32 hipóteses,2 rejeições nominais e0BH. Nenhuma triagem inteiramente favorável. Sazonalidade elevou concordância ADF/KPSS da inadimplência para100% das UFs no total, mas autocorrelação auxiliar persistiu (p≈0,011 nas diferenças sazonais). Pré: concordância passa de51,9% para77,8% com diferença sazonal, abaixo do gate80%; autocorrelação passa a rejeitar fortemente. Habitações total sazonal p0,04082/BH0,45827; habitações pré relativa+sazonal p0,04167/BH0,45827. São nominais, não confirmatórios. Algumas exposições têm insuficiente variação/convergência.

22 testes por UF/exposição/transformação tiveram falha numérica KPSSautolag por divisão degenerada em séries esparsas. Foram registrados como inconclusivos, sem trocar automaticamente a largura para obter aprovação; campos e avisos estão na tabela. Não foram convertidos em p favorável. LogI exige I>0, verificado. Transformações computadas porUF, com painel balanceado e mesmas datas por transformação. DK12/6 e clusterUF são sensibilidades; não certificam ausência de viés dinâmico ou exogeneidade. SPJ anterior permanece registrado; não reaplicado automaticamente.

## Verificações e limitações

15 verificações substantivas: dimensões/famílias, BH independente, amostras comuns entre candidatos e transformações, balanceamento, features sem I/D contemporâneo e diagnóstico sem usar p principal. Notebook executado sem erro, tabelas/figuras incorporadas. Checkpoint14 registra SHA256 de entradas, protocolo, código e tabelas. As análises nacionais/painel são novas, enquanto projeções locais, TY e previsão anteriores foram preservados sem reestimar.

A triagem não rejeitar não comprova adequação; múltiplos diagnósticos podem gerar reprovações ocasionais e ter baixa potência. Regras são fixas e diagnósticos mostrados individualmente. Inferência é condicional à seleçãoBIC; BH não corrige pós-seleção. Novas sensibilidades não constituem confirmação independente. A extensão melhora a adequação nacional sazonal, mas não oferece evidência robusta geral ou causalidade identificada. Pré-pandemia e painel permanecem limitados.

## Relatório

Novo HTML externo: oito seções com guia, fichas porcenário, filtros locais, todos os campos, motivos separados de q0, comparações visuais de diagnósticos, unidades explicadas, grupos/tipologias, exposição temporal, resposta e previsão anteriores. HTML e seu template/gerador não enviados aoGitHub; entregues no chat. Resultados anteriores não são apagados. Fontes metodológicas oficiais: https://www.statsmodels.org/stable/examples/notebooks/generated/stationarity_detrending_adf_kpss.html e https://www.statsmodels.org/stable/diagnostic.html.
