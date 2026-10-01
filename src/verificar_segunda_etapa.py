"""Verificações substantivas: famílias, F, efeitos fixos, vazamento e saídas executadas."""
from segunda_etapa import *
import nbformat
checks=[]
def check(name,condition):
    if not condition:raise AssertionError(name)
    checks.append({'Verificação':name,'Status':'passou'})
previous()
r=read('nacional');check('Família NACIONAL50 linhas, reservas/exclusões preservadas',len(r[r.Família=='NACIONAL'])==50);check('Sensibilidade25 linhas',len(r[r.Família=='DETERMINISTICAS'])==25)
for family,df,n in [('NACIONAL',r[r.Família=='NACIONAL'],50),('DETERMINISTICAS',r[r.Família=='DETERMINISTICAS'],25),('PAINEL',read('painel'),8),('RESPOSTA',read('resposta'),16),('PREVISAO',read('previsao'),4),('TY',read('ty'),4)]:
    check('BH íntegro '+family,np.allclose(df['p BH'],multipletests(df.p.fillna(1),method='fdr_bh')[1]))
    check('Família fixa '+family,len(df)==n and (df['Família n']==n).all())
ct=read('criterios_historico');check('Amostra comparável em todas seleções',ct.groupby(['Período','Exposição','Família'])['n comum'].nunique().eq(1).all())
s=pd.read_parquet(PROC/'segunda_series_historicas.parquet');m,_,_,p,q=select(s,'Total nacional');R=restrict(m,[f'D{j}' for j in range(1,q+1)]);X=pd.DataFrame(m.model.exog,columns=m.model.exog_names);restr=OLS(m.model.endog,X.drop(columns=[f'D{j}' for j in range(1,q+1)])).fit();check('F conjunto restrito = Wald',np.isclose(m.compare_f_test(restr)[0],float(m.wald_test(R,use_f=True,scalar=True).statistic)))
full=pd.read_parquet(PROC/'segunda_series_completas.parquet').astype(float);window=full.iloc[:73].copy();_,x=design(window,EXPOS[0],1,1);modified=window.copy();modified.loc[modified.index[-1],['I',EXPOS[0]]]=[999,999999];_,xm=design(modified,EXPOS[0],1,1);check('Features alvo independem de I/D contemporâneos e futuros',np.allclose(x.iloc[-1],xm.iloc[-1]))
f=read('previsoes_folds');check('Treino anterior a todos alvos',(pd.to_datetime(f['Treino fim'])<pd.to_datetime(f['Data alvo'])).all());check('72/13 alvos por indicador',set(f.groupby(['Período','Exposição']).size())=={72,13})
for file in sorted((ROOT/'notebooks').glob('1[0-3]_*.ipynb')):
    n=nbformat.read(file,as_version=4);nbformat.validate(n);check('Notebook executado sem erro '+file.name,all(c.execution_count is not None and all(o.output_type!='error' for o in c.outputs) for c in n.cells if c.cell_type=='code'))
check('Within vs LSDV',read('validacao_painel')['Status'].eq('passou').all())
for df in [r,read('painel'),read('resposta')]:check('Triagem não resgata significância',not ((df['p BH']<.05)&df['Diagnóstico favorável']).any())
save(pd.DataFrame(checks),'validacao_final');print(pd.DataFrame(checks).to_string(index=False))
