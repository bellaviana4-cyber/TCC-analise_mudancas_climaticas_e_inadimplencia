"""Reestima as especificações existentes sobre o painel PF com três exclusões.

Resultados históricos permanecem nas pastas originais. Cada nova saída fica
associada ao SHA256 do painel, impedindo reutilização de checkpoints de outra base.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import time
import platform
import importlib.metadata

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/processed/df_tcc_2013_2024.csv'
RESULT = ROOT / 'outputs/tables/modalidades_excluidas_20261104'


def conferir_proveniencia_checkpoints(folder, digest):
    files=['analise_estadual.py','sarimax_revisao_final.py',
           'sarimax_por_tipologia_k0_24_20261026.py','sarimax_com_defasagens.py',
           'sarimax_todas_tipologias_20261026.py']
    signature=dict(base_sha256=digest,python=platform.python_version(),
                   versoes={n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','statsmodels']},
                   codigo_sha256_lf={n:hashlib.sha256((ROOT/'src'/n).read_text(encoding='utf-8').encode('utf-8')).hexdigest() for n in files})
    marker=folder/'proveniencia_checkpoints.json'
    if marker.exists():
        assert json.loads(marker.read_text(encoding='utf-8'))==signature, 'Base, código ou ambiente mudou; não reutilize checkpoints desta versão. Preserve a pasta anterior e inicie uma pasta nova.'
    else:
        assert not any((folder/'unidades').rglob('*.csv')), 'Checkpoints sem proveniência: não reutilizar automaticamente.'
        folder.mkdir(parents=True,exist_ok=True)
        temporary=folder/f'.proveniencia_{os.getpid()}.tmp'
        temporary.write_text(json.dumps(signature,ensure_ascii=False,indent=2),encoding='utf-8')
        os.replace(temporary,marker)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('etapa', choices=['granger', 'estacionariedade', 'dlm0', 'dlm0_inferencia', 'dlm_aic_bic', 'dlm_top2', 'dlm3', 'comparar_sarimax', 'sarimax'])
    ap.add_argument('--lag', type=int, choices=[0, 3], default=0)
    ap.add_argument('--fase', choices=['individuais', 'gerais', 'consolidar'], default='individuais')
    ap.add_argument('--uf', default='todas')
    ap.add_argument('--periodo', default='ambos')
    args = ap.parse_args()
    manifest = json.loads((RESULT / 'manifesto.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256(BASE.read_bytes()).hexdigest()
    assert digest == manifest['base_sha256'], 'Painel diferente do manifesto da consolidação'
    assert len(manifest['modalidades_excluidas']) == 3
    os.environ['TCC_BASE_CSV'] = str(BASE)
    os.environ['TCC_OUTPUT_DIR'] = str(RESULT / 'granger')
    import analise_estadual as ae
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        if args.etapa == 'granger':
            ae.granger(ae.load())
        elif args.etapa == 'estacionariedade':
            import estacionariedade_estadual as e
            e.main()
        elif args.etapa == 'dlm0':
            import dlm_painel_log_aic as d
            d.OUT = RESULT / 'dlm0'
            d.FIG = ROOT / 'outputs/figures/modalidades_excluidas_20261104/dlm0'
            d.run()
            p = d.OUT / 'manifest.json'
            metadata = json.loads(p.read_text(encoding='utf-8'))
            metadata['data_especificacao_original'] = metadata.pop('data', None)
            metadata['data_reestimacao'] = '2026-11-04'
            metadata['wrapper_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            p.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
        elif args.etapa == 'dlm0_inferencia':
            import dlm_painel_log_aic as d
            import dlm_inferencia_banda_regra_v3 as v
            d.OUT = RESULT / 'dlm0'
            v.OUT = RESULT / 'dlm0_inferencia'
            v.run()
            p = v.OUT / 'manifest.json'
            metadata = json.loads(p.read_text(encoding='utf-8'))
            metadata['data_reestimacao'] = '2026-11-04'
            metadata['base_sha256'] = digest
            metadata['auditoria_banda_adicional'] = None
            metadata['nota_auditoria_banda'] = 'Calibrações históricas não foram reexecutadas nesta correção; a banda permanece fixada por regra.'
            p.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
        elif args.etapa == 'dlm_aic_bic':
            ae.OUT = RESULT / 'dlm_aic_bic'
            ae.OUT.mkdir(parents=True, exist_ok=True)
            ae.dlm(ae.load())
        elif args.etapa == 'dlm_top2':
            import auditar_dlm_aic_top2 as a
            import inferencia_dlm_top2_aic as v
            a.SOURCE = RESULT / 'dlm_aic_bic/dlm_candidatos.csv'
            a.OUT = RESULT / 'dlm_top2'
            a.REPORT = ROOT / 'outputs/reports/modalidades_excluidas_20261104/dlm_top2.html'
            a.run()
            v.OUT = a.OUT
            v.CANDIDATOS_ORIGINAIS = a.SOURCE
            v.run()
        elif args.etapa == 'dlm3':
            import dlm_lags_3a24_20261026 as d
            d.OUT = RESULT / 'dlm3'
            d.TAX = RESULT / 'dlm0/taxonomia.csv'
            d.OLD = RESULT / 'dlm0/selecao_K.csv'
            d.HASH = digest
            print(json.dumps(d.run(), ensure_ascii=False, indent=2))
        elif args.etapa == 'comparar_sarimax':
            import comparar_sarimax_lags3_24_20261026 as c
            c.OLD = RESULT / 'sarimax0'
            c.NEW = RESULT / 'sarimax3'
            for folder in [c.OLD, c.NEW]:
                summary = json.loads((folder / 'resumo.json').read_text(encoding='utf-8'))
                assert summary['base_sha256'] == digest
            c.main()
        else:
            os.environ['TCC_SARIMAX_LAG_INICIAL'] = str(args.lag)
            import sarimax_por_tipologia_k0_24_20261026 as s
            s.OUT = RESULT / f'sarimax{args.lag}'
            s.UNITS = s.OUT / 'unidades'
            s.HASH = digest
            conferir_proveniencia_checkpoints(s.OUT, digest)
            # A função main verifica o hash novo antes de ler qualquer checkpoint.
            sys.argv = [sys.argv[0], '--fase', args.fase, '--uf', args.uf, '--periodo', args.periodo]
            if args.uf == 'todas' or args.fase == 'consolidar':
                s.main()
            else:
                # Evita dois processos reestimando e gravando a mesma unidade
                # durante retomadas paralelas; não altera a estimação.
                locks = ROOT.parent / '.locks-sarimax'
                locks.mkdir(exist_ok=True)
                period = 'pre' if args.periodo == 'Pré' else 'total'
                lock = locks / f'{args.lag}_{period}_{args.uf}_{args.fase}.lock'
                while True:
                    try:
                        with lock.open('x', encoding='utf-8') as f:
                            f.write(str(os.getpid()))
                        break
                    except FileExistsError:
                        time.sleep(2)
                try:
                    s.main()
                finally:
                    lock.unlink()
    print('CONCLUÍDO', args.etapa, args.uf, args.periodo, flush=True)


if __name__ == '__main__':
    main()
