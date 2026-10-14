# SARIMAX nacional — protocolo e limites

## Pergunta e materiais

A análise investiga se as ocorrências climáticas acrescentam informação à evolução temporal da inadimplência brasileira, sem pressupor causalidade. Complementa os testes de Granger e o painel DLM. A teoria baseia-se em `tcc/capitulos/c3_metodologias_tg_referencia.tex`, seção SARIMAX; a aplicação é o código `src/sarimax.py` e o notebook 24.

A entrada é `outputs/tables/segunda_etapa/series_nacionais_agregadas.csv` (jan/2013–dez/2024; 144 meses). É a agregação publicada na etapa anterior: I = 100 × Σ(carteira inadimplente)/Σ(carteira ativa). O código valida calendário e suporte. As bases originais do SCR/BACEN e Atlas não estão versionadas. Portanto, não se pode refazer independentemente a conciliação por UF nem a classificação COBRADE sem recuperar os arquivos brutos auditados.

## Escolha da série e especificação

Unidade: Brasil×mês, e não UF×mês. Isto evita a aplicação imprópria de um SARIMAX univariado como se fosse um modelo com efeitos fixos. Também significa que resultados nacionais não identificam heterogeneidade estadual.

Resposta `y_t = 100[log(I_t) - log(I_(t-1))]`. Exposição por categoria `x_t = log(1+D_t) - log(1+D_(t-1))`. As transformações são explícitas e não são diferenciação sazonal. Ajusta-se SARIMAX `order=(p,0,q)` e `seasonal_order=(P,0,Q,12)` com constante. Logo, não há dupla diferenciação. O diagnóstico ADF/KPSS é produzido em nível logarítmico e primeira diferença para cada período e total climático. A escolha fixa d=D=0 sobre a série transformada é parcimoniosa, **mas precisa ser reconsiderada** se os diagnósticos indicarem não estacionariedade, ou estrutura sazonal persistente em resíduos.

A forma de implementação do `statsmodels` é uma regressão com erros SARIMA. A equação escrita na monografia coloca a regressão fora do operador ARMA; as duas parametrizações não são algebraicamente iguais em geral. A revisão textual da equação teórica é recomendada.

## Grade pequena e comparação

O baseline é selecionado em uma grade curta de quinze estruturas ARMA, com ordens não sazonais de até três termos autorregressivos ou dois de médias móveis e, quando presente, apenas um termo sazonal AR ou MA. A análise pré-pandemia testa somente as onze primeiras opções. Havendo modelos com Ljung–Box p≥0,05 em 6 e 12 meses, escolhe-se o de menor BIC entre eles; caso nenhum satisfaça ambos diagnósticos, reporta-se o menor BIC com ressalva expressa. Isso impede declarar válido um modelo apenas por BIC. A estrutura ARMA vencedora do baseline é fixada na comparação com SARIMAX, para isolar a adição de exposição e conter a complexidade; logo não se faz otimização exaustiva conjunta de ordens e exposição.

Cada SARIMAX inclui uma única exposição, com lag isolado 0, 1 ou 3 da série transformada de desastres; escolhe-se o menor BIC no treino. O uso de lag isolado é explicitado: o coeficiente não mede efeito acumulado. A amostra comum começa em maio/2013 (três lags após uma diferença), inclusive no baseline. Seleção não usa p-valores.

A exposição central `Clima | Protocolos` corresponde aos códigos climáticos 12/13/14 na auditoria anterior. Também são analisadas tipologias com suporte mínimo (18 meses positivos e 30 registros no treino). As classificações de tipologia do Atlas podem abranger mais de uma subclasse COBRADE. **Não se apresentam grupos COBRADE exatos**: as colunas administrativas de grupos incluem códigos não climáticos ou reclassificações mistas. Reconstrução exata dos grupos exige o Atlas linha a linha.

## Janela temporal e avaliação

No período principal, o treino termina em dez/2022, e o teste cobre jan/2023–dez/2024. As transformações e defasagens são computadas cronologicamente e usam apenas valores passados em cada previsão; o baseline e os SARIMAX são treinados nos mesmos meses. A avaliação usa previsão de um passo com atualização do estado por observação realizada e sem reestimar coeficientes. MAE e RMSE medem erro na escala `100 Δlog(I)`.

