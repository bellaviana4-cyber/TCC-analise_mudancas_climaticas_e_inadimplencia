# Referência atual de DLM: painel em diferenças logarítmicas

Execução real de 06/10/2026. Notebook **22_dlm_painel_diferencas_logaritmicas.ipynb**, 10 células Python executadas sem erros, stdout e SVG reais. O executor usa `compile/exec` em namespace compartilhado (sem exigir kernel Jupyter/socket). Os notebooks anteriores não foram executados. Granger preservado; SARIMAX não executado.

## Retomada e histórico

Main inicial: `027ee8aa245494765d99bff2511b6f60b30ddf41`, fechamento Granger, sem integração das branches DLM. Foram conferidas `analise/dlm` (`3c94482628b86d1789ee98f8d35f6820835a7219`), `analise/dlm-revisao-metodologica` (`c64589abc0f886a4e55e73b32328f8b0206376aa`), `analise/dlm-validacao-final` (`87bee9689528b9d273c660ed2aff19c4739d8c54`) e `analise/dlm-classico-1a10` (`18bc6ef34f02e90810b1cd6d3170c41f81cf94db`). Nenhum AGENTS.md nessas árvores. Protocolos, checkpoints, funções de auditoria/inferência e notebooks 16–21 foram inspecionados para reaproveitar informação, sem importar modelos experimentais. Histórico permanece nesses commits/branches; `dlm_painel_log_historico.json` registra os pontos de referência. CIPS relevante anterior foi copiado como histórico claramente rotulado.

## Base, exposição e amostra

3.888 células, 27×144, calendário jan2013–dez2024, chave UF-mês única e completa. Todas carteiras positivas e CI≤CA, TI=100CI/CA; maior diferença numérica 1,78e−15. Nenhum crédito ausente virou zero. Atlas completo tem datas válidas; recorte contém 40.339 linhas, sem protocolos repetidos/ausentes. A chave municipal/data/código tem 101 repetições, mantidas na contagem A. Identificador de linha = SHA256 fonte + posição original, cabeçalho=1; protocolo preservado como campo auditado. Data_Evento define o mês, não Data_Registro. Não se identifica evento físico regional único.

Total climático = **37.643 registros**, selecionados diretamente por COBRADE 12/13/14 (hidrológico, meteorológico e climatológico). Não somamos grupos sobrepostos. Todos os grupos e tipologias originais foram conciliados UF-mês, diferença zero. Biológicos, tecnológicos e geológicos são excluídos do total central. Isso exclui movimentos de massa/erosão mesmo quando chuva pode ser gatilho. Rótulos originais preservados nas aplicações complementares, com ambiguidades em `taxonomia.csv`: 13310/Chuvas Intensas, 13120/Onda de Frio e 14140/baixa umidade. Referência de códigos: https://www.defesacivil.pr.gov.br/sites/defesa-civil/arquivos_restritos/files/documento/2022-10/cobrade.pdf .

Pré: 2.295 células originais, 2.106 efetivas, ago2013–jan2020 (78×27). Total: 3.888 originais, 3.699 efetivas, ago2013–dez2024 (137×27). Perda: 27 observações pela diferença, mais 162 pelos lags, em cada recorte; não há uso de meses pré2013. Janelas sobrepostas. Total climático tem 27 UFs expostas nas duas, N_eff de contagens ≈14,40/14,04 na janela e ≈13,89/13,65 na amostra efetiva.

21 aplicações planejadas por recorte: central +4 grupos +16 tipologias. **40 estimadas (19 pré/21 total)**. Calor/Baixa Umidade pré (19 registros) e Barragens pré (15) não atingem suporte mínimo; permanecem registradas sem inferência. Estados sem exposição ficam em todos modelos.

## Modelo e inferência

Δlog(I_it)=α_i+λ_t+Σ(k=0..6)β_k Δlog(1+D_i,t−k)+ε_it. MQO não ponderado por FWL, UF e mês-ano completos. K=6 fixo substantivo antes dos resultados, sem busca de K/AR, sem lag de y, spline, nacional agregado ou regimes. Sete coeficientes livres por exposição, rank completo nas 40 aplicações; máximo condicionamento padronizado≈4,97. AIC/BIC são metadados do modelo fixo, não selecionam especificação.

CR1 com G/(G−1)×(n−1)/(n−p_total), p_total=G+T−1+7; contrastes t26 e conjuntos Wald F(r,26). DK6 é comparação única por dependência transversal, Bartlett L=6, correção n/(n−p_total), t(T−1) e F(r,T−1). Ambas são aproximações; categorias concentradas não têm 27 clusters informativos. Não executamos bootstrap/CR2/placebos/interações. BH por período×nível×covariância×endpoint. Na família central, uma aplicação por período, q=p. Famílias de grupos têm 4, tipologias 16; indisponíveis p=1 apenas para cálculo BH, sem declarar teste fictício.

## Estacionariedade e validade

ADF intercepto/AIC, maxlag min(12, limite Schwert admissível); KPSS intercepto/banda auto. Estatísticas, determinísticos, n, lags, críticos e limites p estão nas tabelas. Não concatenar estados. Δlog(I): pré 6 favoráveis, 19 inconclusivas, 2 desfavoráveis (RO, SC); total 18 favoráveis, 8 inconclusivas, 1 desfavorável (RO). A exposição climática Δlog1p(D): 26/25 favoráveis, 1/2 divergentes (ambos testes rejeitam). Séries constantes continuam indisponíveis.

