# DLM clássico, sem spline — protocolo prévio

Registrado em 05/10/2026 antes de novos resultados, por solicitação da autora. Preservar notebooks 16–18, saídas e arquivos anteriores. Uma figura antiga já estava modificada no início desta etapa; não incluí-la nos commits. Não executar Granger ou SARIMAX.

## Pergunta e especificação

Painel é o desenho principal. ΔI em pontos percentuais, UF + mês-ano FE, não ponderado, cobertura municipal relativa C_prop sem log. DLM irrestrito: ΔI_it = α_i + λ_t + Σ(k=1..K) β_k X_i,t-k + ε_it, K=1,...,10. Cada lag tem seu próprio coeficiente: não há spline/Almon. Interpretar '1 a 10' como exclusão do contemporâneo e comparação dos dez horizontes máximos. Principal fixo K10; demais K são sensibilidades, sem seleção por significância. BIC/AIC descritivos em amostra comum usando disponibilidade dos lags até 10. Adicionar somente uma comparação contemporânea 0..10 e uma sensibilidade ΔX com 1..10 por exposição/período. ΔX muda estimando: mudança da exposição registrada, não a mesma intervenção em cobertura de nível.

## Amostra e suporte

Recortes Total jan2013–dez2024 e Pré jan2013–jan2020. Lags/diferenças por UF em calendário contínuo, construídos antes de excluir equações. Para comparar todos desenhos, usar amostra comum elegível para ΔX lag10 (primeira resposta dez2013), sem informação pré2013 inventada. Guardar N, datas, rank, condição padronizada, UFs na janela, concentração por alavancagem e contraste. Manter a triagem ex ante anterior de 48 cenários planejados/46 elegíveis; não eliminar categorias nulas. Falha de rank: reportar não identificável. Matriz/covariância singular não pode ser contornada por pseudoinversa silenciosa para declarar teste.

## Estacionariedade

Reabrir CIPS anterior: nível de I tem evidência sensível a determinísticos; ΔI rejeita raiz unitária em ambos recortes/lags. Não declarar p tabulado=0,01 como valor exato. CIPS anterior das exposições foi indisponível por unidades constantes/quase constantes; não é confirmação de estacionariedade. ADF com intercepto, maxlag3 e autolag BIC; KPSS com intercepto e nlags auto por UF para nível/Δ de I e nível/Δ de todas24 exposições. Séries constantes/quase constantes: diagnóstico indisponível, registrado. Classificação complementar por concordância ADF p<0,05 e KPSS p>=0,05. Testes por UF não corrigem dependência transversal e não certificam estacionariedade global. Não diferenciar repetidamente até obter p favorável. Nível de cobertura permanece estimando principal solicitado (associação com exposição); ΔX é sensibilidade explícita se diagnóstico não sustentado. Séries limitadas podem ter mudanças estruturais; limitação não desaparece por serem proporções.

## Inferência e multiplicidade

α=0,05 e IC95% em todas etapas; essa já era a regra anterior. Reportar p nominal e q BH separadamente; não abandonar multiplicidade ao usar5%. Cluster UF CR1S + DK12 para todos os modelos. CR2/Satterthwaite/HTZ via clubSandwich para K10 principal, contemporâneo e ΔX (46×3), sem fórmulas aproximadas. Wild bootstrap restrito validado na revisão anterior, 4999 em K10 elegíveis e9999 para Total/Onda de Frio e categorias previamente centrais, acumulado e conjunto, sem rank singular permitido. Não repetir bootstrap em dez K apenas para procurar menor p. Famílias48 por K, desenho e endpoint; adicional grade global480 para comparação exploratória dos K. Coeficientes individuais/perfis: descritivos e IC ponto a ponto, não dez oportunidades de resultado. Conjunto CR2 indisponível não é p=1 observado; somente conservador no cálculo BH para manter família planejada.

## Atlas, apresentação e reprodução

A mantém todas40339 linhas; B usa chave UF/IBGE município/data evento/COBRADE, keep-first após verificar taxonomia consistente,40238 chaves;101 linhas adicionais só deixam B, não Atlas/A. C considera município distinto no mês, repetição da chave não muda sua cobertura. Não identifica tempestades físicas únicas. Verificar diretamente esses números e invariância da cobertura sob deduplicação.

Notebook19 novo, tabelas/figuras em dlm_classico, novo HTML offline fora Git; explicações específicas, p/q, escalas e limitações. Não substituir análise nacional anterior: explicar pergunta diferente, preservar como complementar. Publicar branch/PR semmerge depois dos testes. Testes calendário, lags livres, comparação com OLS FE explícito, covariância completa acumulada, metadados K, famílias480/48, deduplicação e igualdade Python/R. Encerrar após execução integral e correção de falhas essenciais; resultados com suporte limitado continuam diagnósticos.
