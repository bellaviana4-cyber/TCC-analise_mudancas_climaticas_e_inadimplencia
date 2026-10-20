"""ADF e KPSS por UF, período e tipologia; warnings registrados, não suprimidos."""
from __future__ import annotations
import warnings
import numpy as np,pandas as pd
from statsmodels.tsa.stattools import adfuller,kpss
from analise_estadual import load,TIPOS,OUT

def _teste_com_warnings(func,*args,**kwargs):
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        p=float(func(*args,**kwargs)[1])
    return p,' | '.join(sorted(set(f'{w.category.__name__}: {str(w.message).strip().replace(chr(10),' ')}' for w in captured)))

def main():
    df=load();rows=[]
    for per,stop in [('Pré','2020-01'),('Total','2024-12')]:
        for uf,g in df[df.mes_ano<=stop].groupby('uf'):
            for var in ['y']+['x_'+x for x in TIPOS]:
                v=g[var].dropna().to_numpy(float)
                rec={'uf':uf,'periodo':per,'serie':var,'N':len(v),
                     'transformacao':'Delta log(I)' if var=='y' else 'Delta log(1+D)',
                     'warning_ADF':'','warning_KPSS':''}
                if not np.isfinite(v).all() or np.ptp(v)<1e-10:
                    rec.update(status='constante ou inválida',p_ADF=np.nan,p_KPSS=np.nan,conclusao='não testável')
                    rows.append(rec);continue
                try:rec['p_ADF'],rec['warning_ADF']=_teste_com_warnings(adfuller,v,regression='c',autolag='BIC')
                except Exception as exc:rec.update(p_ADF=np.nan,warning_ADF=f'Erro: {exc}')
                try:rec['p_KPSS'],rec['warning_KPSS']=_teste_com_warnings(kpss,v,regression='c',nlags='auto')
                except Exception as exc:rec.update(p_KPSS=np.nan,warning_KPSS=f'Erro: {exc}')
                a=rec['p_ADF'];k=rec['p_KPSS']
                rec['status']='calculado' if np.isfinite(a) and np.isfinite(k) else 'falha parcial'
                if np.isfinite(a) and np.isfinite(k):
                    if a<.05 and k>=.05:rec['conclusao']='favorável à estacionariedade (não é prova)'
                    elif a>=.05 and k<.05:rec['conclusao']='sinais contrários à estacionariedade'
                    else:rec['conclusao']='inconclusivo ou divergente'
                else:rec['conclusao']='não determinado'
                rows.append(rec)
    out=pd.DataFrame(rows);out.to_csv(OUT/'estacionariedade_adf_kpss.csv',index=False,encoding='utf-8-sig')
    print('ADF/KPSS',len(out),'avisos ADF',int(out.warning_ADF.str.len().gt(0).sum()),
          'avisos KPSS',int(out.warning_KPSS.str.len().gt(0).sum()))
    print(out[out.serie=='y'].groupby(['periodo','conclusao']).size().to_string())
    print('Tipos de avisos KPSS:',out.loc[out.warning_KPSS.str.len()>0,'warning_KPSS'].value_counts().head(3).to_string())
    return out
if __name__=='__main__':main()