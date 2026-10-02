"""10–13: retomar por hashes; reprodução explícita preserva backup local."""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys, os, zipfile, datetime
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def retomar():
    problemas=[];folder=ROOT/'outputs/tables/segunda_etapa'
    for stage in range(10,14):
        cp=folder/f'checkpoint_{stage}.json'
        if not cp.exists():problemas.append(f'{stage}: checkpoint ausente');continue
        d=json.loads(cp.read_text())
        for name,h in d['entradas'].items():
            paths=list((ROOT/'data').rglob(name)) if (ROOT/'data').exists() else []
            if not paths:problemas.append(f'{stage}: entrada indisponível: {name}')
            elif not any(sha(p)==h for p in paths):problemas.append(f'{stage}: hash da entrada diverge: {name}')
        if sha(ROOT/'src/segunda_etapa.py')!=d['codigo']:problemas.append(f'{stage}: código diverge')
        protocol=ROOT/'docs/segunda_etapa_protocolo.md'
        if not protocol.exists() or sha(protocol)!=d['protocolo']:problemas.append(f'{stage}: protocolo diverge/ausente')
        for name,h in d['tabelas'].items():
            p=folder/name
            if not p.exists() or sha(p)!=h:problemas.append(f'{stage}: snapshot de tabela diverge/ausente: {name}')
    if problemas:
        print('\n'.join(problemas))
        raise SystemExit('Retomada integral10–13 não certificada. Saídas preservadas; nenhum recálculo. Use verificar_saidas_publicadas.py para conferir saídas salvas, ou restaure entradas e peça --reproduzir explicitamente.')
    print('Checkpoints10–13 compatíveis; saídas reutilizadas, sem reestimação.')
if __name__=='__main__':
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group()
    g.add_argument('--retomar',action='store_true');g.add_argument('--reproduzir',action='store_true')
    g.add_argument('--recalcular',action='store_true',help='Alias de --reproduzir; não apaga saídas.')
    args=ap.parse_args();os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
    if not(args.reproduzir or args.recalcular):retomar();raise SystemExit(0)
    for name in ['df_tcc_2013_2024.parquet','BD_Atlas_1991_2024_v1.0_2025.04.14_Consolidado.csv']:
        if not list((ROOT/'data').rglob(name)):raise SystemExit('Entrada ausente: '+name+'; reprodução não iniciada.')
    backup=ROOT/'.checkpoints_locais';backup.mkdir(exist_ok=True)
    target=backup/('antes_reproduzir_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.zip')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for folder in [ROOT/'outputs/tables/segunda_etapa',ROOT/'notebooks']:
            for p in folder.glob('*'):
                if p.is_file():z.write(p,p.relative_to(ROOT))
    for p in sorted((ROOT/'notebooks').glob('1[0-3]_*.ipynb')):
        subprocess.run([sys.executable,str(ROOT/'src/executar_notebooks_categorias.py'),str(p)],check=True)
    subprocess.run([sys.executable,str(ROOT/'src/verificar_segunda_etapa.py')],check=True)
