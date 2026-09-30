"""Auditoria e inferência por protocolos municipais. Consulte docs/ampliacao_metodologia.md."""
from pathlib import Path
import hashlib, json, re, unicodedata, warnings
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.api import OLS
from statsmodels.tsa.stattools import adfuller, kpss, acf
from statsmodels.tsa.seasonal import STL
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.diagnostic import acorr_ljungbox, het_breuschpagan
from statsmodels.tsa.api import VAR

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT/'outputs/tables/ampliacao'
FIGURES = ROOT/'outputs/figures/ampliacao'
PERIODOS = {'Total (2013–2024)': ('2013-01-01','2024-12-01',144), 'Pré-pandemia (até jan/2020)': ('2013-01-01','2020-01-01',85)}
SPECS = ['Principal: 11 dummies', 'Comparação: sem dummies', 'Robustez: diferença sazonal']
DIRECOES = [('Desastres → inadimplência','D','I'),('Inadimplência → desastres','I','D')]

def salvar(df,nome):
    TABLES.mkdir(parents=True,exist_ok=True)
    df.to_csv(TABLES/(nome+'.csv'),index=False,encoding='utf-8-sig')
    return df

def slug(x):
    x=''.join(c for c in unicodedata.normalize('NFKD',x.lower()) if not unicodedata.combining(c))
    return re.sub('[^a-z0-9]+','_',x).strip('_')

