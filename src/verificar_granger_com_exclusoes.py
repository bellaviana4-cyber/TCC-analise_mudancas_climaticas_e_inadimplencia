"""Verifica o teste F com OLS/f_test e o BH por implementação independente."""
import os
from pathlib import Path
import numpy as np
import pandas as pd
from statsmodels.regression.linear_model import OLS
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/tables/modalidades_excluidas_20261104'
os.environ['TCC_OUTPUT_DIR']=str(OUT/'granger')
from analise_estadual import load

def main():
    d=load();g=pd.read_csv(OUT/'granger/granger_aplicacoes.csv')
    assert len(g)==864 and not g.duplicated(['uf','periodo','tipologia']).any()
    checks=[]
    with threadpool_limits(limits=1):
        for _,row in g[g.status.eq('estimado')].iterrows():
            z=d[d.uf.eq(row.uf)&d.mes_ano.le('2020-01' if row.periodo=='Pré' else '2024-12')].sort_values('mes_ano')
            y=z.y.to_numpy();x=z['x_'+row.tipologia].to_numpy();tt=np.arange(7,len(z));p=int(row.p_lags)
            X=np.column_stack([np.ones(len(tt)),(z.mes.to_numpy()[tt,None]==np.arange(2,13)).astype(float)]+[y[tt-j] for j in range(1,p+1)]+[x[tt-j] for j in range(1,p+1)])
            model=OLS(y[tt],X).fit()
            restriction=np.zeros((p,X.shape[1]));restriction[:,-p:]=np.eye(p)
            test=model.f_test(restriction)
            err=abs(float(test.pvalue)-row.p)
            assert err<1e-9,(row.uf,row.tipologia,err)
            assert model.df_resid==row.df_den==len(tt)-(2*p+12)
            checks.append(dict(uf=row.uf,periodo=row.periodo,tipologia=row.tipologia,erro_p=err))
    for _,z in g.groupby(['uf','periodo']):
        assert len(z)==16
        ps=z.p.fillna(1).to_numpy();idx=np.argsort(ps);qq=np.minimum.accumulate((ps[idx]*16/np.arange(1,17))[::-1])[::-1].clip(0,1)
        q=np.empty(16);q[idx]=qq
        ok=z.p.notna().to_numpy()
        assert np.allclose(q[ok],z.q_bh.to_numpy()[ok],atol=1e-12)
    pd.DataFrame(checks).to_csv(OUT/'granger/validacao_independente.csv',index=False)
    print('Teste F e BH conferidos para',len(checks),'modelos estimáveis')

if __name__=='__main__':main()
