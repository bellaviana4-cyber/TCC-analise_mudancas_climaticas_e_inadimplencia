# Ampliação por grupos e tipologias — decisões metodológicas

## Fontes, unidade e auditoria

Entradas locais: `data/processed/df_tcc_2013_2024.parquet` e `data/raw/atlas_desastres/BD_Atlas_1991_2024_v1.0_2025.04.14_Consolidado.csv`. O consolidado do Atlas foi lido como Latin-1, separado por ponto e vírgula; Data_Evento usa dia/mês/ano. Data_Registro não substitui a data da ocorrência. Os hashes SHA256 e o dicionário de colunas/tipos/ausentes ficam nas tabelas da auditoria.

A unidade é **protocolo municipal único** (`Protocolo_S2iD` após remover espaços externos), conforme a decisão do chat “Inspeção de contagem de desastres”, novamente verificada nas bases. Entre 2013 e 2024 há 40.339 protocolos distintos, sem protocolos ausentes ou repetidos. Os 101 registros excedentes na chave município/data/COBRADE têm protocolos distintos: são preservados. Não há identificador validado para reconstruir um fenômeno físico que atinge vários municípios. Os resultados referem-se a registros municipais, não a 40.339 fenômenos independentes.

`grupo_de_desastre` e `descricao_tipologia` são preservados, removendo apenas espaços externos. “Outros” é uma categoria original, não um agrupamento criado aqui. Tipologias como Chuvas Intensas e Onda de Frio aparecem em mais de um grupo: essa classificação original é mantida e explicitada na tabela cruzada. Grupo e tipologia são duas classificações dos mesmos registros; suas somas reconciliam separadamente com o total, mas não devem ser somadas entre si.

A extração consolidada cobre 1991–2024 e contém registros em todos os meses de 2013–2024. O calendário é completado para todas as categorias. Um zero significa **nenhum protocolo observado na extração** naquele mês/categoria, não ausência certificada de fenômenos físicos. Não há painel independente da completude das notificações; subnotificação continua possível. Datas inválidas, protocolos ausentes/repetidos ou lacunas nacionais interrompem o código, em vez de virarem zeros silenciosos. Categorias ausentes são explicitadas como “Sem informação”, caso existam.

O Parquet tem 3.888 linhas, uma por UF × mês (27 × 144). A reconciliação compara, em cada uma dessas células, o total e todas as categorias: as divergências são zero. A taxa nacional é `100 * soma(carteira_inadimplencia_total) / soma(carteira_ativa_total)`, calculada uma única vez, **antes** de combinar com as séries de categorias. Não se faz média de taxas. O Parquet não contém a dimensão modalidade: a unicidade UF × mês garante que esta agregação não multiplica carteiras. Sem os CSVs brutos do SCR, não é possível certificar ausência de sobreposição de modalidades na origem. O script histórico `src/01_consolidar_scr.py` filtra PF e soma as linhas; essa limitação é expressa, não apresentada como uma auditoria concluída da origem.

## Recortes e estacionariedade

Total: janeiro/2013–dezembro/2024 (144 meses). Pré-pandemia: janeiro/2013–janeiro/2020 (85 meses). Cada transformação é calculada **dentro** do recorte. Primeira diferença perde 1 mês (143/84); diferença sazonal das primeiras diferenças perde 13 (131/72). As defasagens do modelo geram perdas adicionais.

ADF: constante, `autolag='AIC'`, máximo padrão de Schwert do statsmodels. ADF H0: raiz unitária. KPSS: constante, `nlags='auto'`; H0: estacionariedade em nível. Estatísticas, defasagens, n da série e n efetivo do ADF estão registrados. P-valores KPSS no limite da tabela são apresentados como limites (≤0,01 ou ≥0,10), não probabilidades exatas. Os avisos são preservados nas tabelas.

