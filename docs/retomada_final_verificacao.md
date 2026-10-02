# Retomada e conclusão — 02/10/2026

## Estado recuperado

Os notebooks 10–13 já estavam integrados à main pelo PR #1, merge f1cc49e502883649e9a228ad1a9162b893e2aea3. A branch analise/adequacao-transformacoes continha apenas o protocolo prévio 1e598373ca0d9b2ec796a5d7b031be30da3fe188. Notebook 14, código, tabelas e documentação foram recuperados de entrega_adequacao_tcc.zip. Os hashes do código, protocolo e das oito tabelas conferem com checkpoint_14.json. Não houve nova estimação nem alteração dos notebooks 05–13 ou de suas tabelas.

## Verificações atuais

`python src/verificar_saidas_publicadas.py`: **65 verificações passaram**. O script verifica as saídas sem precisar das bases: referência histórica 235/29/0/18/4, BH/BY/Holm por implementação independente, famílias fixas, sensibilidades clássico/HC3, dimensão e balanceamento do painel, datas comuns, checkpoints, presença de execução sem erros nos notebooks 05–14 e treino anterior aos alvos de previsão. Isso verifica integridade e consistência das saídas; não substitui os diagnósticos dos modelos nem reproduz estimativas sem as entradas.

O resultado de Onda de Frio tem BH/HAC=0,039558 e triagem favorável, mas BY=0,232525, Holm=0,413384, BH clássico=0,451127 e BH HC3=0,535693. O BIC prefere q=0. Não pode ser apresentado como confirmação robusta ou efeito causal.

## Entradas nesta retomada

As bases originais e os dois Parquets intermediários não estavam no workspace nem no pacote recuperado. A ausência não bloqueou a conclusão porque os notebooks executados, código, tabelas, checkpoints e relatório estavam preservados. Não se afirma reexecução integral nesta sessão. Para reproduzir a estimação, disponibilizar exatamente os arquivos e hashes descritos no README e nos checkpoints. A auditoria das modalidades do SCR bruto permanece indisponível.

## Publicação e preservação

O push HTTPS do terminal falhou por ausência de credenciais; o conector GitHub autorizado foi utilizado. Commit analítico cdac499d43b1014284d1763ba83210c14fcb56a7. Uma transferência truncou estacionariedade_uf.csv; o erro foi detectado antes do merge e corrigido por 1e1846de61f0ffee5dd5c0708667b595b6cefb88, sem reescrever histórico. A árvore corrigida foi comparada à cópia local validada, incluindo o blob integral 76f8731e0f1051e54416381547ecb3f8800b0f78. Apenas novos arquivos da extensão e documentação foram incorporados. Nenhum force push, base bruta ou HTML final foi incluído.

O relatório HTML recuperado já tinha validação visual offline registrada em três larguras na sessão anterior. Nesta retomada, seus dados são conferidos contra as tabelas; a sintaxe e as funções de navegação/filtros são verificadas localmente. Não foi possível repetir o teste gráfico em Chromium: o download do navegador retornou arquivo inválido no ambiente atual. Essa limitação de verificação não altera os resultados estatísticos.

## Conclusão e próximo passo

As etapas autorizadas estão concluídas nos notebooks 10–14, com as exclusões metodológicas documentadas: monetários sem mês-base certificado, GMM não automático, sem bootstrap sob H0 pós-seleção ou simulação de poder para resgatar modelos inadequados, sem validação operacional com vintages. A evidência de precedência robusta continua inconclusiva. Próximo passo acadêmico: incorporar à monografia as estimativas e limitações; nenhum recálculo é necessário para consultar a entrega. Novas investigações exigem outro protocolo e entradas disponíveis, sem selecionar retrospectivamente o menor p.