def preparar():
    files=list((ROOT/'data/raw/atlas_desastres').glob('*.csv'))
    if len(files)!=1: raise ValueError('Esperado exatamente um CSV consolidado do Atlas.')
    ap=files[0]; pp=ROOT/'data/processed/df_tcc_2013_2024.parquet'
    a=pd.read_csv(ap,sep=';',encoding='latin1',low_memory=False)
    d=pd.read_parquet(pp)
    audit=[]
    def rec(k,v): audit.append({'Verificação':k,'Resultado':str(v)})
    for p in [ap,pp]: rec('SHA256 '+p.name,hashlib.sha256(p.read_bytes()).hexdigest())
    rec('Linhas Atlas completo',len(a));rec('Colunas Atlas',len(a.columns));rec('Colunas Parquet',len(d.columns))
    salvar(pd.DataFrame([{'Base':nome,'Coluna':c,'Tipo':str(df[c].dtype),'Ausentes':int(df[c].isna().sum())} for nome,df in [('Atlas completo',a),('Parquet',d)] for c in df]),'dicionario_inspecao')
    a['data']=pd.to_datetime(a.Data_Evento,format='%d/%m/%Y',errors='coerce')
    rec('Datas inválidas Atlas',a.data.isna().sum())
    if a.data.isna().any(): raise ValueError('Data de ocorrência inválida: revisar antes de agregar.')
    rec('Cobertura arquivo Atlas',f'{a.data.min().date()} a {a.data.max().date()}')
    a=a[a.data.dt.year.between(2013,2024)].copy()
    for c in ['Protocolo_S2iD','Sigla_UF','grupo_de_desastre','descricao_tipologia']:
        a[c]=a[c].astype('string').str.strip().replace('',pd.NA)
        rec('Ausentes no recorte: '+c,a[c].isna().sum())
    rec('Protocolos repetidos no recorte',a.Protocolo_S2iD.duplicated().sum())
    rec('Linhas integralmente duplicadas no recorte',a.duplicated().sum())
    if a.Protocolo_S2iD.isna().any() or a.Protocolo_S2iD.duplicated().any():
        raise ValueError('Protocolos ausentes/repetidos: auditoria manual obrigatória; não deduplicar silenciosamente.')
    if a.Sigla_UF.isna().any(): raise ValueError('UF ausente.')
    rec('Protocolos municipais únicos 2013–2024',len(a))
    rec('Excedentes em município/data/COBRADE (mantidos)',a.duplicated(['Cod_IBGE_Mun','data','Cod_Cobrade']).sum())
    for c in ['grupo_de_desastre','descricao_tipologia']: a[c]=a[c].fillna('Sem informação')
    a['mes']=a.data.dt.to_period('M').dt.to_timestamp()
    d['data_base']=pd.to_datetime(d.data_base).dt.to_period('M').dt.to_timestamp()
    rec('Linhas Parquet',len(d));rec('Duplicações UF × mês Parquet',d.duplicated(['uf','data_base']).sum())
    idx=pd.date_range('2013-01-01','2024-12-01',freq='MS')
    assert len(d)==3888 and d.uf.nunique()==27 and not d.duplicated(['uf','data_base']).any()
    assert set(a.Sigla_UF).issubset(set(d.uf))
    grade=pd.MultiIndex.from_product([sorted(d.uf.unique()),idx],names=['uf','data_base'])
    assert set(map(tuple,d[['uf','data_base']].to_numpy())) == set(grade)
    for c in ['carteira_ativa_total','carteira_inadimplencia_total','total_desastres']:
        d[c]=pd.to_numeric(d[c],errors='raise').astype(float)
        assert np.isfinite(d[c]).all()
    assert (d.carteira_ativa_total>0).all() and (d.carteira_inadimplencia_total>=0).all()
    assert (d.carteira_inadimplencia_total<=d.carteira_ativa_total).all()
    rec('Diferença máxima taxa UF vs razão das carteiras',float(np.max(np.abs(d.taxa_inadimplencia-100*d.carteira_inadimplencia_total/d.carteira_ativa_total))))
    sums=d.groupby('data_base')[['carteira_ativa_total','carteira_inadimplencia_total','total_desastres']].sum().reindex(idx)
    series=pd.DataFrame({'Inadimplência':100*sums.carteira_inadimplencia_total/sums.carteira_ativa_total},index=idx)
    # Cobertura da extração: consolidado 1991–2024, presença em TODOS os 144 meses.
    # Zero = nenhum protocolo na extração; não certifica ausência física/subnotificação.
    assert set(idx).issubset(set(a['mes']))
    meta=[{'Chave':'Total nacional','Nível':'Referência','Categoria':'Total nacional'}]
    series['Total nacional']=a.groupby('mes').Protocolo_S2iD.nunique().reindex(idx,fill_value=0)
    reconc=[]
    old=d.set_index(['uf','data_base']).reindex(grade)
    cnt=a.groupby(['Sigla_UF','mes']).Protocolo_S2iD.nunique().reindex(grade,fill_value=0)
    reconc.append({'Nível':'Referência','Categoria':'Total nacional','Total Atlas':int(cnt.sum()),'Total Parquet':int(old.total_desastres.sum()),'Células UF × mês divergentes':int((cnt.values!=old.total_desastres.values).sum()),'Diferença máxima':float(np.max(np.abs(cnt.values-old.total_desastres.values)))})
    for nivel,col,prefix in [('Grupo','grupo_de_desastre','grupo_'),('Tipologia','descricao_tipologia','tipo_')]:
        total=np.zeros(len(idx))
        for cat in sorted(a[col].unique()):
            key=nivel+' | '+cat; sub=a[a[col].eq(cat)]
            series[key]=sub.groupby('mes').Protocolo_S2iD.nunique().reindex(idx,fill_value=0)
            total+=series[key].values
            meta.append({'Chave':key,'Nível':nivel,'Categoria':cat})
            pc=prefix+slug(cat)
            cnt=sub.groupby(['Sigla_UF','mes']).Protocolo_S2iD.nunique().reindex(grade,fill_value=0)
            reconc.append({'Nível':nivel,'Categoria':cat,'Total Atlas':int(cnt.sum()),'Total Parquet':int(old[pc].sum()) if pc in old else np.nan,'Células UF × mês divergentes':int((cnt.values!=old[pc].values).sum()) if pc in old else np.nan,'Diferença máxima':float(np.max(np.abs(cnt.values-old[pc].values))) if pc in old else np.nan})
        assert np.array_equal(total,series['Total nacional'].values)
    rec('Diferença mensal nacional máxima Atlas vs Parquet',float(np.max(np.abs(series['Total nacional']-sums.total_desastres))))
    rec('Meses da extração com protocolos nacionais',a['mes'].nunique())
    rec('Verificação de carteira por modalidade','Parquet tem chave única UF × mês e não contém modalidade. Agregação nacional não duplica carteiras. A origem SCR não pôde ser reauditada sem arquivos brutos; src/01 soma linhas PF e não verifica sobreposição de dimensões.')
    rec('Unidade de contagem','Protocolo municipal único; nenhum identificador validado de fenômeno intermunicipal.')
    rec('Zeros','Nenhum protocolo observado no consolidado para categoria/mês; cobertura da extração 2013–2024, sem garantia de completude da notificação.')
    cross=a.groupby(['grupo_de_desastre','descricao_tipologia']).size().reset_index(name='Protocolos')
    salvar(cross,'classificacao_grupo_tipologia');salvar(pd.DataFrame(reconc),'reconciliacao');salvar(pd.DataFrame(audit),'auditoria')
    pd.DataFrame(meta).to_json(ROOT/'data/processed/categorias_meta.json',orient='records',force_ascii=False)
    series.index.name='data';series.to_parquet(ROOT/'data/processed/series_categorias.parquet')
    return series,pd.DataFrame(meta),pd.DataFrame(audit)

