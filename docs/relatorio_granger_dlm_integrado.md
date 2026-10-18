# Relatório integrado de Granger e DLM

Este documento registra a apresentação integrada solicitada pela autora em 05/10/2026. Não muda especificações, coeficientes, hipóteses, famílias de testes ou conclusões das análises executadas. Nenhum Granger, DLM ou SARIMAX foi reestimado para gerar o relatório.

## Fontes e escopo

- Granger final: notebook 15 e `outputs/tables/granger_fechamento/`. Inclui 42 cenários principais (21 exposições × 2 períodos) e 126 sensibilidades, mantendo os cenários inelegíveis.
- DLM principal atual: notebook 19 e `outputs/tables/dlm_classico/`. Coeficientes livres, ΔI, cobertura municipal relativa, UF+mês-ano FE, não ponderado, K10/lags1–10. Grade K1–9 apenas comparativa; desenhos com contemporâneo e ΔX no K10.
- Revisões preservadas: notebooks17–18 e `outputs/tables/dlm_validacao_final/`. Robustezes/placebos/interações/nacional são explicitamente identificados como resultados smooth anteriores, sem apresentá-los como novas verificações do DLM clássico.
- Contexto descritivo nacional: `outputs/tables/segunda_etapa/series_nacionais_agregadas.csv`. Taxa nacional é razão das somas das carteiras, nunca média simples das taxas.
- Cenários descritivos: `outputs/tables/relatorio_granger_dlm/escalas_exposicao.csv`, 48 linhas. Mediana e P90 entre coberturas positivas, máximo e número de células positivas, por exposição e período bruto. Derivados das exposições auditadas e recalculados diretamente do Atlas íntegro com concordância confirmada. São cenários de escala, não intensidade física nem efeito causal médio.

## Conteúdo e leitura

O HTML standalone contém filtros de período, nível (total/grupo/tipologia/agregado analítico), exposição, desenho clássico e K; abas Granger/DLM clássico/nacional anterior; coeficientes, curvas acumuladas, forest plot e contexto descritivo. Números e interpretações mudam com o filtro. Cada figura informa a pergunta, a escala, o método de inferência e as limitações; as tabelas ficam disponíveis como alternativa acessível ao gráfico.

Granger usa teste conjunto HAC12, BH42 principal e BH126 nas sensibilidades; global168/BY/Holm são identificados. DLM K10 usa CR2/Satterthwaite nos IC; comparações K<10 usam CR1S com rótulo distinto. Intervalos são ponto a ponto, não bandas simultâneas ou IC ajustados por BH. Bootstrap fornece p e erro Monte Carlo, sem intervalos inventados.

O texto separa significância nominal, após BH, falta de estimabilidade e indisponibilidade inferencial. Não interpreta não rejeição como ausência, não compara coeficientes de unidades distintas como equivalentes, não define duração pelo último lag significativo e não atribui causalidade antropogênica aos registros.

Resultados centrais explicitados: dez rejeições BH no Granger principal, com apenas Granizo total combinando BH e triagem ampliada (ainda sensível); zero acumulados BH/CR2 ou BH/bootstrap no DLM clássico principal; quatro acumulados e dez testes conjuntos BH/HAC no nacional anterior, com auditoria de influência/lead que limita a conclusão. O sinal histórico de Onda de Frio continua não robusto.

## Reprodução

Com as tabelas versionadas disponíveis, o gerador não exige bases brutas nem caches intermediários:

```bash
python src/relatorio_granger_dlm.py --output ../relatorio_granger_dlm_integrado.html
python src/verificar_relatorio_granger_dlm.py ../relatorio_granger_dlm_integrado.html --screenshots ../qa-relatorio-integrado
```

Use o ambiente científico fixado em `requirements-dlm-classico.lock.txt`. A validação visual automatizada usa adicionalmente `playwright==1.51.0`, com Chromium134/headless shell1161. Se necessário:

```bash
python -m pip install playwright==1.51.0
python -m playwright install chromium
```

A conferência opcional de cenários exige os arquivos locais íntegros autorizados, mas não reestima modelos nem grava tabelas antigas:

```bash
python src/relatorio_granger_dlm.py --verificar-escalas --output ../relatorio_granger_dlm_integrado.html
```

A verificação aplica SHA256 do Atlas do checkpoint, reconstrói municípios distintos por UF-mês e compara as 48 linhas. O SHA íntegro é `6ca29008a60a30e9f45d0f451da7750f850d8902704487798e1ef39ca3da44af`. O script usa as regras e denominadores já auditados em `src/dlm_revisao.py`, sem modificar o Atlas.

## Validação e limites

O teste compara o payload com todas as fontes atuais, verifica a identidade C(K)=soma β e os IC do último C com o contraste acumulado, percorre 48 combinações período/nível/exposição, dez horizontes e três desenhos. Testa abas, inelegibilidade, exportação CSV, ausência de erro JavaScript e ausência de requisição externa com o navegador offline. O HTML inclui fontes/hashes para download. Inspeção visual complementar de Granizo/Granger, Frio/DLM e Frio/nacional.

O gerador incorpora dados e recursos essenciais; links do GitHub são referências opcionais. A impressão conserva a seleção atual e a aba ativa; não exporta automaticamente todas as combinações dos filtros. Para consultar outra combinação, altere os filtros ou exporte CSV.

O relatório não amplia o escopo da inferência disponível: CR2/bootstrap nos K menores não foram adicionados; testes conjuntos CR2 indisponíveis permanecem indisponíveis; a análise nacional e robustezes aprofundadas são anteriores/smooth, claramente marcadas. Estacionariedade de todas as exposições não foi certificada. A validação do documento verifica integridade de apresentação, não substitui a auditoria metodológica já registrada.

## Publicação

Código gerador, verificador, cenários agregados e registro de validação podem integrar a branch `analise/dlm-classico-1a10`/PR7. O arquivo HTML final é entregue somente no chat, conforme instrução da autora. Nenhuma base bruta, captura temporária ou HTML entra no Git; nenhum merge autorizado/executado.
