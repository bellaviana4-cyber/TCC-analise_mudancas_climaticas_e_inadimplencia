# Segunda etapa — protocolo registrado antes dos novos testes

Data de registro: 30/09/2026. Base remota: cee778561fbed9cb3157b47eca934618be1bcff8. Extensão informada pelos resultados anteriores; não é confirmação independente. Nenhum novo p-valor de relação exposição–inadimplência foi calculado antes deste documento.

## Pergunta, unidade e prioridades

H0 principal: o histórico de exposição a desastres não acrescenta informação à equação dinâmica da variação mensal da taxa de inadimplência PF, condicionado ao próprio histórico e à sazonalidade. Rejeição indica precedência preditiva condicional, sem identificação causal estrutural. Hipóteses secundárias: associação dentro de UF, resposta acumulada em horizontes fixos, e redução do erro fora da amostra. Nacional total é prioritário; pré-pandemia é exploratório, sobretudo se ADF/KPSS inconclusivos.

Recortes imutáveis: 2013-01 a 2024-12 (144 meses), 2013-01 a 2020-01 (85). Transformações começam dentro de cada recorte. Taxa nacional = 100 × soma das carteiras inadimplentes / soma das carteiras ativas. UF: mesma razão em cada UF. Nenhuma média simples nacional. Preservar 05–09 e BH anterior; reutilizar hashes, classificações e tabelas anteriores sem reexecutar a auditoria histórica.

## Nacional: dinâmica e determinísticas

Equação ADL em ΔI (pontos percentuais) com Δlog(1+exposição), constante e 11 dummies. Ordens próprias p=1..6 no total, 1..3 no pré; q=1..3 para exposição. Inclui ΔI(t−12) fixo em todos os candidatos para permitir persistência sazonal além de médias mensais. Isto é uma extensão planejada motivada pelo diagnóstico anterior. BIC da equação de inadimplência em amostra comum desde lag 12; n−k≥30 e n≥3k. Seleção de q positivo permite teste conjunto, mas registrar também ótimo incluindo q=0; se q=0 for preferido, não chamar a evidência de robusta. Reajustar modelo escolhido somente na mesma amostra comum (sem recuperar meses). AIC é registrado como descritivo, sem gerar outro teste escolhido por significância.

Sensibilidade determinística única: no total acrescentar indicador de março/2020 a fevereiro/2021; é janela externa fixa, não data otimizada pelos dados. Pré não duplica teste. Zivot–Andrews (uma quebra endógena, c e ct) e ADF/KPSS avaliam integração, sem substituir transformação por menor p-valor; quebra estimada não vira controle automático. CUSUM e interação dos termos dinâmicos com pós-março/2020 avaliam estabilidade, sem interpretar data endógena como causal.

Diagnósticos: BG LM e F em 1 e 12 meses, ACF12, BP, ARCH(3), CUSUM, estabilidade da matriz companheira dos lags próprios, RESET, Cook e sensibilidade retirando o mês mais influente. Estatísticas e exclusão ficam registradas. F clássico, HC3 e Wald-F HAC(12) são reportados; HAC é referência para BH, mas não salva autocorrelação, instabilidade ou estacionariedade inconclusiva. IC HAC pontuais para cada lag e soma dos coeficientes; a soma não é efeito estrutural nem resposta total do sistema. Influência é material se mudança da soma superar 1 erro-padrão HAC; não retirar permanentemente extremos.

Triagem favorável exige ADF/KPSS convergentes em ambas as diferenças, BG1/BG12≥5%, CUSUM≥5%, raiz própria<1, RESET≥5%, q=0 não preferido e influência não material. BP/ARCH desfavoráveis são destacados e exigem sensibilidade robusta; não excluir da família. Testes diagnósticos são triagem, não prova dos pressupostos.

Toda–Yamamoto: no máximo total nacional e protocolos climáticos × dois períodos (4 hipóteses reservadas). Apenas se primeira diferença convergente nas duas séries e nenhum indício de I(2); d_max=1 como limite conservador, mesmo se uma exposição for I(0). VAR em I e log(1+D), 11 dummies; k=1..6 total/1..3 pré por BIC em amostra comum k máximo+1; ajustar k+1 e testar apenas primeiros k lags de D na equação I. Se modelo-base ADL tiver autocorrelação ou instabilidade, não executar TY como resgate. Registrar inviabilidade, sem inventar p-valor. Bootstrap temporal sob H0 não é obrigatório: só justificável se dinâmica e estabilidade adequadas e procedimento reproduzir seleção; não usar bootstrap condicional de ordem para resolver pós-seleção. Esta entrega prioriza inferência exploratória transparente e avaliação OOS; registrar por que bootstrap não foi aplicado.

