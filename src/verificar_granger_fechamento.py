"""Verificações substantivas15; --somente-saidas não requer estimar modelos."""
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from hashlib import sha256
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/tables/granger_fechamento'


def verify(saved_only=False):
    from statsmodels.stats.multitest import multipletests
    checks=[]
    def check(name,value):
        if not value:raise AssertionError(name)
        checks.append({'Verificação':name,'Status':'passou'})
    r=pd.read_csv(OUT/'resultados.csv');m=pd.read_csv(OUT/'matriz42.csv')
    check('168 cenários/42 matriz',len(r)==168 and len(m)==42)
    check('Todos21 nomes × dois períodos',r.groupby(['Especificação','Período']).size().eq(21).all())
    check('Categorias completas e únicas',not r.duplicated(['Período','Exposição','Especificação']).any())
    for fam,n in [('PRINCIPAL',42),('SENSIBILIDADES',126)]:
        g=r[r.Família==fam];check('Família '+fam,len(g)==n and g['Família n'].eq(n).all())
        for method,col in [('fdr_bh','p BH'),('fdr_by','p BY'),('holm','p Holm')]:
            check(col+' '+fam,np.allclose(g[col],multipletests(g.p.fillna(1),method=method)[1]))
    check('BH global168 íntegro',np.allclose(r['p BH global168'],multipletests(r.p.fillna(1),method='fdr_bh')[1]))
    z=r[r.p.notna()]
    check('Datas e n comuns entre especificações',z.groupby(['Período','Exposição'])['n efetivo'].nunique().eq(1).all())
    check('119/60 amostras efetivas',set(z['n efetivo'])=={119,60})
    check('GL mínimos',z.GL.ge(30).all() and z['n efetivo'].ge(3*z.k).all())
    check('P ausente só em cenários não estimados',r.p.isna().eq(r['Categoria resultado'].eq('Não estimado')).all())
    check('Exclusões mantidas no ajuste',r.loc[r.p.isna(),'p BH'].eq(1).all())
    check('Triagem ampliada não resgata básica',not (r['Triagem ampliada']&~r['Triagem básica']).any())
    check('Triagem com motivo explícito',z['Triagem ampliada'].eq(z.Motivos.str.startswith('Sem indicação')).all())
    check('Intervalos ordenados',z['IC baixo'].le(z['IC alto']).all())
    check('Pré não recebe mudança pós2020',z.loc[z['Período'].str.startswith('Pré'),'Estabilidade p'].isna().all())
    cr=pd.read_csv(OUT/'criterios_bic.csv')
    check('BIC em n comum',cr.groupby(['Período','Exposição'])['n comum'].nunique().eq(1).all())
    if not saved_only:
        from granger_fechamento import inputs,design,fit,SPECS,PERIODS,OLS,restrict
        raw,keys=inputs()
        for per,(ini,fim) in PERIODS.items():
            s=raw.loc[ini:fim]
            for key in ['Total nacional','Tipologia | Onda de Frio']:
                mm,p,q,*_=fit(s,key,SPECS[0]);R=restrict(mm,[f'D{i}' for i in range(1,q+1)])
                X=pd.DataFrame(mm.model.exog,columns=mm.model.exog_names);restricted=OLS(mm.model.endog,X.drop(columns=[f'D{i}' for i in range(1,q+1)])).fit()
                check('F restrito=Wald '+per+key,np.isclose(mm.compare_f_test(restricted)[0],float(mm.wald_test(R,use_f=True,scalar=True).statistic)))
            for spec in SPECS:
                a=s.iloc[:60].copy();b=a.copy();b.iloc[-1,b.columns.get_loc('I')]=99;b.iloc[-1,b.columns.get_loc('Total nacional')]=999999
                check('Features sem alvo contemporâneo '+per+spec,np.allclose(design(a,'Total nacional',spec).drop(columns='y').iloc[-1],design(b,'Total nacional',spec).drop(columns='y').iloc[-1]))
        old=pd.read_csv(ROOT/'outputs/tables/adequacao/nacional.csv');new=r[r.Especificação==SPECS[3]].merge(old[old.Transformação=='Diferença sazonal'],on=['Período','Exposição'])
        check('BIC sazonal reproduz p14 sem trocar família',np.allclose(new.p_x,new.p_y,equal_nan=True,rtol=1e-8,atol=1e-12))
    path=OUT/'checkpoint_15.json'
    if saved_only and path.exists():
        c=json.loads(path.read_text())
        for name,h in c['entradas'].items():check('Entrada hash '+name,sha256((ROOT/name).read_bytes()).hexdigest()==h)
        for name,h in c['codigo'].items():check('Código hash '+name,sha256((ROOT/name).read_bytes()).hexdigest()==h)
        for name,h in c['tabelas'].items():check('Tabela hash '+name,sha256((OUT/name).read_bytes()).hexdigest()==h)
    if not saved_only:pd.DataFrame(checks).to_csv(OUT/'validacao.csv',index=False,encoding='utf-8-sig')
    print(f'{len(checks)} verificações passaram.');return checks

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--somente-saidas',action='store_true');args=ap.parse_args();verify(args.somente_saidas)
