# Divergências entre o PDF e a main — etapa DLM

1. O PDF ainda descreve 2020–2024 e 1.620 UF-mês; a pipeline atual da main consolida 2013–2024 e espera 3.888 UF-mês (144 × 27). Para DLM, a cobertura deve ser validada diretamente na base processada antes da estimação.
2. O PDF define corretamente o painel com FE de UF e tempo, mas não explicita que FE mês-ano completo identifica β pela variação relativa entre UFs no mesmo mês. Isso deve entrar na versão final.
3. O PDF chama Σβk de “efeito acumulado de longo prazo”. Para K finito, recomenda-se “efeito acumulado no horizonte K”.
4. A formulação de Almon no PDF é conceitualmente central, mas a implementação deve recuperar a covariância dos β por transformação matricial e usar essa covariância no IC de cada lag e da soma.
5. A frase do PDF de que os β com TWFE são identificados “exclusivamente pelas variações temporais dentro de cada unidade” é incompleta: com FE temporais completos, a identificação decorre da variação within-UF líquida de choques comuns de cada mês, isto é, também da heterogeneidade transversal da exposição em cada data.
6. O PDF pressupõe cluster por UF, mas 27 clusters exigem cautela de pequena amostra e robustez inferencial.
7. A main final de Granger registra sinal exploratório sensível para Granizo no período total; isso não deve determinar especificações do DLM nem seleção de K/q.
