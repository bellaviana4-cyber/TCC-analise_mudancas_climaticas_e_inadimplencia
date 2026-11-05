"""Confere cobertura, reconciliação de saldos e agregação independente nos extremos."""
from pathlib import Path
import hashlib
import json
import os
import importlib.util
import pandas as pd
import numpy as np
import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW = Path(os.environ.get('TCC_RAW_BACEN', ROOT/'data/raw/bacen'))
OUT = ROOT / 'outputs/tables/modalidades_excluidas_20261104'
EXCLUDED = ['Financiamentos imobiliários', 'Financiamentos de títulos e valores mobiliários', 'Outros créditos']


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base = ROOT / 'data/processed/df_tcc_2013_2024.csv'
    d = pd.read_csv(base, sep=';')
    dates = pd.period_range('2013-01', '2024-12', freq='M').astype(str)
    assert len(d) == 3888 and d.uf.nunique() == 27
    assert not d.duplicated(['uf', 'mes_ano']).any()
    for uf, g in d.groupby('uf'):
        assert sorted(g.mes_ano) == list(dates), uf
    assert (d.carteira_ativa_total > 0).all()
    assert (d.carteira_inadimplencia_total > 0).all()
    assert np.allclose(d.taxa_inadimplencia, 100*d.carteira_inadimplencia_total/d.carteira_ativa_total)
    spec = importlib.util.spec_from_file_location('scr', ROOT/'src/01_consolidar_scr.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    files = mod.listar_arquivos()
    mod.validar_cobertura(files)
    # Consulta independente: exclusão pelos rótulos exatos da fonte e saldos DECIMAL.
    con = duckdb.connect()
    checks = []
    for period, p in (files[0], files[-1]):
        query = """SELECT uf,
        sum(cast(replace(replace(carteira_ativa,'.',''),',','.') as decimal(30,2))) ca,
        sum(cast(replace(replace(carteira_inadimplencia,'.',''),',','.') as decimal(30,2))) ci
        FROM read_csv(?, delim=';', all_varchar=true)
        WHERE cliente='PF' AND modalidade NOT IN (?, ?, ?) GROUP BY uf ORDER BY uf"""
        q = con.execute(query, [str(p), *EXCLUDED]).df()
        target = d[d.mes_ano.eq(str(period))].sort_values('uf')
        assert list(q.uf) == list(target.uf)
        for src, dest in [('ca', 'carteira_ativa_total'), ('ci', 'carteira_inadimplencia_total')]:
            err = float(np.abs(q[src].to_numpy(float) - target[dest].to_numpy(float)).max())
            assert err < .02, (period, src, err)
            checks.append(dict(mes=str(period), campo=dest, diferenca_maxima_reais=err))
        labels = con.execute("SELECT distinct modalidade FROM read_csv(?, delim=';', all_varchar=true) WHERE cliente='PF'", [str(p)]).df()
        assert set(EXCLUDED) <= set(labels.modalidade)
    pd.DataFrame(checks).to_csv(OUT/'validacao_agregacao_independente.csv', index=False)
    sources=[]
    for period, p in files:
        sources.append(dict(mes=str(period), arquivo=p.name, bytes=p.stat().st_size, sha256=sha(p)))
    pd.DataFrame(sources).to_csv(OUT/'fontes_scr_sha256.csv', index=False)
    atlas = Path(os.environ.get('TCC_RAW_ATLAS', ROOT/'data/raw/atlas_desastres')) / 'BD_Atlas_1991_2024_v1.0_2025.04.14_Consolidado.csv'
    manifest = dict(periodo=['2013-01','2024-12'], linhas=3888, ufs=27, meses=144,
                    base_sha256=sha(base), atlas_sha256=sha(atlas), modalidades_excluidas=EXCLUDED,
                    filtro='PF; exclusão por modalidade antes de somar ambos os saldos por UF-mês',
                    total_atlas=int(d.total_desastres.sum()), validacao_extremos=checks)
    (OUT/'manifesto.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
