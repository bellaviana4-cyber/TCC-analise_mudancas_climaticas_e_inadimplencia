# Referência atual: DLM clássico em painel, diferenças logarítmicas

Protocolo definido em 06/10/2026 antes da estimação. O capítulo `c3_metodologias_tg.tex` orienta o DLM finito; a base atual define períodos e unidades. Granger preservado e SARIMAX não executado.

## Decisões prévias

| decisão | por que | implementação | consequência para interpretação |
|---|---|---|---|
| Painel não ponderado de 27 UFs | mesma estrutura em ambos recortes | UF + mês-ano completos, MQO/FWL | coeficiente comum; UFs sem registros permanecem |
| y=Δlog(I); x=Δlog(1+D) | escolha substantiva da autora, comparação coerente | log natural antes da diferença, dentro da UF e do recorte | unidades logarítmicas, não pontos percentuais |
| D=registros administrativos | preservar medida solicitada | linha original do CSV, identificada pelo hash da fonte + número de linha; contar por UF e mês de Data_Evento | não eventos físicos únicos, intensidade ou área atingida |
| Total climático central | classificação sem sobreposição | selecionar uma vez linhas cujo COBRADE começa em 12/13/14 | hidrológico/meteorológico/climatológico; geológicos excluídos mesmo quando chuva pode ser gatilho |
| Grupos/tipologias originais complementares | preservar taxonomia e ambiguidades | um modelo por coluna original, nunca simultâneos | Outros/biológicos/barragens não exclusivamente climáticos |
| K=6 fixo, incluindo k=0 | janela mensal de curto prazo: choque imediato, perda de renda e transmissão à inadimplência nos meses seguintes; parcimônia | 7 coeficientes livres; nenhuma seleção AIC/BIC | não exclui associação após 6 meses; não prova duração do fenômeno |
| Sem AR, spline ou regime | DLM clássico explicável | nenhum lag de y | sem resposta recursiva autorregressiva |
| Estacionariedade | diagnósticos nacionais não validam UFs | ADF intercepto, AIC, máximo min(12, regra Schwert admissível); KPSS intercepto/banda auto | inconclusão preserva análise exploratória; não rejeição não confirma |
| Inferência CR1 | autocorrelação/heterocedasticidade dentro de UF | G/(G−1) × (n−1)/(n−p_total); t26 e Wald F(r,26) | correção não elimina problemas de poucos clusters efetivos |
| Comparação DK | dependência transversal esperada no histórico | Bartlett, largura 6 meses, scores agregados por mês; t(T−1), F(r,T−1); mesma correção n/(n−p_total) | aproximação de T grande, sensível à largura; não corrige endogeneidade |
| Suporte mínimo | não confundir pouca exposição com precisão | mínimo 24 registros, 12 células positivas, 5 UFs, 8 meses positivos na janela; rank completo e variação TWFE | exclusões documentadas sem p fabricado; concentração Neff<5/top1>50%/top2>80% recebe ressalva |
| BH | aplicações paralelas por categoria | família por período × nível (Central/Grupo/Tipologia) × covariância × endpoint; testes indisponíveis apenas p=1 conservador no ajuste | p nominal e q separados; endpoints beta0, soma0:6, soma1:6, conjunto0:6 e conjunto1:6 separados |

## Modelo efetivo

Δlog(I_it)=α_i+λ_t+Σ(k=0..6)β_k Δlog(1+D_i,t−k)+ε_it.
I=100 carteira_inadimplencia_total/carteira_ativa_total>0. Recortes: jan2013–jan2020 e jan2013–dez2024, sobrepostos. Diferenciar após recortar e defasar somente por UF: primeira equação ago2013, perda de 7 meses por UF. Dados faltantes param a auditoria; zeros apenas ausência de registros na fonte completa conciliada, não ausência de crédito.

FWL por dupla centralização apenas em painel balanceado com calendário idêntico; equivalência com dummies explícitas verificada. Solução por sistema de posto completo, nunca pseudoinversa para mascarar falhas. Critérios informativos no modelo fixo usam p_total=G+T−1+7; não são usados para seleção.

ADF: Δz_t=c+γ z_(t−1)+Σφ_j Δz_(t−j)+u_t; H0 γ=0 (raiz unitária), H1 γ<0. KPSS: z_t=c+r_t+u_t; r_t=r_(t−1)+η_t; H0 Var(η)=0, H1 Var(η)>0. Ambos p≥0,05: inconclusivo. ADF rejeita/KPSS não: favorável, não certificação. Ambos rejeitam: divergente. ADF não/KPSS rejeita: evidência desfavorável registrada, sem transformação automática. Determinísticos com tendência mudam a hipótese para estacionariedade em torno da tendência; esta execução fixa intercepto. Testes por UF não corrigem dependência transversal. CIPS histórico sobre ΔI/cobertura não é teste de Δlog(I)/Δlog1p(D) e fica separado, sem transferência de validação.

Normalidade e homocedasticidade não são condições universais de consistência com inferência robusta. Exogeneidade estrita: E[ε_it | X_i1,…,X_iT,α_i,{λ_s}]=0; a origem natural não garante a condição. TWFE identifica pela variação após remover ambos os FE, não por toda variação bruta dentro da UF. Não assumir cointegração.

Soma: variância c'Vc; bandas das figuras pontuais, não simultâneas. Soma β relaciona pulso unitário em Δlog1p(D) à mudança acumulada em log(I) no horizonte. Cenários: aumento persistente D: δx no início, zero depois; pulso de um mês em D: +δx no início e −δx no seguinte. Resposta = convolução com β, acumulada e convertida por 100[exp(resposta log acumulada)−1]. Isso é variação relativa de I, não pontos percentuais, desastre único ou causalidade de longo prazo.
