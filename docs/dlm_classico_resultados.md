# DLM clássico, sem spline: lags de 1 a 10

O protocolo foi registrado em 05/10/2026 antes da estimação (commit f5bd4e6). Esta extensão segue o pedido da autora e preserva notebooks 16–18 e resultados anteriores. Granger e SARIMAX não foram executados. A análise nacional anterior permanece complementar; não foi reestimada nesta etapa.

## Especificação e amostra

Principal: ΔI em pontos percentuais, cobertura municipal relativa em nível, FE de UF e mês-ano, sem ponderação, K=10 e dez coeficientes livres para lags 1–10. Não há spline ou Almon. K=1,...,9 são comparações de horizonte, sem seleção por significância. As sensibilidades K=10 incluem contemporâneo (0–10) e exposição em primeira diferença (ΔX, lags 1–10).

Foram executados 552 modelos: 460 da grade (46 cenários elegíveis × 10), 46 com contemporâneo e 46 com ΔX. Todos utilizam a mesma amostra por exposição/período: dezembro/2013–dezembro/2024, 3.591 UF-mês e 133 meses; ou dezembro/2013–janeiro/2020, 1.998 UF-mês e 74 meses. A disponibilidade de ΔX no lag 10 fixa o início comum. Não há dados anteriores a 2013 inventados.

α=0,05 e IC95% já eram utilizados anteriormente. O p-valor é calculado; não pode ser fixado em 0,05. P nominal e q BH são apresentados separadamente. Famílias de 48 por K/desenho/endpoint e grade exploratória de 480. K=10 utiliza CR2/Satterthwaite/HTZ em R e bootstrap restrito com 4.999/9.999 sorteios. K=1,...,9 têm inferência comparativa CR1S/DK, sem novo CR2/bootstrap para cada horizonte.

## Estacionariedade: verificação e ressalvas

O CIPS preservado favorece ΔI nos dois recortes e nos lags 1/2. A taxa em nível é sensível ao período e ao determinístico. P=0,01 é uma saída limitada da tabela CIPS, não um valor exato. O CIPS anterior das exposições ficou indisponível devido a unidades constantes/quase constantes: isso não confirmou sua estacionariedade.

Novos diagnósticos ADF com intercepto, maxlag=3 e BIC; KPSS com intercepto e bandwidth automático, por UF. A concordância favorável é ADF p<0,05 e KPSS p≥0,05. Séries constantes e falhas numéricas (incluindo bandwidth automático infinito) ficam explicitamente indisponíveis. Não foram realizadas diferenciações reiteradas para obter p favorável. Esses testes individuais não corrigem dependência transversal.

ΔI apresentou concordância em 26/27 UFs no total e 22/27 no pré; I em nível, 5/27 e 1/27. Cobertura total em nível: 12/27 no total, com 26 testes calculáveis; ΔX: 21/27. No pré: 21/27 em nível, com 26 calculáveis; 22/27 em ΔX. Não existe confirmação de estacionariedade de toda exposição em nível. ΔX é uma sensibilidade predefinida e muda o estimando para associação com mudança da exposição; não representa a mesma intervenção nem garante todos os pressupostos.

| periodo   | serie             | transformacao   |   UFs |   calculaveis |   concordantes |   fracao_todas_ufs |
|:----------|:------------------|:----------------|------:|--------------:|---------------:|-------------------:|
| Pré       | I                 | delta           |    27 |            27 |             22 |          0.814815  |
| Pré       | I                 | nivel           |    27 |            27 |              1 |          0.037037  |
| Pré       | tipo_onda_de_frio | delta           |    27 |             2 |              1 |          0.037037  |
| Pré       | tipo_onda_de_frio | nivel           |    27 |             2 |              2 |          0.0740741 |
| Pré       | total_desastres   | delta           |    27 |            27 |             22 |          0.814815  |
| Pré       | total_desastres   | nivel           |    27 |            26 |             21 |          0.777778  |
| Total     | I                 | delta           |    27 |            27 |             26 |          0.962963  |
| Total     | I                 | nivel           |    27 |            27 |              5 |          0.185185  |
| Total     | tipo_onda_de_frio | delta           |    27 |             3 |              2 |          0.0740741 |
| Total     | tipo_onda_de_frio | nivel           |    27 |             4 |              4 |          0.148148  |
| Total     | total_desastres   | delta           |    27 |            27 |             21 |          0.777778  |
| Total     | total_desastres   | nivel           |    27 |            26 |             12 |          0.444444  |

## Atlas e integridade

