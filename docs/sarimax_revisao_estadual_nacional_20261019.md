# Revisão SARIMA versus SARIMAX — TCC (19/10/2026)

## Objetivos e base

A análise principal compara SARIMA sazonal e SARIMAX sazonal em **27 UFs × 2 períodos**, com tipologias exógenas escolhidas **apenas por suporte e estimabilidade no treino**. A complementar compara SARIMA e SARIMAX na **série nacional**, com **as 16 tipologias simultaneamente**, após testar posto e condicionamento.

A fonte é a base consolidada mensal `df_tcc_2013_2024.csv`; SHA-256 **46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36**. 27 UFs × 144 meses = 3.888 linhas. Sem reauditoria dos registros individuais do Atlas. As 16 tipologias são preservadas como classificação operacional de desastres do estudo, sem subdivisão ou reclassificação.

## Verificação anterior à alteração (16 exógenas, UF por UF)

O sistema original usava 16 colunas `Δlog(1+D)` simultâneas em cada UF e período. O posto da matriz de treino foi **inferior a 16 nas 27 UFs pré-pandemia e em 26 das 27 UFs no período total**. Apenas **MG/Total** teve posto 16 no treino, embora MG, MS, RS, SC e SP tenham posto 16 na amostra total. Isso demonstra não identificação dos 16 coeficientes em 53 das 54 comparações de treinamento; a sazonalidade ARMA não cria variação onde uma exógena é constante nem resolve colinearidade exata.

**Não confundir:** um software pode retornar parâmetros em matriz singular por regularização numérica ou escolha arbitrária; esses parâmetros não seriam individualmente identificados por variação da amostra. Não se deve interpretar tais estimativas como 16 efeitos separados defensáveis.

## Modelo e procedimento comum

- Resposta estadual: `y_it = 100 Δlog(taxa_inadimplencia_it)` (143 valores no período completo). Resposta nacional: `100 Δlog(100 × Σ carteira_inadimplente / Σ carteira_ativa)`. **Não se usa média aritmética das taxas estaduais.**
- Exposição estadual: `x_it = Δlog(1 + registros_tipologia_it)`; exposição nacional: primeiro **somar os registros** de cada tipologia entre UFs, depois aplicar `Δlog(1 + soma)`. Nunca somar as séries log-diferenciadas estaduais.
- A sazonalidade anual é obrigatória no grid. Modelos candidatos no treino: ARMA `(0,0,0)`, `(1,0,0)`, `(0,0,1)` e `(1,0,1)` com sazonal `(1,0,0,12)`, mais `(1,0,0) × (0,0,1,12)`. `d=D=0` porque a transformação log-diferença já foi feita externamente.
- Seleção do modelo de referência: preferir candidatos convergidos sem rejeição de Ljung–Box 12 a 5%; minimizar BIC entre eles. Sem candidato que passe, utilizar menor BIC convergido com ressalva. A escolha é feita **apenas no treino** e a ordem é mantida igual no par SARIMA/SARIMAX.
- Período pré: treino fevereiro/2013–janeiro/2019, 72 observações; teste fevereiro/2019–janeiro/2020, 12. Período completo: treino fevereiro/2013–dezembro/2022, 119; teste janeiro/2023–dezembro/2024, 24.
- Previsões de **um passo à frente**, sem reestimar parâmetros no teste, atualizando o filtro com inadimplência passada efetivamente observada. As `x_t` de desastres são contemporâneas e conhecidas no teste: trata-se de **previsão condicional**, não previsão em tempo real anterior ao desastre.
- No SARIMAX, as colunas são padronizadas com médias/desvios calculados **somente no treino**, para favorecer a otimização. Coeficientes originais são reconstruídos dividindo pelo desvio do treino.
- Critérios de comparação: RMSE/MAE no teste; BIC no treino com a mesma ordem ARMA; LR conjunto (qui-quadrado com gl igual ao número de exógenas, **exploratório**, pois há seleção prévia); Ljung–Box; p individuais, BH por modelo e BH global na família estadual. O BIC penaliza naturalmente regressores adicionais.

## Análise principal — redução estadual pré-definida

Para cada UF/período, sobre a **amostra de treino exclusivamente**: (1) manter tipologias com **pelo menos três meses de ocorrência positiva**; (2) ordenar por número de meses com ocorrência e ordem original da taxonomia para desempate; (3) acrescentar sequencialmente apenas colunas não constantes e independentes; (4) descartar candidato que leve a número de condição > 1.000 após padronização; (5) limitar a no máximo **9 exógenas no pré** ou **12 no total**, por parcimônia. Esse limite adicional significa que nem toda variável estimável entra automaticamente: ele é declarado, não ocultado, e **não utiliza o p-valor nem o teste para seleção**.

São **53 de 54** comparações possíveis: DF pré ficou sem exógena que atingisse suporte mínimo. Dos 53 SARIMAX estaduais comparáveis, **14 tiveram RMSE menor** e **39 tiveram RMSE maior** do que o SARIMA sazonal pareado. **Nenhum dos 53 melhorou o BIC no treino.** A mediana de variação percentual de RMSE (SARIMAX versus SARIMA) foi de **+7,19%**: positiva significa pior desempenho do SARIMAX.

| Período | Comparáveis | SARIMAX melhor no RMSE | Mediana Δ RMSE (%) | SARIMAX melhor no BIC |
| --- | --- | --- | --- | --- |
| Pré | 26 | 7 | 6,15 | 0 |
| Total | 27 | 7 | 9,09 | 0 |

