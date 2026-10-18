# Desastres e inadimplência: associações e precedência preditiva

Este repositório contém códigos, análises e materiais do TCC sobre desastres e inadimplência no crédito brasileiro. O escopo empírico atual distingue associação defasada (DLM), precedência preditiva condicional (Granger) e causalidade não identificada. Não atribui os registros do Atlas às mudanças climáticas.

## Objetivo

O trabalho investiga associações entre registros de desastres e a inadimplência de pessoas físicas no sistema de crédito brasileiro em **2013 a 2024**, bem como informação preditiva dos registros passados. Os modelos não identificam efeitos causais estruturais.

Para isso, são combinadas informações sobre crédito e inadimplência provenientes do **Sistema de Informações de Crédito do Banco Central do Brasil (SCR/BACEN)** com dados de ocorrências de desastres naturais disponibilizados pelo **Atlas Digital de Desastres no Brasil**.

A análise atual usa dois DLMs clássicos e preserva os testes Granger anteriores. Categorias administrativas, hidrometeorológicas, geológicas, biológicas e tecnológicas são distinguidas por código COBRADE; nem todo registro é exclusivamente climático.

## Dados

O trabalho utiliza duas principais fontes de dados:

### Sistema de Informações de Crédito — SCR/BACEN

Dados do Sistema de Informações de Crédito do Banco Central do Brasil utilizados para construção dos indicadores relacionados ao mercado de crédito e à inadimplência de pessoas físicas.

### Atlas Digital de Desastres no Brasil

Dados municipais de ocorrências de desastres naturais, contendo informações como tipo de desastre, localização e período de ocorrência.

O período analisado compreende os anos de **2013 a 2024**.

Os arquivos brutos não são armazenados neste repositório devido ao volume dos dados. As bases devem ser inseridas localmente nos diretórios indicados na seção de estrutura do projeto.

## Metodologia

A análise empírica utiliza métodos de séries temporais para investigar a relação entre desastres naturais e inadimplência.

As principais técnicas consideradas são:

* **Teste de Granger**, utilizado para avaliar informação preditiva condicional dos registros anteriores, sem demonstração de causalidade estrutural ou validação fora da amostra;

* **Modelos de Defasagens Distribuídas (Distributed Lag Models)**, utilizados para estimar associações defasadas condicionais, com coeficientes livres nos dois desenhos atuais;

* **Painel UF × mês com efeitos fixos**, para estimar associações entre cobertura municipal de registros e variação mensal da inadimplência;

* **Projeções locais, Toda–Yamamoto e previsão temporal**, como análises complementares, conforme os critérios de viabilidade documentados. SARIMAX não foi estimado nesta segunda etapa.

Também são realizados procedimentos de diagnóstico e tratamento das séries temporais, incluindo testes de estacionariedade e análise da estrutura de autocorrelação.

## Estrutura do repositório

```text
.
├── data/
│   ├── raw/
│   │   ├── bacen/
│   │   └── atlas_desastres/
│   ├── interim/
│   └── processed/
│
├── notebooks/
├── src/
│
├── outputs/
│   ├── figures/
│   └── tables/
│
├── docs/
│
└── tcc/
    ├── capitulos/
    ├── figuras/
    └── bibliografia/
```

### `data/raw`

Contém os arquivos originais obtidos diretamente das fontes de dados.

Os arquivos armazenados neste diretório não devem ser alterados manualmente.

### `data/interim`

Contém bases intermediárias resultantes das etapas de limpeza, padronização, agregação e transformação dos dados.

### `data/processed`

Contém as bases finais utilizadas nas análises estatísticas e nos modelos.

### `notebooks`

Contém os notebooks responsáveis pelas análises exploratórias, procedimentos estatísticos e estimação dos modelos.

Os notebooks são organizados de forma sequencial de acordo com as etapas da análise.

### `src`

Contém os scripts responsáveis pelas etapas de preparação, transformação e integração das bases de dados, além de funções e rotinas reutilizáveis ao longo do projeto.

### `outputs`

Contém os principais resultados produzidos pelas análises:

* `figures/`: gráficos utilizados nas análises e na monografia;
* `tables/`: tabelas e resultados estatísticos.

### `docs`

Contém documentação complementar do projeto, como dicionário de variáveis, decisões metodológicas e descrição do processamento das bases.

### `tcc`

Contém os arquivos relacionados ao texto final da monografia, incluindo capítulos, figuras e referências bibliográficas.

