"""Executa as duas grades corrigidas sem reutilizar resultados históricos."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import subprocess
import sys
import argparse
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'src/reestimar_com_exclusoes.py'

def run(job):
    lag, period, unit, phase=job
    env=os.environ.copy()
    for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
        env[key]='1'
    env['PYTHONIOENCODING']='utf-8'
    command=[sys.executable,str(SCRIPT),'sarimax','--lag',str(lag),'--periodo',period,'--uf',unit,'--fase',phase]
    result=subprocess.run(command,env=env,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    if result.returncode:
        raise RuntimeError(f'{job}: {result.stderr[-3000:]}')
    return job

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--workers',type=int,default=6)
    parser.add_argument('--lags',nargs='+',type=int,choices=[0,3],default=[0,3])
    parser.add_argument('--periodos',nargs='+',choices=['Pré','Total'],default=['Pré','Total'])
    parser.add_argument('--ufs',nargs='+')
    parser.add_argument('--fases',nargs='+',choices=['individuais','gerais'],default=['individuais','gerais'])
    args=parser.parse_args()
    assert 1 <= args.workers <= 12
    units=sorted(pd.read_csv(ROOT/'data/processed/df_tcc_2013_2024.csv',sep=';',usecols=['uf']).uf.unique())+['Brasil']
    if args.ufs:
        assert set(args.ufs)<=set(units)
        units=args.ufs
    for phase in args.fases:
        jobs=[(lag,per,uf,phase) for lag in args.lags for per in args.periodos for uf in units]
        errors=[]
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures=[pool.submit(run,job) for job in jobs]
            for n,future in enumerate(as_completed(futures),1):
                try:
                    print(n,'/',len(jobs),future.result(),flush=True)
                except Exception as exc:
                    errors.append(str(exc))
                    print('FALHA',str(exc),flush=True)
        if errors:
            raise RuntimeError('\n'.join(errors))
    if not args.ufs and set(args.fases)=={'individuais','gerais'} and set(args.lags)=={0,3} and set(args.periodos)=={'Pré','Total'}:
        for lag in [0,3]:
            run((lag,'ambos','todas','consolidar'))
        print('DUAS GRADES CONCLUÍDAS',flush=True)

if __name__=='__main__':main()
