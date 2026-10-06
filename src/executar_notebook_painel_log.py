"""Executa células Python reais em namespace compartilhado, sem kernel/socket.
Saídas stdout/stderr reais; nenhuma contagem ou resultado sintético. Falhas interrompem.
"""
import json,io,contextlib,traceback,sys
from pathlib import Path

def execute(path):
 p=Path(path);nb=json.loads(p.read_text());env={'__name__':'__main__'};count=0
 for cell in nb['cells']:
  if cell['cell_type']!='code':continue
  count+=1;cell['execution_count']=count;cell['outputs']=[];out=io.StringIO();err=io.StringIO()
  def emit(mime,data):cell['outputs'].append({'output_type':'display_data','data':{mime:data},'metadata':{}})
  env['emit']=emit
  try:
   with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):exec(compile(''.join(cell['source']),str(p)+':cell'+str(count),'exec'),env)
  except Exception as e:
   cell['outputs'].append({'output_type':'error','ename':type(e).__name__,'evalue':str(e),'traceback':traceback.format_exc().splitlines()});p.write_text(json.dumps(nb,ensure_ascii=False,indent=1));raise
  if out.getvalue():cell['outputs'].append({'output_type':'stream','name':'stdout','text':out.getvalue().splitlines(True)})
  if err.getvalue():cell['outputs'].append({'output_type':'stream','name':'stderr','text':err.getvalue().splitlines(True)})
  print('Célula',count,'executada',flush=True)
 nb['metadata']['execution']={'engine':'Python exec/compile em namespace compartilhado','stdout':'capturado da execução real','code_cells':count};p.write_text(json.dumps(nb,ensure_ascii=False,indent=1));return nb
if __name__=='__main__':execute(sys.argv[1])