## Fluxo de processamento

O projeto segue, de forma geral, o seguinte fluxo:

```text
Dados brutos
    │
    ├── SCR / BACEN
    │
    └── Atlas Digital de Desastres
    │
    ▼
Limpeza e padronização
    │
    ▼
Construção das bases intermediárias
    │
    ▼
Integração das fontes
    │
    ▼
Base final de análise
    │
    ├── Análise descritiva
    ├── Testes de estacionariedade
    ├── Causalidade de Granger
    ├── Modelos de defasagens distribuídas
    └── Painel, resposta temporal e previsão
```

## Reprodutibilidade

Os dados brutos e bases processadas de grande volume não são versionados pelo Git.

Para reproduzir as análises, os arquivos das fontes originais devem ser armazenados localmente nas seguintes pastas:

```text
data/raw/bacen/
data/raw/atlas_desastres/
```

As etapas de processamento foram estruturadas de forma que as bases utilizadas nas análises possam ser reconstruídas a partir dos dados originais por meio dos scripts disponíveis em `src/`.

## Status

Projeto em desenvolvimento. A entrega atual é a extensão 21, documentada no fim deste arquivo. Etapas anteriores abaixo são históricas e não substituem a inferência atual. O HTML final contém somente os DLMs clássicos atuais, o Granger preservado e uma comparação identificada com o clássico anterior.


## Ampliação: grupos e tipologias (2013–2024 e pré-pandemia)

A ampliação mantém os notebooks 05 e 06 e acrescenta:

- `notebooks/07_estacionariedade_grupos_tipologias.ipynb`: auditoria do Atlas/Parquet, reconciliação e estacionariedade por recorte;
- `notebooks/08_granger_grupos.ipynb`: execução conjunta das famílias de testes e interpretação de grupos/referência;
- `notebooks/09_granger_tipologias.ipynb`: resultados e interpretações por tipologia;
- `outputs/tables/ampliacao/`: resultados completos, incluindo não significativos;
- `docs/ampliacao_metodologia.md`: decisões, hipóteses, limitações e reprodução.

A unidade validada é protocolo municipal: 40.339 registros únicos em 2013–2024, com reconciliação integral ao Parquet. São 4 grupos e 16 tipologias. Pré-pandemia termina em **janeiro de 2020**, inclusive (85 meses).

Nesta execução, 29 das 235 hipóteses únicas na direção desastres → inadimplência têm significância nominal, mas nenhuma permanece após Benjamini–Hochberg. A estacionariedade da inadimplência transformada é inconclusiva no pré-pandemia; a inferência desse recorte é exploratória. Consulte os notebooks para as limitações e os resultados inversos. Não se trata de prova de ausência de efeitos causais.

Após instalar as dependências e disponibilizar localmente as duas bases:

```powershell
python -m pip install -r requirements.txt -r requirements-ampliacao.txt
python src/executar_notebooks_categorias.py
```

O HTML standalone é entregue separadamente, fora do GitHub. Seu gerador está em `src/relatorio_categorias.py`; o template textual é código-fonte, sem dados embutidos. Para gerar uma cópia fora do repositório:

```powershell
python src/relatorio_categorias.py --output ..\relatorio_grupos_tipologias_tcc.html
```

Os notebooks incluem os gráficos; a execução também produz PNGs locais em `outputs/figures/ampliacao/`. Não são versionadas as bases brutas nem as séries intermediárias.


## Segunda etapa: dinâmica, exposição e localização geográfica

Extensão informada pela análise anterior; protocolo registrado **antes dos novos testes**, commit `b667d451519711dc0fa2f48ad3d0138e360e86be`. Não é confirmação independente e não busca significância por alterações dos recortes.

| Notebook executado | Conteúdo |
|---|---|
| `10_dinamica_nacional_segunda_etapa.ipynb` | ADL com ordens próprias/cruzadas diferentes, amostra comum BIC, sazonalidade, quebras, diagnósticos e TY condicionado à viabilidade |
| `11_exposicao_gravidade_segunda_etapa.ipynb` | Auditoria de frequência, municípios, deslocamento e habitações; foco COBRADE12/13/14; modelos e BH da família nacional completa |
| `12_painel_uf_segunda_etapa.ipynb` | UF×mês, TWFE dinâmico, DK, sensibilidade SPJ e influência das UFs |
| `13_resposta_previsao_segunda_etapa.ipynb` | Projeções locais1/3/6/12 meses; previsão expansiva sem divisão aleatória; IC e limitações de disponibilidade |

