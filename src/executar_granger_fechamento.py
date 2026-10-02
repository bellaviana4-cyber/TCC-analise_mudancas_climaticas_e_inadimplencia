"""Retomada15 por hashes; invalidar nunca inicia recálculo silencioso."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
NB=ROOT/'notebooks/15_fechamento_granger_grupos_tipologias.ipynb'

def notebook_source():
    d=json.loads(NB.read_text())
    s=json.dumps([(c['cell_type'],c['source']) for c in d['cells']],ensure_ascii=False,sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()

def resume():
    from verificar_granger_fechamento import verify
    p=ROOT/'outputs/tables/granger_fechamento/checkpoint_15.json'
    if not p.exists():raise RuntimeError('Checkpoint15 ausente; use --reproduzir explicitamente.')
    c=json.loads(p.read_text())
    if c['protocolo']!=hashlib.sha256((ROOT/'docs/granger_fechamento_protocolo.md').read_bytes()).hexdigest():
        raise RuntimeError('Protocolo mudou; não reutilizar estimativas automaticamente.')
    if c.get('notebook_codigo')!=notebook_source():raise RuntimeError('Código/documentação do notebook mudou; checkpoint incompatível.')
    verify(saved_only=True)
    d=json.loads(NB.read_text());cells=[x for x in d['cells'] if x['cell_type']=='code']
    if not all(x.get('execution_count') is not None and not any(o['output_type']=='error' for o in x.get('outputs',[])) for x in cells):
        raise RuntimeError('Notebook não está completamente executado.')
    print('Retomada15: hashes e saídas conferidos; nenhuma estimativa reexecutada. Isso não certifica pressupostos.')

if __name__=='__main__':
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group()
    g.add_argument('--retomar',action='store_true');g.add_argument('--reproduzir',action='store_true');args=ap.parse_args()
    os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
    if args.reproduzir:
        subprocess.run([sys.executable,str(ROOT/'src/executar_notebooks_categorias.py'),str(NB)],check=True)
    resume()
