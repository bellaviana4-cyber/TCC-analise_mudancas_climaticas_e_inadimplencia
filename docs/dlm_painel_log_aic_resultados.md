# DLM em painel: referência com seleção AIC de 1 a 24 meses

Revisão de 06/10/2026, executada após recuperar o pedido completo e verificar a main. A publicação anterior K6 foi confirmada no commit `ba0865e` (não permaneceu apenas local). Notebook 22 e suas tabelas/documentação não foram sobrescritos. Esta revisão usa notebook **23_dlm_painel_selecao_aic_1a24.ipynb**, 9 células Python executadas com stdout/figuras reais; executor compile/exec em namespace compartilhado. Não refaz Granger, SARIMAX, nacional, spline, AR ou regimes.

## O que foi feito e por quê

Mantivemos y=Δlog(I), x=Δlog(1+D), MQO não ponderado, UF + mês-ano completos e 27 UFs em todas aplicações. Cada candidato inclui contemporâneo e todos lags até K. AIC minimizado separadamente por exposição/recorte, K=1,...,24, com contagem de efeitos fixos. AIC gaussiano segue convenção OLS; variância estimada contada adicionalmente só somaria constante 2.

As duas entradas têm SHA256 idêntico ao manifesto K6: base processada `46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36`, Atlas `6ca29008a60a30e9f45d0f451da7750f850d8902704487798e1ef39ca3da44af`. Calendário, 27×144 células, TI e todas contagens conciliados novamente. 40.339 registros, 37.643 no central por COBRADE 12/13/14; 101 repetições de chave mantidas. Não somamos categorias sobrepostas.

Amostra comum a todos candidatos e ao escolhido: fev2015–jan2020 (60×27=1620), fev2015–dez2024 (119×27=3213). Cada recorte perde 675 células: 27 pela diferença, 648 por 24 lags. Não foi recuperado período pré2013 nem reexpandido o modelo curto. A comparação com notebook 22 envolve amostra e horizonte, não apenas K.

42 aplicações planejadas (1 central +4 grupos +16 tipologias, nos dois recortes), 1008 candidatos registrados: 936 estimados, 72 sem suporte. **39 modelos finais: 18 pré, 21 total.** Nenhum candidato elegível falhou por rank/condicionamento. Cada aplicação tem o mesmo K em todas UFs, mas pode mudar entre exposições e períodos.

## Horizonte selecionado

| Exposição | K pré | K total |
|---|---:|---:|
| Total climático | 1 | 1 |
| Grupo Climatológico | 1 | 1 |
| Grupo Hidrológico | 1 | 1 |
| Grupo Meteorológico | 1 | 9 |
| Grupo Outros | 1 | 1 |
| Alagamentos | 1 | 1 |
| Chuvas Intensas | 15 | 16 |
| Doenças infecciosas | 1 | 1 |
| Enxurradas | 1 | 1 |
| Erosão | 1 | 1 |
| Estiagem e Seca | 1 | 1 |
| Granizo | 1 | 1 |
| Incêndio Florestal | 1 | 6 |
| Inundações | 1 | 1 |
| Movimento de Massa | 1 | 5 |
| Onda de Calor e Baixa Umidade | indisponível | 14 |
| Onda de Frio | indisponível | 1 |
| Tipologia Outros | 1 | 1 |
| Rompimento/Colapso de barragens | indisponível | 4 |
| Tornado | 1 | 1 |
| Vendavais e Ciclones | 14 | 9 |

Os candidatos completos e ΔAIC estão em candidatos_AIC.csv. K2 é próximo do mínimo central em ambos recortes. Chuvas Intensas pré tem 15/16/17 próximos; no total 8/15/16/17. Meteorológico total tem 1/9/10 próximos; Calor/Baixa Umidade total tem 1/2/11/14/15. Assim, o mínimo não identifica um horizonte preciso. K1, escolhido em muitas categorias, é fronteira inferior da grade, sem provar inexistência após um mês. Nenhum mínimo em K24. Não impusemos diferença de K entre desastres.

## Suporte e aplicações indisponíveis

Onda de Frio pré: janela 60 registros e 6 UFs; amostra comum 38 registros, 13 UF-mês positivos, **4 UFs** e 8 meses expostos, N_eff≈1,47. Não atinge mínimo de 5 UFs. É uma mudança real de suporte após retirar meses, não resultado não significativo. Calor/Baixa Umidade pré tem 19 registros na janela, 17 efetivos em 3 UFs; Barragens pré tem 15 registros e só 7 células/6 meses positivos. Nenhuma recebe inferência. Critérios de suporte herdados do protocolo K6 foram aplicados à janela e à amostra comum, sem relaxamento posterior.

