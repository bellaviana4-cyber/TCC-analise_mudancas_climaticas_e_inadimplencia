# Mudanças Climáticas e Inadimplência

Repositório do TCC **“Mudanças Climáticas e Inadimplência: uma análise do impacto de desastres naturais no sistema de crédito brasileiro”**.

## Análises estatísticas — notebooks principais

A análise principal das três metodologias está organizada em **três notebooks**, com código, diagnósticos, tabelas e interpretação. As auditorias acrescentadas após a unificação — comparação dos dois menores AICs, inclusão de K=0 como verificação e SARIMAX com defasagens climáticas — possuem **scripts próprios em `src/`**, documentados e reproduzíveis; os notebooks apresentam suas sínteses. Para reproduzir também essas extensões, execute os scripts indicados abaixo.

| Ordem | Notebook principal | Conteúdo |
|---|---|---|
| 1 | [Causalidade de Granger](notebooks/01_granger_ufs_tipologias.ipynb) | 27 UFs × 2 períodos × 16 tipologias; BIC com 1–6 defasagens, F conjunto, BH, ADF/KPSS e resíduos/Ljung–Box |
| 2 | [DLM de painel — AIC principal, BIC comparativo](notebooks/02_dlm_painel_aic_bic.ipynb) | TWFE por MQO, grade K=1–24, cinco hipóteses, testes FE/RE, DK, multiplicidade, perfis de coeficientes e curvas acumuladas |
| 3 | [SARIMA × SARIMAX estadual e nacional](notebooks/03_sarima_sarimax_estadual_nacional.ipynb) | Diagnóstico de posto, exógenas por tipologia, sazonalidade anual, busca de ordens por BIC via `statsmodels`, comparação independente e pareada, previsão fora da amostra e warnings |

> **Classificação:** utilizamos as 16 tipologias da base consolidada do Atlas, sem criar grupos de desastres. O painel cobre 2013–2024; os períodos pré-pandemia e completo se sobrepõem.

## Como executar

1. Clone o repositório e instale as dependências Python, preferencialmente em ambiente virtual:

   ```bash
   python -m pip install -r requirements-revisao-estadual.txt
   ```

2. Disponibilize a base consolidada `df_tcc_2013_2024.csv` em `data/processed/` (ou configure a variável de ambiente `TCC_BASE_CSV`). **Os dados brutos e processados não são versionados**; veja [`data/README.md`](data/README.md). O SHA-256 esperado da versão auditada é `46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36`.
3. Abra os notebooks pelo Jupyter ou VS Code **a partir da raiz do projeto**, na ordem acima. Execute cada um com **Run All**. As células de cálculo incluem verificações e salvam tabelas em `outputs/tables/`.
4. O notebook SARIMA/SARIMAX reestima os candidatos da análise principal por padrão (`FORCAR_REESTIMACAO=True`). Se a execução for interrompida, ajuste para `False` para retomá-la a partir dos checkpoints. Evite executar notebooks simultaneamente sobre os mesmos arquivos de saída.
5. Para reproduzir **também** as extensões acrescentadas posteriormente, execute na raiz os scripts listados na seção seguinte. `src/sarimax_com_defasagens.py` mantém as unidades já registradas nos CSVs, permitindo retomar execuções interrompidas; não interpreta automaticamente arquivos existentes como uma nova reestimação integral.

### Leitura dos resultados já executados

Os notebooks principais versionados contêm outputs de uma execução conferida sobre o painel com o SHA-256 acima. Isso inclui tabelas, gráficos e a avaliação dos diagnósticos. Para números completos e CSVs de auditoria, consulte [as tabelas estatísticas](outputs/tables/) e [a documentação técnica](docs/auditoria_metodologica_20261020.md).

| Verificação | Resultado da execução atual |
|---|---|
| Granger | 864 aplicações; 627 estimáveis; 14 rejeições com BH local, sendo duas com Ljung–Box rejeitado |
| DLM | 29 tipologia×período estimáveis; o **AIC escolheu K=1 em 21/29**, e em oito casos escolheu K maior; DK por regra não apresentou rejeições após os ajustes na auditoria dos dois menores AICs |
| SARIMA/SARIMAX | 53 comparações estaduais; em 16 o SARIMAX melhorou RMSE; nenhuma melhora BIC; série nacional com 16 exógenas e sem ganho de RMSE/BIC |

**Interpretação:** testes de Granger avaliam precedência preditiva; DLM estima associações condicionais às transformações e efeitos fixos; SARIMAX compara ajuste e previsão condicional. Nenhuma etapa, isoladamente, constitui identificação de efeitos causais.

### Respostas à orientação e revisão de defasagens — outubro de 2026

O [roteiro completo da revisão de 26/10/2026](docs/roteiro_respostas_orientadora_20261026.md) reúne a construção do SARIMAX defasado, os dois menores AICs dos DLMs, a função do Driscoll–Kraay, o efeito das bandas nos erros-padrão, as escolhas metodológicas e os resultados auditados. **Os DLMs com horizontes fixados em 6 ou 12 meses foram retirados da análise corrente.**