**Conclusão:** nenhuma rejeição ajustada com todos os diagnósticos favoráveis. Vendavais/Ciclones tem rejeiçõesHAC apósBH, porém q0 é preferido e há limitações de RESET/estacionariedade; testes clássicos/HC3 não confirmam evidência ajustada. As quatro medidas climáticas, o painel e as projeções locais não dão confirmação robusta. Acrescentar desastres não melhora o RMSE nas72 previsões do período total. Pré-pandemia tem13 alvos: descrição, sem inferência qualificada. Ausência de evidência robusta não prova ausência de impactos.

Documentação: [protocolo](docs/segunda_etapa_protocolo.md), [resultados e interpretação](docs/segunda_etapa_resultados.md), [fontes](docs/segunda_etapa_fontes.md), [progresso/checkpoints](docs/segunda_etapa_progresso.md). Tabelas completas em `outputs/tables/segunda_etapa/`, com famílias fixas, p originais/ajustados, coeficientes/IC, amostras, diagnósticos e exclusões. Os notebooks05–09 e seus resultados ajustados permanecem preservados. O ajuste do10 era provisório com reservas p=1; o11 contém a família nacional final50, sem reduzir hipóteses.

### Reprodução

As entradas continuam locais e ignoradas peloGit:

- `data/processed/df_tcc_2013_2024.parquet` — SHA256 `49991105866dc140e959bfd9200b780c76edae0b8c95c31040bcdbde7811afe5`.
- `data/raw/atlas_desastres/BD_Atlas_1991_2024_v1.0_2025.04.14_Consolidado.csv` — SHA256 `6ca29008a60a30e9f45d0f451da7750f850d8902704487798e1ef39ca3da44af`.

```powershell
python -m pip install -r requirements-segunda-etapa.txt
# Reestimar a segunda etapa integralmente, preservando05–09:
python src/executar_segunda_etapa.py --recalcular
# Verificar saídas publicadas, sem bases locais nem reestimação:
python src/verificar_saidas_publicadas.py
# Verificação original com os intermediários disponíveis:
# python src/verificar_segunda_etapa.py
# O HTML final e seu gerador são entregues separadamente no chat.
```

O executor usa processosPython novos e captura tabelas/Markdown/PNG sem depender de socketsJupyter. `--recalcular` é um alias de `--reproduzir` e preserva um backup local antes de reexecutar; para retomar trabalho validado, leia tabelas/checkpoints antes de executar novamente. Checkpoints registram hashes de entradas, código, protocolo e tabelas; etapas futuras só podem reutilizá-los após conferir diferenças de código/entradas. Não certificar equivalência de código modificado por mera presença deCSV.

Limitações centrais: p-valores condicionais à seleçãoBIC; dados administrativos e zeros de significado incompleto; nenhuma unicidade de pessoas/imóveis; monetários excluídos por mês-base não confirmado; SCRbruto não disponível; sem vintagesAtlas; confundimento econômico deUF não eliminado; dependência e viés dinâmico do painel. BootstrapH0 e simulação de poder não foram usados para resgatar modelos reprovados. HTML final e bases brutas não são publicados.


## Extensão 14: transformações e adequação

O notebook executado `notebooks/14_adequacao_transformacoes.ipynb` compara primeiras diferenças, variações relativas e suas versões com diferença sazonal. Utiliza datas comuns e famílias fixas de **200 hipóteses nacionais e 32 de painel**, sem escolher transformações pelo menor p-valor. [Protocolo prévio](docs/adequacao_protocolo.md), [resultados completos](docs/adequacao_resultados.md) e [verificação da retomada](docs/retomada_final_verificacao.md).

**Conclusão atual:** 41 cenários nacionais têm triagem diagnóstica favorável, todos no período total e nas versões sazonais. Há 44 rejeições nominais e 11 após BH/HAC; apenas Onda de Frio sazonal combina BH com triagem favorável (p=0,002176; BH=0,039558). Esse sinal é exploratório: BIC prefere q=0, BH clássico/HC3 e BY/Holm não confirmam significância. Os demais resultados ajustados têm limitações diagnósticas. No painel: 2 nominais, nenhuma após BH, autocorrelação persistente. As melhorias não estabelecem precedência robusta geral ou causalidade estrutural.