O Ljung–Box 12 não rejeitou a 5% em **41 dos 53 SARIMAX** estaduais comparáveis. Logo, os demais precisam de ressalva de especificação residual. Nenhuma das 53 hipóteses conjuntas de exógenas foi rejeitada após BH entre modelos. Duas associações individuais sobreviveram BH global (395 testes de coeficientes): **Enxurradas em Pernambuco, pré e total** (coeficientes positivos), mas seus modelos pioraram o BIC e o RMSE e os testes conjuntos não sobreviveram BH. Além disso, há seleção de modelo prévia e testes condicionais: não atribuir causalidade e não interpretar esses dois achados como robustez geral.

### Comparação de cada UF

Δ RMSE = 100 × (RMSE do SARIMAX / RMSE do SARIMA − 1). Valores **negativos** indicam melhora do SARIMAX.

| UF | Exógenas pré | Δ RMSE pré (%) | Exógenas total | Δ RMSE total (%) |
| --- | --- | --- | --- | --- |
| AC | 3 | -1,60 | 8 | -7,53 |
| AL | 2 | 8,52 | 8 | 19,66 |
| AM | 8 | 15,59 | 9 | -4,58 |
| AP | 3 | 8,17 | 6 | -8,36 |
| BA | 8 | 18,27 | 11 | 30,48 |
| CE | 9 | -1,46 | 10 | 26,46 |
| DF | 0 | — | 1 | -0,24 |
| ES | 9 | 14,43 | 12 | 17,54 |
| GO | 8 | 1,69 | 10 | 4,37 |
| MA | 5 | -3,38 | 6 | 41,75 |
| MG | 9 | 16,66 | 12 | 1,69 |
| MS | 9 | 47,07 | 12 | -2,53 |
| MT | 9 | 9,28 | 11 | 22,02 |
| PA | 9 | 47,53 | 11 | 39,85 |
| PB | 3 | 0,11 | 6 | 2,07 |
| PE | 5 | 2,65 | 10 | 34,83 |
| PI | 2 | -7,89 | 4 | 24,65 |
| PR | 9 | -6,83 | 10 | 9,09 |
| RJ | 9 | 16,64 | 11 | 6,15 |
| RN | 3 | 2,38 | 9 | 37,20 |
| RO | 4 | -2,72 | 6 | 1,95 |
| RR | 2 | 2,94 | 3 | 1,71 |
| RS | 9 | 17,44 | 12 | 28,21 |
| SC | 9 | 7,19 | 12 | 10,52 |
| SE | 2 | 5,10 | 9 | -6,30 |
| SP | 9 | 23,50 | 12 | 26,08 |
| TO | 3 | -4,70 | 4 | -2,08 |

## Análise complementar — Brasil (16 variáveis simultâneas)

A matriz de 16 exposições nacionais apresentou posto **16/16 no treino e na amostra completa** nos dois períodos, com números de condição do treino de **7,94** (pré) e **5,14** (total). As duas especificações SARIMAX com 16 exógenas e sazonalidade anual convergiram.

| Período | Exógenas | RMSE SARIMA | RMSE SARIMAX | Δ RMSE (%) | Δ BIC treino | p LR | p Ljung–Box |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pré | 16 | 1,67 | 2,15 | 29,01 | 57,21 | 0,80 | 0,00 |
| Total | 16 | 1,35 | 1,50 | 10,58 | 64,11 | 0,72 | 0,03 |

**No nacional, o SARIMAX piorou o RMSE em ambos os períodos** e teve BIC maior; os testes conjuntos não rejeitaram, e ambos os SARIMAX apresentaram autocorrelação residual pelo Ljung–Box a 5%. Portanto, as 16 exógenas são *identificáveis* nessa série, mas **não trouxeram ganho preditivo ou de parcimônia nas especificações estimadas**.

## Conclusão metodológica

A série nacional permite identificar as 16 tipologias juntas, mas, com as ordens sazonais testadas e estas amostras, não sustenta superioridade do SARIMAX. Por UF, a redução por suporte permite 53 análises pareadas; a inclusão de desastres só reduz RMSE em 14 casos e eleva o BIC em todos. Não rejeição de hipóteses não demonstra ausência de efeito econômico; modelos condicionais, multiplicidade, informação esparsa, classificação administrativa e diagnóstico residual impedem conclusões causais.

## Arquivos e reprodução

- Script único de estimação: `src/sarimax_revisao_final.py`.
- Gerador de relatório/notebooks: `src/gerar_relatorio_sarimax_revisao.py`.
- Notebooks: `32_sarimax_estadual_tipologias_estimaveis.ipynb` e `33_sarimax_nacional_16_tipologias.ipynb`.
- Tabelas: `outputs/tables/sarimax_revisao_20261019/` (auditoria, seleção, coeficientes, previsões agregadas, comparações, resumos).
- Relatório offline: `outputs/reports/relatorio_sarimax_revisao_20261019.html`.

Com a base já processada no caminho padrão (não versionada, por privacidade e volume), executar:

```bash
python src/sarimax_revisao_final.py nacional
python src/sarimax_revisao_final.py estadual
python src/gerar_relatorio_sarimax_revisao.py
```

Se a base estiver em outro caminho, usar `TCC_BASE_CSV` apontando ao arquivo com o SHA acima. Reexecutar primeiro o SARIMA/SARIMAX se a base mudar. A inferência após seleção de ordens e regressoras não foi formalmente ajustada; BH controla apenas a multiplicidade das famílias de testes identificadas.