# Checkpoint da validação final DLM

Base: branch analise/dlm-revisao-metodologica, remoto c64589abc0f886a4e55e73b32328f8b0206376aa; PR5 aberto contraanalise/dlm. PR4 aberto contra main027ee8a; discussões vazias. Gitfetch confirmou estado sem atualização posterior. Branch nova analise/dlm-validacao-final. Protocolo local c8e2ffc antes dos novos resultados, publicação posterior. Nenhum Granger/SARIMAX/merge.

## Preservação e execução
Os44hashes da revisão anterior foram verificados; nenhuma fonte/notebook16/17/tabela/figura antiga alterada. 46principais reconciliados; 92novas sensibilidades sazonais/DF;2modelos conjuntos com3agregados. Todas503linhas de multiverse têm metadados reconstruídos e coeficientes anteriores reconciliados. A correção não muda a especificação principal nem coeficientes históricos.

R4.3.3/clubSandwich0.5.10:140modelos reconciliados Python/R. Primeiro estágio da execução detectou falha em linear_contrast com chamada inverse_var=FALSE para pesos todos iguais1; casos afetados foram descartados e reprocessados com parametrização correta para pesos uniformes. P/df dos46acumulados principais conferidos contra revisão anterior. Não confundir essa falha corrigida com suporte insuficiente. Aliases de FE sazonais removidos antes dos contrastes; rank e coeficientes conferidos.

WCR11:278hipóteses rank-checadas,4999/9999sorteios,0singulares. Principais,placebos/interações e conjuntos das sensibilidades foram conferidos. Validação externa4escalares/interações com4999pesos idênticos (wildboottest0.3.2), diferenças estatísticas máximas<2e-11. Dois conjuntos com99refits independentes statsmodels/cov_cluster (<2e-12), limite do pacote escalar explicitado. Esses99não são a inferência substantiva, que usa4999/9999.

Inversão dos11acumulados centrais em grades determinísticas:9intervalos limitados na grade; Onda de Frio pré/total não se fecha mesmo ampliando36SE. low/high ausentes nesses casos, grade e resolução preservadas. Não apresentar extremidades da grade como IC finito.

Bootstrap principal/placebos/interações/novos conjuntos:0rejeiçõesBH. CR2principal/sazonalidade/semDF/conjuntoCOBRADE:0acumuladosBH. Inferência indisponível nos testesHTZ é reportada, não tratada como nulidade. Suporte da janela e contraste separado de exposiçãox0 e df.

Nacional:4centrais da revisão anterior reconciliados, HACcalendário conferido contra statsmodels em amostra contínua. J4/AR0/1/2/HAC6/18,leave-year e meses/janela selecionados por exposição, sem comprimir calendário. ARprincipais estáveis; resposta0–24 e ICdelta com covariância completa (AR/exposição/cruzadas). As4associaçõesBH/HAC anteriores não foram apagadas. Retirar2022 muda Onda de Frio para negativo; outras3mantêm sinal nas sensibilidades executadas, com variação de magnitude/precisão. Não promover pnominais das retiradas a nova descoberta.

## Validação
Notebook18:35células reais executadas em IPython,0erros. Mesmo executor documentado no notebook17; namespace compartilhado e outputs reais. 13novas verificações passaram, incluindo metadados, calendários inválidos, FE explícitos, suporte, covariâncias cruzadas na dinâmica, bootstrap externo, CR2 e singularidades. Testes anteriores/outputs preservados por hashes.

HTML novo:35tópicos, narrativas por filtros,perfis,forest/suporte,CR2,cenários e gráficos nacionais com comentários específicos. Playwright/Chromium:0errosJS,0requisições externas; filtros,textos nacionais,CSV,desktop/mobile verificados. HTML permanece foraGit. Limitações remanescentes são identificacionais/mensuração, não erros conhecidos invalidantes.

## Reprodução
Python3.12, versões em requirements-dlm-validacao-final.lock.txt; metadados e sessãoR nas tabelas. R/clubSandwich0.5.10 requerido para reprodução da inferência; plm2.6.3 foi usado nos CIPS preservados da revisão anterior. Em R, instalar versão arquivada com remotes::install_version('clubSandwich',version='0.5.10',upgrade='never') se necessário.

```
python -m pip install -r requirements-dlm-validacao-final.lock.txt
# Bases nos caminhos anteriores, não versionadas.
python src/dlm_validacao_final.py --reproduzir
python src/dlm_validacao_final.py --retomar
python src/executar_notebook_dlm_revisao.py notebooks/18_validacao_final_dlm.ipynb
```

Rscript no PATH ou DLM_R_EXEC apontando para executávelR. Não são necessários caminhos temporários específicos deste ambiente. --retomar confere hashes; --reproduzir reestima e recria próprias saídas, sem sobrescrever revisões anteriores. As tabelas de sensibilidades usam pnominal claramente separado de famíliasBH. Bandas robustas simultâneas não foram inventadas: CR2ponto-a-ponto e inversãoWCR; bandasCR1condicionais históricas ficam disponíveis como comparação.

## Limitações remanescentes
Poucas UFs informativas; CR2 pressupõe independência entreclusters; dependência transversal e spillovers podem permanecer; exposição administrativa não mede intensidade/população/área; duração física desconhecida; alterações no cadastro; curvas lineares/suavizadas e seleçãoJ/AR condicionais. Exclusões reduzem amostra e alteram população/perguntas. Sem equivalência arbitrária, potência observada ou atribuição climática causal.
