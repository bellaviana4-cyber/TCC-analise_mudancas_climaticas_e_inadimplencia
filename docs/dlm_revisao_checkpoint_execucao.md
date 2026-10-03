# Checkpoint final da revisão DLM

Execução integral concluída em 03/10/2026. Branch: `analise/dlm-revisao-metodologica`, a partir do DLM `3c94482628b86d1789ee98f8d35f6820835a7219`. Main e PR #4 recuperados; discussão do PR vazia. Notebook 16, código, resultados antigos e Granger preservados.

## Origem e integridade

O protocolo foi registrado localmente **antes da estimação**, no commit `1641dfd`. O commit remoto correspondente é `4fdd7e08dc4fd532b1830bfe9d2da6b891b6c928`. A publicação ocorreu depois da execução; não se confunde o momento do registro local com a data do commit remoto. A implementação local `2d1ac02` corresponde ao remoto `56a23829dfc67d7fb8bec1777c19cffa8ddb9aec`.

CSV e parquet concordam. Painel de 3.888 UF-mês, 27 × 144. Atlas: 40.339 registros, 40.238 chaves municipais e 101 repetições. Reconciliação exata em cada UF-mês, não apenas em somas nacionais.

## Execução

- 24 exposições × 2 períodos; 46 estimadas. Calor/baixa umidade e barragens no pré não atingem suporte mínimo e permanecem na família planejada de 48.
- Spline J=3 em 45 modelos; J=4 em Alagamentos pré. K=12 para todos. Amostras principais: 3.564 no total (132 × 27) e 1.971 no pré (73 × 27). Placebos perdem três meses finais.
- WCR11: 4.999/9.999 draws, H0 imposta, reabsorção de FE. Categorias centrais recebem 9.999. Acumulado, defasado, conjuntos e interações calculados. Algoritmo conferido contra reestimação direta.
- R 4.3.3; clubSandwich 0.5.10; plm 2.6.3. Coeficientes conferidos Python/R em 120 modelos: 46 principais, 46 placebos, 24 interações e 4 rastreios históricos.
- CR2/Satterthwaite para contrastes. A aproximação HTZ de **17 dos 46 testes conjuntos principais** fica indisponível por suporte/df insuficientes. Não é um p observado igual a 1. `df_raw` conserva o diagnóstico da aproximação.
- BH global do painel: cluster 3 acumulados/15 conjuntos; DK 2/12; CR2 0/0; WCR 0/0. Isso não demonstra ausência de impacto.
- Nacional complementar: **4 acumulados diretos e 10 conjuntos após BH/HAC**. Acumulados: Inundações, calor/baixa umidade e frio no total; naturais não diretamente climáticos no pré. Não são confirmação do painel. Soma direta difere da resposta recursiva quando há lags próprios.
- CIPS de ΔI rejeita nos dois recortes; nível é sensível ao determinístico. P tabelado é limitado em 0,01/0,10. Testes de exposição ficam não calculáveis quando há UF com menos de três níveis: triagem conservadora do diagnóstico, não exclusão do modelo. Não confundir série binária com variância nula.
- Onda de Frio pré histórica A/K3: soma 0,047964 reproduzida; cluster p=0,000589; CR2 p=0,155921, df=1,345935; WCR p=0,3461. **Sinal anterior não robusto.**
- 56 leave-outs: 27 UFs individuais e as duas dominantes em cada período. O suporte remanescente está explícito; MS+SC não se torna especificação principal.
- Verificações: shifts, chave, reconciliação, spline/covariância, C(h), interação, pesos, BH, N_eff, FWL, WCR, leave-out, Python/R e razão nacional.

## Notebook e HTML

Notebook 17: **35 células de código executadas, zero erros**. O ambiente bloqueou sockets TCP/IPC do Jupyter. As células foram executadas de fato por IPython em processo isolado, com namespace compartilhado e outputs MIME reais. O executor está versionado. A primeira falha por intermediário vazio foi corrigida com gravação atômica e reprodução integral; não houve alteração de especificação para procurar resultados.

O HTML fica fora do Git. Navegação, filtros, gráficos, downloads e JavaScript são verificados em Chromium; imagens de QA são inspecionadas. A síntese distingue painel principal e associações nacionais complementares.

## Reprodução

```bash
python -m pip install -r requirements-dlm-revisao.txt
# R: install.packages(c("clubSandwich", "plm"))
# Bases locais, não versionadas:
# data/processed/df_tcc_2013_2024.csv
# data/processed/df_tcc_2013_2024.parquet (conferência adicional)
# data/raw/atlas_desastres/atlas.csv
python src/executar_dlm_revisao.py --reproduzir
python src/executar_dlm_revisao.py --retomar
# Todas as células, usando resultados hash-validados:
python src/executar_notebook_dlm_revisao.py notebooks/17_revisao_metodologica_dlm.ipynb
# Para reestimar dentro do notebook, definir DLM_REPRODUZIR=1 antes do comando.
```

Rscript precisa estar no PATH. Em ambiente isolado, `DLM_R_EXEC` pode apontar para o executável R. Configurar R_HOME/R_LIBS_SITE somente quando aplicável. Nenhum caminho temporário deste ambiente é obrigatório na máquina da usuária.

Hashes das entradas, código, protocolo, tabelas e versões Python estão em `outputs/tables/dlm_revisao/checkpoint.json`. A retomada falha explicitamente se houver divergência. Bootstrap e bandas condicionais não resolvem mensuração, confundimento ou concentração. Nenhum SARIMAX ou merge automático.