## Exposição: poucas medidas e auditoria específica nova

Comparabilidade: contagem total, 4 grupos e 16 tipologias originais. Foco climático: COBRADE natural com prefixo 12 (hidrológico), 13 (meteorológico), 14 (climatológico). Mantém códigos originais e tabela de inclusão por código/grupo/tipologia; geológicos como movimento de massa/erosão excluídos do foco por mecanismo climático não certificado, permanecem na comparação histórica; biológicos/tecnológicos e Outros não entram automaticamente. A classificação do Atlas não será reescrita.

Quatro medidas climáticas: protocolos (frequência); municípios distintos por UF/mês (abrangência); desabrigados+desalojados (registros de deslocamento); habitações danificadas+destruídas (registros de dano). Pessoas e habitações não são indivíduos ou imóveis únicos; campos de condição podem ter sobreposição e mudar entre protocolos. Não somar total de danos a seus componentes. Auditar ausentes, zeros informados, valores negativos, quantis, máximos, participação do maior registro e cobertura por ano/UF. Lacuna em componente implica indicador ausente naquele protocolo e agregado; não completar com zero. Sem protocolo = zero observado na extração, não ausência física certificada. Indicador inferencial elegível se ≥95% dos protocolos completos, ≥95% células UF/mês completas, todos os meses nacionais completos, ≥24 protocolos e ≥12 meses positivos no recorte; caso contrário apenas descritivo. Reservar teste excluído na família com p=1 para ajuste, p original permanece ausente.

PEPR_total_privado será auditado e comparado à soma dos componentes, sem somar ambos. Só entra em modelos se unidade, correção monetária e mês-base desta versão forem verificáveis na fonte oficial. Manual antigo já informa correção monetária: não deflacionar uma segunda vez por suposição. Sem confirmação de mês-base do consolidado 2025, excluir monetários da inferência e registrar bloqueio. Não ampliar família nacional para indicador monetário nesta rodada.

## Famílias pré-definidas, antes de resultados

Todas na direção desastres → inadimplência. BH a 5% e BY sob dependência arbitrária, sem promessa de independência/PRDS. Famílias mantêm hipóteses inelegíveis como p=1 no ajuste, sem fabricar teste.

- NACIONAL: 21 séries históricas + 4 exposições climáticas × 2 períodos = **50** hipóteses. BH dos p HAC, p clássico e HC3 separados. Durante etapa nacional inicial, 8 hipóteses de exposições futuras permanecem reservadas com p=1; ajuste completo na etapa 11, sem reduzir família.
- DETERMINISTICAS: mesmas 25 séries apenas período total com janela pandêmica = **25** sensibilidades. Nunca substituir NACIONAL por esta família.
- TY: **4** hipóteses reservadas, conforme viabilidade acima.
- PAINEL: 4 exposições climáticas × 2 períodos = **8**, p Driscoll–Kraay; sensibilidades em largura 6/12 e agrupamento UF separadas, sem selecionar menor p.
- RESPOSTA: municípios súbitos e protocolos de estiagem em janela de 3 meses × 2 períodos × horizontes 1,3,6,12 = **16**. BH e Holm, IC simultâneos Bonferroni (16). Sem horizonte zero, sem direção inversa.
- PREVISAO: protocolos e municípios climáticos × 2 períodos = **4** comparações reservadas; BH se viável.

P-valores de modelos escolhidos por BIC permanecem condicionais/pós-seleção, exploratórios; BH não resolve seleção ou má especificação. Não qualificar a extensão como teste confirmatório independente. Resultados significativos ajustados com diagnósticos favoráveis, nominais, inadequados/inconclusivos e não significativos serão distinguidos.

## Painel UF × mês

Alternativa transparente a GMM: ADL de ΔI com efeitos fixos UF e mês-calendário completo (choques comuns), lags próprios 1,2,3,12 e Δlog-exposição 1,2,3 fixos. Painel balanceado completo por cenário; não agregar 27 testes separados. Inferência Driscoll–Kraay Bartlett largura 12, aproximação t/F com 26 GL, sensibilidade largura 6 e cluster UF (27, limitado sob dependência entre UFs). DK explora T relativamente longo; não depende de N grande. Efeitos UF e calendário removem diferenças permanentes e choques comuns, sem garantir exogeneidade. Não usar carteira contemporânea como controle de mecanismos; não incluir indicadores econômicos sem cobertura oficial compatível verificada.

