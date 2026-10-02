# Fechamento de Granger — resultados executados

## Desenho e escopo

Protocolo publicado antes dos novos testes no commit f9396ee451421c2373b6e3f4badbd5ab0942bee9. Extensão exploratória informada05–14. Notebook15 executado integralmente: referência nacional,4 grupos e16 tipologias ×2 períodos. Fonte agregada SHA256 c613ebd61e25c05ebb4a4e0f3520c6570d673068d0b2ee2b6fc090468e1df679, correspondente ao checkpoint11. Nenhuma base bruta ou método seguinte reexecutado.

Principal fixa: Δ12ΔI; Δ12Δlog(1+D); intercepto; lags próprios1,2,3,12 e desastres1,2,3. Granger condicional na equação da inadimplência, não VAR/sistema. IC95% e teste conjunto HAC12, clássico/HC3 reportados. Três sensibilidades finitas: simples+dummies, relativa sazonal e sazonal BIC. Família principal42, sensibilidades126 e ajuste global168; nenhuma exclusão diagnóstica antes dos ajustes.

## Cobertura e amostras

Pré85 meses e total144 antes das transformações; amostras comuns finais60 e119, ambas fev/2015 até respectivos términos. Não foram usadas observações anteriores ao recorte para construir transformações ou lags. Principal: k8 e GL52/111. Dois cenários pré inelegíveis: Onda de Calor e Baixa Umidade(14 meses positivos,19 protocolos) e Rompimento/Colapso de barragens(6 meses positivos,15 protocolos). Permanecem na matriz e famílias; p original ausente,1 somente no ajuste. Total: todos21 estimados. Todos os nomes administrativos originais preservados; a tabela anterior permite categorias ambíguas/múltiplos grupos. **Códigos numéricos do Atlas não constam na entrada agregada validada; a base bruta ausente impede sua recuperação, sem afetar as contagens disponíveis.** A interpretação climática não transforma Outros/doenças/barragens em eventos climáticos.

| Família | Período | Planejados | Estimáveis | Nominais | BH | BY | Holm | Triagem básica | Ampliada |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Principal | Pré |21|19|8|5|1|1|0|0|
| Principal | Total |21|21|9|5|1|1|6|4|
| Sensibilidades | Pré |63|57|20|11|5|5|0|0|
| Sensibilidades | Total |63|63|22|9|1|1|37|20|

**Rejeições ajustadas não equivalem a resultados interpretáveis.** Todos os resultados pré continuam limitados por estacionariedade inconclusiva da inadimplência. No total, apenas Granizo combina BH e triagem ampliada na principal. Hidrológico, Chuvas Intensas e Vendavais/Ciclones passam essa triagem, mas só rejeitam nominalmente na principal. Triagem significa ausência de indicação pelos critérios examinados, não prova de adequação.

## Granizo: sinal novo, sensível à inferência

Principal total: p HAC=0,000268726; BH42=0,005643; BY42=0,024417; Holm42=0,011018. Também mantém ajuste global168(Holm≈0,04353). Soma dos coeficientes≈0,032262 pp por unidade de Δ12Δlog(1+D), IC95% pontual HAC[0,012810;0,051713]; não é resposta causal acumulada. A soma depende da forma do choque nas variáveis transformadas, não significa que um protocolo aumente I em0,032pp.

**Não persiste no clássico/HC3**(BH≈0,5306/0,4292) nem na seleção BIC(p≈0,1167; q0 preferido). A relativa sazonal conserva BH, mas não BY/Holm. Estabilidade geral principal p≈0,136 não rejeita; isso não comprova estabilidade. Portanto: sinal exploratório sensível à covariância e à especificação; não confirmação robusta, causal, nem validação de capacidade preditiva fora da amostra.

## Onda de Frio e histórico

Principal total: p≈0,01610; BH42≈0,05635, com autocorrelação curta e mudança pós-março2020(p≈0,002352). Não reúne ajuste e adequação. BIC sazonal reproduz exatamente p14≈0,002175706; BH nesta nova família126≈0,022845, BY≈0,12376 e Holm≈0,25021. Triagem ampliada favorável, mas q0 preferido e clássico/HC3 não sustentam ajuste. O BH histórico14≈0,03956 continua preservado; a diferença de BH decorre da família nova, não substitui o histórico.

Análise anterior05–09:235 testes distintos selecionados,29 nominais,0BH;18/29 com autocorrelação do sistema e4/29 passando triagem anterior. Etapa14:41 cenários nacionais com triagem básica favorável, apenas Onda de Frio tambémBH. Nesta etapa15 a ordem fixa, nova família e diagnóstico ampliado mudam o desenho: não comparar contagens de rejeição como medida direta de progresso. Estabilidade total na principal falha nominalmente em14/21; CUSUM pode não rejeitar simultaneamente. O teste anterior de interações(p≈0,00018) e o CUSUM(p≈0,639) continuam documentados; não foram removidos ou usados para selecionar data.

## Interpretação e encerramento

A revisão cobre todos os grupos/tipologias nos dois períodos. A evidência segue exploratória: os sinais ajustados pré têm inferência comprometida; no total Granizo satisfaz a triagem da principal HAC, mas depende da inferência/especificação. Outros sinais ajustados têm limitações ou seleção BIC e preferência por q0. Não há confirmação robusta e geral de desastres→inadimplência. Não rejeitar também não prova ausência de efeito.

Os recortes se sobrepõem; significância diferente não testa diferença de efeito entre períodos. Precedência condicional não identifica causalidade estrutural, e o teste conjunto não fornece sozinho sinal ou magnitude. Atlas é exposição retrospectiva por contagem, não gravidade única nem informação garantidamente disponível em tempo real. Não foram adicionados controles econômicos sem fonte/cobertura compatível. Podemos encerrar esta etapa e avançar para outro método com esse mapa de limitações preservado. Nenhum método seguinte executado.

## Reprodução, integridade e limitações materiais

Notebook15 reproduzido integralmente no ambiente registrado; a validação substantiva compara F restrito/Wald, ausencia de alvo contemporâneo, famílias, GL e reprodução dos p BIC sazonais14. Conferência de saídas históricas não é reprodução integral05–14 nem diagnóstico estatístico. Bases df_tcc_2013_2024.parquet e BD_Atlas_1991_2024_v1.0_2025.04.14_Consolidado.csv indisponíveis: impedem reconstrução da integração bruta, códigos e reprodução integral10–13, não a análise15 baseada em agregados hash-conferidos. Checkpoints antigos são snapshots e não serão relabelados como execução atual. Bootstrap/TY não adicionais: não corrigiriam automaticamente a instabilidade/autocorrelação/estacionariedade.

Fontes metodológicas primárias: [ADF](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.adfuller.html), [KPSS](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.kpss.html), [BG](https://www.statsmodels.org/stable/generated/statsmodels.stats.diagnostic.acorr_breusch_godfrey.html), [RESET](https://www.statsmodels.org/stable/generated/statsmodels.stats.diagnostic.linear_reset.html), [correções múltiplas](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html). HAC12 é sensibilidade/referência previamente registrada, com aproximações de pequena amostra; não garantia de tamanho correto em60 observações ou modelo mal especificado.
