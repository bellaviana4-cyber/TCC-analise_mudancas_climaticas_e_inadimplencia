"""Exporta a síntese numérica sem sobrescrever a documentação do projeto.

O README é mantido como apresentação editorial do estudo. Este script calcula
contagens das tabelas e grava somente docs/resumo_execucao.md.
"""
from pathlib import Path
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'outputs/tables/modalidades_excluidas_20261104'
DESTINO = ROOT / 'docs/resumo_execucao.md'


def main():
    manifest = json.loads((B / 'manifesto.json').read_text(encoding='utf-8'))
    base = ROOT / 'data/processed/df_tcc_2013_2024.csv'
    assert hashlib.sha256(base.read_bytes()).hexdigest() == manifest['base_sha256'], 'Painel diferente do manifesto'

    g = pd.read_csv(B / 'granger/granger_aplicacoes.csv')
    sel = pd.read_csv(B / 'dlm0/selecao_K.csv')
    tip = pd.read_csv(B / 'dlm_aic_bic/dlm_selecao.csv')
    inf = pd.read_csv(B / 'dlm0_inferencia/resultados.csv')
    d3 = json.loads((B / 'dlm3/resumo.json').read_text(encoding='utf-8'))
    tests0 = inf[inf.covariancia.eq('DK_regra') & inf.p_Holm_familia.lt(.05)]
    bandas = '; '.join(f'{nome}: {total}' for nome, total in d3['rejeicoes_por_banda'].items())
    rows = [
        f"| Granger | {int(g.status.eq('estimado').sum())}/{len(g)} estimáveis; {int(g.rejeicao_nominal.sum())} rejeições nominais e {int(g.rejeicao_bh.sum())} após BH |",
        f"| Granger: diagnóstico residual | {int((g.rejeicao_bh & g.ljungbox_p.lt(.05)).sum())} aplicações com rejeição BH também rejeitaram no Ljung–Box |",
        f"| DLM ampliado, 0 a K | {int(sel.status.eq('selecionado').sum())}/{len(sel)} estimáveis; {len(tests0)} contrastes com rejeição após ajustes na banda de referência |",
        f"| DLM por tipologia | {int(tip[tip.criterio.eq('AIC')].status.eq('estimado').sum())}/32 estimáveis por AIC; {int(tip[tip.criterio.eq('BIC')].status.eq('estimado').sum())}/32 por BIC |",
        f"| DLM ampliado, 3 a K | {d3['estimaveis']}/{d3['n_aplicacoes']} estimáveis; rejeições ajustadas por banda: {bandas} |",
    ]
    for lag in [0, 3]:
        s = json.loads((B / f'sarimax{lag}/resumo.json').read_text(encoding='utf-8'))
        assert s['base_sha256'] == manifest['base_sha256']
        individual = pd.read_csv(B / f'sarimax{lag}/resumo.csv')
        general = pd.read_csv(B / f'sarimax{lag}/geral.csv')
        assert len(individual) == 896 and len(general) == 56
        both = int((individual.delta_BIC.lt(0) & individual.melhora_rmse_pct.gt(0)).sum())
        general_both = int((general.delta_BIC.lt(0) & general.melhora_rmse_pct.gt(0)).sum())
        rows.append(
            f"| SARIMAX individual, {lag} a K | {s['univariados_estimados']}/896 estimáveis; "
            f"{s['delta_BIC_menor_zero']} com BIC menor; {s['RMSE_melhora']} com RMSE menor; "
            f"{both} com ambos menores |"
        )
        rows.append(
            f"| SARIMAX geral, {lag} a K | {s['gerais_estimados']}/56 estimados; "
            f"{general_both} com BIC e RMSE menores |"
        )

    dimensions = (
        f"Painel: {manifest['linhas']:,} observações; {manifest['ufs']} UFs e {manifest['meses']} meses. "
        f"Registros do Atlas: {manifest['total_atlas']:,}.\n\n"
    ).replace(',', '.')
    text = (
        '# Resumo numérico da execução\n\n'
        'Esta página é gerada por [gerar_sintese_base_corrigida.py](../src/gerar_sintese_base_corrigida.py) '
        'a partir das tabelas publicadas. A interpretação está em [Resultados](resultados.md).\n\n'
        + dimensions + '| Análise | Resumo |\n| --- | --- |\n'
        + '\n'.join(rows)
        + '\n\nO BH de Granger é por UF e recorte. Os contrastes DLM usam os ajustes da grade e de família. '
        'No SARIMAX, a comparação é com o SARIMA da mesma unidade e recorte.\n\n'
        f"SHA-256 do painel: {chr(96)}{manifest['base_sha256']}{chr(96)}.\n\n"
        '[Índice das tabelas](../outputs/tables/modalidades_excluidas_20261104/README.md) · '
        '[Reprodução](reproducao.md)\n'
    )
    DESTINO.write_text(text, encoding='utf-8')
    print(f'Síntese numérica atualizada: {DESTINO.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