São avaliados nível, log (log1p para contagens), primeira diferença, diferença do log, diferença sazonal, primeira diferença seguida de sazonal e diferença do log seguida de sazonal. ADF rejeita e KPSS não rejeita: convergência favorável; o contrário: convergência desfavorável; demais casos são distinguidos entre conflito e inconclusão. Uma classificação favorável não prova estacionariedade, especialmente em séries esparsas. STL robusta e perfis mensais descrevem sazonalidade; não provam raiz unitária sazonal. ACF sazonal negativa após diferenciação pode indicar sobrediferenciação.

Mantêm-se as transformações históricas ΔI e Δlog(1+D) para comparabilidade. Quando ADF/KPSS não convergem, o modelo é **exploratório**, explicitamente marcado e não qualificado como achado robusto. Não há busca por transformações para obter significância. Não se suprime a limitação mudando automaticamente a transformação; as alternativas diagnosticadas permitem uma etapa futura de modelagem específica.

Critério operacional pré-especificado de raridade: menos de 12 meses positivos **ou** menos de 24 protocolos no recorte. É uma cautela analítica, não um teorema de tamanho amostral. Séries raras permanecem nas descritivas e ADF/KPSS, mas não recebem inferência Granger convencional. Séries constantes não admitem os testes. Nenhuma categoria é fundida.

## Modelos e seleção de ordem

São sistemas bivariados independentes: uma série de desastre por vez + inadimplência nacional. Não condicionam simultaneamente às demais categorias ou à economia. Três especificações: (1) primeiras diferenças + constante e 11 dummies (janeiro referência); (2) mesmas diferenças + constante; (3) diferença sazonal das primeiras diferenças + constante. Dummies permitem médias distintas para cada mês; não removem automaticamente correlação residual ou mudanças estruturais.

Cada equação é estimada por OLS. Granger compara o modelo irrestrito com outro que retira **somente** as p defasagens da variável causadora. Constante, dummies e defasagens próprias permanecem nos dois modelos, na mesma amostra. Testa-se conjuntamente H0: todos os coeficientes retirados são zero. O F tem p graus de liberdade no numerador e n − q no denominador. A hipótese secundária inverte causa e alvo; não significa que inadimplência provoque fenômenos naturais.

Máximo de 12 meses, limitado por `n−p−q ≥ 30` e `n−p ≥ 3q`, com `q=2p+12` (dummies) ou `2p+1`. Isso resulta em máximo 12/6 para total/pré com dummies, 12/11 sem dummies e 12/9 na robustez. AIC/BIC usam amostra comum dentro de cada categoria/período/especificação (início no lag máximo). Critérios: `log det(Σ_ML) + penalidade * 2q/n`, penalidade 2 no AIC e log(n) no BIC. Os modelos escolhidos são reajustados com toda a amostra disponível para aquela ordem. BIC é referência; AIC é comparação.

Para reproduzir a regra do notebook 06, a seleção para o **teste de Granger** é restrita a ordens positivas, 1…máximo. Também é reportado o ótimo incluindo p=0. Se este for zero, não há defasagens cruzadas a testar no modelo irrestritamente preferido; o teste em ordem positiva é identificado como condicionado à exigência de dinâmica e excluído da síntese favorável. Não se inventa p-valor para VAR(0). Designs singulares/inviáveis são registrados. A sensibilidade contém todas as ordens positivas estimáveis, sem escolher retrospectivamente o menor p-valor.

## Diagnósticos e múltiplos testes

Para AIC **e** BIC: estabilidade pelos autovalores da matriz companheira (módulo <1); Portmanteau multivariado ajustado com horizonte maior que p; Ljung–Box auxiliar por equação com ajuste de 2p parâmetros dinâmicos e horizonte >2p; ACF(12/24), Jarque–Bera e Breusch–Pagan. Portmanteau é o diagnóstico primário de autocorrelação do sistema; testes residuais são aproximações assintóticas, particularmente limitadas nas amostras menores e com determinísticas. Limites ±1,96/√n da ACF são uma triagem pontual, não bandas simultâneas nem teste formal de raiz sazonal.