## Resultado central

| Período | K | Soma β0..K | IC95% CR1 | p CR1 | IC95% DK6 | p DK6 |
|---|---:|---:|---|---:|---|---:|
| Pré | 1 | −0,000063 | [−0,001656; 0,001531] | 0,936145 | [−0,001920; 0,001795] | 0,946366 |
| Total | 1 | 0,001146 | [−0,000302; 0,002594] | 0,115735 | [−0,000101; 0,002393] | 0,071274 |

Central tem uma aplicação por período: q=p. β0: pré 0,000139, pCR1=0,746; total 0,000623, pCR1=0,103. Soma1K: pré −0,000201, pCR1=0,622; total 0,000524, pCR1=0,165. Testes conjuntos também não rejeitam a 5% em CR1/DK6. **Sem evidência acumulada central a 5% na especificação escolhida.** Não rejeição não comprova ausência de associação. P distintos nas janelas sobrepostas não demonstram mudança temporal.

## Associações acumuladas complementares

Todas rejeições BH de soma0K ocorreram no total. Valores abaixo são usuais após seleção, sem incorporar sua incerteza, em unidades logarítmicas.

| Exposição | K | Soma β0..K | q CR1 | q DK6 | Leitura |
|---|---:|---:|---:|---:|---|
| Hidrológico | 1 | 0,001901 | 0,006954 | 0,018471 | rejeição em ambas covariâncias; grupo Atlas misto |
| Alagamentos | 1 | 0,003929 | 0,018140 | 0,006646 | rejeição em ambas covariâncias |
| Enxurradas | 1 | 0,002230 | ≥0,05 | 0,035081 | sensível à covariância |
| Movimento de Massa | 5 | 0,020125 | 0,000306 | 0,001756 | geológico, fora do central |
| Onda de Frio | 1 | 0,008121 | 0,018140 | 0,012929 | rótulo ambíguo e concentrado |
| Rompimento/Colapso de barragens | 4 | 0,073092 | 0,002488 | 0,001756 | tecnológico, fora do central |

Onda de Frio total: 10 UFs expostas, N_eff≈2,67, top1≈55,8%, top2≈73,5% na amostra efetiva. Seu q pequeno não transforma concentração e ambiguidade em evidência climática homogênea. Total climático usa códigos, Hidrológico usa grupo original com categorias geológicas; os estimandos não são idênticos. Não chamar as duas rejeições de prova robusta ou causal. Somatórios com K distintos descrevem horizontes distintos.

Nas cinco famílias de endpoints e duas covariâncias há 104 rejeições nominais e 73 BH entre 390 testes calculados. Essas contagens misturam endpoints e covariâncias correlacionados; não são 73 fenômenos independentes nem prova geral. A tabela resultados.csv preserva todas aplicações; o HTML mostra todas rejeições, sem escolher apenas as favoráveis. Conjunto pode rejeitar sem soma, por compensação entre coeficientes.

## Estacionariedade, resíduos e inferência

ADF/KPSS nas séries transformadas completas dos recortes foram reexecutados, sem concatenar UFs. Δlog(I): pré 6 favoráveis, 19 inconclusivas, 2 desfavoráveis (RO/SC); total 18 favoráveis, 8 inconclusivas, 1 desfavorável (RO). Mesma transformação não certifica estacionariedade; não rejeição KPSS não a comprova. Testes completos não são certificados específicos da subamostra fev2015. CIPS histórico de ΔI/cobertura e diagnóstico nacional não validam estas séries.

Correlação residual absoluta média central≈0,1914 pré/0,1852 total. Cluster UF permite dependência dentro da UF, mas não entre estados. DK com Bartlett L6 é única comparação e tem banda fixa, independente de K. VIF central≈1,197/1,165; correlação máxima dos lags≈0,405/0,377. Células de maior influência parcial: PB jun2015 pré, MT ago2024 total. Não foram removidas UFs/células. Levene/Ljung–Box são descritivos; CD ingênuo sob efeitos de tempo não fornece teste calibrado.

CR1 com t26/F(r,26); DK6 com t(T−1)/F(r,T−1), correções finitas explicitadas no protocolo. Categorias concentradas têm poucos clusters informativos. Todos IC/p/q são **usuais, calculados tratando K escolhido como fixo e ignorando a incerteza de seleção; não são inferência seletiva formal**; BH não incorpora a seleção AIC. AIC gaussiano de trabalho também não elimina dependência/heterocedasticidade. Essas limitações impedem declarar validação da regressão ou causalidade.

