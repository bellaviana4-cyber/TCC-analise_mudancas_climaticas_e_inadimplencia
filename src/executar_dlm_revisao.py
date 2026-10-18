"""CLI de reprodução e retomada com hashes; nenhum resultado desejado é hardcoded."""
import argparse, json, os, subprocess, sys, shutil, importlib.metadata, datetime
import numpy as np
import pandas as pd
from dlm_revisao import *

def prepare_r():
 manifest=[];exps=get_exps()
 for p in CACHE.glob('*.json'):
  if not p.name.startswith(('main_','leads_','interaction_','coldtrace_')):continue
  z=json.loads(p.read_text());rows=[]
  for key,value in z.items():
   for i,row in enumerate(np.atleast_2d(value)):rows.append(dict(endpoint=key,row=i,**{f'z{j}':x for j,x in enumerate(row)}))
  pd.DataFrame(rows).to_csv(p.with_suffix('.contrasts.csv'),index=False)
  bits=p.stem.split('_');design=bits[0];per='Total' if design=='interaction' else ('Pré' if bits[1]=='Pre' else 'Total');c='tipo_onda_de_frio' if design=='coldtrace' else list(exps)[int(bits[-1])]
  manifest.append(dict(id=p.stem,design=design,periodo=per,coluna=c,exposicao=label(c)))
  pd.DataFrame({'estimate':np.load(p.with_suffix('.npz'))['b']}).to_csv(p.with_suffix('.coef.csv'),index=False)
 pd.DataFrame(manifest).sort_values('id').to_csv(CACHE/'r_manifest.csv',index=False)
 d=load_panel();z=d[['uf','data_base']].copy()
 for c in ['total_desastres','grupo_climatologico','grupo_hidrologico','grupo_meteorologico']:z[c]=exps[c]['C_prop']
 z.to_csv(CACHE/'cips_exposicoes_input.csv',index=False)

def run_r():
 exe=os.getenv('DLM_R_EXEC') or shutil.which('Rscript')
 if not exe:raise RuntimeError('Rscript indisponível: instale R, clubSandwich e plm. Não substituir CR2/CIPS por aproximações.')
 cmd=[exe,str(ROOT/'src/dlm_revisao_inferencia.R'),str(ROOT)] if Path(exe).name=='Rscript' else [exe,'--vanilla','--slave','--file='+str(ROOT/'src/dlm_revisao_inferencia.R'),'--args',str(ROOT)]
 result=subprocess.run(cmd,capture_output=True,text=True)
 if result.returncode:raise RuntimeError(result.stdout+result.stderr)
 print("R: CR2 e CIPS executados; coeficientes Python/R reconciliados.")

def cold_trace():
 d=load_panel();e=get_exps();r=pd.read_csv(OUT/'principais.csv');rows=[]
 for per,(start,end) in PERIODS.items():
  keep=d.data_base.between(start,end);J=int(r[(r.periodo==per)&(r.coluna=='tipo_onda_de_frio')].J.iloc[0]);q=lag_frame(d.loc[keep],np.log1p(e['tipo_onda_de_frio']['A'][keep]))
  for name,B,K in [('Historico A K3',basis(3,method='irrestrito'),3),('A smooth K12',basis(12,J),12)]:
   f=model(q,B,K=K);rows.append(result_row(f,dict(periodo=per,coluna='tipo_onda_de_frio',exposicao=label('tipo_onda_de_frio'),especificacao=name),True));export_r(f,'coldtrace_'+('Pre' if per=='Pré' else per)+'_'+str(K))
 save(pd.DataFrame(rows),'onda_frio_rastreio_A')

def checkpoint():
 tracked=[ROOT/'docs/dlm_revisao_protocolo.md',ROOT/'src/dlm_revisao.py',ROOT/'src/dlm_revisao_inferencia.R',ROOT/'src/executar_dlm_revisao.py',ROOT/'src/verificar_dlm_revisao.py',ROOT/'src/dlm_revisao_relatorio.py',ROOT/'src/executar_notebook_dlm_revisao.py',ROOT/'requirements-dlm-revisao.txt']
 inputs=[ROOT/'data/processed/df_tcc_2013_2024.csv',ROOT/'data/raw/atlas_desastres/atlas.csv']
 outs=list(OUT.glob('*'));outs=[p for p in outs if p.name!='checkpoint.json']
 data=dict(status='executado e validado',timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),origem='3c94482628b86d1789ee98f8d35f6820835a7219',arquivos={str(p.relative_to(ROOT)):sha(p) for p in tracked+inputs+outs},versoes={x:importlib.metadata.version(x) for x in ['numpy','pandas','scipy','statsmodels','patsy','nbformat','nbclient']})
 (OUT/'checkpoint.json').write_text(json.dumps(data,indent=2,ensure_ascii=False))

def resume():
 cp=json.loads((OUT/'checkpoint.json').read_text())
 for p,h in cp['arquivos'].items():
  assert (ROOT/p).exists() and sha(ROOT/p)==h,'Hash divergente: '+p
 from verificar_dlm_revisao import verify
 print(verify().to_string(index=False));return cp

def run():
 run_all();cold_trace();prepare_r();run_r();final_fdr()
 from dlm_revisao_relatorio import figures,write_results,dynamics_support,classify
 from verificar_dlm_revisao import verify
 dynamics_support();figures();verify();classify();write_results();checkpoint()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--retomar',action='store_true');p.add_argument('--reproduzir',action='store_true');a=p.parse_args()
 if a.retomar:resume()
 elif a.reproduzir:run()
 else:p.error('Use --retomar ou --reproduzir')
