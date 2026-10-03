# Protocolo da revisão DLM — registrado antes dos novos modelos

Data: 2026-10-03. Origem: `analise/dlm`, commit `3c94482628b86d1789ee98f8d35f6820835a7219`; main `027ee8aa245494765d99bff2511b6f60b30ddf41`. PR #4 aberto, sem comentários. Notebook 16, src/dlm.py e saídas históricas ficam preservados. Granger será apenas lido. SARIMAX não será executado.

## Auditoria e estimando

27 UFs × 144 meses (2013–2024); pré até jan/2020 inclusive. Dependente principal: primeira diferença de `100 CI/CA`, em pontos percentuais. Não se usam meses anteriores ao início de 2013; lags construídos antes de excluir observações da robustez pandêmica, sem preencher intervalos. Primeira observação utilizável principal: jan/2014; pré tem 73 meses; total, 132 meses.

A = linhas/registros originais; B = ocorrências **municipais** distintas pela chave UF + código IBGE municipal + data exata do evento + COBRADE. Não é identificação de tempestades meteorológicas únicas: um evento regional pode atingir muitos municípios. A auditoria encontra 101 repetições da chave, nenhuma linha exata duplicada; campos de grupo/tipologia consistentes nas chaves. B é uma aproximação auditável, não certeza de duplicidade administrativa. Linhagem fica local; contagens públicas agregadas.

C = municípios distintos com registro na UF-mês, independentemente de repetição; C_prop = C/número de municípios (base territorial 2022 fixa). **Principal: C_prop em escala 0–1**, sem log. Ela mede cobertura municipal relativa documentada, não população, área, gravidade ou exposição física objetiva. Escolhida pela interpretação de extensão da exposição e menor sensibilidade a repetição administrativa, antes de p-valores. A e B com log1p e C com log1p são sensibilidades. Mudança de exposição muda o estimando e sua unidade; comparar cenários plausíveis, não coeficientes brutos de unidades diferentes.

Denominadores: tabela IBGE 2022, reproduzida pela FAPESPA; soma 5570, inclui DF e Fernando de Noronha como unidades equivalentes. O IBGE documenta estabilidade do número de municípios desde 2013 até 2021. Não usar divisão territorial posterior a 2024. Fonte: https://www.fapespa.pa.gov.br/sistemas/pcn2023/tabelas/1-territorio/1-numero-de-municipio-e-area-territorial-2022.htm e https://www.agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/33005-ibge-atualiza-lista-de-municipios-distritos-e-subdistritos-municipais-do-pais-3

## Taxonomia

Original preservada: total, quatro grupos, 16 tipologias. Não há hierarquia única tipologia→grupo. COBRADE 12/13/14: clima/hidrometeorologia; 11/15: natural não diretamente climático; 2: tecnológico/antrópico. Criam-se três agregados analíticos. Movimentos de massa e erosão podem ser influenciados por chuva, mas código não certifica gatilho; biológico não é automaticamente clima. Incêndio pode ter origem antrópica mesmo com código climatológico. Nenhuma categoria removida. Chuvas Intensas com 13310 e Onda de Frio com 13120 são inconsistências nome/código explícitas; agregados por código são sensibilidades substantivas, não correções silenciosas.

## Suporte (antes de resultados)

Por exposição/medida/período: ocorrências B, soma da medida, zeros, skew, UF-mês positivos, UFs, meses, top1/top2, HHI espacial e temporal, top mês, variação within, N_eff=1/HHI. N_eff de cobertura proporcional não é df inferencial. Calcular também métricas na amostra efetiva após lags.

Não estimável: B<24, UF-mês positivos<12, UFs<5, meses<8 ou variação within≈0. Alta concentração: N_eff<5, top1>50%, top2>80% ou top mês>25%, desde que atinja suporte mínimo. Estimável: B≥100, células≥50, UFs≥10, meses≥24, N_eff≥10 e top1≤30%; restante com ressalvas. Alta concentração é estimada descritivamente, com força interpretativa limitada; não é excluída para buscar resultado nulo ou significativo. Rank completo da matriz residualizada e graus de liberdade positivos obrigatórios.