## Escala dos cenários

Cada β relaciona Δlog1p(D) a Δlog(I) no lag; não são pontos percentuais ou elasticidade simples em D. Mudança persistente D0→D1 gera um pulso δx=log(1+D1)−log(1+D0); pulso de nível por um mês gera δx e depois −δx. Convolução com β, acumulação em log(I), conversão por 100[exp(resposta)−1]. Soma β é associação acumulada no horizonte escolhido, sem interpretação automática de longo prazo ou desastre físico único. Cenários, perfis e IC pontuais são exportados.

## Verificações realizadas e reprodução

Notebook 23 executado sem erros, 9 células Python. Conferidos calendário/lags até 24 por UF, N/datas comuns, AIC/penalização FE, mínimo e ΔAIC, SQR não crescente nos candidatos aninhados, 42 famílias planejadas, BH, matrizes e variância da soma, cenários por convolução, manifesto e entradas.

FWL vs MQO de dummies explícitas nas centrais em K1/K24: diferença β máxima<7e−17, CR1<4e−19; AIC concordante. DK vs statsmodels<9e−20. São verificações numéricas, não provas dos pressupostos econométricos.

HTML offline com filtros período/exposição/covariância, curva ΔAIC, perfis, somas, todos candidatos, suporte, classificação, ADF/KPSS e cenários. JavaScript verificado em 84 combinações, incluindo callback de download CSV. **Revisão visual do HTML em Chromium não realizada:** executável ausente e instalação retornou arquivo inválido. Não se declara inspeção visual inexistente.

```bash
python -m pip install -r requirements-dlm-painel-log.lock.txt
python src/executar_notebook_painel_log.py notebooks/23_dlm_painel_selecao_aic_1a24.ipynb
python src/relatorio_dlm_painel_log_aic.py
python src/verificar_dlm_painel_log_aic.py
node src/verificar_relatorio_dlm_painel_log_aic.cjs
```

Entradas não versionadas: data/processed/df_tcc_2013_2024.csv e data/raw/atlas_desastres/atlas.csv. Capítulo corrigido em tcc/capitulos/c3_metodologias_tg_referencia.tex; outputs/tables/dlm_painel_log_aic/manifest.json registra versões/hashes. Código separado e versão histórica intacta. README indica notebook 23 como referência. Publicação direta na main autorizada explicitamente nesta conversa, sem force push.


## Correções metodológicas de 07/10/2026

A inferência usual ignora a escolha de K por AIC; não houve inferência seletiva formal. IC95% não têm cobertura pós-seleção demonstrada, e BH não fornece garantia de FDR global nem corrige p-valores pós-seleção. As rejeições são exploratórias.

A regra original de suporte contemporâneo foi mantida. Onda de Frio no pré está **bloqueada pela regra de suporte**, não demonstrada como impossível de estimar: com K24 há regressoras não nulas em seis UFs, posto 25/25 e condição da matriz de regressoras de aproximadamente 10,24. Quatro UFs referem-se à exposição contemporânea nas datas das equações. A auditoria distingue essas medidas em `outputs/tables/dlm_painel_log_aic_revisao/suporte_regressores_auditoria.csv`.

O condicionamento da covariância padronizada CR1 dos testes conjuntos é aproximadamente 37.463 em Calor/Baixa Umidade total (K14), 13.312 em Chuvas Intensas total (K16) e 8.627 em Chuvas Intensas pré (K15). Isso não demonstra erro algébrico na implementação, mas sinaliza fragilidade da aproximação Wald. 27 UFs não equivalem a 27 clusters igualmente informativos; p-valores muito pequenos desses testes não são evidência conclusiva. Ver `condicionamento_covariancias.csv` na mesma pasta de revisão.

Mantém-se a especificação diante dos casos inconclusivos com não rejeição KPSS, conforme decisão da autora, sem reclassificá-los como favoráveis; preservam-se também os casos desfavoráveis. A ressalva deve acompanhar as conclusões.

O capítulo recebeu correções das expansões quadrática/cúbica de Almon, das variáveis auxiliares e da afirmação sobre colinearidade. Almon continua apenas alternativa teórica. A aplicação e os cenários são descritos em Δlog(I)/Δlog(1+D), com associação acumulada para cenário definido, em unidades logarítmicas ou variação relativa percentual, nunca automaticamente pontos percentuais ou impacto total de um desastre.

Nenhuma regra de seleção, estimativa, exclusão ou p-valor foi alterada nesta revisão editorial e metodológica. Publicação na main autorizada explicitamente pela autora nesta conversa, preservando histórico e sem force push.
