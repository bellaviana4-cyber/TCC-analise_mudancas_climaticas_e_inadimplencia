# Revisão estadual do TCC — resultados, método e limitações (19/10/2026)

## Escopo e proveniência

A base mensal enviada anteriormente à Biblioteca do projeto foi recuperada por intervalos e reconstruída com o **SHA-256 idêntico ao manifesto de 06/10/2026: `46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36`**. O painel contém 27 UFs, 144 meses, 3.888 chaves únicas, sem lacunas; os valores de `taxa_inadimplencia` reproduzem `100 × carteira_inadimplencia_total / carteira_ativa_total`. O total de registros do painel é 40.339 e iguala a reconciliação histórica versionada; **não foi possível reler o Atlas bruto de 76,9 MB nesta sessão**. As 16 tipologias do Atlas foram mantidas literalmente como variáveis operacionais, sem subdivisão por grupos ou reclassificação.

Todos os resultados abaixo foram computados sobre essa base estadual; esta entrega NÃO substitui a auditoria original Atlas/SCR nem validação causal. Para o recorte definido neste TCC, todas as 16 tipologias do Atlas são tratadas na classificação operacional adotada, sem nova divisão.

## Granger: 27 UFs × 2 períodos × 16 tipologias

864 aplicações planejadas, 627 estimadas, 227 exposições constantes e 10 sem posto completo na grade. Em cada UF×período×tipologia: variável resposta `Δlog(I)`; exposição `Δlog(1+D)`; até 6 lags de cada série, intercepto e 11 dummies sazonais. A seleção de p entre 1 e 6 usa BIC **em amostra comum de 6 lags** (N=78 pré e N=137 total), não usa p-valores. H₀ conjunta: todos os coeficientes climáticos defasados são zero, via F clássico. BH a 5% preserva 16 posições por UF×período; exposições não estimáveis ocupam 1 apenas no ajuste, mas **não são relatadas como p observado**. Escolha de p não incorporada formalmente à distribuição F. Em particular, BH é local à família, não global às 864 aplicações.

**45 rejeições nominais; 14 após BH.** Destas, 12 não rejeitam Ljung–Box no modelo estimado; 2 possuem autocorrelação residual sinalizada. Sinais pré-pandemia dependem também da estacionariedade.

### Todas as 14 rejeições BH de Granger

| uf   | periodo   | tipologia                          |   p_lags |           p |        q_bh |   ljungbox_p |
|:-----|:----------|:-----------------------------------|---------:|------------:|------------:|-------------:|
| AL   | Pré       | tipo_alagamentos                   |        1 | 0.00746945  | 0.0398371   |   0.274391   |
| AL   | Pré       | tipo_chuvas_intensas               |        1 | 0.0113519   | 0.0454075   |   0.310762   |
| AL   | Pré       | tipo_enxurradas                    |        1 | 0.00746945  | 0.0398371   |   0.274391   |
| AL   | Pré       | tipo_inundacoes                    |        1 | 0.00746945  | 0.0398371   |   0.274391   |
| MG   | Pré       | tipo_chuvas_intensas               |        3 | 0.000370043 | 0.00592069  |   0.80268    |
| MT   | Pré       | tipo_doencas_infecciosas           |        3 | 0.00105999  | 0.0169598   |   0.727862   |
| PA   | Pré       | tipo_alagamentos                   |        2 | 0.0012735   | 0.020376    |   0.681278   |
| PE   | Pré       | tipo_enxurradas                    |        1 | 0.000686036 | 0.0109766   |   0.326433   |
| PI   | Pré       | tipo_outros                        |        4 | 0.000292561 | 0.00468097  |   0.393329   |
| RN   | Pré       | tipo_chuvas_intensas               |        4 | 0.000128011 | 0.00204818  |   0.775986   |
| RR   | Pré       | tipo_alagamentos                   |        3 | 3.71184e-08 | 2.96947e-07 |   0.00388829 |
| RR   | Pré       | tipo_chuvas_intensas               |        5 | 1.63365e-11 | 2.61385e-10 |   0.196025   |
| ES   | Total     | tipo_onda_de_calor_e_baixa_umidade |        4 | 0.00153497  | 0.0245595   |   0.660475   |
| RR   | Total     | tipo_alagamentos                   |        3 | 9.93841e-14 | 1.59015e-12 |   0.00123522 |

## DLM de painel: AIC, BIC e efeitos fixos/aleatórios

