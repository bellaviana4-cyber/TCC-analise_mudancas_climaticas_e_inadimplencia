"""Executa 07–09 em processos Python novos, capturando tabelas, Markdown e PNG.
Alternativa sem sockets Jupyter. As células são executadas integralmente e qualquer erro interrompe.
"""
from pathlib import Path
import sys,os,subprocess,io,contextlib,base64
import nbformat
ROOT=Path(__file__).resolve().parents[1]
def executar(path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.display import display,Image
    path=Path(path).resolve();os.chdir(path.parent)
    shell=InteractiveShell.instance(); nb=nbformat.read(path,as_version=4)
    outputs=[]
    def publish(data,metadata=None,**kwargs):
        outputs.append(nbformat.v4.new_output('display_data',data=data,metadata=metadata or {}))
    shell.display_pub.publish=publish
    def show(*args,**kwargs):
        for num in plt.get_fignums():
            buf=io.BytesIO();plt.figure(num).savefig(buf,format='png',dpi=90,bbox_inches='tight')
            display(Image(data=buf.getvalue()))
    plt.show=show
    count=0
    for cell in nb.cells:
        if cell.cell_type!='code':continue
        count+=1;outputs=[];stdout=io.StringIO();stderr=io.StringIO()
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            result=shell.run_cell(cell.source,store_history=False,silent=True)
        if result.error_before_exec or result.error_in_exec:
            print(stdout.getvalue());print(stderr.getvalue());raise RuntimeError(f'Erro na célula {count}: {result.error_before_exec or result.error_in_exec}')
        if stdout.getvalue():outputs.insert(0,nbformat.v4.new_output('stream',name='stdout',text=stdout.getvalue()))
        if stderr.getvalue():outputs.append(nbformat.v4.new_output('stream',name='stderr',text=stderr.getvalue()))
        cell.outputs=outputs;cell.execution_count=count
        print(f'{path.name}: célula {count} executada',flush=True)
    nb.metadata['execution']={'status':'completed','mode':'fresh Python process; IPython cells; no Jupyter sockets','python':sys.version.split()[0]}
    nbformat.validate(nb);nbformat.write(nb,path)
    print('CONCLUÍDO',path.name,path.stat().st_size,flush=True)
if __name__=='__main__':
    if len(sys.argv)>1:executar(sys.argv[1])
    else:
        for p in sorted((ROOT/'notebooks').glob('0[789]_*.ipynb')):
            subprocess.run([sys.executable,__file__,str(p)],check=True)
