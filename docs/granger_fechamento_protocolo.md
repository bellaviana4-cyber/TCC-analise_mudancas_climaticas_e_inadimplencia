# Fechamento de Granger — protocolo antes dos novos testes

Registro: 02/10/2026. Base main: 6aa18087e7c711c97a060a41a5c398909687ecb0.
Extensão exploratória informada pelos notebooks 05–14; não confirmação independente.

## Entradas, recortes e cobertura

Reutilizar a série nacional agregada publicada em outputs/tables/segunda_etapa/series_nacionais_agregadas.csv, SHA256 c613ebd61e25c05ebb4a4e0f3520c6570d673068d0b2ee2b6fc090468e1df679, conferido no checkpoint11. Ela contém a taxa nacional ponderada por carteira, não média simples, e protocolos agregados. Não reconstruir pessoas/imóveis ou auditar novamente bases brutas ausentes.
Conferir classificação original, 4 grupos e 16 tipologias; suas somas mensais devem reconciliar com total nacional. Preservar classificações e resultados anteriores.
Recortes fixos: jan/2013–jan/2020 (85 meses) e jan/2013–dez/2024 (144). São sobrepostos, não independentes. Todas as transformações/defasagens dentro do recorte. Matriz obrigatória: (1 total + 4 grupos + 16 tipologias) × 2 = 42 cenários.

## Hipótese e modelo principal

H0: coeficientes das defasagens 1–3 dos desastres são conjuntamente zero na equação da inadimplência, condicionada ao seu próprio histórico. Granger na equação: não é VAR nem teste de todo o sistema; permite precedência preditiva condicional, não causalidade estrutural.
Principal fixa: y=Δ12ΔI (pontos percentuais), x=Δ12Δlog(1+D). Intercepto, y(t−1), y(t−2), y(t−3), y(t−12), x(t−1..3). Lags fixos cobrem curto prazo trimestral e persistência anual, sem seleção pelo p. Diferença sazonal controla sazonalidade nesta versão; não acrescentar 11 dummies redundantes como ajuste automático. A escolha sazonal é motivada pelos diagnósticos anteriores, não por confirmação independente. Muda o estimando, consome meses e pode induzir MA/sobrediferenciação.
Usar datas comuns começando no índice25 original para todas as especificações: 119 observações total e60 pré, se completas. GL≥30, n≥3k e posto completo. Sem winsorização, eliminação permanente de extremos ou STL bilateral. Sem exposição contemporânea na equação.

## Sensibilidades finitas

1. ΔI e Δlog(1+D), mesmos lags fixos, intercepto +11 dummies mensais.
2. 100Δ12Δlog(I) e Δ12Δlog(1+D), mesmos lags fixos, intercepto; I>0 exigido.
3. Principal sazonal com p próprio1..6 no total/1..3 no pré, I12 fixo, q=0..3, BIC em amostra comum e limites de GL. Reportar melhor q>0 para teste conjunto e ótimo geral incluindo q0, como no14. Sensibilidade pós-seleção explícita; não substituir principal pelo menor p.
Variação relativa sem diferença sazonal e demais modelos05–14 permanecem disponíveis como evidência anterior; não reexecutar indiscriminadamente. Não executar painel, previsão ou outro método novo nesta solicitação.

## Estacionariedade, adequação e estabilidade

