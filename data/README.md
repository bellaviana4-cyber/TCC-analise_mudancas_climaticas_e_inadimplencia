# Dados do estudo

O estudo combina informações mensais de crédito a pessoas físicas e registros de desastres naturais, de janeiro de 2013 a dezembro de 2024. A unidade de observação é **UF–mês**. O painel é balanceado, com **27 UFs, 144 meses e 3.888 linhas**, sem duplicação dessa chave.

## Fontes

| Fonte | Informação utilizada |
| --- | --- |
| [SCR.data — Banco Central do Brasil](https://www.bcb.gov.br/estabilidadefinanceira/scrdata) | Saldos da carteira ativa e da carteira inadimplente por UF, mês, tipo de cliente e modalidade |
| [Atlas Digital de Desastres no Brasil](https://atlasdigital.mdr.gov.br/paginas/index.xhtml) | Data, UF, região, grupo e tipologia dos registros municipais de desastres |

A definição do indicador está na [metodologia do SCR.data](https://www.bcb.gov.br/content/estabilidadefinanceira/scr/scr.data/scr_data_metodologia.pdf). O saldo inadimplente considera operações com pelo menos uma parcela vencida há mais de 90 dias.

A extração do Atlas utilizada é `BD_Atlas_1991_2024_v1.0_2025.04.14_Consolidado.csv`, restrita no processamento a 2013–2024. Os [identificadores de integridade das fontes](../outputs/tables/modalidades_excluidas_20261104/manifesto.json) permitem distinguir essa extração de revisões posteriores das bases.

## Construção da taxa de inadimplência

1. Selecionam-se as operações de pessoas físicas (`cliente = PF`).
2. Padronizam-se os rótulos das modalidades quanto a acentuação, espaços e maiúsculas.
3. Excluem-se **financiamentos imobiliários**, **financiamentos de títulos e valores mobiliários** e **outros créditos**.
4. Somam-se, por UF e mês, a carteira ativa e a carteira inadimplente das operações mantidas.
5. Calcula-se `taxa_inadimplencia = 100 × carteira_inadimplencia_total / carteira_ativa_total`.

A mesma filtragem é aplicada aos dois saldos antes da agregação. Para regiões, Brasil e agregações anuais, calcula-se a razão entre as somas dos saldos correspondentes, multiplicada por 100.

## Registros de desastres

As contagens do Atlas são agregadas por UF e mês, com colunas para as 16 tipologias e os quatro grupos. Os dois conjuntos classificam os mesmos registros e não devem ser somados entre si. Na integração ao calendário, os meses sem registros na extração recebem contagem zero.

O período completo contém **40.339 registros municipais**. O **total climático**, empregado no exercício ampliado do DLM, considera os prefixos COBRADE **12 (hidrológico), 13 (meteorológico) e 14 (climatológico)**, totalizando **37.643 registros**. As contagens não medem diretamente intensidade, danos ou população atingida.

## Painel publicado

O arquivo [processed/df_tcc_2013_2024.csv](processed/df_tcc_2013_2024.csv) utiliza separador `;`.

| Variável ou conjunto | Descrição |
| --- | --- |
| `uf`, `regiao` | Identificação da UF e da região |
| `mes_ano`, `ano`, `mes` | Referências temporais |
| `carteira_ativa_total` | Saldo ativo das operações mantidas |
| `carteira_inadimplencia_total` | Saldo inadimplente das mesmas operações |
| `taxa_inadimplencia` | Razão entre os dois saldos, em percentual |
| `total_desastres` | Total de registros municipais na UF e no mês |
| `grupo_*` | Contagens segundo os grupos do Atlas |
| `tipo_*` | Contagens segundo as tipologias do Atlas |
| `qtd_registros`, `qtd_maus` | Contagens de linhas da fonte SCR agregadas no processamento; não representam número de contratos ou de pessoas |

O SHA-256 do painel é:

```text
d795e0ed176cc4628e1b02a81bc32ecab449f24aefc3e9be91d291479f46c043
```

O [manifesto](../outputs/tables/modalidades_excluidas_20261104/manifesto.json) registra filtro, cobertura e hashes. As [verificações da agregação](../outputs/tables/modalidades_excluidas_20261104/validacao_agregacao_independente.csv) conferem os saldos de janeiro de 2013 e dezembro de 2024 nas 27 UFs, reaplicando o recorte aos arquivos originais. As diferenças observadas são inferiores a um centavo.

## Arquivos para reconstrução

| Pasta | Conteúdo esperado |
| --- | --- |
| `raw/bacen/` | 144 arquivos `scrdata_YYYYMM.csv`, de janeiro de 2013 a dezembro de 2024 |
| `raw/atlas_desastres/` | O consolidado do Atlas utilizado na análise |
| `interim/` | Agregados intermediários produzidos pelos scripts |
| `processed/` | Painel integrado publicado |

Os CSVs do SCR devem conter `uf`, `cliente`, `modalidade`, `carteira_ativa` e `carteira_inadimplencia`. O Atlas deve conter `Sigla_UF`, `regiao`, `Data_Evento`, `descricao_tipologia` e `grupo_de_desastre`; a auditoria climática utiliza também `Cod_Cobrade`. Os leitores esperam separador `;`.

Os dados brutos e intermediários não são redistribuídos. O [guia de reprodução](../docs/reproducao.md) descreve a preparação das pastas e a exigência de um único consolidado durante a preparação do Atlas.