Quando lag=0 é usado, a exposição do mês alvo é observada e a previsão é **condicional**, não operacional. Com lag≥1, a exposição já é histórica no início do mês alvo, supondo disponibilidade tempestiva do Atlas — hipótese não verificada. Não se afirma disponibilidade em tempo real dos registros administrativos. O recorte pré-pandemia encerra em janeiro/2020; a amostra menor limita inferência e comparações diretas.

## Inferência e verificação

Estimadores por máxima verossimilhança via `statsmodels.tsa.statespace.SARIMAX`, com restrições de estacionariedade e invertibilidade, tendência constante e checagem explícita de convergência. Os modelos não convergentes são listados e excluídos da escolha. Há testes Ljung–Box (lags 6,12), ARCH(3), Jarque–Bera, parâmetros, IC95%, p e BH por período após escolha. Os p-valores, inclusive q BH, não incorporam a escolha da estrutura/lag por BIC; são exploratórios. Ljung–Box favorável não prova ausência de estrutura residual. Normalidade não é critério absoluto.

Se o SARIMAX vencer por BIC, mas apresentar autocorrelação residual relevante, a conclusão deve registrar ressalva diagnóstica; não se declara o modelo adequado apenas por BIC. A amostra nacional é pequena para muitos parâmetros. Os termos sazonais são testados sem impor integração sazonal. A hipótese principal continua sendo de associação temporal condicional, não causalidade.

## Reprodutibilidade

Execute `python src/sarimax.py` na raiz do repositório. Dependências: Python 3.11, numpy, pandas, scipy, statsmodels, matplotlib. O workflow `.github/workflows/sarimax.yml` executa o script e valida arquivos de saída ao alterar este protocolo na branch `analise/sarimax-nacional`.

Saídas: `outputs/tables/sarimax/` (oito tabelas e resumo JSON), `outputs/figures/sarimax/` (três gráficos quando houver previsões) e `outputs/reports/relatorio_sarimax.html` (HTML offline com menu lateral). Os números e interpretações devem ser verificados **após execução bem-sucedida**. A publicação do código isoladamente não comprova execução da estimação.

## Conexão com etapas anteriores

Granger investiga precedência preditiva condicional; o DLM estadual estuda associações distribuídas com efeitos fixos UF e mês; o SARIMAX nacional modela a autocorrelação/sazonalidade e compara previsão condicional com baseline. As três perspectivas não identificam automaticamente causalidade. Na etapa anterior de Granger, rejeições nominais não permaneceram após BH; o DLM principal também não apresentou associação robusta para o total climático. Resultados SARIMAX podem convergir ou divergir por mudança de unidade, controles, transformação e amostra.
A rotina de previsão preserva a identificação da série `y` ao incorporar observações sequenciais ao estado filtrado.

Resultados interpretados e ressalvas: [`sarimax_resultados.md`](sarimax_resultados.md). O relatório inclui ACF, histograma, Q-Q e evolução dos resíduos da referência no treino. Não declarar modelo aprovado se nenhum candidato satisfizer ambos os testes Ljung–Box.

## Auditoria adicional antes do encerramento

A revisão final investiga se a autocorrelação residual pode ser reduzida com uma grade pequena de ARMA, harmônicos sazonais (até 2 pares seno/cosseno) e intervenções de calendário predefinidas para março/abril de 2020 e janela março/2020–dezembro/2021. Essa auditoria é documentada em `outputs/tables/sarimax/triagem_residual.csv`; os termos só serão incorporados ao modelo final caso exista justificativa diagnóstica. A seleção não utiliza o período de teste 2023–2024.

A ACF padronizada da primeira triagem mostrou autocorrelações persistentes nos lags 3 e 6. Por isso, a segunda triagem `src/sarimax_diagnostico_lags.py` avalia ordens autorregressivas esparsas com esses lags e sazonalidade subanual (3/6), além da sazonalidade anual. Resultado em `outputs/tables/sarimax/triagem_lags_especificos.csv`. Nenhuma especificação é aprovada apenas por mínimo BIC sem diagnóstico. Essas tentativas após examinar os resíduos são consideradas exploração de especificações.