## Especificações

Principal: UF FE + mês-ano FE, não ponderado; identifica exposição relativa dentro de mês, líquida de diferenças permanentes. Associação para UF média; não é efeito causal, pois há confundidores UF-tempo e possíveis spillovers.

K_max=12, perfil específico de cada exposição. Base natural cúbica `patsy.cr(lag,df=J)` sem restrição de centralização, J∈{3,4}; coeficiente spline inclui componente constante no perfil de lags (não um intercepto duplicado da equação). Z_j=Σ_k X_(t-k)B_j(k); β=Bθ, Vβ=B Vθ B'. BIC em amostra idêntica, J menor desempata. Reportar AIC/BIC e ambos os perfis; inferência condicionada à base escolhida, não corrige seleção de J. Estabilidade entre J é obrigatória para alegar robustez. Principal comparável também com J=3 fixo como sensibilidade.

Quantidades: β0, Σ1..12β, Σ0..12β; C(h) com covariância completa. Pulso isolado: C(h) resume mudança da taxa, condicional ao modelo; não confundir com aumento permanente de exposição. Bandas simultâneas condicionais: simulação t multivariada da covariância cluster, 9999 draws, max-|t| ao longo dos 13 horizontes; cobertura aproximada, não ajustada entre exposições nem pela seleção de J.

Horizontes secundários ex ante: súbitos (alagamentos, enxurradas, inundações, granizo, vendavais/ciclones, tornados, massa) K=6, com K=3 sensibilidade irrestrita; persistentes (seca/estiagem, incêndio, calor/baixa umidade) K=12, K=6 sensibilidade; Onda de Frio, erosão, doenças, barragens, Outros, grupos e total: K=12 por ambiguidade/agregação. Não escolher horizonte por p. Horizonte efetivo descritivo: primeiro h com ≥90% da soma |β|, reportado apenas como concentração de massa absoluta da curva; não duração causal e inconclusivo sem estabilidade/bandas/suporte.

Leads t+1..t+3: incluídos conjuntamente além dos lags, teste conjunto zero; amostra perde últimos 3 meses. Não são associações substantivas. Robustez somente defasada k=1..12 refaz base nesse domínio; não é apenas subtrair β0.

Pós_t = 1 a partir de **fev/2020**, consistente com pré até jan/2020; não representa data epidemiológica exata. Interação com data da resposta (não data da exposição), transição explicitada: pulsos anteriores podem ter resposta pós. γ teste conjunto; acumulados pré β, pós β+γ, diferença γ. Não comparar p dos recortes sobrepostos.

Pandemia: excluir respostas mar/2020–dez/2021; como lags podem conter exposição desse intervalo em 2022, não descrever como amostra totalmente livre de pandemia. Região×mês-ano FE (UF FE mantida), rank checado, remoção de variação regional comum. Pesos fixos: média CA UF em 2013/Σ médias; não contemporâneos; estimando orientado à carteira base. Observações por UF iguais, pesos não renovados em recortes/leave-out.

## Inferência

Cluster-UF CR1S com correção de tamanho e t/F (G−1). CR2 Bell–McCaffrey generalizado e Satterthwaite **via clubSandwich R**, contrastes lineares e Wald HTZ conjunto; não aproximar CR2 com df=N_eff. R `lm` com FE explícitos permite verificar igualdade dos coeficientes. Caso dependências impossíveis, reportar indisponibilidade, jamais afirmar robustez completa.

Wild cluster **restricted** bootstrap, pesos Rademacher por UF, 4999 draws para todos os modelos principais estimáveis (inclui tipologias), 9999 para Onda de Frio e categorias previamente centrais; null-imposed para acumulado e teste conjunto. Refazer absorção de FE para as perturbações por cluster, incluindo FE temporais; isso é necessário porque multiplicar resíduos por pesos UF destrói ortogonalidade temporal. P Monte Carlo (1+exceed)/(B+1), SE MC reportado. Também bootstrap puramente defasado e interação. Poucos clusters com exposição não são resolvidos automaticamente por bootstrap.