ADF/KPSS por série transformada e recorte, com mesma regra anterior (ADF BIC, máximo min(12,n/4); KPSS largura automática). Concordância: ADF<5%, KPSS≥5%; ADF≥5%/KPSS<5% indica não estacionariedade; outros desacordos/falhas são inconclusivos. Registrar estatísticas, lags, limites tabulares e avisos. Usar toda série transformada para triagem, registrar também seu n; teste dinâmico usa datas comuns.
Exposição elegível: sem ausentes/negativos, pelo menos12 meses positivos, soma de protocolos≥24, variação positiva; n/GL/posto conforme acima. Cenários raros/inviáveis mantidos, p original ausente e p=1 só para correção. Diagnóstico ruim não exclui teste da família.
Diagnósticos da equação: BG1/BG12 LM e F, BP, ARCH3, RESET HC3, CUSUM, ACF1/12, raiz autorregressiva e Cook. Influência: refit removendo apenas a linha de maior Cook, sem alterar a série original; mudança da soma comparada com1SE robusto. Dados finitos em todos os diagnósticos exigidos. Não rejeitar não prova adequação; múltiplos diagnósticos também têm erros de tamanho/potência.
Estabilidade adicional no total: indicador pós-março/2020 e interações com todos os termos próprios e da exposição, em equação separada com posto/GL conferidos. Testar conjuntamente indicador/interações por HAC; reportar também teste dos termos da exposição em interação. Sem usar datas endógenas. Sensibilidade não troca equação principal. Pré não recebe esse teste, pois março2020 está fora de sua janela. Divergência entre CUSUM e teste de mudança é registrada, não apagada. Uma rejeição nominal de estabilidade limita a interpretação, mesmo se ajuste do diagnóstico não rejeitar.
Triagem principal: concordância das duas séries, BG1/BG12, RESET e CUSUM≥5%, raiz<1, influência≤1SE; no total estabilidade adicional finita e p≥5%. BP/ARCH informam limites e justificam sensibilidade robusta. q0 é parcimônia, separado da adequação. Mostrar triagem básica e ampliada separadamente para comparação com14.

## Inferência e famílias

Referência: Wald-F HAC12, correção pequena amostra e t/F com GL residual. Reportar clássico/HC3 e IC95% pontuais de cada lag e soma; soma não é IRF ou resposta causal acumulada. Não escolher covariância pelo menor p. HAC não cura dinâmica inadequada. Bootstrap sob H0 não aplicado automaticamente, principalmente se estabilidade/resíduos inadequados; não expandir métodos para obter rejeição.
Família PRINCIPAL42. Família SENSIBILIDADES126 (3×42). BH, BY e Holm das famílias inteiras, antes de filtrar diagnósticos; reservas p=1. Ajustar clássico/HC3 nas mesmas famílias como sensibilidades. Reportar ainda BH/BY/Holm global168 para tornar visível multiplicidade entre principal e sensibilidades, sem substituir famílias prévias.
Estabilidade: família separada de84 cenários totais (21 exposições×4 especificações), para o teste geral; mesma dimensão para os testes de interações de exposição. Não misturar diagnóstico com família de Granger nem usar correção de estabilidade para esconder rejeição nominal.
Os resultados05–14 mantêm p ajustados/famílias originais. Onda de Frio do14 permanece exploratória. Comparações pré/total não são teste de mudança nem confirmação independente.

## Entrega e retomada

Notebook15 executado, matriz42, tabelas completas168, coeficientes, estacionariedade, diagnósticos, ambiente, validações e checkpoint com hashes. HTML standalone externo, todas categorias e os dois períodos, inclusive exclusões. Código/template do HTML permanecem externos nesta etapa. Registrar conclusão de encerramento de Granger mesmo se não houver cenários adequados. Nenhum próximo método é executado.
Executor antigo: implementar --retomar por etapas/hashes com manifestos novos versionados. Checkpoints10–13 anteriores são snapshots históricos, não garantem que todas as tabelas atuais tenham hashes antigos. Não relabelar execução histórica como reprodução atual. Sem entradas originais, verificar saídas/histórico e registrar limites; não reconstruir hashes brutos a partir de arquivos agregados. Invalidação não provoca recálculo silencioso.
Publicar protocolo antes de estimar, commits separados, PR/merge sem force push, preservar05–14. Fontes metodológicas: documentação oficial statsmodels (ADF/KPSS, BG, RESET, CUSUM, Wald/HAC); nenhum p ajustado certifica pressupostos ou identifica impacto climático causal.
