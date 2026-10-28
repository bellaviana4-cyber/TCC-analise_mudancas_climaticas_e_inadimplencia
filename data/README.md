# Dados

A análise utiliza dados mensais do Sistema de Informações de Crédito (SCR/Banco Central do Brasil) e do Atlas Digital de Desastres do Brasil. Os dados brutos, intermediários e a base processada não estão publicados neste repositório.

Fontes institucionais: [SCR.data — Banco Central do Brasil](https://www.bcb.gov.br/estabilidadefinanceira/scrdata) ([metodologia do indicador](https://www.bcb.gov.br/content/estabilidadefinanceira/scr/scr.data/scr_data_metodologia.pdf)) e [Atlas Digital de Desastres no Brasil](https://atlasdigital.mdr.gov.br/paginas/index.xhtml). Para reproduzir os resultados, deve-se usar a mesma edição das bases e as transformações descritas no código.

## Organização esperada

| Pasta | Conteúdo |
| --- | --- |
| `raw/bacen/` | 144 arquivos mensais `scrdata_YYYYMM.csv` (janeiro/2013 a dezembro/2024) |
| `raw/atlas_desastres/` | Um CSV consolidado do Atlas, com a identificação da UF, data do evento, grupo e tipologia |
| `interim/` | Tabelas agregadas por UF e mês |
| `processed/` | Base final `df_tcc_2013_2024.csv` |

A preparação usa apenas pessoas físicas nos dados do SCR e calcula a taxa de inadimplência como a razão entre saldo inadimplente e carteira ativa, multiplicada por 100. Os registros do Atlas são somados por UF, mês, grupo e tipologia. Meses sem desastre recebem contagem zero após a integração.

## Reconstituir a base

Após obter os arquivos originais nas fontes institucionais, mantê-los nas pastas acima e executar na raiz:

```bash
python src/01_consolidar_scr.py
python src/02_preparar_atlas.py
python src/03_integrar_bases.py
```

Os scripts esperam arquivos SCR separados por `;`, com as colunas `uf`, `cliente`, `carteira_ativa` e `carteira_inadimplencia`. O CSV do Atlas deve conter `Sigla_UF`, `regiao`, `Data_Evento`, `descricao_tipologia` e `grupo_de_desastre`, também separado por `;`. Mudanças nos arquivos de origem, regras de classificação ou revisões das bases podem produzir resultados diferentes.

A base auditada tinha **3.888 linhas (27 UFs × 144 meses)** e o SHA-256:

```text
46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36
```

Os scripts de modelagem atuais conferem esse hash antes de reestimar. Se a base reconstruída tiver hash diferente, a execução será interrompida; nesse caso é preciso reconciliar as fontes e as transformações, e não desativar a validação. Para consultar os resultados já obtidos, use os CSVs publicados em `outputs/tables/`.

Os dados brutos são mantidos fora do controle de versão. Não é necessário incluí-los num repositório público para consultar o código, os notebooks ou os resultados exportados.