As análises 05–13 e seus ajustes foram preservados. A reprodução da extensão requer `data/processed/segunda_series_completas.parquet` e `segunda_painel.parquet`, produzidos pela etapa 11. Seus hashes estão em `outputs/tables/adequacao/checkpoint_14.json`. Esses intermediários e as bases brutas não são publicados.

```powershell
python -m pip install -r requirements-segunda-etapa.txt
# Apenas conferir as saídas entregues (sem reestimar):
python src/verificar_saidas_publicadas.py
# Reexecutar 14 somente com os intermediários e hashes conferidos:
python src/executar_notebooks_categorias.py notebooks/14_adequacao_transformacoes.ipynb
```

O HTML final permanece externo ao GitHub. Na retomada de 02/10/2026, foram recuperados e conferidos os resultados executados, sem recalcular análises anteriores. Ausência de evidência robusta não demonstra ausência de impactos econômicos dos desastres.


## Encerramento 15: mapa completo de Granger

[Notebook 15 executado](notebooks/15_fechamento_granger_grupos_tipologias.ipynb), [protocolo](docs/granger_fechamento_protocolo.md), [resultados e limitações](docs/granger_fechamento_resultados.md) e [matriz dos 42 cenários](outputs/tables/granger_fechamento/matriz42.csv).

Total nacional, quatro grupos e 16 tipologias nos recortes jan/2013–jan/2020 (85 meses) e jan/2013–dez/2024 (144 meses). Principal sazonal com ordens fixas; três sensibilidades finitas, famílias BH/BY/Holm de 42 e 126 hipóteses e sensibilidade global de 168. Ajustes históricos preservados. Amostras efetivas comuns: 60 e 119 meses.

**Conclusão:** há dez rejeições BH na principal (cinco por período); nove têm limitações na triagem. Granizo no período total combina BH e triagem ampliada favorável na referência HAC, mas perde a rejeição nas inferências clássica/HC3 e no BIC. É um sinal exploratório sensível à especificação. Onda de Frio também não fornece confirmação robusta. A estacionariedade da inadimplência pré-pandemia permanece inconclusiva. Dois cenários pré são inelegíveis por escassez, preservados na matriz e na família. Podemos encerrar Granger com essas limitações documentadas; nenhum método seguinte foi executado.

```powershell
python -m pip install -r requirements-granger-fechamento.txt
# Reutilizar resultados após conferir entradas, código, protocolo e tabelas:
python src/executar_granger_fechamento.py --retomar
# Conferir saídas sem reestimar (não certifica pressupostos):
python src/verificar_granger_fechamento.py --somente-saidas
# Reprodução integral apenas da etapa 15, com agregados publicados:
python src/executar_granger_fechamento.py --reproduzir
# Etapas antigas: conferir sem recálculo; exige bases/hashes compatíveis:
python src/executar_segunda_etapa.py --retomar
# Reproduzir 10–13 exige bases originais; preserva backup local:
python src/executar_segunda_etapa.py --reproduzir
```

A etapa 15 usa agregados com hash validado, sem publicar bases brutas. A ausência das bases impede recuperar códigos numéricos originais do Atlas e reconstruir integralmente 10–13; os nomes e contagens foram preservados. A retomada distingue verificação de arquivos, reprodução e diagnósticos estatísticos. Checkpoints históricos divergentes ou entradas ausentes interrompem a retomada sem recálculo silencioso. O HTML final é entregue fora do repositório.

## Revisão metodológica 17 — DLM

[Notebook 17](notebooks/17_revisao_metodologica_dlm.ipynb), [protocolo pré-estimação](docs/dlm_revisao_protocolo.md), [resultados e discussão](docs/dlm_revisao_resultados.md) e [checkpoint de execução](docs/dlm_revisao_checkpoint_execucao.md).

Revisão em painel UF × mês com cobertura municipal relativa, smooth DLM de horizonte comum 12 meses, curvas incrementais/acumuladas, CR2/Satterthwaite, wild cluster restricted bootstrap e DK. Resultados do notebook 16 preservados. O sinal positivo pré-pandemia de Onda de Frio não é robusto à inferência ampliada, mesmo mantendo a especificação histórica. Nenhuma rejeição principal do painel permanece após BH com CR2/WCR. A análise nacional complementar tem quatro acumulados diretos e dez perfis conjuntos após BH/HAC; seus estimandos e limitações são diferentes dos do painel.