Viés com y defasado permanece. Sensibilidade split-panel jackknife temporal 2β_full−(β_half1+β_half2)/2, removendo lags que atravessam cada metade; não atribuir IC original ao estimador corrigido. Exige homogeneidade temporal; comparar metades e registrar divergência. Viés material se soma SPJ divergir mais de 1 SE DK; nesse caso não qualificar como evidência robusta. Autocorrelação: equação auxiliar dos resíduos com lags1/12, mesmo design/FE, Wald DK; dependência entre UFs via correlações e Pesaran CD descritivo (FE de tempo pode distorcer distribuição). Não usar CD como certificação. Estacionariedade: ADF/KPSS ΔI por UF, sem testar apenas UFs favoráveis; painel exploratório quando convergência <80%. Influência: retirar cada UF separadamente, reportar amplitude dos coeficientes, sem selecionar estados.

## Resposta e previsão

Projeções locais nacionais, associativas: I(t+h)−I(t), h=1,3,6,12, sobre mudança log da abrangência de eventos súbitos (prefixos12/13) ou mudança log da soma de protocolos de seca/estiagem nos 3 meses anteriores inclusive t (14110/14120), controles ΔI(t) e lags1,2,3,12, exposição lags1,2,3, dummies e janela pandêmica no total. HAC max(12,h), IC pontual e simultâneo; controles são contemporâneos ao mês t para resposta a partir do mês seguinte, sem afirmar choque exógeno. Usar apenas data de evento não prova disponibilidade de informação. Janela3 não identifica duração física da estiagem.

Previsão 1 mês, janelas expansivas com início mínimo 72 meses e mínimo 24 previsões para comparação inferencial. Pré tem apenas 13 previsões e será descritivo. Escolher p por BIC no treino do benchmark (1..6 ou1..3; lag12 fixo, dummies); modelo acrescido preserva p e escolhe q=1..3 no mesmo treino/amostra. Transformação log/diferença é fixa e causal; nenhuma normalização global/STL ou seleção usando teste. Somar previsão de ΔI à última taxa, erro em pp. RMSE/MAE; diferença pareada de MSE, IC bootstrap circular em blocos6, 1.999 repetições semente20260930, teste HAC de média do diferencial. Models aninhados: teste/IC são descritivos, não DM confirmatório convencional. Data_Registro avalia atraso e inconsistências; não comprova revisões/vintages. Se não houver vintages, exercício pseudo-OOS de dados revisados, não desempenho operacional certificado.

Poder/efeitos detectáveis: opcional condicionado a especificação estável. Preferir não simular tamanho/poder de um modelo reprovado. Justificar explicitamente a decisão.

## Checkpoints, publicação e reprodução

10 dinâmica nacional e comparação histórica; 11 auditoria de exposição e modelos; 12 painel; 13 resposta/previsão. Cada notebook executado antes de publicar commit de etapa. Arquivos brutos e intermediários em data ignorados; outputs apenas agregados. HTML fora do repositório. src/segunda_etapa.py concentra regras reproduzíveis. Dependências fixadas com versões efetivas. Checkpoints incluem hashes de entradas/protocolo/código e status por etapa; não reutilizar se código/entradas mudarem. Nenhuma etapa anterior será recalculada nesta extensão.

## Fontes metodológicas e pendências

- Statsmodels: BG, CUSUM, ADF/KPSS, Zivot–Andrews, cov_nw_groupsum (DK), OLS/Wald; https://www.statsmodels.org/stable/
- Dhaene & Jochmans (2015), Split-panel Jackknife Estimation of Fixed-effect Models, Review of Economic Studies 82:991–1030; https://www.repository.cam.ac.uk/items/566eded3-b3fa-4239-b061-eb3240b097ea
- Toda & Yamamoto (1995), Statistical inference in vector autoregressions with possibly integrated processes, Journal of Econometrics 66:225–250.
- Atlas manual oficial: https://atlasdigital.mdr.gov.br/arquivos/Atlas_Digital_Desastres_Manual_Aplicacao.pdf (acesso integral bloqueado na consulta; versão histórica menciona correção monetária).
- MIDR atualização consolidado2024: https://www.gov.br/mdr/pt-br/noticias/atlas-digital-de-desastres-no-brasil-e-atualizado-com-dados-consolidados-de-2024/
- COBRADE: validar prefixos naturais na classificação oficial antes do indicador climático.
