# fechamento da especificação e da inferência do dlm — versão 4

## decisão

Adotar DLM finito irrestrito em painel, estimado por MQO com efeitos fixos de UF e mês-ano, contemporâneo e lags consecutivos até K_AIC. Não incluir lags de y; não impor Almon ou mudar transformação para obter significância. Covariância principal: Driscoll–Kraay/Bartlett com banda determinada pelo tamanho temporal da amostra. Bonferroni simultâneo entre K e Holm entre exposições permanecem. As versões anteriores são históricas.

## pergunta e correspondência com a monografia

Pergunta operacional: mudanças na exposição administrativa aos desastres estão associadas às mudanças da taxa de inadimplência PF, no mesmo mês e nos meses seguintes, depois de controlar efeitos comuns temporais e diferenças médias entre UFs?

y_it=Δlog(I_it), x_it=Δlog(1+D_it).

y_it = α_i + λ_t + Σ(k=0..K*) β_k x_i,t−k + ε_it.

A seção de efeitos fixos do capítulo de referência já prevê UF e tempo. Almon é alternativa de restrição do perfil; não exigência de todo DLM. A base é UF×mês e a pergunta permite a comparação dentro de UF condicionada aos efeitos temporais. Modelar o agregado nacional substituiria a pergunta e descartaria variação estadual, portanto não é a alternativa final desta etapa.

A regressão de cada exposição é separada, e seus coeficientes não equivalem a efeitos parciais controlando todas as outras categorias. A hipótese causal não é identificada. Presume-se um perfil β comum entre UFs por aplicação; não se inferem efeitos específicos estaduais. As FE atuam na escala transformada, não como interceptos da taxa em nível.

K* minimiza o AIC entre 1..24 na mesma amostra comum e sem reexpansão final. É o AIC gaussiano de trabalho; com dependência residual não se reivindica seleção ótima para previsão. Recortes jan/2013–jan/2020 e jan/2013–dez/2024; equações desde fev/2015: T60/N1620 e T119/N3213. K específico por exposição/período, comum entre UFs. Total central: COBRADE 12/13/14; grupos e tipologias do Atlas são análises secundárias, com divergências e categorias não climáticas explícitas.

## por que não impor almon

Nos 39 modelos selecionados, VIF máximo por aplicação 1,09–6,33, mediana 1,25; correlação absoluta máxima entre lags 0,512. Não há colinearidade extrema generalizada que torne necessária a restrição polinomial. Vendavais/Ciclones pré tem VIF máximo 6,33 e merece ressalva. Um polinômio introduziria forma adicional, com risco de viés de restrição; não resolveria dependência residual temporal ou entre UFs. Os testes conjuntos finais evitam inversão de covariâncias mal condicionadas, usando união de coordenadas.

## o que os resíduos mostram

No total climático, a correlação residual absoluta média é 0,191362 no pré e 0,185201 no total. Esses números isolados são descritivos. CD ingênuo não é calibrado para efeitos temporais estimados; não é usado para escolher covariância ou atestar independência.

Ljung–Box lag12 nominal rejeita em 13/27 UFs no pré e 20/27 no total; com Holm entre UFs, 7/27 e 16/27. São diagnósticos sobre resíduos estimados, não testes com cobertura pós-seleção demonstrada.

Uma tentativa de calibração por bootstrap estacionário marginal independente com reprojeção TWFE foi auditada e rejeitada. Em simulação nula com UFs independentes e AR(1) de parâmetro 0,5, ela rejeitou em 74% (T60) e 60% (T119) de 50 réplicas, incompatível com 5%. Seus p não são utilizados, tampouco se alega que ela comprovou dependência entre UFs. A tentativa e a falha estão arquivadas em `outputs/tables/dlm_auditoria_rejeitada_v4`. O estudo de mecanismo impediu incorporar um diagnóstico incorreto. Não equivale a falha do estimador DLM ou de DK.

Permanece como evidência: correlações residuais amostrais e autocorrelação temporal. Não foi estabelecida independência entre UFs por diagnóstico formal calibrado. Um teste de dependência válido não é pré-requisito para adotar covariância robusta à possível dependência.

## inferência escolhida e justificativa

O conjunto de autocorrelação temporal e correlação residual amostral não oferece justificativa suficiente para impor independência entre UFs à inferência principal. DK é escolhido por sua capacidade de acomodar dependência transversal e temporal sob condições assintóticas. Não é escolhido pelo p dos efeitos; não há regra de mudar de CR1 para DK se um preteste rejeitar. Não é necessário provar dependência por um teste para usar uma covariância robusta a ela.