```bash
python -m pip install -r requirements-dlm-revisao.txt
# Instalar R e, no R: install.packages(c("clubSandwich", "plm"))
python src/executar_dlm_revisao.py --reproduzir
python src/executar_dlm_revisao.py --retomar
python src/executar_notebook_dlm_revisao.py notebooks/17_revisao_metodologica_dlm.ipynb
```

O executor IPython evita sockets em ambientes restritos e executa células reais, preservando seus outputs. As bases locais devem estar nos caminhos documentados no checkpoint. Granger não foi reestimado; SARIMAX não foi executado. HTML standalone entregue separadamente, fora do Git. O PR da revisão tem como base `analise/dlm`; não há merge automático.


## Validação final dos DLMs

Notebook18 preserva a implementação e saídas dos notebooks16/17. Corrige metadados, avalia suporte da matriz/contrastes, sazonalidade estadual, DF, agregados conjuntos e influência nacional; valida bootstrap externamente. Consulte `docs/dlm_validacao_final_protocolo.md`, `docs/dlm_validacao_final_resultados.md` e `docs/dlm_validacao_final_checkpoint.md`. Saídas: `outputs/tables/dlm_validacao_final/` e `outputs/figures/dlm_validacao_final/`. Reprodução: `python src/dlm_validacao_final.py --reproduzir`, com bases locais e R/clubSandwich0.5.10. O HTML é entregue separadamente e não é versionado. Granger/SARIMAX não foram reexecutados.

## Entrega atual 21: seleção, dependência, regimes e classificação

[Protocolo](docs/dlm_ajustes5_protocolo.md), [resultados e interpretações](docs/dlm_ajustes5_resultados.md) e [notebook executado](notebooks/21_dlm_inferencia_selecao_regimes.ipynb). Extensão exploratória na mesma base; regras registradas antes dos novos ajustes, sem confirmação independente. DLMs clássicos, sem spline. BIC em amostra comum; proteção simultânea conservadora Bonferroni para a grade K/AR, seguida de BY principal entre categorias sobrepostas e BH comparativo.

Painel: 46 modelos, inferência DK12 principal, DK6/18 sensibilidades; 138 covariâncias brutas conferidas independentemente. Auditoria de 351 pares de UFs por modelo evidencia dependência residual; bootstrap anterior por UF não a resolve automaticamente. Nacional: 69 ajustes com Selic, IPCA e crescimento IBC-Br defasados, fontes oficiais mensais SGS4390/433/24364. Total principal com regimes até fev/2020, mar/2020–dez/2021 e jan/2022–dez/2024; K/AR selecionados conjuntamente, histórico de lags contínuo. Pré mantém até jan/2020. Nacional comum total é comparação pré-definida.

**Resultado atual:** nenhuma soma acumulada passa busca+BY/BH no principal. Vendavais/Ciclones mantém dois testes conjuntos nacionais após busca+BY (pré K3/AR0 e total/regimes K1/AR1), sem demonstrar aumento acumulado. Nenhuma igualdade específica da exposição entre regimes é rejeitada após a proteção e BY; isso não demonstra igualdade. Tecnológico/antrópico tem conjunto significativo somente no comparador comum total e não é exclusivamente climático. Doenças Infecciosas total/regimes não tem posto completo; Calor/Baixa Umidade e Barragens pré mantêm raridade. Fase de 22 meses limita a calibração HAC; covariância robusta não corrige confundimento.

Auditoria por códigos preserva nomes originais do Atlas e explicita agregações/divergências; grupos administrativos não equivalem a clima exclusivo. Granger preserva dez rejeições BH42 com ressalvas. Título e conclusões distinguem associação, precedência preditiva e causalidade não identificada.

```bash
python src/dlm_ajustes5.py
python src/verificar_dlm_ajustes5.py
python src/relatorio_dlm_ajustes5.py
python src/verificar_relatorio_dlm_ajustes5.py
```

Saídas em `outputs/tables/dlm_ajustes5/`, incluindo snapshots oficiais públicos dos controles, hashes, diagnósticos, candidatos inelegíveis e famílias planejadas. 898 verificações numéricas; HTML offline conferido em 312 cenários, sem erros JavaScript nem requisições externas, exportação e mobile aprovados. Notebook executado em processo Python/IPython com saídas gravadas. Entradas privadas locais exigidas pelo pipeline: `data/processed/df_tcc_2013_2024.csv` e `data/raw/atlas_desastres/atlas.csv`, hashes auditados. HTML final fora do Git; todos os pontos de entrada integrados geram a revisão atual. O gerador anterior expõe `build_baseline` somente para consulta histórica.
