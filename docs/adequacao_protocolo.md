# Extensão de adequação — protocolo registrado antes de estimar

Data: 01/10/2026. Extensão exploratória informada pelos resultados anteriores; não é confirmação independente. Não alterar 05–13 ou seus resultados. Períodos fixos: jan/2013–dez/2024 e jan/2013–jan/2020. Nenhuma seleção usa o p de desastres.

## Hipóteses e transformações

Investigar se o histórico de exposição acrescenta informação à dinâmica da inadimplência, após transformações justificadas por escala, persistência e sazonalidade. Comparar quatro especificações finitas, sem continuar diferenciando até obter aprovação:

1. Referência: ΔI e Δlog(1+D), 11 dummies mensais.
2. Escala relativa: 100Δlog(I) e Δlog(1+D), 11 dummies. I deve ser estritamente positivo. O desfecho é variação logarítmica percentual, não pontos percentuais da taxa.
3. Sazonal: Δ12ΔI e Δ12Δlog(1+D), intercepto sem dummies redundantes.
4. Escala relativa + sazonal: 100Δ12Δlog(I) e Δ12Δlog(1+D), intercepto.

A diferença sazonal modifica o objeto estudado e elimina 12 meses adicionais. Pode introduzir dependência do tipo média móvel e sobrediferenciação. Não constitui reparo automático; ACF, variância e resíduos serão reportados. Sem winsorização, remoção permanente de extremos ou ajuste sazonal bilateral. Sem busca de recortes, quebras ou potências pela significância.

## Nacional

25 exposições: total nacional, 4 grupos, 16 tipologias e 4 medidas climáticas. Duas janelas × quatro especificações = família fixa de 200 hipóteses, BH e Holm com exclusões reservadas como p=1 apenas no ajuste. Cada cenário mantém p próprio 1–6 no total e 1–3 no pré; q de exposição 0–3; I12 fixo. BIC usa mesma amostra entre candidatos, GL≥30 e n≥3k. Para comparar as quatro transformações, usam-se datas comuns a todas, iniciando após 25 meses; estatísticas de estacionariedade usam toda série transformada disponível. Reportar também BIC melhor com q=0 e melhor com q>0. Não comparar BIC entre desfechos em escalas diferentes. A seleção do modelo positivo permite o teste conjunto; preferência q0 é evidência de parcimônia/predição, não falha de pressuposto.

Inferência de referência HAC12 (IC t) e sensibilidades clássico/HC3. Não escolher a covariância por p menor. Os p condicionais à seleção não incorporam incerteza de seleção. BH não corrige seleção de modelo.

## UF × mês

Mesmas quatro transformações, quatro indicadores climáticos e dois períodos = família fixa de 32 hipóteses. Efeitos fixos UF e mês-calendário, lags próprios 1,2,3,12 e exposição1,2,3, DK12 com aproximação t/F26; comparação DK6 e cluster UF. Amostras comuns por período/indicador em todas transformações. Variáveis transformadas e defasadas dentro de cada UF, sem atravessar fronteiras. Estacionariedade de ambos componentes por UF reportada. Sem GMM, sem buscar estados significativos, sem nova previsão ou reestimar projeções locais: são exercícios distintos preservados.

## Diagnósticos e interpretação

Concordância ADF/KPSS (ADF p<0,05 e KPSS p≥0,05) é triagem de estacionariedade; não rejeitar não comprova pressuposto. ADF não rejeita/KPSS rejeita sugere não estacionariedade; outros desacordos são inconclusivos.

Nacional: estacionariedade das duas séries, BG1/BG12, RESET HC3, CUSUM, raiz autorregressiva<1 e sensibilidade à exclusão do maior Cook (mudança da soma≤1SE robusto). BP/ARCH informam heterocedasticidade; HAC não corrige especificação. Separar adequação dos pressupostos de utilidade q0. Exibir cada falha, sem rótulo agregado que esconda o motivo.

Painel: concordância de pelo menos80% das UFs em cada série, autocorrelação auxiliar DK≥0,05 e raiz<1. Reportar influência leave-one-UF-out≤1SE como condição adicional. Não chamar painel de validado: viés dinâmico e exogeneidade seguem não certificados. IC DK não elimina confundimento. Modelo sem indicação nesses diagnósticos não prova causalidade.

Não selecionar retrospectivamente a transformação que produza p menor ou todos os diagnósticos não rejeitados. Exibir todos os cenários, perdas amostrais, falhas/inconclusões, p originais/ajustados e unidades. Uma melhoria diagnóstica sem significância também é resultado. Não misturar novas famílias com as anteriores; preservar todos os ajustes anteriores.

## Reprodução e fontes

Reutilizar Parquet intermediário e painel validados, conferir entradas por SHA256 e preservar saída antiga. Statsmodels: documentação oficial de stationarity_detrending_adf_kpss e stats.diagnostic. Novos arquivos: src/adequacao_series.py, notebook14, outputs/tables/adequacao. Checkpoint registra hashes e famílias. Relatório HTML offline somente no chat, com guia, fichas por cenário, diagnóstico item a item e gráficos; não publicar HTML nem template.
