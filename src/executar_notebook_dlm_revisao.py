"""Execute actual cells in isolated-process IPython, without ZMQ/network sockets.

Semantics: one shared namespace, ordered code cells, real display outputs and errors.
Useful when the managed environment cannot create TCP/IPC Jupyter kernel sockets.
"""
from pathlib import Path
import argparse, os, warnings
import nbformat
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

def execute(path):
 path=Path(path).resolve();os.chdir(path.parent.parent)
 n=nbformat.read(path,as_version=4);shell=InteractiveShell.instance();count=0
 warnings.filterwarnings('ignore',category=FutureWarning)
 for cell in n.cells:
  if cell.cell_type!='code':continue
  count+=1;cell.outputs=[];cell.execution_count=count
  with capture_output(stdout=True,stderr=True,display=True) as captured:
   res=shell.run_cell(cell.source,store_history=True)
  if captured.stdout:cell.outputs.append(nbformat.v4.new_output('stream',name='stdout',text=captured.stdout))
  if captured.stderr:cell.outputs.append(nbformat.v4.new_output('stream',name='stderr',text=captured.stderr))
  for item in captured.outputs:cell.outputs.append(nbformat.v4.new_output('display_data',data=item.data,metadata=item.metadata))
  err=res.error_before_exec or res.error_in_exec
  if err:
   cell.outputs.append(nbformat.v4.new_output('error',ename=type(err).__name__,evalue=str(err),traceback=[]));nbformat.write(n,path);raise err
  print(f'Célula {count} executada',flush=True)
 n.metadata['execution']={'executor':'IPython em processo isolado; sem sockets ZMQ','code_cells':count,'errors':0}
 nbformat.validate(n);nbformat.write(n,path);return count
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('path');a=p.parse_args();execute(a.path)
