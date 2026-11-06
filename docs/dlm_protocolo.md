# Protocolo metodológico pré-interpretação — DLM

Registro elaborado antes da interpretação dos resultados da etapa DLM. A main em 027ee8a é a fonte de verdade operacional; o PDF do TCC é a referência conceitual.

- Unidade principal: painel balanceado UF × mês, 27 UFs. A base atual é construída para jan/2013–dez/2024 (3.888 UF-mês); o recorte pré-pandemia termina em jan/2020. A execução deve validar novamente cobertura, duplicidades e lacunas.
- Dependente: taxa de inadimplência PF = 100 × carteira inadimplente / carteira ativa. Não se usa média simples entre UFs.
- Exposições: total, quatro grupos e tipologias da taxonomia consolidada. Modelos são separados por exposição; tipologias não são empilhadas simultaneamente.
- Estimabilidade ex ante: estimável se ≥100 eventos, ≥50 UF-mês positivos, ≥10 UFs expostas, variação within positiva e concentração máxima por UF ≤75%; estimável com ressalvas se ≥24 eventos, ≥12 UF-mês positivos, ≥5 UFs e variação within positiva; demais não estimável. O critério não usa p-valores.
- Transformação principal de exposição: log1p(contagem), por assimetria/zeros e interpretação estável. Contagem em nível é robustez, não mecanismo de seleção por significância.
- Estacionariedade: resultados nacionais de Granger não são transferidos automaticamente ao painel. A execução deve documentar testes/padrões estaduais; diferenciação da dependente só é adotada se exigida pela evidência e muda o estimando.
- FE principal: UF + mês-ano completo. O coeficiente é identificado por diferenças de exposição entre UFs dentro do mesmo mês, após remover heterogeneidade permanente. Robustez limitada: UF + mês do ano; UF + tendência.
- Horizonte: K ∈ {3,6,9,12}, fixado antes dos resultados. Seleção principal por BIC entre modelos comparáveis, com AIC reportado; desempate pelo menor K. K não é escolhido por significância.
- DLM irrestrito é o ponto de partida. Almon é acionado quando o perfil irrestrito apresenta forte dependência dos lags (correlação máxima >0,80 ou condition number >30); q ∈ {2,3}, q<K, escolhido por BIC/parcimônia, nunca por p-valor.
- Koyck não é principal. Só seria justificável se o perfil empírico e o mecanismo substantivo sustentassem decaimento geométrico monotônico.
- Inferência principal: erros-padrão clusterizados por UF. Como há 27 clusters, isso é limitação explícita; robustez deve considerar inferência alternativa apropriada sem buscar significância.
- Quantidades centrais: β0; perfil β0…βK; teste conjunto H0: β0=…=βK=0; efeito acumulado no horizonte K = Σβk, com variância calculada pela matriz completa de covariância.
- Multiplicidade: BH/FDR por famílias coerentes de período × nível (Total/Grupo/Tipologia), separadamente para teste conjunto e efeito acumulado. P nominal e p ajustado permanecem visíveis.
- Diagnóstico não depende de significância: autocorrelação, heterocedasticidade, dependência transversal, multicolinearidade e estabilidade. Classes: adequado; adequado com ressalvas; inadequado para inferência substantiva.
- Leakage: todos os shifts são feitos dentro da UF e há assert de que o primeiro mês de cada UF não recebe lag da UF anterior.
- Robustez limitada: irrestrito × Almon; K vizinhos; log1p × nível; três estruturas temporais; total × pré-pandemia. A tabela multiverse deve ser curta e transparente.
- Terminologia recomendada para a redação final: substituir “efeito acumulado de longo prazo” por “efeito acumulado no horizonte K”, pois K é finito.
- Interpretação: associação condicional, não efeito causal estrutural. FE temporais reduzem confundimento nacional comum, mas não certificam exogeneidade estrita nem eliminam confundidores UF-tempo.