Para navegar pelas notas de cada etapa e distinguir resultados atuais de materiais históricos, veja também o [índice da documentação](docs/README.md).

### Auditoria das 16 tipologias simultâneas — 26/10/2026

Foi realizada a tentativa de SARIMAX com **as 16 tipologias obrigatórias, sem exclusões por suporte ou teto numérico**, nos quatro blocos consecutivos. Das **216 matrizes estaduais** (27 UFs × 2 recortes × 4 blocos), somente **4 foram identificáveis**, todas de **Minas Gerais no período completo**. Nos outros casos, colunas sem variação e/ou dependência linear impossibilitaram estimar separadamente os coeficientes; não se atribuiu BIC, valor-p ou efeito nulo a modelos impossíveis de identificar.

Em MG/total, os quatro SARIMAX com 16 tipologias convergiram. O BIC escolheu o bloco apenas contemporâneo entre eles, mas **nenhum venceu o SARIMA pelo BIC**; o contemporâneo melhorou RMSE condicional em 4,57%, enquanto os blocos com atrasos pioraram fortemente. Os resultados não representam as outras 53 aplicações. A especificação final depende da discussão sobre subconjuntos estaduais, tipologias raras, agrupamentos e análise nacional.

**Protocolo e resultados:** [Auditoria do SARIMAX com 16 tipologias](docs/sarimax_16_tipologias_estimabilidade_20261026.md), [código reproduzível](src/sarimax_todas_tipologias_20261026.py) e [tabelas por UF/bloco](outputs/tables/sarimax_todas_tipologias_20261026/).

### Busca sistemática de defasagens climáticas no SARIMAX — 26/10/2026

A sensibilidade estadual mais recente foi reestimada usando **quatro blocos consecutivos e aninhados de 0 a 3 meses**: `[0]`, `[0,1]`, `[0,1,2]`, `[0,1,2,3]`. Para comparar os BICs na mesma amostra, mantivemos a ordem temporal SARIMA e as tipologias constantes entre os quatro candidatos; um limite amostral reduziu as tipologias elegíveis a no máximo **4 (pré)** e **6 (total)**, selecionadas por suporte, posto e condicionamento apenas no treino.

- **54** aplicações UF × período; **53** estimáveis, totalizando **212** ajustes climáticos convergidos.
- O **BIC selecionou `[0]` nos 53/53** modelos, e nenhum SARIMAX venceu o SARIMA pelo BIC.
- Em **19/53** testes o SARIMAX teve RMSE menor que SARIMA; a mediana geral de melhora foi **−2,34%**.
- O Ljung–Box sobre **inovações padronizadas com ajuste de graus de liberdade ARMA** rejeitou em **39/53** modelos; isso limita a interpretação de inferência e não deve ser confundido com o diagnóstico de resíduos brutos usado na revisão anterior.

**Reprodução:** `python src/sarimax_lags_sistematicos.py`. Veja o [protocolo, resultados, limitações e tabelas da revisão](docs/sarimax_busca_sistematica_lags_20261026.md), além dos CSVs em [`outputs/tables/sarimax_lags_sistematicos_20261026/`](outputs/tables/sarimax_lags_sistematicos_20261026/). As análises anteriores continuam preservadas para comparação histórica. A busca é sistemática **dentro dessa grade curta** — não escolhe lags por tipologia nem prova ótimo global.

### Complemento anterior sobre defasagens — 24/10/2026

A análise de sensibilidade posterior à unificação dos notebooks está descrita na
[nota metodológica sobre as defasagens](docs/nota_defasagens_20261024.md) e no
[painel interativo de defasagens](outputs/reports/defasagens_metodos.html).

- **DLM:** conferência dos dois menores AICs em cada tipologia/período. Nos 29 casos estimáveis, todos os segundos valores têm ΔAIC inferior a 2, proximidade em parte decorrente do aninhamento dos candidatos. A inferência principal com DK por regra permanece sem rejeições após os ajustes também para o segundo K.
- **SARIMAX:** comparação de blocos climáticos `[0]`, `[0,1]` e `[0,1,3]` na mesma amostra e com as tipologias elegíveis simultaneamente. Em 53 casos estimáveis, o BIC escolheu `[0]`; nenhum SARIMAX superou o SARIMA pelo BIC, e 16 tiveram menor RMSE no teste.
- **Reprodução:** `python src/auditar_dlm_aic_top2.py`, `python src/inferencia_dlm_top2_aic.py`, `python src/sarimax_com_defasagens.py` e `python src/gerar_painel_defasagens.py`. A extensão usa o mesmo painel auditado e preserva os resultados históricos.

**Auditoria adicional do AIC (K=0):** a grade principal começa em K=1, mas o modelo apenas contemporâneo teria AIC menor em 18/29 combinações, incluindo 17/21 escolhas originais de K=1. Esse resultado alerta para a influência do limite inferior na seleção, sem alterar automaticamente os DLMs. Consulte [a revisão de defasagens](docs/nota_defasagens_20261024.md) e execute `python src/auditar_dlm_k0.py` para reproduzir.

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
