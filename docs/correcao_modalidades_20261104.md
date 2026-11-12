# Construção e validação do painel de crédito

A versão final utiliza operações de pessoas físicas após excluir financiamentos imobiliários, financiamentos de títulos e valores mobiliários e outros créditos. A seleção é aplicada nos arquivos mensais originais do SCR antes da agregação por UF e mês.

## Critério de construção

A padronização dos rótulos precede a filtragem. Os saldos ativos e inadimplentes são somados sobre as mesmas operações mantidas. A taxa é calculada como 100 vezes a razão entre esses saldos. Os procedimentos estão em [01_consolidar_scr.py](../src/01_consolidar_scr.py) e [03_integrar_bases.py](../src/03_integrar_bases.py).

A exclusão de modalidades altera os saldos de crédito e a taxa de inadimplência. Ela não altera, por si, a quantidade de registros do Atlas.

## Verificações publicadas

- Cobertura completa de janeiro de 2013 a dezembro de 2024 nas 27 UFs.
- 3.888 observações e nenhuma duplicação da chave UF–mês.
- Recálculo da taxa a partir dos dois saldos em todo o painel.
- Reaplicação dos filtros aos arquivos originais de janeiro de 2013 e dezembro de 2024, comparando os saldos das 27 UFs com os do painel. As diferenças são inferiores a um centavo.
- Registro dos hashes dos 144 arquivos mensais do SCR e da extração do Atlas.
- Verificação independente dos testes F estimáveis de Granger e das famílias BH.
- Verificações da seleção dos horizontes, das amostras e das métricas SARIMAX.

O [manifesto](../outputs/tables/modalidades_excluidas_20261104/manifesto.json) identifica os dados. As [tabelas de validação](../outputs/tables/modalidades_excluidas_20261104/README.md) permitem conferir as etapas.

## Identificação da versão

O painel tem SHA-256 `d795e0ed176cc4628e1b02a81bc32ecab449f24aefc3e9be91d291479f46c043`.

A pasta `modalidades_excluidas_20261104` identifica a execução que incorporou esse recorte e reúne as tabelas da versão final. O nome é mantido para preservar os vínculos entre códigos, manifestos e saídas. As versões anteriores permanecem no [histórico](historico.md).

Consulte [Dados](../data/README.md), [Metodologia](metodologia_e_sensibilidades.md), [Resultados](resultados.md) e [Reprodução](reproducao.md).