Uma cópia local truncada do Atlas (4.981.760 bytes, até 2005) foi detectada por assert antes da estimação. O anexo completo foi recuperado: 76.923.764 bytes, SHA256 6ca29008a60a30e9f45d0f451da7750f850d8902704487798e1ef39ca3da44af, igual ao checkpoint anterior. CSV e Parquet do painel também conferem.

A preserva 40.339 registros. B contém 40.238 chaves municipais distintas: UF + código IBGE do município + data do evento + COBRADE. As 101 linhas adicionais são retiradas somente de B; a fonte original permanece intacta. Grupo/tipologia são consistentes dentro dessas chaves. C conta municípios distintos, e sua cobertura foi confirmada idêntica antes/depois da deduplicação. As 24 exposições do cache foram reconciliadas diretamente ao Atlas por UF-mês. Essa chave não identifica tempestades físicas únicas nem duração de desastres.

## Resultados da grade: CR1S comparativo

|   K |   modelos |   acumulados_nominais_CR1 |   acumulados_BH48_CR1 |   acumulados_BH480_CR1 |   conjuntos_BH48_CR1 |
|----:|----------:|--------------------------:|----------------------:|-----------------------:|---------------------:|
|   1 |        46 |                         7 |                     0 |                      0 |                    0 |
|   2 |        46 |                         5 |                     0 |                      0 |                    1 |
|   3 |        46 |                         4 |                     2 |                      2 |                    4 |
|   4 |        46 |                         5 |                     2 |                      2 |                    5 |
|   5 |        46 |                         3 |                     2 |                      2 |                   16 |
|   6 |        46 |                         4 |                     1 |                      1 |                   21 |
|   7 |        46 |                         6 |                     1 |                      1 |                   27 |
|   8 |        46 |                         8 |                     2 |                      2 |                   30 |
|   9 |        46 |                         5 |                     2 |                      2 |                   35 |
|  10 |        46 |                         4 |                     1 |                      1 |                   35 |

Nos 460 modelos, houve 51 acumulados nominais e 13 após BH480: Calor/Baixa Umidade total K=8/9; Frio total K=3,...,10; Tornado pré K=3,...,5. São repetições de três categorias sob horizontes diferentes, não 13 descobertas independentes. Não representam sustentação robusta demonstrada: CR2/bootstrap não foram executados nos K menores. BH480 não é necessariamente maior que BH48 para cada hipótese, pois a distribuição e os ranks da família mudam. BIC preferiu K=1 em 45 cenários e K=6 em um; isso não demonstra duração de um mês.

## Principal K=10: CR2 e bootstrap

