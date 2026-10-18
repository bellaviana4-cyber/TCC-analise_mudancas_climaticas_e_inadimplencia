# Checkpoint DLM clássico

Execução concluída em 05/10/2026. Protocolo anterior à estimação: f5bd4e6. 552 modelos estimados, 138 matrizes reconciliadas Python/R para CR2, 92 testes wild bootstrap, zero sorteios singulares. 33 verificações passaram. Notebook 19: 16 células executadas com IPython compartilhado em processo, zero erros. O notebook inspeciona outputs reais do pipeline e reestima o exemplo principal; RUN_ANALYSIS=True permite reprodução integral.

Dados conferidos por SHA256 com o checkpoint final anterior; Atlas truncado recuperado antes da estimação. Todas 24 exposições reconciliadas ao Atlas completo por UF-mês. Arquivos antigos preservados. Uma figura da etapa05 já estava modificada na retomada e não integra esta publicação.

HTML standalone fora Git, testado offline no Chromium: filtros, interpretação, gráficos, download CSV e ausência de requisições externas essenciais. Documentação distingue nominal, BH, inferência indisponível e comparações K menores sem CR2/bootstrap novos. Granger/SARIMAX não executados; nenhum merge.

Reproduzir: instalar requirements-dlm-classico.lock.txt; R4.3.3 e clubSandwich0.5.10. Executar src/dlm_classico.py, src/verificar_dlm_classico.py e o notebook19. DLM_R_EXEC pode indicar um wrapper Rscript. Bases brutas e intermediários não publicados.
