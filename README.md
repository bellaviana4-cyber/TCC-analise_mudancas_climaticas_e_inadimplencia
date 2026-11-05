# Mudanças climáticas e inadimplência

Trabalho de conclusão de curso de Isabella Viana Bambirra, Estatística/UFSCar.

## Base corrigida: exclusões antes da agregação

Os arquivos mensais do SCR são filtrados para pessoas físicas e excluem **financiamentos imobiliários**, **financiamentos de títulos e valores mobiliários** e **outros créditos** antes de somar a carteira ativa e a inadimplente por UF e mês. A taxa é 100 × carteira inadimplente / carteira ativa. As agregações regionais e nacionais usam os saldos, não a média das taxas de UFs.

Período: janeiro/2013 a dezembro/2024. Painel: 27 UFs × 144 meses = 3.888 observações. Recorte pré-pandemia: até janeiro/2020; os períodos se sobrepõem. O Atlas disponível contém 40.339 registros municipais, dos quais 37.643 integram o total climático por COBRADE 12/13/14. Registros administrativos não são fenômenos físicos independentes.

**Resultados vigentes:** [outputs/tables/modalidades_excluidas_20261104](outputs/tables/modalidades_excluidas_20261104). As demais pastas de resultados e os notebooks históricos usam versões anteriores; seus números não devem ser citados como resultados da base corrigida. A monografia LaTeX é entregue separadamente e não integra esta atualização.

## Resultados da execução corrigida

| Análise | Resultado |
| --- | --- |
| Granger | 627 de 864 estimáveis; 56 rejeições nominais, 16 após BH local; 3 dessas rejeições com autocorrelação residual |
| DLM 0..K | 39 de 42 aplicações com seleção AIC estimável |
| DLM 3..K | 39 de 42 estimáveis; nenhuma rejeição após os ajustes nas três bandas DK |
| SARIMAX 0..K | Reestimação em andamento; resultados da base anterior não são válidos para esta versão |
| SARIMAX 3..K | Reestimação em andamento; resultados da base anterior não são válidos para esta versão |

As evidências são exploratórias. Granger avalia precedência preditiva, sem identificar causalidade estrutural. O BH é por UF/período entre 16 tipologias, sem controle global das 864 aplicações nem correção formal pela seleção BIC. DLM e SARIMAX também possuem incerteza pós-seleção. Ausência de rejeição não prova ausência de associação.

## Notebooks

1. [Descritiva](notebooks/01_analise_descritiva.ipynb)
2. [Estacionariedade](notebooks/02_estacionariedade.ipynb)
3. [Granger](notebooks/03_granger_ufs_tipologias.ipynb)
4. [DLM](notebooks/04_dlm_painel_aic_bic.ipynb)
5. [SARIMA/SARIMAX](notebooks/05_sarima_sarimax_estadual_nacional.ipynb)

## Integridade e reprodução

O [manifesto](outputs/tables/modalidades_excluidas_20261104/manifesto.json) identifica o painel e as fontes. SHA256 do painel CSV: `d795e0ed176cc4628e1b02a81bc32ecab449f24aefc3e9be91d291479f46c043`. Os 144 arquivos mensais possuem hashes em `fontes_scr_sha256.csv`. A agregação dos saldos nos extremos da amostra foi verificada por consulta independente; os 627 testes F de Granger e todas as famílias BH foram conferidos por uma segunda implementação.

Instale `requirements-reestimacao-exclusoes.lock.txt`. Disponibilize os CSVs mensais do SCR em `data/raw/bacen` e o consolidado Atlas em `data/raw/atlas_desastres` ou defina `TCC_RAW_BACEN` e `TCC_RAW_ATLAS`. Os dados originais não são redistribuídos; o painel agregado corrigido está em `data/processed/df_tcc_2013_2024.csv`.

```text
python src/01_consolidar_scr.py
python src/02_preparar_atlas.py
python src/03_integrar_bases.py
python src/auditar_base_com_exclusoes.py
python src/reestimar_com_exclusoes.py granger
python src/reestimar_com_exclusoes.py estacionariedade
python src/verificar_granger_com_exclusoes.py
python src/reestimar_com_exclusoes.py dlm0
python src/reestimar_com_exclusoes.py dlm3
python src/executar_reestimacao_sarimax.py
python src/gerar_sintese_base_corrigida.py
```

Para a auditoria COBRADE do DLM 0..K, disponibilize uma cópia do mesmo Atlas em `data/raw/atlas_desastres/atlas.csv` (essa cópia deve ser criada **depois** da etapa 02, que requer um único consolidado na pasta). A reestimação verifica o hash do painel no manifesto e utiliza pastas novas; checkpoints históricos não são reutilizados.

## Diferenças em relação aos resumos dos chats anteriores

Esta execução independente encontrou 40.339 registros do Atlas e 627 aplicações Granger estimáveis, em vez de 40.338 e 631 mencionados nos chats. O DLM 3..K apresentou 39 aplicações estimáveis, em vez de 40. As tabelas desta pasta e seus hashes documentam os números efetivamente reproduzidos. A contagem de 16 rejeições BH de Granger e de três casos com autocorrelação foi confirmada.
