"""Atualiza o índice público usando somente saídas da base com exclusões."""
from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'outputs/tables/modalidades_excluidas_20261104'

def main():
    manifest=json.loads((B/'manifesto.json').read_text(encoding='utf-8'))
    g=pd.read_csv(B/'granger/granger_aplicacoes.csv')
    d3=json.loads((B/'dlm3/resumo.json').read_text(encoding='utf-8'))
    sel=pd.read_csv(B/'dlm0/selecao_K.csv')
    tip=pd.read_csv(B/'dlm_aic_bic/dlm_selecao.csv')
    inf=pd.read_csv(B/'dlm0_inferencia/resultados.csv')
    tests0=inf[inf.covariancia.eq('DK_regra') & inf.p_Holm_familia.lt(.05)]
    rows=[]
    for lag in [0,3]:
        p=B/f'sarimax{lag}/resumo.json'
        if p.exists():
            s=json.loads(p.read_text(encoding='utf-8'))
            assert s['base_sha256']==manifest['base_sha256']
            assert s['resumo_linhas']==896
            assert s['geral_linhas']==56
            rows.append(f"| SARIMAX {lag}..K | {s['univariados_estimados']} de 896 individuais estimáveis; {s['delta_BIC_menor_zero']} com BIC menor e {s['RMSE_melhora']} com RMSE menor; {s['gerais_estimados']} gerais estimados |")
        else:
            rows.append(f'| SARIMAX {lag}..K | Reestimação em andamento; resultados da base anterior não são válidos para esta versão |')
    text=f'''# Mudanças climáticas e inadimplência

Trabalho de conclusão de curso de Isabella Viana Bambirra, Estatística/UFSCar.

## Base corrigida: exclusões antes da agregação

Os arquivos mensais do SCR são filtrados para pessoas físicas e excluem **financiamentos imobiliários**, **financiamentos de títulos e valores mobiliários** e **outros créditos** antes de somar a carteira ativa e a inadimplente por UF e mês. A taxa é 100 × carteira inadimplente / carteira ativa. As agregações regionais e nacionais usam os saldos, não a média das taxas de UFs.

Período: janeiro/2013 a dezembro/2024. Painel: 27 UFs × 144 meses = 3.888 observações. Recorte pré-pandemia: até janeiro/2020; os períodos se sobrepõem. O Atlas disponível contém 40.339 registros municipais, dos quais 37.643 integram o total climático por COBRADE 12/13/14. Registros administrativos não são fenômenos físicos independentes.

**Resultados vigentes:** [outputs/tables/modalidades_excluidas_20261104](outputs/tables/modalidades_excluidas_20261104). As demais pastas de resultados e os notebooks históricos usam versões anteriores; seus números não devem ser citados como resultados da base corrigida. A monografia LaTeX é entregue separadamente e não integra esta atualização.

## Resultados da execução corrigida

| Análise | Resultado |
| --- | --- |
| Granger | {int(g.status.eq('estimado').sum())} de 864 estimáveis; {int(g.rejeicao_nominal.sum())} rejeições nominais, {int(g.rejeicao_bh.sum())} após BH local; {int((g.rejeicao_bh & g.ljungbox_p.lt(.05)).sum())} dessas rejeições com autocorrelação residual |
| DLM 0..K | {int(sel.status.eq('selecionado').sum())} de 42 aplicações com seleção AIC estimável |
| DLM por tipologia, AIC/BIC | {int(tip[tip.criterio.eq('AIC')].status.eq('estimado').sum())} de 32 estimáveis por critério; os dois menores AICs são comparados separadamente |
| DLM 0..K, inferência ampliada | {len(tests0)} contrastes rejeitam após ajustes da grade e Holm por família em DK pela regra; nenhum do total climático central |
| DLM 3..K | {d3['estimaveis']} de 42 estimáveis; nenhuma rejeição após os ajustes nas três bandas DK |
{chr(10).join(rows)}

As evidências são exploratórias. Granger avalia precedência preditiva, sem identificar causalidade estrutural. O BH é por UF/período entre 16 tipologias, sem controle global das 864 aplicações nem correção formal pela seleção BIC. DLM e SARIMAX também possuem incerteza pós-seleção. Ausência de rejeição não prova ausência de associação.

## Notebooks

1. [Descritiva](notebooks/01_analise_descritiva.ipynb)
2. [Estacionariedade](notebooks/02_estacionariedade.ipynb)
3. [Granger](notebooks/03_granger_ufs_tipologias.ipynb)
4. [DLM](notebooks/04_dlm_painel_aic_bic.ipynb)
5. [SARIMA/SARIMAX](notebooks/05_sarima_sarimax_estadual_nacional.ipynb)

## Integridade e reprodução

O [manifesto](outputs/tables/modalidades_excluidas_20261104/manifesto.json) identifica o painel e as fontes. SHA256 do painel CSV: `{manifest['base_sha256']}`. Os 144 arquivos mensais possuem hashes em `fontes_scr_sha256.csv`. A agregação dos saldos nos extremos da amostra foi verificada por consulta independente; os 627 testes F de Granger e todas as famílias BH foram conferidos por uma segunda implementação.

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
python src/reestimar_com_exclusoes.py dlm0_inferencia
python src/reestimar_com_exclusoes.py dlm_aic_bic
python src/reestimar_com_exclusoes.py dlm_top2
python src/reestimar_com_exclusoes.py dlm3
python src/executar_reestimacao_sarimax.py
python src/gerar_sintese_base_corrigida.py
```

Para a auditoria COBRADE do DLM 0..K, disponibilize uma cópia do mesmo Atlas em `data/raw/atlas_desastres/atlas.csv` (essa cópia deve ser criada **depois** da etapa 02, que requer um único consolidado na pasta). A reestimação verifica o hash do painel no manifesto e utiliza pastas novas; checkpoints históricos não são reutilizados.

## Diferenças em relação aos resumos dos chats anteriores

Esta execução independente encontrou 40.339 registros do Atlas e 627 aplicações Granger estimáveis, em vez de 40.338 e 631 mencionados nos chats. O DLM 3..K apresentou 39 aplicações estimáveis, em vez de 40. As tabelas desta pasta e seus hashes documentam os números efetivamente reproduzidos. A contagem de 16 rejeições BH de Granger e de três casos com autocorrelação foi confirmada.
'''
    (ROOT/'README.md').write_text(text,encoding='utf-8')
    (ROOT/'docs/correcao_modalidades_20261104.md').write_text(text.replace('](outputs/','](../outputs/').replace('](notebooks/','](../notebooks/'),encoding='utf-8')
    print('Índice e síntese atualizados')

if __name__=='__main__':main()