Para cada período e tipologia, TWFE de UF e mês-ano: `Δlog(I_it)=α_i+λ_t+Σ_{k=0}^K β_k Δlog(1+D_i,t-k)+ε_it`. Horizonte **K=1 a 24**, todos os candidatos em amostra comum (fev/2015 a jan/2020: 1.620 UF-mês; fev/2015 a dez/2024: 3.213 UF-mês). Ajustes MQO irrestritos; seleção minimizando AIC ou BIC gaussiano com a contagem explícita dos efeitos fixos. Cinco hipóteses testadas: β₀=0; Σ₀ᴷβ=0; Σ₁ᴷβ=0; todos β₀..K=0; todos β₁..K=0. Wald para conjuntos de coeficientes, t para contrastes escalares.

**29 de 32 aplicações estimáveis.** Não estimáveis pré: Onda de Frio, Onda de Calor e Baixa Umidade e Rompimento/Colapso de barragens (UFs e/ou UF-mês com exposição insuficiente). Em 29/29, o BIC selecionou **K=1**. O AIC selecionou horizonte maior em 8 combinações de tipologia × período. O antigo arquivo de candidatos AIC/BIC forneceu a mesma seleção, agora reestimada e comparada no painel recuperado.

### Seleções AIC × BIC em que K difere

| periodo   | tipologia                            |   K_AIC |   K_BIC |
|:----------|:-------------------------------------|--------:|--------:|
| Pré       | tipo_chuvas_intensas                 |      15 |       1 |
| Pré       | tipo_vendavais_e_ciclones            |      14 |       1 |
| Total     | tipo_chuvas_intensas                 |      16 |       1 |
| Total     | tipo_incendio_florestal              |       6 |       1 |
| Total     | tipo_movimento_de_massa              |       5 |       1 |
| Total     | tipo_onda_de_calor_e_baixa_umidade   |      14 |       1 |
| Total     | tipo_rompimento_colapso_de_barragens |       4 |       1 |
| Total     | tipo_vendavais_e_ciclones            |       9 |       1 |

**Inferência:** covariância cluster UF como comparação clássica; Driscoll–Kraay com banda L=floor(4(T/100)^(2/9)) como sensibilidade (L=3 pré, L=4 total), DK6 e DK12. A média absoluta da correlação entre estados varia próximo a 0,19; isso não certifica independência. A inferência não elimina confundimento nem corrige endogeneidade.

**Pós-seleção:** p/q usuais tratam K escolhido como fixo. O campo `p_grade_bonferroni=min(24p,1)` e BH aplicado depois oferecem uma proteção simples conservadora entre a grade e as tipologias, supondo calibração pontual, mas não são inferência seletiva exata e não corrigem testes mal calibrados. Famílias BH separadas por período × critério × covariância × hipótese; não se deve somar testes correlacionados de famílias diferentes. Os conjuntos foram Wald nesta revisão, distintos do máximo |t| por coordenação empregado no relatório histórico v4. Em K elevados, matrizes de covariância mal condicionadas exigem cautela adicional.

**Com BIC + DK por regra e proteção de K + BH, nenhuma hipótese rejeita a 5%.** Na sensibilidade BIC + DK12 aparecem três rejeições (Movimento de Massa no período completo, soma defasada e conjuntos) que **não persistem na banda por regra nem DK6**. AIC + DK regra inclui quatro rejeições pré de conjuntos Wald de Chuvas Intensas e Vendavais/Ciclones; estas não reproduzem a conclusão histórica baseada em testes de máximo |t|, de modo que devem ficar exploratórias.

### Efeitos fixos e aleatórios

Para os 29 modelos BIC K1 ajustamos pooled com dummies de tempo, dois efeitos fixos e um GLS RE de intercepto estadual com dummies de tempo; testamos F contra ausência de interceptos estaduais, LM Breusch–Pagan para componente de intercepto estadual e Hausman clássico de inclinações FE/RE quando cov(FE)−cov(RE) é definida positiva. Os F e LM não rejeitaram a 5% nas 29 aplicações; Hausman ficou disponível em 22 e também não rejeitou. **Em 7**, a matriz da diferença de covariâncias impossibilitou um Hausman clássico confiável, e não se inventou p-valor. Mantivemos TWFE na comparação principal pelo estimando intra-UF e a comparabilidade com os modelos anteriores, não por busca de significância. F/LM/Hausman clássicos não corrigem automaticamente dependência/heterocedasticidade; theta RE estimado igual a zero para boa parte das aplicações é compatível com pouco componente aleatório interceptual na dependente transformada.

## SARIMA/SARIMAX por UF e período

54 SARIMA ajustados e selecionados por BIC em treinamento cronológico, dentre 7 especificações parcimoniosas ARMA/sazonal anual AR com d=D=0 após diferença log externa. O Ljung–Box 12 no treino não rejeita em 35/54; nos outros 19, o menor BIC convergente é mantido com ressalva. Treino total até dez/2022 (119 observações transformadas) e teste jan/2023–dez/2024 (24 meses). Treino pré até jan/2019 (72), teste fev/2019–jan/2020 (12). Previsões de um passo sem reestimar parâmetros no teste, filtrando com y realizado nos meses anteriores.

