# Checkpoint — segunda etapa

Base: cee778561fbed9cb3157b47eca934618be1bcff8. Branch: analise/segunda-etapa-dinamica-exposicao.
Protocolo registrado: b667d451519711dc0fa2f48ad3d0138e360e86be.

## Etapa10 concluída

Notebook10 executado integralmente, tabelas e gráficos incorporados. Sem alterar05–09. Conferência histórica:235/29/0/18/4. ADL:21 séries ×2 períodos,2 exclusões pré por raridade; sensibilidade pandêmica21 séries total. Família nacional50 e determinísticas25 reservadas, ajuste ainda inclui exposições futuras com p=1; ajuste final será completado sem diminuir famílias. TY total nacional: k2+d_max1, Wald p0,428945, Portmanteau p0,129486; pré excluído por integração inconclusiva. ADL total nacional: p próprio1,q1,p HAC0,320593,BG1 p0,070149,BG12 p0,686805; RESET p0,014559 e q0 preferido impedem triagem favorável. Nenhum modelo histórico ADL passou todos os critérios de triagem; isso não significa que todos tenham o mesmo problema.

Próximo passo exato: executar11_exposicao_gravidade_segunda_etapa.ipynb, completar oito hipóteses de exposição reservadas, auditar cobertura e disponibilidade. Não recalcular05–09 nem ADL histórico já validado. Intermediários podem ser reconstruídos somente se ausentes; saídas existentes são checkpoints para leitura.

## Etapa11 concluída

CSV consolidado reutilizado após conferir SHA256, sem repetir auditoria de protocolos. Auditoria nova de deslocamento, habitações, monetários, sobreposições, extremos e atrasos. Notebook11 executado integralmente. Família nacional50 completada, família determinísticas25, TY4 preservadas. Valores monetários excluídos da inferência por mês-base não confirmado; não deflacionados novamente. Próximo: executar12_painel_uf_segunda_etapa.ipynb; preservar resultados nacionais e a auditoria já executados. Commit etapa10:7dc4bb8077b18e75c3be72e68f6b1510d63c2e45.

## Etapa12 concluída

Notebook12 executado, oito modelos de painel TWFE com27 UFs, lags próprios1,2,3,12 e exposição1,2,3. Nenhuma rejeição nominal DK nem após BH. Autocorrelação residual rejeitada no total em todos os quatro indicadores (p≈0,011–0,013). Pré: convergência ADF/KPSS em51,9% das UFs, abaixo do gate80%. SPJ, metades e remoção de cada UF apresentados como sensibilidades; nenhuma prova de causalidade. Etapa11 commit:8fa41dd152ea0b9e935be4e153c59d52bc82b140. Próximo: notebook13 resposta/previsão; não refazer10–12.

## Etapa13 concluída

Notebook13 executado:16 projeções locais,0 nominais/0BH; previsão expansiva com72/13 alvos por indicador, sem ganho observado no total. Etapa12 commit:c128108350d37511245899e8be2a7df933ae6b71. Próximo: gerar HTML externo offline, validar interface e hashes remotos, abrirPR e integrar após verificações. Análise10–13 não deve ser recalculada ao retomar se tabelas/checkpoints estiverem preservados.
