# regra reproduzível de banda dk — versão 3

## decisão antes da nova execução

Manter modelo, transformações Δlog(I)/Δlog(1+D), efeitos fixos, seleção K_AIC em 1..24, suporte, amostra comum e proteção simultânea Bonferroni sobre a seleção. Holm permanece principal entre exposições. Granger não é reexecutado e SARIMAX não é iniciado.

A covariância principal passa a DK_regra, Bartlett, L=floor[4(T/100)^(2/9)], limitada a T−1. T é o número de meses distintos da amostra comum das equações, e não N UF-mês, número de registros, meses da base completa ou K. Pré: T60 → L3; total: T119 → L4. A mesma banda vale para todos os candidatos K e exposições do recorte porque T é comum. Logo a banda não depende de seleção AIC, beta, resíduos ou p. Não é seleção automática da persistência dos scores: é uma regra determinística de referência baseada no tamanho da amostra.

A regra está documentada no código de statsmodels (S_hac_groupsum / S_hac_simple): https://www.statsmodels.org/stable/_modules/statsmodels/stats/sandwich_covariance.html . A própria documentação ressalva que não é necessariamente ótima no painel. Optamos por transparência, parcimônia e evitar escolher banda pela significância. Esta decisão ocorreu após observar os resultados históricos, embora registrada antes do recálculo: não transforma o estudo em confirmação prospectiva.

DK6 e DK12 são sensibilidades, CR1 comparação. A auditoria estende L3/4/6/12/18/24 sem selecionar a conclusão pelo menor p. Não há proteção pela escolha posterior entre bandas. T60 e T119 continuam limitados; L24/T60=0,4 é especialmente delicado. ACF dos scores é descritiva, não valida automaticamente banda curta.

Inferência aproximada: t(T−1), correção N/(N−p_total), variância das somas com covariâncias completas. A proteção Bonferroni entre K continua condicionada à validade uniforme dos testes pontuais; não é inferência seletiva exata ou prova de estacionariedade/exogeneidade.

V2 preservada em arquivos próprios. V3 exporta coeficientes e intervalos de todos os candidatos, cinco endpoints, perfis, cenários e manifestos. Conferir K/beta idênticos ao histórico, L calculado com T correto, covariância contra statsmodels e multiplicidade.

Reprodução: python src/dlm_inferencia_banda_regra_v3.py; python src/verificar_dlm_inferencia_banda_regra_v3.py; python src/dlm_banda_dk_auditoria_v3.py; python src/relatorio_tcc_roteiro_v3.py.