def transformacoes(s,credito=False):
    l=np.log(s) if credito else np.log1p(s)
    return {'Nível':s,'Log':l,'Primeira diferença':s.diff(),'Diferença do log':l.diff(),'Diferença sazonal':s.diff(12),'Diferença + sazonal':s.diff().diff(12),'Diferença do log + sazonal':l.diff().diff(12)}

def teste_est(s):
    x=s.dropna().astype(float)
    row={'n':len(x),'ADF especificação':'c; autolag AIC; máximo padrão Schwert','KPSS especificação':'c; nlags auto','ADF n efetivo':np.nan,'ADF estatística':np.nan,'ADF p':np.nan,'ADF lags':np.nan,'KPSS estatística':np.nan,'KPSS p':np.nan,'KPSS lags':np.nan,'KPSS limite':'','Conclusão':'Não aplicável: série constante','Avisos':''}
    if x.nunique()<2:return row
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter('always')
        try:
            ad=adfuller(x,regression='c',autolag='AIC');kp=kpss(x,regression='c',nlags='auto')
            row.update({'ADF n efetivo':ad[3],'ADF estatística':ad[0],'ADF p':ad[1],'ADF lags':ad[2],'KPSS estatística':kp[0],'KPSS p':kp[1],'KPSS lags':kp[2],'KPSS limite':'p ≥ 0,10' if kp[1]==.1 else 'p ≤ 0,01' if kp[1]==.01 else 'Interpolado'})
            ar=ad[1]<.05;kr=kp[1]<.05
            row['Conclusão']='Estacionária: convergente' if ar and not kr else 'Não estacionária: convergente' if not ar and kr else 'Conflitante: ambos rejeitam' if ar else 'Inconclusiva: nenhum rejeita'
        except (ValueError,OverflowError,ZeroDivisionError) as e:row['Conclusão']='Não aplicável: '+str(e)
        row['Avisos']=' | '.join(dict.fromkeys(str(w.message) for w in ws))
    return row

