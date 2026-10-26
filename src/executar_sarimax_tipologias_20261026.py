"""Executa os SARIMAX individuais em paralelo por UF e período, com retomada.

Cada unidade grava resultados somente na própria pasta, sem sobreposição.
O comando principal imprime progresso e registra falhas para eventual reprise.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from analise_estadual import load

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"src/sarimax_por_tipologia_k0_24_20261026.py"
OUT=ROOT/"outputs/tables/sarimax_por_tipologia_k0_24_20261026"


def single(job):
    period,unit,phase,inicio_lags=job
    cmd=[sys.executable,str(SCRIPT),"--fase",phase,"--periodo",period,"--uf",unit]
    env=os.environ.copy()
    env["OPENBLAS_NUM_THREADS"]="1"
    env["OMP_NUM_THREADS"]="1"
    env["MKL_NUM_THREADS"]="1"
    env["PYTHONDONTWRITEBYTECODE"]="1"
    env["TCC_SARIMAX_LAG_INICIAL"]=str(inicio_lags)
    try:
        result=subprocess.run(cmd,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,timeout=1800,check=False)
        return period,unit,result.returncode,result.stdout,result.stderr
    except subprocess.TimeoutExpired as exc:
        return period,unit,124,"",f"tempo excedido de 1800s: {exc}"


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--workers",type=int,default=4)
    parser.add_argument("--fase",choices=["individuais","gerais"],default="individuais")
    parser.add_argument("--ufs",nargs="*")
    parser.add_argument("--periodo",choices=["Pré","Total","ambos"],default="ambos")
    parser.add_argument("--inicio-lags",type=int,choices=[0,3],default=0,
                        help="0 reproduz a análise original; 3 testa somente lags 3..K")
    args=parser.parse_args()
    assert 1 <= args.workers <= 16
    periods=["Pré","Total"] if args.periodo=="ambos" else [args.periodo]
    units=args.ufs if args.ufs else sorted(load().uf.unique())+["Brasil"]
    jobs=[(p,u,args.fase,args.inicio_lags) for p in periods for u in units]
    print(f"Iniciando {len(jobs)} unidades ({args.fase}, lags {args.inicio_lags}..24) com {args.workers} processos simultâneos",flush=True)
    failures=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs={pool.submit(single,job):job for job in jobs}
        for n,fut in enumerate(as_completed(futs),1):
            period,uf,code,stdout,stderr=fut.result()
            print(f"[{n}/{len(jobs)}] {period}/{uf}: " +
                  ("concluído" if code==0 else f"falhou (código {code})"),flush=True)
            if code!=0:
                failures.append((period,uf,code,stderr[-1700:]))
                print("  erro:",stderr[-500:].replace("\n"," "),flush=True)
    if failures:
        for item in failures:print("FALHA",item,flush=True)
        raise SystemExit(f"{len(failures)} unidades falharam; checkpoints preservados")
    print("Todas as unidades individuais concluídas",flush=True)


if __name__=="__main__":main()
