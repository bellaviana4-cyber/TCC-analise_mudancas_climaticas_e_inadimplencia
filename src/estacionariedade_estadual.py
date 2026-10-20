"""ADF e KPSS sobre as séries transformadas das 27 UFs nos dois recortes."""
import warnings
import numpy as np,pandas as pd
from statsmodels.tsa.stattools import adfuller,kpss
from analise_estadual import load,TIPOS,OUT

def main():
 df=load();rows=[]
 for period,stop in [('Pré','2020-01'),('Total','2024-12')]:
  for uf,g in df[df.mes_ano<=stop].groupby('uf'):
   for var in ['y']+['x_'+v for v in TIPOS]:
    v=g[var].dropna().to_numpy(float)
    row={'uf':uf,'periodo':period,'serie':var,'N':len(v),'transformacao':'Delta log(I)' if var=='y' else 'Delta log(1+D)'}
    if not np.isfinite(v).all() or np.ptp(v)<1e-10:
     row.update(status='constante ou inválida',p_ADF=np.nan,p_KPSS=np.nan,conclusao='não testável');rows.append(row);continue
    try:row['p_ADF']=float(adfuller(v,regression='c',autolag='BIC')[1])
    except Exception:row['p_ADF']=np.nan
    try:
     with warnings.catch_warnings():
      warnings.simplefilter('ignore');row['p_KPSS']=float(kpss(v,regression='c',nlags='auto')[1])
    except Exception:row['p_KPSS']=np.nan
    a=row['p_ADF'];k=row['p_KPSS'];row['status']='calculado' if np.isfinite(a) and np.isfinite(k) else 'falha parcial'
    if np.isfinite(a) and np.isfinite(k):
     if a<.05 and k>=.05:row['conclusao']='favorável à estacionariedade (não é prova)'
     elif a>=.05 and k<.05:row['conclusao']='sinais contrários à estacionariedade'
     else:row['conclusao']='inconclusivo ou divergente'
    else:row['conclusao']='não determinado'
    rows.append(row)
 out=pd.DataFrame(rows);out.to_csv(OUT/'estacionariedade_adf_kpss.csv',index=False,encoding='utf-8-sig')
 print('ADF/KPSS',len(rows));print(out[out.serie=='y'].groupby(['periodo','conclusao']).size().to_string())
if __name__=='__main__':main()