| periodo   | exposicao                                   |   estimate |         low |        high |         p |       df |        q |
|:----------|:--------------------------------------------|-----------:|------------:|------------:|----------:|---------:|---------:|
| Total     | Total de desastres                          |  0.0202288 |  -0.0923876 |  0.132845   | 0.700655  | 11.2127  | 0.951156 |
| Total     | Grupo | Climatológico                       |  0.0715485 |  -0.116932  |  0.260029   | 0.425637  | 12.4791  | 0.951156 |
| Total     | Grupo | Hidrológico                         | -0.0616551 |  -0.251733  |  0.128423   | 0.494744  | 12.5665  | 0.951156 |
| Total     | Grupo | Meteorológico                       | -0.0739669 |  -0.820485  |  0.672552   | 0.75714   |  2.616   | 0.951156 |
| Total     | Grupo | Outros                              | -0.0258529 |  -0.375186  |  0.323481   | 0.67526   |  1.35238 | 0.951156 |
| Total     | Tipologia | Alagamentos                     | -0.218726  |  -2.69364   |  2.25619    | 0.676338  |  1.56048 | 0.951156 |
| Total     | Tipologia | Chuvas Intensas                 | -0.206646  |  -0.478238  |  0.0649449  | 0.120724  |  9.89582 | 0.951156 |
| Total     | Tipologia | Doenças infecciosas             | -0.0447901 |  -2.66472   |  2.57514    | 0.898199  |  1.16412 | 0.979854 |
| Total     | Tipologia | Enxurradas                      |  0.363964  |  -0.487119  |  1.21505    | 0.306532  |  4.23296 | 0.951156 |
| Total     | Tipologia | Erosão                          |  0.0243293 |  -0.647606  |  0.696264   | 0.777874  |  1.12627 | 0.951156 |
| Total     | Tipologia | Estiagem e Seca                 |  0.0440343 |  -0.20939   |  0.297458   | 0.714077  | 13.3996  | 0.951156 |
| Total     | Tipologia | Granizo                         | -1.03722   |  -3.3245    |  1.25005    | 0.274017  |  3.90207 | 0.951156 |
| Total     | Tipologia | Incêndio Florestal              |  0.0987389 |  -0.414793  |  0.61227    | 0.641554  |  4.96697 | 0.951156 |
| Total     | Tipologia | Inundações                      |  0.199836  |  -0.565929  |  0.965601   | 0.466163  |  2.98255 | 0.951156 |
| Total     | Tipologia | Movimento de Massa              | -1.86283   |  -5.28368   |  1.55803    | 0.20021   |  3.75257 | 0.951156 |
| Total     | Tipologia | Onda de Calor e Baixa Umidade   |  1.29524   |  -6.07674   |  8.66722    | 0.303331  |  1.09693 | 0.951156 |
| Total     | Tipologia | Onda de Frio                    | -1.42516   |  -6.34697   |  3.49665    | 0.187534  |  1.09871 | 0.951156 |
| Total     | Tipologia | Outros                          | -0.112041  |  -1.53297   |  1.30889    | 0.758804  |  1.91866 | 0.951156 |
| Total     | Tipologia | Rompimento/Colapso de barragens |  1.48919   | -11.3669    | 14.3453     | 0.736117  |  2.98082 | 0.951156 |
| Total     | Tipologia | Tornado                         |  7.76056   | -12.121     | 27.6421     | 0.2491    |  2.16334 | 0.951156 |
| Total     | Tipologia | Vendavais e Ciclones            | -0.0761466 |  -0.979132  |  0.826839   | 0.778392  |  2.35429 | 0.951156 |
| Total     | Clima/hidrometeorologia                     |  0.0255066 |  -0.102158  |  0.153172   | 0.673589  | 13.2782  | 0.951156 |
| Total     | Natural não diretamente climático           | -0.0395675 |  -0.554785  |  0.47565    | 0.664281  |  1.35091 | 0.951156 |
| Total     | Tecnológico/antrópico                       | -0.12245   |  -2.40451   |  2.15961    | 0.771921  |  1.4224  | 0.951156 |
| Pré       | Total de desastres                          | -0.0710365 |  -0.17584   |  0.0337671  | 0.163151  | 10.6168  | 0.951156 |
| Pré       | Grupo | Climatológico                       | -0.134927  |  -0.283291  |  0.0134376  | 0.0691079 |  7.77914 | 0.951156 |
| Pré       | Grupo | Hidrológico                         |  0.0350488 |  -0.330251  |  0.400348   | 0.832262  |  8.67907 | 0.951156 |
| Pré       | Grupo | Meteorológico                       | -0.01895   |  -0.744505  |  0.706605   | 0.873247  |  1.3168  | 0.974787 |
| Pré       | Grupo | Outros                              | -0.245511  |  -4.75763   |  4.2666     | 0.832214  |  1.93622 | 0.951156 |
| Pré       | Tipologia | Alagamentos                     | -0.646082  |  -4.67601   |  3.38384    | 0.7212    |  8       | 0.951156 |
| Pré       | Tipologia | Chuvas Intensas                 | -0.303008  |  -1.12122   |  0.515206   | 0.304983  |  2.67153 | 0.951156 |
| Pré       | Tipologia | Doenças infecciosas             | -0.163589  |  -8.37349   |  8.04631    | 0.920688  |  1.53174 | 0.982068 |
| Pré       | Tipologia | Enxurradas                      |  0.0825833 |  -0.942791  |  1.10796    | 0.820411  |  3.23516 | 0.951156 |
| Pré       | Tipologia | Erosão                          | -2.24878   |  -5.39879   |  0.901219   | 0.124523  |  4.78129 | 0.951156 |
| Pré       | Tipologia | Estiagem e Seca                 | -0.185244  |  -0.361083  | -0.00940558 | 0.040841  |  9.91726 | 0.951156 |
| Pré       | Tipologia | Granizo                         | -1.01996   |  -7.83388   |  5.79397    | 0.680865  |  3.35641 | 0.951156 |
| Pré       | Tipologia | Incêndio Florestal              |  0.171897  |  -1.48759   |  1.83138    | 0.673993  |  1.80407 | 0.951156 |
| Pré       | Tipologia | Inundações                      |  0.512405  |  -1.875     |  2.89981    | 0.50806   |  2.49118 | 0.951156 |
| Pré       | Tipologia | Movimento de Massa              | -0.604311  |  -4.19032   |  2.9817     | 0.609147  |  2.66272 | 0.951156 |
| Pré       | Tipologia | Onda de Frio                    | -0.828489  | -12.635     | 10.978      | 0.606429  |  1.12699 | 0.951156 |
| Pré       | Tipologia | Outros                          | -0.654008  |  -4.42736   |  3.11935    | 0.578308  |  2.39458 | 0.951156 |
| Pré       | Tipologia | Tornado                         |  8.07666   | -38.4927    | 54.646      | 0.423161  |  1.45279 | 0.951156 |
| Pré       | Tipologia | Vendavais e Ciclones            | -0.0390062 |  -1.08904   |  1.01103    | 0.810063  |  1.26137 | 0.951156 |
| Pré       | Clima/hidrometeorologia                     | -0.0692159 |  -0.193048  |  0.0546164  | 0.239242  |  9.37303 | 0.951156 |
| Pré       | Natural não diretamente climático           | -0.249097  |  -3.83042   |  3.33222    | 0.794457  |  2.0183  | 0.951156 |
| Pré       | Tecnológico/antrópico                       |  0.105204  |  -6.30633   |  6.51674    | 0.952692  |  2.13483 | 0.994113 |

