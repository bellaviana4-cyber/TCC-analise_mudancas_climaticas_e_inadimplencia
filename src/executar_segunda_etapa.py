"""Executa 10–13 em processos novos; --recalcular substitui saídas da segunda etapa."""
from pathlib import Path
import argparse, subprocess, sys, os
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--recalcular',action='store_true',help='Remove tabelas/checkpoints da segunda etapa e reestima tudo. Não toca05–09.');args=ap.parse_args()
    if args.recalcular:
        for p in (ROOT/'outputs/tables/segunda_etapa').glob('*'):
            if p.is_file():p.unlink()
    os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
    for p in sorted((ROOT/'notebooks').glob('1[0-3]_*.ipynb')):
        subprocess.run([sys.executable,str(ROOT/'src/executar_notebooks_categorias.py'),str(p)],check=True)
    subprocess.run([sys.executable,str(ROOT/'src/verificar_segunda_etapa.py')],check=True)
