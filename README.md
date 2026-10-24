# Mudanças Climáticas e Inadimplência

Repositório do TCC **“Mudanças Climáticas e Inadimplência: uma análise do impacto de desastres naturais no sistema de crédito brasileiro”**.

## Análises estatísticas — notebooks principais

A execução das três metodologias está concentrada em **três notebooks autossuficientes**, organizados para leitura, reprodução e revisão. Cada notebook contém o código integral necessário à sua metodologia, decisões de modelagem, diagnóstico de dados, estimação, testes, tabelas, gráficos e interpretação. Não é necessário executar scripts externos de `src/` para recalcular os modelos.

| Ordem | Notebook principal | Conteúdo |
|---|---|---|
| 1 | [Causalidade de Granger](notebooks/01_granger_ufs_tipologias.ipynb) | 27 UFs × 2 períodos × 16 tipologias; BIC com 1–6 defasagens, F conjunto, BH, ADF/KPSS e resíduos/Ljung–Box |
| 2 | [DLM de painel — AIC × BIC](notebooks/02_dlm_painel_aic_bic.ipynb) | TWFE por MQO, grade K=1–24, seleção independente por AIC/BIC, testes FE/RE, DK, multiplicidade, perfis de coeficientes e curvas acumuladas |
| 3 | [SARIMA × SARIMAX estadual e nacional](notebooks/03_sarima_sarimax_estadual_nacional.ipynb) | Diagnóstico de posto, exógenas por tipologia, sazonalidade anual, busca de ordens por BIC via `statsmodels`, comparação independente e pareada, previsão fora da amostra e warnings |

> **Classificação:** utilizamos as 16 tipologias da base consolidada do Atlas, sem criar grupos de desastres. O painel cobre 2013–2024; os períodos pré-pandemia e completo se sobrepõem.

## Como executar

1. Clone o repositório e instale as dependências Python, preferencialmente em ambiente virtual:

   ```bash
   python -m pip install -r requirements-revisao-estadual.txt
   ```

2. Disponibilize a base consolidada `df_tcc_2013_2024.csv` em `data/processed/` (ou configure a variável de ambiente `TCC_BASE_CSV`). **Os dados brutos e processados não são versionados**; veja [`data/README.md`](data/README.md). O SHA-256 esperado da versão auditada é `46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36`.
3. Abra os notebooks pelo Jupyter ou VS Code **a partir da raiz do projeto**, na ordem acima. Execute cada um com **Run All**. As células de cálculo incluem verificações e salvam tabelas em `outputs/tables/`.
4. O notebook SARIMA/SARIMAX reestima os candidatos por padrão (`FORCAR_REESTIMACAO=True`), podendo levar alguns minutos. Se a execução for interrompida, ajuste para `False` para retomá-la a partir dos checkpoints por unidade e período. Evite executar notebooks simultaneamente sobre os mesmos arquivos de saída.

### Leitura dos resultados já executados

Os notebooks principais versionados contêm outputs de uma execução conferida sobre o painel com o SHA-256 acima. Isso inclui tabelas, gráficos e a avaliação dos diagnósticos. Para números completos e CSVs de auditoria, consulte [as tabelas estatísticas](outputs/tables/) e [a documentação técnica](docs/auditoria_metodologica_20261020.md).

| Verificação | Resultado da execução atual |
|---|---|
| Granger | 864 aplicações; 627 estimáveis; 14 rejeições com BH local, sendo duas com Ljung–Box rejeitado |
| DLM | 29 tipologia×período estimáveis; **K=1 em todos os casos pelo BIC**; oito escolhas AIC diferentes |
| SARIMA/SARIMAX | 53 comparações estaduais; em 16 o SARIMAX melhorou RMSE; nenhuma melhora BIC; série nacional com 16 exógenas e sem ganho de RMSE/BIC |

**Interpretação:** testes de Granger avaliam precedência preditiva; DLM estima associações condicionais às transformações e efeitos fixos; SARIMAX compara ajuste e previsão condicional. Nenhuma etapa, isoladamente, constitui identificação de efeitos causais.

### Complemento sobre defasagens — outubro de 2026

A análise de sensibilidade posterior à unificação dos notebooks está descrita na
[nota metodológica sobre as defasagens](docs/nota_defasagens_20261024.md) e no
[painel interativo de defasagens](outputs/reports/defasagens_metodos.html).

- **DLM:** conferência dos dois menores AICs em cada tipologia/período. Nos 29 casos estimáveis, todos os segundos valores têm ΔAIC inferior a 2, proximidade em parte decorrente do aninhamento dos candidatos. A inferência principal com DK por regra permanece sem rejeições após os ajustes também para o segundo K.
- **SARIMAX:** comparação de blocos climáticos `[0]`, `[0,1]` e `[0,1,3]` na mesma amostra e com as tipologias elegíveis simultaneamente. Em 53 casos estimáveis, o BIC escolheu `[0]`; nenhum SARIMAX superou o SARIMA pelo BIC, e 16 tiveram menor RMSE no teste.
- **Reprodução:** `python src/auditar_dlm_aic_top2.py`, `python src/inferencia_dlm_top2_aic.py`, `python src/sarimax_com_defasagens.py` e `python src/gerar_painel_defasagens.py`. A extensão usa o mesmo painel auditado e preserva os resultados históricos.

**Sensibilidade adicional de horizonte comum:** [nota do DLM K=6/K=12](docs/revisao_dlm_horizontes_fixos_20261024.md). A inclusão exploratória de K=0 mostrou AIC inferior em 18/29 combinações (17/21 escolhas K=1). Para não depender exclusivamente da busca por AIC, foram estimados DLMs irrestritos com K=12 fixo e K=6 como sensibilidade; a inferência DK por regra não rejeitou hipóteses após os ajustes em K=12 e rejeitou dois testes conjuntos de Movimento de Massa/Total em K=6. Para reproduzir: `python src/dlm_horizontes_predefinidos.py`. Essa extensão é exploratória, pois os horizontes foram propostos após a análise inicial.

## Organização e histórico

```text
notebooks/
  01_granger_ufs_tipologias.ipynb
  02_dlm_painel_aic_bic.ipynb
  03_sarima_sarimax_estadual_nacional.ipynb
  README.md
  historico/                  # versões exploratórias, preliminares e revisões anteriores
src/                          # implementações históricas e utilitários complementares
outputs/tables/               # resultados e diagnósticos exportados pelos notebooks
docs/                         # documentação técnica e relatórios de execução
```

Os notebooks antigos **não foram excluídos**: encontram-se em [`notebooks/historico/`](notebooks/historico/), preservados para rastreabilidade, mas não representam a sequência principal atual. O [README anterior](docs/readme_historico_20261020.md) também foi arquivado para preservar referências e decisões das etapas anteriores. O relatório [HTML integrado](outputs/reports/relatorio_integrado_interativo_20261020.html) reúne os resultados das três metodologias.

A definição final de quais resultados serão considerados principais na monografia e a atualização de seu texto serão feitas posteriormente, após a validação definitiva do código.
