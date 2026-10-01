# Resultados da segunda etapa — o que a evidência sustenta

Esta é extensão informada, não confirmação independente. Preservamos os resultados anteriores (235 hipóteses,29 nominais,0BH,18 nominais com autocorrelação do sistema,4 passando triagem). Nenhum resultado desta etapa sustenta precedência robusta com significância ajustada e todos os diagnósticos favoráveis.

## Nacional

50 cenários planejados,48 estimáveis e2 excluídos por raridade no pré;25 sensibilidades com janela pandêmica. Teste conjunto de lags na equação ΔI; BIC em amostra comum, lags próprios e exposição separados,11 dummies e I12 fixo. Referência p=HAC12, não p clássico. **7 rejeições nominais e2 apósBH** na família nacional. São Vendavais e Ciclones: total pHAC0,00010139/BH0,005069; pré pHAC0,00039747/BH0,009937. Não classificadas como evidência robusta: q0 preferido nos dois e RESET rejeita (0,00756/0,02355); pré ΔI inconclusiva. Sensibilidade pandêmica tem4 nominais e1BH, também Vendavais/Ciclones, com BG1p0,02497 e q0 preferido. BH de clássicos/HC3 é reportado separadamente; diferença entre estimativas de covariância é limitação, não justificativa para escolher o menor p. Os p-valores são condicionais à seleção BIC, sem inferência pós-seleção corrigida.

Total nacional: lags próprios1, exposição1; pHAC0,320593, soma0,008858pp/Δlog, IC95%[-0,008730;0,026445]; BG1p0,07015,BG12p0,6868,CUSUMp0,6395, mas RESETp0,01456 e q0 preferido. Resíduos da equação melhoraram, sem solução integral de especificação. Portmanteau antigo é diagnóstico multivariado diferente de BG; não comparar taxas de aprovação diretamente.

Quatro medidas climáticas (protocolos, municípios, deslocamento, habitações) não foram significativas em nenhum período. Valores não certificam indivíduos/imóveis únicos. Cobertura formal100%, sem garantir que zeros foram investigados; sobreposição e extremos registrados. PEPR_total_privado coincide com soma dos componentes até arredondamento (máxima diferençaR$0,02), sem somar total a componentes; excluído de modelos por mês-base não confirmado. Foco climático por COBRADE12/13/14 preserva classificação original.

TY executado em total nacional e protocolos climáticos no período total, com d_max1, k2+1; restrições somente primeiros2 lags de D. Nenhuma rejeição (totalp0,428945). Pré não executado por gate de integração. Não usar raízes unitárias dos níveis como reprovação automática de VAR aumentado: o Portmanteau é registrado. A robustez TY não identifica causalidade estrutural.

## UF × mês

8 testes TWFE de ΔI,27 UFs, choque comum de mês-calendário, lags próprios1,2,3,12 e exposição1–3 fixos. DK12 com26GL; sensibilidades DK6/cluster UF, SPJ e leave-one-UF-out. **Nenhuma rejeição nominal ouBH**. Menor p no total: habitações0,06925/BH0,5540. Autocorrelação auxiliar rejeitada em todos indicadores total (p0,011–0,013); pré convergência estacionária51,9%UFs, abaixo80%. Não destacar estados nem interpretar DK/SPJ como cura da especificação. SPJ muda pontos e depende de homogeneidade; IC não corrigido não é IC de SPJ. Within duas vias conferido contra LSDV explícito.

## Resposta e previsão

16 projeções locais (súbitos mensal, seca janela3; horizontes1/3/6/12; ambos períodos): nenhuma rejeição nominal ouBH/Holm. Intervalos simultâneos incluem zero. Longos horizontes mostram instabilidade CUSUM; estimativas associativas, não choques causais identificados. Banda Bonferroni16 e HAC consideram comparação/sobreposição sob pressupostos, sem corrigir identificação.

Expansiva72 meses, horizonte1, ordens escolhidas em cada treino, mesmos controles próprios na comparação. Período total72 previsões por indicador: RMSE referência0,088528pp; com protocolos0,089384; municípios0,089435. MAE também aumenta. ΔMSE médio é negativo: não há ganho. Testes HAC exploratórios não significativos (p0,1591/0,1459;BH0,3182). IC bootstrap em blocos6 do diferencial é descritivo e pode divergir do teste HAC; intervalo de municípios fica ligeiramente abaixozero, indicando possível piora, não melhora. Não selecionar inferência mais favorável entre métodos. Pré13 previsões: descrição de erros e IC, sem inferência qualificada (p original ausente, p exploratório separado).

Data_Registro: mediana1 dia,Q90=12,Q99=77;11 datas anteriores ao evento;11,82% registrados em mês posterior. Não há vintages de publicação/revisão. Previsão é pseudo-OOS de dados revisados, não validação operacional real-time. SCR bruto ausente, auditoria da sobreposição de modalidades de origem permanece indisponível. Sem controles econômicos oficiais adicionais de cobertura compatível; painel absorve choques comuns, não todo confundimento de UF.

## Decisões não executadas

Sem nova deflação: mês-base monetário não certificado; sem GMM automático: N pequeno/T longo e risco de instrumentos; sem bootstrapH0 pós-seleção nacional ou simulação de poder: não usados para resgatar dinâmica inadequada. O bootstrap de erro OOS foi executado, sendo outro procedimento. Nenhum recorte alterado por significância. Nenhuma conclusão de ausência absoluta de impacto: indicadores administrativos, escala mensal/agregada e potência limitam a evidência.

## Conclusão

A segunda etapa melhora a documentação, a medida de exposição, a localização geográfica e a avaliação de previsão. A evidência de precedência desastres→inadimplência **continua inconclusiva**. Há rejeições ajustadas restritas a Vendavais/Ciclones com limitações de especificação; as medidas climáticas, o painel, as projeções locais e a previsão não fornecem confirmação robusta. É defensável relatar ausência de evidência robusta nas amostras e modelos examinados, sem concluir inexistência de efeitos econômicos dos desastres.

O painel usa peso igual por UF×mês, interpretando uma associação comum entre estados; não é uma estimativa nacional ponderada por carteira. Exposições são contagens/registros em log, sem denominador populacional externo. Os efeitos fixos absorvem tamanho permanente, não mudanças econômicas/populacionais específicas.