Um acumulado nominal CR2: Estiagem/Seca pré, −0,185244 pp/unidade de cobertura; IC95% [−0,361083; −0,009406]; p=0,040841; q=0,951156. Um pulso de +10 pp de cobertura corresponde a −0,018524 pp, IC [−0,036108; −0,000941]; esse IC não é ajustado por BH. Nenhum acumulado após BH/CR2 nos três desenhos K=10. Teste conjunto CR2 principal: nove calculados e 37 indisponíveis; nenhum calculado após BH. Indisponibilidade não confirma a hipótese nula.

Bootstrap K=10: 92 testes com zero sorteios singulares. Dois acumulados nominais: Climatológico pré, p=0,0224; Estiagem/Seca pré, p=0,0134. Nenhum após BH. Nenhum teste conjunto nominal ou após BH. Não selecionar a covariância que produz menor p.

## Onda de Frio e Granizo

Frio total: C(10)=−1,425162, IC CR2 [−6,346974; 3,496649], p=0,187534, df=1,098715; bootstrap p=0,2594. Pré: C(10)=−0,828489, IC [−12,635008; 10,978029], p=0,606429, df=1,126985; bootstrap p=0,7027. O CR1 total p=2,666×10^-8 permanece discordante, com concentração elevada. ΔX muda os sinais pontuais, mas tem estimando diferente e nenhum acumulado nominal CR2. O sinal histórico A/log1p/K3 não foi recuperado artificialmente. Granizo não apresentou acumulado nominal CR2 no principal clássico K=10; Granger não foi refeito para forçar concordância.

## Interpretação e limitações

β_k mede associação incremental com ΔI; C(h)=Σβ_k resume o acumulado de um pulso, com covariância completa. Para ΔX, um pulso na mudança representa outra exposição, não um pulso isolado em X. Exposição persistente combina respostas. IC95% CR2 ponto a ponto não é banda simultânea; K menores usam CR1S comparativo. Não rejeição não demonstra equivalência.

Perfis livres podem oscilar; não inferir duração, persistência ou reversão apenas da estimativa pontual. N_eff da exposição, alavancagem/contraste e df CR2 são distintos; consulte suporte_design.csv. Não há atribuição causal antropogênica, medida de intensidade/população ou controle completo de confundimento UF-tempo/spillovers. CR2 pressupõe clusters independentes; DK é comparação com pressupostos diferentes.

## Reprodução e entrega

Python 3.12; R 4.3.3 e clubSandwich 0.5.10. Versões em requirements-dlm-classico.lock.txt, versoes.json e r_session.txt. `python src/dlm_classico.py` executa o pipeline (Rscript no PATH ou DLM_R_EXEC). `python src/verificar_dlm_classico.py` executa os testes; `python src/dlm_classico_relatorio.py` gera HTML fora do Git.

Notebook 19: 16 células reais, zero erros, saídas inspecionadas e reestimação representativa. RUN_ANALYSIS=True recalcula o pipeline integral; por padrão, não repete os 552 modelos já executados. Passaram 33 verificações. Intermediários em data/interim/dlm_classico são regeneráveis. HTML standalone offline apenas no chat; nenhuma base bruta publicada. Fontes técnicas: statsmodels ADF/KPSS, clubSandwich linear_contrast/Wald_test. O bootstrap reutiliza a implementação validada externamente na etapa 18, sem alegar nova validação externa de cada modelo clássico.