def estacionariedade(series,meta):
    coverage=[];tests=[];season=[]
    allmeta=[{'Chave':'Inadimplência','Nível':'Crédito','Categoria':'Inadimplência'}]+meta.to_dict('records')
    for periodo,(ini,fim,n) in PERIODOS.items():
        for m in allmeta:
            s=series[m['Chave']].loc[ini:fim];assert len(s)==n
            common={'Período':periodo,**m}
            rare=m['Nível']!='Crédito' and ((s>0).sum()<12 or s.sum()<24)
            coverage.append({**common,'Meses':len(s),'Início':str(s.index.min().date()),'Fim':str(s.index.max().date()),'Total ocorrências':float(s.sum()) if m['Nível']!='Crédito' else np.nan,'Meses com ocorrência':int((s>0).sum()),'Proporção zeros':float((s==0).mean()),'Média':s.mean(),'Desvio-padrão':s.std(),'Variância':s.var(),'Valores distintos':s.nunique(),'Rara':bool(rare),'Elegível Granger':bool(s.nunique()>1 and not rare),'Cobertura':'Extração disponível; notificação completa não certificada' if m['Nível']!='Crédito' else '27 UFs em todos os meses'})
            for nome,x in transformacoes(s,m['Nível']=='Crédito').items():
                tests.append({**common,'Transformação':nome,'Perda meses':n-x.notna().sum(),**teste_est(x)})
            stl=STL(s.astype(float),period=12,robust=True).fit()
            v=np.var(stl.seasonal+stl.resid)
            season.append({**common,'ACF(12) nível':acf(s,nlags=12,fft=False)[12] if s.nunique()>1 else np.nan,'Força sazonal STL':max(0,1-np.var(stl.resid)/v) if v>0 else np.nan,'Nota':'STL descritiva; não é teste de raiz sazonal'})
    return salvar(pd.DataFrame(coverage),'cobertura'),salvar(pd.DataFrame(tests),'estacionariedade'),salvar(pd.DataFrame(season),'sazonalidade')

def design(y,p,dummies,start=None):
    X=pd.DataFrame({'const':1.},index=y.index)
    if dummies:
        for month in range(2,13):X[f'mês_{month}']=(y.index.month==month).astype(float)
    for lag in range(1,p+1):
        for col in ['I','D']:X[f'{col}_lag{lag}']=y[col].shift(lag)
    start=p if start is None else start
    X=X.iloc[start:];Y=y.iloc[start:]
    if X.isna().any().any() or np.linalg.matrix_rank(X.values)<X.shape[1]:raise ValueError('Design singular/incompleto')
    return Y,X

def sistema(y,p,dummies,start=None):
    Y,X=design(y,p,dummies,start)
    mods={c:OLS(Y[c],X).fit() for c in ['I','D']}
    resid=np.column_stack([mods[c].resid for c in ['I','D']])
    sign,ld=np.linalg.slogdet(resid.T@resid/len(Y))
    if sign<=0:raise ValueError('Covariância residual singular')
    return Y,X,mods,ld

def max_lag(n,dummies):
    d=12 if dummies else 1
    ok=[p for p in range(1,13) if n-p-(d+2*p)>=30 and n-p>=3*(d+2*p)]
    return max(ok) if ok else 0

def granger(y,p,dummies):
    Y,X,mods,ld=sistema(y,p,dummies)
    # Mesmas datas e controles sazonais no modelo restrito e irrestrito.
    A=[np.array([[mods[t].params[f'{c}_lag{lag}'] for c in ['I','D']] for t in ['I','D']]) for lag in range(1,p+1)]
    companion=A[0] if p==1 else np.vstack([np.hstack(A),np.hstack([np.eye(2*(p-1)),np.zeros((2*(p-1),2))])])
    root=float(max(abs(np.linalg.eigvals(companion))))
    rows=[]
    for direction,cause,target in DIRECOES:
        model=mods[target]; cols=[f'{cause}_lag{l}' for l in range(1,p+1)]
        restricted=OLS(Y[target],X.drop(columns=cols)).fit()
        f,pv,df=model.compare_f_test(restricted)
        R=np.zeros((p,len(model.params)))
        for i,c in enumerate(cols): R[i,X.columns.get_loc(c)]=1
        hc=model.get_robustcov_results(cov_type='HC3').wald_test(R,use_f=True,scalar=True)
        ha=model.get_robustcov_results(cov_type='HAC',maxlags=12,use_correction=True).wald_test(R,use_f=True,scalar=True)
        rows.append({'Direção':direction,'Defasagem':p,'F':float(f),'p':float(pv),'p HC3':float(hc.pvalue),'p HAC12':float(ha.pvalue),'GL numerador':int(df),'GL denominador':int(model.df_resid),'n efetivo':int(model.nobs),'Raiz máxima':root,'Estável':root<1})
    return rows,mods