Banda: L=floor[4(T/100)^(2/9)]. T é o número de meses da amostra comum das equações, não N=27T ou K. Pré T60/L3; total T119/L4. A regra de referência independe dos resíduos/p e não é uma banda ótima garantida. Foi adotada após observar o histórico; não torna o estudo confirmatório prospectivo.

DK6/DK12 e L3/4/6/12/18/24 são sensibilidades. CR1 UF é comparação, não principal, pois não acomoda automaticamente correlação entre UFs. Não selecionar a banda/covariância que produz rejeição. DK não corrige fatores omitidos correlacionados à exposição, endogeneidade ou raiz unitária, nem deixa os resíduos independentes.

A inferência usa t(T−1) e correção N/(N−p_total); contrastes usam a covariância completa. A proteção de seleção Bonferroni cobre a grade K1..24 por endpoint/aplicação, desde que testes pontuais sejam válidos uniformemente. Não é seletiva exata. Holm por família período×nível×endpoint é principal; Holm global105 é sensibilidade mais abrangente por período. Não há proteção conjunta entre períodos/covariâncias. IC de seleção não é simultâneo entre todas exposições. Os alvos são projeções específicas de cada K, não efeitos estruturais únicos.

## leitura final e encerramento

Na referência DK por regra + seleção protegida + Holm: nenhum dos cinco endpoints rejeita a 5% em ambos recortes. A soma do total climático não rejeita em nenhuma banda avaliada. Movimento de Massa e Barragens rejeitam apenas em algumas bandas mais longas no total e são categorias fora do total climático. Evidência sensível, exploratória, sem impacto causal demonstrado. Não rejeição não comprova zero; proteção conservadora reduz poder.

K, amostra, estimativas e resultados v3 preservados. Nenhuma busca de significância ou nova transformação. Documentação, notebook de conferência e relatório de fechamento consolidam a decisão: ajuste técnico desta etapa encerrado dentro deste escopo, análise observacional exploratória. Granger não reexecutado; SARIMAX não iniciado. Publicação GitHub pendente da autorização anterior, sem nova tentativa de push.

## referências e reprodução

- Driscoll–Kraay e implementação de banda: https://www.statsmodels.org/stable/_modules/statsmodels/stats/sandwich_covariance.html
- Juodis–Reese: https://arxiv.org/abs/1810.03715 (problema do CD com efeitos temporais).
- Politis–Romano (1994): https://doi.org/10.1080/01621459.1994.10476870 (bootstrap estacionário; a adaptação diagnóstica aqui não é validada automaticamente pelo artigo).
- Berk et al.: https://arxiv.org/abs/1306.1059 (princípio simultâneo; não se reivindica PoSI exato).

Reproduzir inferência: scripts v3. Auditoria rejeitada, apenas para reproduzir a falha (não usar p): `python src/dlm_fechamento_diagnosticos_v4.py`; verificação do mecanismo: `python src/verificar_dlm_fechamento_v4.py`; relatório: `python src/relatorio_tcc_fechamento_v4.py`.

## revisão do relatório: menu lateral e todas as rejeições (2026-10-07)

As comparações são apresentadas com DK por regra (L3 pré/L4 total), DK6 e DK12. CR1 e bandas adicionais constam do histórico numérico. A comparação preserva K, coeficientes, amostra e estatísticas da especificação correspondente.

A aba Principais resultados conta e lista todos os cinco endpoints rejeitados, nos dois períodos. Com proteção da seleção e Holm por família: DK por regra=0 e DK6=0 em ambos; DK12=2 no pré e 5 no total. Pré: Vendavais/Ciclones K14 rejeita conjunto0K (0,000487) e conjunto1K (0,000451). Total: Movimento de Massa K5 rejeita soma0K (0,033607), conjunto0K (0,000862), conjunto1K (0,000798); Barragens K4 rejeita soma0K (0,017135) e soma1K (0,011639). Com BH, acrescentam-se as duas somas0K de Movimento de Massa/Barragens em DK6 total (q=0,042135). Não há rejeição Holm persistente nas três bandas.

A base mensal tem 18 aplicações elegíveis no pré e 21 no total. São 630 linhas planejadas (42×5×3), 585 calculadas (39×5×3); as indisponíveis mantêm status de suporte. Os recortes se sobrepõem e não constituem um teste de mudança estrutural.

O relatório inclui comparação visual dos intervalos nas três bandas, mapa dos cinco testes, AIC, perfis, cenários, FAQ das dúvidas metodológicas e tabelas exportáveis. A navegação lateral e os valores dos filtros foram verificados por JavaScript; esta revisão não contou com renderização visual em navegador. O identificador DK_regra do seletor original foi confirmado correto; não foi necessário corrigi-lo.