DK bandwidth12 Bartlett, referência t(T−1) aproximada. Dependência transversal: CD de Pesaran e correlação residual média. Autocorrelação: correlação residual lag1/12 descritiva + teste auxiliar de lag1 com cluster. Heterocedasticidade: associação resíduos²/exposição descritiva. Diagnóstico não é prova de exogeneidade.

Onda de Frio: retirar cada UF (27), destacar cada exposta, e retirar duas UFs dominantes simultaneamente apenas como suporte. Reavaliar o suporte e rank de cada retirada; não chamar estimável modelo que perde suporte. Não promover especificação após exclusão.

## Estacionariedade e nacional

ADF/KPSS por UF apenas complementares; Fisher-ADF não é válido sob dependência arbitrária. Pesaran CIPS via `plm::cipstest`, drift/trend em nível, drift em ΔI, lags1 e2 predefinidos, ambos períodos; raiz unitária sob dependência comum, não prova estacionariedade de todas UFs. ΔI mantida, nunca nível para obter significância.

DLM nacional complementar: taxa ponderada 100ΣCI/ΣCA; cobertura nacional Σmunicípios afetados/5570; ΔI, smooth K12, dummies mensais, tendência e dinâmica própria lags1/2 selecionada BIC entre p=0,1,2 em amostra comum; HAC12. Não interpretar acumulado como multiplicador dinâmico de longo prazo com lags próprios (reportar como soma direta do componente exposição). Resposta total dinâmica separada por recursão quando p>0. Total, grupos, tipologias estimáveis no agregado (≥24 B e≥12 meses positivos), agregados analíticos. Poder/amostra curta e confundimento nacional explícitos.

Decomposição CI/CA: apenas Onda de Frio, Granizo e tipologias previamente centrais; Δlog CI/CA são crescimentos nominais, não crédito real corrigido por inflação; decomposição interpretativa sem nova busca de hipóteses.

## Multiplicidade e multiverse

Famílias principais globais de 48 hipóteses (24 exposições×2 períodos), uma para soma acumulada e outra para perfil; p=1 para não estimáveis apenas no ajuste. Também reportar famílias originais período×nível como comparação, nunca substituição para alegar robustez. Placebos família própria de 48; heterogeneidade família24. BH por inferência separada (CR1S, CR2, bootstrap, DK), não misturar robustezes. Agregados analíticos sobrepostos incluídos, nenhuma correção hierárquica. BH depende de hipóteses de dependência; BY como sensibilidade global. Lags não são oportunidades de declaração.

Multiverse finita one-factor-at-a-time: J alternativo, A/B/C, irrestrito K3/K6, Almon quadrático K12, horizonte mecanismo, somente defasado, pandemia, região-tempo, ponderado. Todos os estimáveis, sem produto cartesiano. Categoria central = lista prévia do usuário e qualquer sobrevivente FDR, sem usar para selecionar especificação.

Classificação final: suporte mínimo/rank primeiro; alta concentração limita qualquer conclusão; placebo ajustado/instabilidade de sinal limita; inferência discordante é sensível à inferência; retirada dominante desestabilizando é sensível ao suporte; J/horizonte muda conclusão é sensível ao horizonte. Ausência de rejeição não prova ausência de impacto. Robustez requer conjunto de evidências, não menor p.

## Fontes técnicas

- https://jepusto.github.io/clubSandwich/articles/panel-data-CRVE.html
- https://jepusto.github.io/clubSandwich/reference/linear_contrast.html
- https://s3alfisc.github.io/fwildclusterboot/articles/wild_bootstrap.html
- https://rdrr.io/cran/plm/src/R/test_cips.R
- https://patsy.readthedocs.io/en/latest/spline-regression.html