F clássico requer hipóteses sobre erros. Reportam-se também Wald-F HC3 e HAC com 12 lags e correção de amostra como sensibilidades; não corrigem um modelo dinâmico mal especificado. Significância com autocorrelação/instabilidade não é tratada como confirmação robusta.

**Famílias BH dos modelos selecionados:** uma família por direção; cada uma inclui todas as categorias (total, grupos e tipologias), os dois períodos, as três especificações e as ordens selecionadas por AIC/BIC. Um mesmo modelo escolhido por ambos critérios entra uma só vez. Essa família ampla evita fragmentar a correção em dezenas de pequenos grupos favoráveis. Os p-valores ajustados são unidos novamente às duas linhas dos critérios. Também é fornecido Benjamini–Yekutieli (BY), conservador sob dependência arbitrária, pois categorias e períodos se sobrepõem. BH é a referência solicitada; sua garantia formal pressupõe independência ou dependência positiva apropriada, não verificada aqui.

**Famílias da sensibilidade:** separadas das anteriores, uma por direção, contendo todos os lags, categorias, períodos e especificações. Esse ajuste não é intercambiável com o BH dos selecionados. Os p-valores permanecem exploratórios: a correção não elimina incerteza pós-seleção da ordem nem especificação incorreta.

A coluna “Evidência com diagnósticos favoráveis” exige BH <5%, HAC12 <5%, estabilidade, Portmanteau ≥5%, ausência de pico ACF12 na equação-alvo, ADF/KPSS convergentes nas duas séries e ótimo incluindo zero diferente de zero. Não é prova de robustez universal. Consistência entre critérios, especificações e períodos é apresentada separadamente. Os períodos se sobrepõem: concordância não é replicação independente e diferenças de significância não são teste formal de mudança de efeito.

Granger indica precedência/conteúdo preditivo condicionado à especificação; o F conjunto não informa o sinal do efeito. Não permite concluir que desastres aumentam inadimplência nem estabelecer causalidade estrutural. Contagem não mede intensidade, perdas ou população afetada. A escala nacional pode ocultar efeitos locais e inclui tipologias não estritamente climáticas (p.ex., doenças infecciosas e barragens), preservadas conforme a fonte.

## Execução e saídas

1. Instale `requirements.txt` e `requirements-ampliacao.txt` em ambiente virtual.
2. Coloque as duas entradas nos caminhos acima.
3. Execute notebooks 07, 08 e 09, nessa ordem. O 07 reconstrói/audita as séries e testa estacionariedade. O 08 executa todos os sistemas (inclusive tipologias) para calcular BH na família completa, e interpreta grupos + referência. O 09 usa essas tabelas e verifica numericamente um teste; interpreta todas as tipologias.
4. Para executar e gravar todas as saídas sem depender de sockets Jupyter: `python src/executar_notebooks_categorias.py`. Cada notebook roda em um processo Python novo; todas as células são executadas via IPython e erros interrompem a execução. Esta foi a rota usada nesta entrega, pois o runtime não disponibilizou sockets para um kernel externo.
5. Alternativa de cálculo: `python src/analise_categorias.py`. Para gerar o HTML: `python src/relatorio_categorias.py --output CAMINHO_FORA_DO_REPOSITORIO.html`.

Tabelas em `outputs/tables/ampliacao/`; figuras em `outputs/figures/ampliacao/`; séries intermediárias em `data/processed/`, ignoradas pelo Git. O HTML é standalone com Plotly e dados embutidos; deve permanecer fora do repositório. Os notebooks 05/06 não foram alterados. Tabelas de resultados contêm estatísticas agregadas; nenhum protocolo individual ou base bruta é versionado.

Documentação primária consultada:
- https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.compare_f_test.html
- https://www.statsmodels.org/stable/generated/statsmodels.tsa.vector_ar.var_model.VARResults.test_whiteness.html
- https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html
- https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.adfuller.html
- https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.kpss.html