Evidência desfavorável na dependente é um comprometimento da validação: a regressão completa **não é apresentada como validada**; resultados são associações exploratórias condicionadas às hipóteses. Não eliminar UFs para melhorar testes, não substituir transformação, não assumir cointegração. FE e covariância robusta não corrigem raízes unitárias. O diagnóstico nacional fornecido no pedido é referência externa a esta execução; o CIPS anterior foi sobre I/ΔI/cobertura, não prova da transformação atual. Testes por UF não certificam painel nem corrigem dependência transversal.

## Principais resultados centrais

| Período | Soma β0..β6 | IC95% CR1 | p CR1 | IC95% DK6 | p DK6 |
|---|---:|---|---:|---|---:|
| Pré | 0,002709 | [−0,006075; 0,011493] | 0,531682 | [−0,004475; 0,009893] | 0,455025 |
| Total | 0,004372 | [−0,001265; 0,010009] | 0,122966 | [−0,000122; 0,008865] | 0,056438 |

β0: pré 0,000048, p CR1=0,911; total 0,000623, p CR1=0,053. Soma1..6: pré 0,002661 (p=0,520), total 0,003749 (p=0,165). Teste conjunto0..6: p CR1=0,823/0,324; DK6=0,610/0,116. Todos valores e perfis estão exportados. Não há rejeição central a 5%. Isso não demonstra ausência de associação; p diferentes entre recortes sobrepostos não demonstram mudança temporal.

Categorias: Movimento de Massa total tem soma0..6=0,017838, p CR1=0,000281, q=0,004498; DK6 p=0,003678, q=0,058849. Soma1..6 também rejeita em CR1, sem BH/DK. Não sustentamos associação acumulada robusta dessa categoria diante da comparação de covariâncias. É geológica, não componente central climático. Há rejeições contemporâneas e conjuntas nas tabelas; o HTML lista todas sem selecionar apenas favoráveis. Somatório pode compensar coeficientes de sinais opostos mesmo quando o teste conjunto rejeita.

## Diagnósticos

Correlação residual absoluta média do central: 0,1694 pré, 0,1729 total; máximas 0,654/0,602. Cluster UF não resolve dependência entre estados, justificando DK6. CD ingênuo sob FE de tempo não é teste calibrado; seus valores ficam estritamente descritivos, sem inferir ausência pelo seu p. Levene/Ljung–Box são descritos como diagnósticos, com pressupostos e resíduos estimados, não validação definitiva. Há dispersão heterogênea e autocorrelação residual registrada por UF. VIF central máximo 2,59/2,33; correlação máxima dos lags 0,390/0,373. Influência por scores de UF e alavancagem exportada; células com maior influência parcial: RR jan2019 pré e TO jul2024 total. Não excluímos UFs ou células para alterar significância.

## Escala e cenários

β está em unidades logarítmicas, não pontos percentuais. Contraste 0→1 em D: δx=log2. Aumento persistente em nível D gera pulso em Δlog1p(D); pulso de um mês em D gera +log2 depois −log2. Cenários usam convolução e acumulam resposta em log(I), convertendo por 100[exp(resposta)−1], com IC pontuais transformados monotonamente. Um pulso de nível retorna a resposta acumulada a zero em h=7 sob o DLM finito, pois a diferença negativa compensa a positiva; não extrapolar isso como fato físico/causal. Uma mudança persistente D=0→1 corresponde a variação relativa estimada de I ao fim de seis meses ≈0,188% pré/0,303% total, sem rejeição central. Não é 0,188/0,303 pontos percentuais.

## Verificação e reprodução

HTML: JavaScript real verificado em Node/DOM mínimo em 84 combinações (21 exposições ×2 períodos ×2 covariâncias), com callback CSV e ausência de scripts externos. Revisão visual em Chromium não foi possível: o executável de navegador não está instalado no ambiente. Não foi declarada uma inspeção visual que não ocorreu.


FWL versus dummies: diferença máxima β<7e−17, covariância CR1<8e−21; DK contra statsmodels<3e−21; variância da soma igual à soma de todos elementos da covariância. Validações usam as duas aplicações centrais. Lags de todas aplicações passam teste de borda/UF e calendário completo; arquivo de verificação adiciona testes determinísticos por UF. Bandas são pontuais, não simultâneas.

Entradas não versionadas: `data/processed/df_tcc_2013_2024.csv` e `data/raw/atlas_desastres/atlas.csv`. Capítulo arquivado sem alteração em `tcc/capitulos/c3_metodologias_tg_referencia.tex`; correções são documentadas, não inseridas silenciosamente no texto original. Manifesto SHA256 em `outputs/tables/dlm_painel_log/manifest.json` com versões. Python e dependências em `requirements-dlm-painel-log.lock.txt`.

```bash
python -m pip install -r requirements-dlm-painel-log.lock.txt
python src/executar_notebook_painel_log.py notebooks/22_dlm_painel_diferencas_logaritmicas.ipynb
python src/verificar_dlm_painel_log.py
python src/relatorio_dlm_painel_log.py
```

Não afirmar causalidade. Exogeneidade estrita requer condição em todo histórico, não só origem natural. Não atribuir registros a mudança climática antropogênica. K6 limita horizonte; a interpretação não decide causalidade, ausência ou invariância temporal.
