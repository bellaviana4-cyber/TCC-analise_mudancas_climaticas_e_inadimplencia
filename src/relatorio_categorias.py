"""Gera HTML offline fora do repositório; não publica o relatório."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
from plotly.offline import get_plotlyjs
from analise_categorias import *

def records(df):return json.loads(df.to_json(orient='records',date_format='iso',force_ascii=False))
def build(output):
    output=Path(output).resolve()
    if output.is_relative_to(ROOT):raise ValueError('O HTML deve ser salvo fora do repositório.')
    tables={p.stem:records(pd.read_csv(p)) for p in sorted(TABLES.glob('*.csv'))}
    s=pd.read_parquet(ROOT/'data/processed/series_categorias.parquet');m=pd.read_json(ROOT/'data/processed/categorias_meta.json')
    series={k:{'datas':[str(x.date()) for x in s.index],'valores':s[k].tolist()} for k in s.columns}
    diag={}
    selected=pd.read_csv(TABLES/'granger_selecionados.csv')
    for _,r in selected.drop_duplicates(['Período','Chave','Especificação','Defasagem']).iterrows():
        ini,fim,_=PERIODOS[r['Período']];z=s.loc[ini:fim]
        y=pd.DataFrame({'I':z.Inadimplência.diff(),'D':np.log1p(z[r['Chave']]).diff()})
        if r['Especificação']==SPECS[2]:y=y.diff(12)
        y=y.dropna();Y,X,mods,_=sistema(y,int(r['Defasagem']),r['Especificação']==SPECS[0])
        key='||'.join([r['Período'],r['Chave'],r['Especificação'],str(r['Defasagem'])])
        diag[key]={'datas':[str(t.date()) for t in Y.index],**{v:{'residuos':mods[v].resid.tolist(),'acf':acf(mods[v].resid,nlags=24,fft=False).tolist()} for v in ['I','D']}}
    payload={'tabelas':tables,'series':series,'meta':records(m),'diagnosticos':diag,'periodos':list(PERIODOS),'specs':SPECS}
    template=(Path(__file__).with_name('relatorio_categorias_template.txt')).read_text()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(template.replace('/*PLOTLY_INLINE*/',get_plotlyjs()).replace('/*PAYLOAD*/',json.dumps(payload,ensure_ascii=False,allow_nan=False).replace('</','<\\/')),encoding='utf-8')
    print(output)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args();build(args.output)
