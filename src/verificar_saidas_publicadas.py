"""Verifica checkpoints e inferência salva sem bases brutas nem reestimação.

Execute da raiz: python src/verificar_saidas_publicadas.py
Depende apenas de numpy e pandas. Não substitui os testes originais dos modelos.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
checks = []


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append(name)


def adjusted(values, method):
    """Implementação independente de BH, BY e Holm, incluindo reservas p=1."""
    p = np.asarray(values.fillna(1), dtype=float)
    order = np.argsort(p)
    ranked = p[order]
    n = len(p)
    if method == "holm":
        a = np.maximum.accumulate(ranked * np.arange(n, 0, -1))
    else:
        a = ranked * n / np.arange(1, n + 1)
        if method == "by":
            a *= np.sum(1 / np.arange(1, n + 1))
        a = np.minimum.accumulate(a[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.clip(a, 0, 1)
    return out


def family(path, n):
    d = pd.read_csv(path)
    check(f"Família fixa: {path.name}, {n}", len(d) == n and d['Família n'].eq(n).all())
    for col, method in [('p BH', 'bh'), ('p BY', 'by'), ('p Holm', 'holm')]:
        check(f"{path.parent.name}/{path.name}: {col}", np.allclose(d[col], adjusted(d.p, method), atol=1e-12))
    check(f"p válidos: {path.name}", d.p.dropna().between(0, 1).all())
    return d


old = pd.read_csv(ROOT / 'outputs/tables/ampliacao/granger_selecionados.csv')
old = old[old['Direção'] == 'Desastres → inadimplência'].drop_duplicates(
    ['Período', 'Chave', 'Especificação', 'Direção', 'Defasagem'])
nom = old[old.p < .05]
check('Referência histórica 235/29/0/18/4',
      [len(old), len(nom), int((old['p BH'] < .05).sum()),
       int((nom['Portmanteau p'] < .05).sum()), int(nom['Diagnóstico favorável'].sum())]
      == [235, 29, 0, 18, 4])

base = ROOT / 'outputs/tables/segunda_etapa'
national = pd.read_csv(base / 'nacional.csv')
for name, n in [('NACIONAL', 50), ('DETERMINISTICAS', 25)]:
    d = national[national['Família'] == name]
    check(name + ' dimensão e BH', len(d) == n and np.allclose(d['p BH'], adjusted(d.p, 'bh')))
for name, n in [('painel', 8), ('resposta', 16), ('previsao', 4), ('ty', 4)]:
    family(base / (name + '.csv'), n)

a = ROOT / 'outputs/tables/adequacao'
r = family(a / 'nacional.csv', 200)
p = family(a / 'painel.csv', 32)
for col in ['p clássico', 'p HC3']:
    check('BH sensibilidade ' + col, np.allclose(r['p BH ' + col], adjusted(r[col], 'bh')))
check('Nacional: 192 estimáveis, 44 nominais, 11 BH, 41 triagens',
      [r.p.notna().sum(), (r.p < .05).sum(), (r['p BH'] < .05).sum(),
       r['Diagnóstico favorável'].sum()] == [192, 44, 11, 41])
strong = r[(r['p BH'] < .05) & r['Diagnóstico favorável']]
check('Único BH + triagem: Onda de Frio sazonal total, q0 preferido',
      len(strong) == 1 and strong.iloc[0]['Exposição'] == 'Tipologia | Onda de Frio'
      and strong.iloc[0]['Transformação'] == 'Diferença sazonal'
      and strong.iloc[0]['Período'] == 'Total (2013–2024)' and strong.iloc[0]['q0 preferido'] == True)
check('Painel: 2 nominais, 0 BH, 0 triagens',
      [(p.p < .05).sum(), (p['p BH'] < .05).sum(), p['Diagnóstico favorável'].sum()] == [2, 0, 0])
check('Painel balanceado em 27 UFs', p['n efetivo'].eq(27 * p['Meses efetivos']).all())
criteria = pd.read_csv(a / 'criterios.csv')
check('Amostra comum entre candidatos', criteria.groupby(
    ['Período', 'Exposição', 'Transformação'])['n comum'].nunique().eq(1).all())
for name, d in [('nacional', r[r.p.notna()]), ('painel', p)]:
    check('Datas comuns entre transformações ' + name, all(d.groupby(
        ['Período', 'Exposição'])[c].nunique().eq(1).all() for c in ['Início amostra', 'Fim amostra']))
check('Triagem independente do p principal', r[r.p.notna()].apply(
    lambda x: x['Diagnóstico favorável'] == x['Motivos diagnósticos'].startswith('Sem indicação'), axis=1).all())
manifest = json.loads((a / 'checkpoint_14.json').read_text())
for name, sha in manifest['tabelas'].items():
    check('SHA256 tabela ' + name, hashlib.sha256((a / name).read_bytes()).hexdigest() == sha)
for key, path in [('codigo', ROOT / 'src/adequacao_series.py'),
                  ('protocolo', ROOT / 'docs/adequacao_protocolo.md')]:
    check('SHA256 ' + key, hashlib.sha256(path.read_bytes()).hexdigest() == manifest[key])
for i in range(5, 15):
    path = next((ROOT / 'notebooks').glob(f'{i:02}_*.ipynb'))
    notebook = json.loads(path.read_text())
    cells = [c for c in notebook['cells'] if c['cell_type'] == 'code']
    check('Execução salva sem erro ' + path.name, bool(cells) and all(
        c.get('execution_count') is not None and not any(
            o['output_type'] == 'error' for o in c.get('outputs', [])) for c in cells))
folds = pd.read_csv(base / 'previsoes_folds.csv')
check('Treino anterior ao alvo', (pd.to_datetime(folds['Treino fim']) < pd.to_datetime(folds['Data alvo'])).all())
check('Previsão: 72/13 alvos por indicador', set(folds.groupby(['Período', 'Exposição']).size()) == {72, 13})
print(f'{len(checks)} verificações passaram; sem reestimar modelos.')
for name in checks:
    print('OK: ' + name)
