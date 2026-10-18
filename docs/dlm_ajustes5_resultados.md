# Desastres e inadimplência: associações e precedência preditiva

## Escopo e execução
Extensão exploratória de cinco ajustes, com regras em `dlm_ajustes5_protocolo.md` registradas antes dos novos ajustes. DLM clássico, coeficientes livres; não usa spline. Dados 2013–2024, 27 UFs, cobertura municipal por categoria, Atlas SHA256 `6ca29008a60a30e9f45d0f451da7750f850d8902704487798e1ef39ca3da44af`. Granger não reestimado.

## 1. Seleção e inferência
BIC em amostra comum: K1–10; AR0–2 no nacional. Bonferroni conservador protege a grade inteira: M10 para soma painel, M30 nacional comum, M90 para três somas de regime. Conjunto M10/30; perfis M55/165/495. Depois, BY principal e BH comparativo entre categorias/períodos. Famílias pré-definidas incluem inelegíveis sem apresentar p=1 como teste calculado. Proteção depende da validade aproximada marginal e se refere às projeções da grade, não garante correta especificação nem modelo verdadeiro. Não é bootstrap pós-seleção nem confirmação independente.

## 2. Painel e dependência
46 modelos, betas e K anteriores preservados: 45 K1, Alagamentos pré K6. DK12 principal; DK6/18 sensibilidades. 138 covariâncias brutas conferidas contra `cov_nw_groupsum`; correção e df temporais registrados. Nenhuma soma ou conjunto passa a referência seleção+BY/DK12. Correlação residual média absoluta dos 351 pares por modelo: 0,166–0,177 no pré; 0,203–0,204 no total. Máximos chegam a 0,778/0,679. Diagnóstico descritivo após FE de tempo, sem CD ingênuo. Bootstrap por UF anterior não resolve automaticamente essa dependência.

## 3. Nacional, regimes e controles
Controles mensais oficiais: Selic SGS4390 (%mês), IPCA SGS433 (%mês, IBGE via BCB), 100Δlog IBC-Br dessazonalizado SGS24364. Lag1, 144 meses completos; 2012 apenas auxilia borda. Snapshot da revisão disponível em 05/10/2026, com SHA/URL/extrato; não vintage em tempo real e sem interpolação. Dados públicos dos controles versionados, bases privadas não.

69 ajustes nacionais: 22 pré com controles constantes, 24 total comum comparativo, 23 total com regimes principais. Total comum N134; pré N75. Regimes da resposta fixos até fev/2020, mar/2020–dez/2021 (22 meses), jan/2022–dez/2024 (36 meses). Intercepto/AR/betas variam; controles/tendência/sazonalidade comuns. Histórico de lags contínuo dentro do período original. K/AR compartilhados selecionados conjuntamente. Doenças infecciosas com regimes tem posto incompleto em todos os 30 candidatos; pré Calor/Baixa Umidade e Barragens mantêm raridade. Nenhum substituído por especificação que produza significância. Todos os regimes estimados têm dinâmica AR estável; Ljung–Box12 não rejeita nominalmente nos 69 ajustes, mas isso não valida exogeneidade ou todas as hipóteses residuais. Ljung–Box nominal, condição e admissibilidade documentados. A fase de 22 meses pode tornar HAC12 frágil; proteção pela grade não conserta testes marginais mal calibrados.

Somas principais: 91 estimáveis de 96 planejadas; nenhuma passa busca+BY ou busca+BH. Conjuntos principais: 45 estimáveis de 48; dois passam BY:
- Vendavais/Ciclones pré: K3, AR0; p marginal 1,829044e−9, p busca 5,487131e−8, qBY 0,0000117437. Coeficientes pontuais −3,073; −5,342; +11,016 pp/unidade nos meses 1/2/3. A soma +2,601 não passa BY; IC dentro da grade para +1 pp de cobertura: [−0,147895; +0,199911] pp. O terceiro mês positivo é compatível com aumento da variação mensal no ajuste, mas o intervalo do perfil não é corrigido globalmente entre categorias; não é descoberta mensal global nem aumento acumulado demonstrado.
- Vendavais/Ciclones total/regimes: K1, AR1; p marginal 1,480950e−6, p busca 4,442851e−5, qBY 0,004754. Pontos do lag1 negativos nos três regimes (−3,173; −1,776; −7,344 pp/unidade). O conjunto de três betas rejeita zero, mas nenhuma soma por regime passa BY96. Não é evidência de aumento da inadimplência.

Igualdade específica de betas de exposição entre regimes: 23 estimáveis de 24; nenhum passa busca+BY/BH. Isso não demonstra igualdade dos betas. Comparação total comum: Tecnológico/antrópico conjunto K5 AR1 qBY 0,000306, sem soma significativa. Não é categoria exclusivamente climática nem descoberta do principal. Fontes/controles podem ser canais econômicos; associações condicionais não são efeito total.

## 4. Classificação
Auditoria de 24 séries por códigos, grupos originais e contagens. 12/13/14 = hidro/meteorológico/climatológico por código, não atribuição às mudanças climáticas. 11/15 e 2xx complementares. Rótulos Atlas preservados. Alertas: 13310 (calor) sob Chuvas Intensas; 13120 (frentes frias/ZC) em Onda de Frio; 14140 (baixa umidade) em Calor/Baixa Umidade; Movimento de Massa geológico sob grupo Hidrológico; Outros mistura natural/tecnológico. Não interpretar administração como taxonomia climática exclusiva. Não reduzir famílias após inspecionar p.

## 5. Comunicação
Título/conclusões explicitam associação (DLM), precedência preditiva condicional (Granger) e causalidade não identificada. Granger conserva dez rejeições BH42; somente Granizo total tem triagem ampliada favorável no principal, ainda sensível a inferência e especificação. Triagem ampliada é finita, não ilimitada nem validação causal. Teste não é validação de previsão fora da amostra. Revisão anterior fica como comparação, não evidência atual robusta. Nenhuma soma positiva atual autoriza afirmar aumento acumulado por desastre.

## Reprodução
`python src/dlm_ajustes5.py`
`python src/verificar_dlm_ajustes5.py`
`python src/relatorio_dlm_ajustes5.py`
`python src/verificar_relatorio_dlm_ajustes5.py`
898 verificações numéricas aprovadas; 312 cenários interativos offline, zero erros JS/requisições externas, CSV com 7 linhas neste filtro e mobile390px conferidos. Notebook21 executado em processo Python/IPython, outputs gravados, sem kernel remoto. HTML offline com MathML, filtros, perfil, matriz de correlação, controles/regimes, fonte/taxonomia e CSV. Não publicar HTML ou bases privadas no Git.