def diagnosticos(y,p,dummies,mods):
    h=min(max(12,p+4),len(y)//3)
    ex=pd.DataFrame({f'mês_{m}':(y.index.month==m).astype(float) for m in range(2,13)},index=y.index) if dummies else None
    var=VAR(y,exog=ex).fit(p)
    port=var.test_whiteness(nlags=h,adjusted=True)
    rows=[]
    for target,model in mods.items():
        ac=acf(model.resid,nlags=24,fft=False);lim=1.96/np.sqrt(model.nobs)
        # Ljung–Box auxiliar com 2p parâmetros dinâmicos, horizonte > 2p.
        hl=min(max(12,2*p+4),len(model.resid)//2)
        lb=acorr_ljungbox(model.resid,lags=[hl],model_df=2*p,return_df=True).iloc[0]
        bp=het_breuschpagan(model.resid,model.model.exog)
        rows.append({'Equação':'Inadimplência' if target=='I' else 'Desastres','Portmanteau horizonte':h,'Portmanteau p':float(port.pvalue),'Ljung–Box horizonte':hl,'Ljung–Box p':float(lb.lb_pvalue),'ACF(12)':float(ac[12]),'ACF(24)':float(ac[24]),'Limite ACF':lim,'Pico sazonal':bool(abs(ac[12])>lim),'Jarque–Bera p':float(stats.jarque_bera(model.resid).pvalue),'Breusch–Pagan p':float(bp[1])})
    return rows

def executar_granger(series,meta,coverage,station):
    selected=[];lags=[];ics=[];diags=[];skips=[]
    for periodo,(ini,fim,n) in PERIODOS.items():
        for m in meta.to_dict('records'):
            common={'Período':periodo,**m}
            cr=coverage[(coverage.Período==periodo)&(coverage.Chave==m['Chave'])].iloc[0]
            if not cr['Elegível Granger']:
                skips.append({**common,'Motivo':'Constante ou rara (<12 meses positivos ou <24 protocolos); inferência assintótica frágil.'});continue
            raw=series.loc[ini:fim]
            base=pd.DataFrame({'I':raw['Inadimplência'].diff(),'D':np.log1p(raw[m['Chave']]).diff()})
            for spec in SPECS:
                yy=(base.diff(12) if spec==SPECS[2] else base).dropna()
                dm=spec==SPECS[0];mx=max_lag(len(yy),dm)
                cc={**common,'Especificação':spec,'Máximo lag':mx,'n transformado':len(yy)}
                if mx==0:skips.append({**cc,'Motivo':'Graus de liberdade insuficientes'});continue
                criteria=[];cache={}
                for p in range(mx+1):
                    try:
                        Y,X,models,ld=sistema(yy,p,dm,mx)
                        q=X.shape[1];ne=len(Y)
                        criteria.append({**cc,'Defasagem':p,'n comum IC':ne,'Parâmetros/equação':q,'GL comum':ne-q,'AIC':ld+2*2*q/ne,'BIC':ld+np.log(ne)*2*q/ne})
                    except (ValueError,np.linalg.LinAlgError) as e:skips.append({**cc,'Defasagem':p,'Motivo':str(e)})
                ct=pd.DataFrame(criteria);ics.extend(criteria)
                positive=ct[ct.Defasagem>0]
                if positive.empty:continue
                for p in positive.Defasagem.astype(int):
                    rr,mods=granger(yy,p,dm);cache[p]=(rr,mods)
                    lags.extend([{**cc,**r} for r in rr])
                for criterion in ['AIC','BIC']:
                    p=int(positive.loc[positive[criterion].idxmin(),'Defasagem'])
                    pzero=int(ct.loc[ct[criterion].idxmin(),'Defasagem'])
                    # A análise histórica restringe Granger a p>=1; p=0 é benchmark explícito.
                    rr,mods=cache[p];dg=diagnosticos(yy,p,dm,mods)
                    transformD='Diferença do log + sazonal' if spec==SPECS[2] else 'Diferença do log'
                    transformI='Diferença + sazonal' if spec==SPECS[2] else 'Primeira diferença'
                    stD=station[(station.Período==periodo)&(station.Chave==m['Chave'])&(station.Transformação==transformD)].iloc[0]['Conclusão']
                    stI=station[(station.Período==periodo)&(station.Chave=='Inadimplência')&(station.Transformação==transformI)].iloc[0]['Conclusão']
                    for r in rr:
                        target='Inadimplência' if r['Direção']==DIRECOES[0][0] else 'Desastres'
                        diag=next(x for x in dg if x['Equação']==target)
                        selected.append({**cc,**r,'Critério':criterion,'Ótimo incluindo zero':pzero,'Zero preferido':pzero==0,'Estacionariedade I':stI,'Estacionariedade D':stD,**diag})
                    diags.extend([{**cc,'Critério':criterion,'Defasagem':p,**g} for g in dg])
            print(periodo,m['Chave'],flush=True)
    sel=pd.DataFrame(selected);lag=pd.DataFrame(lags)
    # Famílias amplas por direção: ambos períodos, todas categorias/especificações.
    # Não contar duas vezes o mesmo modelo escolhido pelos dois critérios.
    keys=['Período','Chave','Especificação','Direção','Defasagem']
    unique=sel.drop_duplicates(keys).copy()
    for direction,g in unique.groupby('Direção'):
        for method,col in [('fdr_bh','p BH'),('fdr_by','p BY')]: unique.loc[g.index,col]=multipletests(g.p,method=method)[1]
        unique.loc[g.index,'Tamanho família']=len(g)
    sel=sel.merge(unique[keys+['p BH','p BY','Tamanho família']],on=keys,validate='many_to_one')
    for direction,g in lag.groupby('Direção'):
        lag.loc[g.index,'p BH sensibilidade']=multipletests(g.p,method='fdr_bh')[1]
    sel['Significativo nominal']=sel.p<.05;sel['Significativo BH']=sel['p BH']<.05
    sel['Diagnóstico favorável']=sel['Estável']&(sel['Portmanteau p']>=.05)&~sel['Pico sazonal']&(sel['Estacionariedade I']=='Estacionária: convergente')&(sel['Estacionariedade D']=='Estacionária: convergente')&~sel['Zero preferido']
    sel['Evidência com diagnósticos favoráveis']=sel['Significativo BH']&sel['Diagnóstico favorável']&(sel['p HAC12']<.05)
    return salvar(sel,'granger_selecionados'),salvar(lag,'granger_sensibilidade'),salvar(pd.DataFrame(ics),'criterios'),salvar(pd.DataFrame(diags),'diagnosticos'),salvar(pd.DataFrame(skips,columns=list(dict.fromkeys([k for r in skips for k in r])) or ['Período','Chave','Motivo']),'inviaveis')

if __name__=='__main__':
    s,m,a=preparar();c,t,z=estacionariedade(s,m);r=executar_granger(s,m,c,t)
    print(r[0].groupby(['Período','Nível','Direção'])[['Significativo nominal','Significativo BH','Evidência com diagnósticos favoráveis']].sum().to_string())