**SARIMAX com 16 exógenas contemporâneas simultâneas**, sem acrescentar lags automaticamente. Pré-pandemia: 27/27 matrizes sem posto 16. Total: somente MG, MS, RS, SC, SP têm posto 16, os demais 22 são impossíveis de identificar no modelo completo. Entre as cinco UFs, somente MG mantém posto 16 na amostra de treino, condição necessária à previsão comparativa não vazada. Todos os cinco SARIMAX convergiram em amostra total. Em todos, o BIC ficou pior; nenhum teste de LR das 16 exposições rejeitou H₀ a 5%. Das 80 associações individuais, 2 p nominais abaixo de 0,05 (MS barragens e RS estiagem), **0 após BH** local por UF×período. Os testes nominais não autorizam alegação causal ou associação robusta.

### Comparação dos cinco ajustes SARIMAX completos

| uf   | periodo   |   rank_treino |   p_conjunto |   delta_BIC |   RMSE_SARIMA |   RMSE_SARIMAX |   variacao_RMSE_pct |
|:-----|:----------|--------------:|-------------:|------------:|--------------:|---------------:|--------------------:|
| MG   | Total     |            16 |      0.34929 |      61.829 |        1.3563 |         1.2861 |             -5.1775 |
| MS   | Total     |            15 |      0.28434 |      60.702 |        4.4967 |       nan      |            nan      |
| RS   | Total     |            15 |      0.23645 |      59.757 |        1.7312 |       nan      |            nan      |
| SC   | Total     |            15 |      0.81659 |      68.522 |        1.5047 |       nan      |            nan      |
| SP   | Total     |            15 |      0.49489 |      63.996 |        1.3605 |       nan      |            nan      |

O único desempenho fora da amostra comparável é Minas Gerais no total: SARIMAX RMSE 1,2861 e SARIMA RMSE 1,3563; melhora relativa ≈5,18%. Trata-se de **previsão condicional** à exposição contemporânea observada, não previsão operacional do desastre antes de ocorrer. Um RMSE melhor não significa p LR significativo. Para MS, RS, SC, SP a décima sexta tipologia só varia fora do treino; não há comparação fora da amostra válida com 16 exógenas livres. No pré, nenhum SARIMAX 16-exógenas é identificado.

## Estacionariedade e diagnóstico

ADF H₀: raiz unitária; KPSS H₀: estacionariedade. Para `Δlog(I)` estadual, a inspeção pré indicou 16 séries favoráveis, 10 inconclusivas e 1 contrária; no completo 24 favoráveis, 2 inconclusivas e 1 contrária. Classificação diagnóstica, não certificado. Mudanças de janela, valores-limite e escolha de lag produzem diferenças para avaliações históricas; a série pré merece cautela. ADF/KPSS para as 16 variáveis transformadas e 27 UFs por período encontram-se em `estacionariedade_adf_kpss.csv`.

O erro padrão de Granger é clássico e falha da hipótese de ruído branco pode afetar sua calibração; DLM usa análise de sensibilidade de covariâncias; os SARIMA/SARIMAX apresentam diagnósticos LR e Ljung–Box, ARCH e normalidade. Os resultados não são independentes entre UFs e períodos, e há rótulos administrativos mistos.

## Conclusão central

A análise encontra precedência preditiva local e associações dependentes do método e da inferência, mas **não identifica evidência causal robusta e generalizável** de aumento da inadimplência por registros de desastres. A seleção BIC favorece DLMs curtos, sem rejeições protegidas nas hipóteses sob DK por regra. Os cinco SARIMAX de 16 exógenas identificáveis não apresentam melhora do BIC nem relevância conjunta a 5%. Não rejeição não comprova ausência de impacto econômico. Persistem limitações de taxonomia, mensuração, estacionariedade, modelos multivariados esparsos e incerteza pós-seleção.

## Reprodução

Instale numpy/pandas/scipy/statsmodels, defina (opcional) TCC_BASE_CSV e TCC_OUTPUT_DIR, disponibilize o painel original com hash acima e execute `python src/analise_estadual.py granger`, `python src/analise_estadual.py dlm`, `python src/estacionariedade_estadual.py`, `python src/sarimax_estadual.py Pré` e `python src/sarimax_estadual.py Total`. Para recomputar as tabelas-mestre e o HTML, execute `python src/finalizar_entrega.py`. O Atlas bruto não é requerido para reproduzir os modelos sobre o painel já auditado; seria necessário somente para uma auditoria independente de registros individuais, não realizada nesta revisão. O protocolo não adicionou modelos reduzidos como se fossem SARIMAX completos.