# DLM clássico com janela selecionada por exposição e período

Protocolo registrado em 05/10/2026 antes de estimar os novos resultados inferenciais.

## Seleção

Estimar separadamente as 24 exposições e os dois períodos originais. Preservar triagem prévia e categorias inelegíveis. Painel: comparar K=1,...,10 pelo BIC na amostra comum histórica de dezembro/2013 em diante; desempatar pelo menor K. AIC é comparação documentada, sem escolher pelo p-valor. Nacional: comparar conjuntamente K=1,...,10 e lags próprios p=0,1,2 pelo BIC na mesma amostra por categoria/período; desempatar por menor número de parâmetros, K e p. Exposição em cobertura municipal relativa; dependente ΔI. Somente coeficientes livres, sem spline. Nenhuma alteração do Granger.

Selecionar a janela significa incluir todos os lags 1,...,K, e não um único mês escolhido. Categorias distintas podem selecionar o mesmo K. Não se forçam escolhas diferentes. A janela selecionada não é duração física do desastre nem duração comprovada do efeito. O modelo sem exposição é comparador BIC, não uma exclusão por significância.

## Inferência e limitações

Recalcular CR2/Satterthwaite para os contrastes do painel selecionado, reconciliando uma implementação Python com resultados R/clubSandwich já versionados nos K10. Wild cluster bootstrap restrito por UF, 4.999 sorteios para acumulado e conjunto, com singularidades explicitadas. Não chamar o teste conjunto de bootstrap de HTZ. Nacional: HAC12 com correção de pequena amostra e distribuição t/F; lags próprios selecionados junto de K, estabilidade AR e Ljung–Box12 documentados. BH em 48 hipóteses planejadas separadamente por desenho, método e endpoint; indisponíveis entram como p=1 somente no denominador da família e continuam indisponíveis no resultado.

Os testes, intervalos e bootstrap são condicionais à especificação selecionada. Não incorporam a incerteza da seleção de K/p; BH não resolve essa incerteza. Tratar os novos sinais como exploratórios, nunca mais robustos só por p menor. Diagnósticos não servem para buscar nova especificação até obter rejeição; falhas permanecem visíveis.

## Preservação

Novas saídas em outputs/tables/dlm_selecionado, notebook 20 e código próprio. Notebooks 16–19 e tabelas históricas imutáveis. O HTML atualizado deve separar seleção atual, painel K10 anterior, nacional spline anterior e Granger preservado, sem misturar versões ou promover significância histórica como resultado atual. Não publicar bases brutas nem HTML no GitHub.

## Execução e resultados

Foram estimados 46 modelos por desenho (92 no total), com 460 candidatos no painel e 1.380 no nacional. Dois cenários por desenho continuam não estimáveis: Onda de Calor/Baixa Umidade e Rompimento/Colapso de Barragens no pré-pandemia. Painel: 45 escolhas K1; Alagamentos pré K6. Nacional: 42 escolhas K1; Outros total K5; Vendavais e Ciclones total K2 e pré K3; Tecnológico/antrópico total K8.

Nenhum acumulado ou teste conjunto do painel rejeita após BH48, com a inferência descrita acima. No nacional, os três acumulados BH/HAC são Meteorológico total (negativo), Vendavais e Ciclones total (negativo) e Outros total (positivo). Há seis rejeições conjuntas; não equivalem a seis aumentos acumulados. O comparador sem exposição tem BIC menor para Meteorológico e Vendavais total. Outros tem vantagem BIC pequena e inclui categorias não exclusivamente climáticas. Inundações e Onda de Frio do nacional spline anterior não permanecem após BH na especificação nacional atual.

469 verificações numéricas aprovadas, incluindo escolhas BIC em amostra comum, somas de coeficientes, covariâncias e cinco reconciliações CR2 com R. As quatro células do notebook 20 foram executadas sequencialmente no processo Python e suas saídas gravadas; o ambiente bloqueia sockets do kernel Jupyter. HTML validado offline em 48 combinações e dois desenhos, exportação CSV aprovada, zero erros JavaScript e zero requisições externas; capturas desktop e mobile inspecionadas.

Reprodução a partir da raiz do repositório, com as bases brutas nos caminhos históricos:

```bash
OPENBLAS_NUM_THREADS=1 python src/dlm_selecionado.py
python src/verificar_dlm_selecionado.py
python src/relatorio_dlm_selecionado.py --output /caminho/relatorio.html
python src/verificar_relatorio_dlm_selecionado.py /caminho/relatorio.html
```

Para preservar o HTML revisado anterior como histórico, fornecer `--historical /caminho/relatorio_anterior.html` ao gerador. Sem esse argumento, usa-se o relatório histórico reproduzível do gerador versionado. A execução nova não reestima Granger e não modifica resultados históricos.
