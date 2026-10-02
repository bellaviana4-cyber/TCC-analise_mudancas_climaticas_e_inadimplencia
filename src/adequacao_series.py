"""Extensão finita de transformação; regras prévias em adequacao_protocolo.md."""
from segunda_etapa import *
AOUT=ROOT/'outputs/tables/adequacao'; AOUT.mkdir(parents=True,exist_ok=True)
SPECS={'Diferença simples':(False,False),'Variação relativa':(True,False),'Diferença sazonal':(False,True),'Relativa e sazonal':(True,True)}
def safe_station(x):
    try:return station(x)
    except (ValueError, OverflowError, ZeroDivisionError) as e:
        return {"ADF p":np.nan,"KPSS p":np.nan,"Estacionária":False,"Avisos":"Teste inconclusivo: falha numérica "+type(e).__name__}

def write(df,name):
    df.to_csv(AOUT/(name+'.csv'),index=False,encoding='utf-8-sig');return df

def transform(s,key,spec):
    log,season=SPECS[spec]
    if log and (s.I<=0).any():raise ValueError('I não positiva')
    y=(100*np.log(s.I) if log else s.I).diff(); x=np.log1p(s[key]).diff()
    if season:y=y.diff(12);x=x.diff(12)
    return y,x

def station_label(st):
    if st['Estacionária']:return 'Sem indicação de não estacionariedade'
    if st.get('ADF p',1)>=.05 and st.get('KPSS p',1)<.05:return 'Indicação de não estacionariedade'
    return 'Inconclusiva'

def design_new(s,key,spec,p,q):
    y,x=transform(s,key,spec)
    X=pd.DataFrame({'const':1.},index=s.index) if SPECS[spec][1] else deterministics(s.index)
    for l in list(range(1,p+1))+[12]:X[f'I{l}']=y.shift(l)
    for l in range(1,q+1):X[f'D{l}']=x.shift(l)
    d=pd.concat([y.rename('y'),X],axis=1).iloc[25:].dropna().astype(float)
    return d

def fit_selected(s,key,spec):
    rows=[];cache={};mx=6 if len(s)>100 else 3
    for p in range(1,mx+1):
        for q in range(4):
            d=design_new(s,key,spec,p,q);n=len(d);k=len(d.columns)-1;X=d.drop(columns='y')
            if n-k<30 or n<3*k or np.linalg.matrix_rank(X)<k:continue
            m=OLS(d.y,X).fit();cache[p,q]=m;rows.append({'p próprio':p,'q exposição':q,'n comum':n,'k':k,'BIC':m.bic,'AIC':m.aic})
    cr=pd.DataFrame(rows)
    if cr.empty or not (cr['q exposição']>0).any():raise ValueError('Amostra/GL/design insuficiente')
    pos=cr[cr['q exposição']>0].sort_values(['BIC','p próprio','q exposição']).iloc[0]
    best=cr.sort_values(['BIC','p próprio','q exposição']).iloc[0]
    return cache[int(pos['p próprio']),int(pos['q exposição'])],cr,int(pos['p próprio']),int(pos['q exposição']),bool(best['q exposição']==0),float(pos.BIC-best.BIC)

def reasons_nat(r):
    problems=[]
    for k,label in [('Estacionária I','Estacionariedade da inadimplência'),('Estacionária D','Estacionariedade da exposição')]:
        if not r[k]:problems.append(label+' '+r[k+' status'].lower())
    for k,label in [('BG1 p','Autocorrelação curta'),('BG12 p','Autocorrelação até 12 meses'),('RESET p','Forma da equação (RESET)'),('CUSUM p','Instabilidade (CUSUM)')]:
        if r[k]<.05:problems.append(label)
    if r['Raiz própria']>=1:problems.append('Dinâmica autorregressiva instável')
    if abs(r['Δ soma influência'])>r['SE soma']:problems.append('Influência material de um mês')
    return '; '.join(problems) or 'Sem indicação nos diagnósticos examinados'

def run_national():
    raw=pd.read_parquet(PROC/'segunda_series_completas.parquet');keys=[c for c in raw if c!='I' and not c.startswith(('Súbitos |','Seca |'))];assert len(keys)==25
    rows=[];stations=[];criteria=[];co=[];residuals=[]
    for per,(ini,fim) in PERIODS.items():
        s=raw.loc[ini:fim]
        for spec in SPECS:
            for key in keys:
                common={'Período':per,'Unidade':'Brasil','Exposição':key,'Transformação':spec,'Família':'ADEQUACAO_NACIONAL','Modelo':'ADL BIC; datas comuns; I12','Unidade efeito':'variação logarítmica percentual de I' if SPECS[spec][0] else 'pontos percentuais de I'}
                y,x=transform(s,key,spec);sy=safe_station(y);sx=safe_station(x)
                for name,v,st in [('Inadimplência',y,sy),('Exposição',x,sx)]:stations.append({**common,'Série':name,**st,'Status':station_label(st),'n transformado':v.notna().sum(),'Variância':v.var(),'ACF1':acf(v.dropna(),nlags=1,fft=False)[1],'ACF12':acf(v.dropna(),nlags=12,fft=False)[12]})
                if s[key].isna().any() or (s[key]>0).sum()<12 or s[key].sum()<24:
                    rows.append({**common,'p':np.nan,'Diagnóstico favorável':False,'Motivos diagnósticos':'Excluído: ausente/constante/raro'});continue
                try:m,cr,p,q,qzero,bicdelta=fit_selected(s,key,spec)
                except ValueError as e:rows.append({**common,'p':np.nan,'Diagnóstico favorável':False,'Motivos diagnósticos':'Excluído: '+str(e)});continue
                criteria.extend([{**common,**v} for v in cr.to_dict('records')]);R=restrict(m,[f'D{l}' for l in range(1,q+1)]);hc=m.get_robustcov_results(cov_type='HAC',maxlags=12,use_correction=True,use_t=True);h3=m.get_robustcov_results(cov_type='HC3',use_t=True);v=R.sum(axis=0);sm=float(v@m.params);se=float(np.sqrt(v@hc.cov_params()@v));dg=diag(m);ii=dg.pop('Índice influente');keep=np.arange(m.nobs)!=ii;minus=OLS(m.model.endog[keep],m.model.exog[keep]).fit();delta=float(v@minus.params-sm);t=stats.t.ppf(.975,m.df_resid)
                r={**common,**dg,'Estacionária I':sy['Estacionária'],'Estacionária D':sx['Estacionária'],'Estacionária I status':station_label(sy),'Estacionária D status':station_label(sx),'p próprio':p,'q exposição':q,'q0 preferido':qzero,'BIC perda para ótimo':bicdelta,'n efetivo':int(m.nobs),'GL':int(m.df_resid),'Início amostra':str(m.model.data.row_labels.min().date()),'Fim amostra':str(m.model.data.row_labels.max().date()),'Soma coeficientes':sm,'SE soma':se,'IC baixo':sm-t*se,'IC alto':sm+t*se,'Δ soma influência':delta,'F HAC':float(hc.wald_test(R,use_f=True,scalar=True).statistic),'p':float(hc.wald_test(R,use_f=True,scalar=True).pvalue),'p clássico':float(m.wald_test(R,use_f=True,scalar=True).pvalue),'p HC3':float(h3.wald_test(R,use_f=True,scalar=True).pvalue)}
                r['Motivos diagnósticos']=reasons_nat(r);r['Diagnóstico favorável']=r['Motivos diagnósticos'].startswith('Sem indicação');r['Adequação e utilidade']=r['Diagnóstico favorável'] and not qzero;rows.append(r)
                for l in range(1,q+1):j=m.model.exog_names.index(f'D{l}');ci=hc.conf_int()[j];co.append({**common,'Lag':l,'Coeficiente':m.params.iloc[j],'IC baixo':ci[0],'IC alto':ci[1]})
                if key=='Total nacional':
                    for date,value in m.resid.items():residuals.append({**common,'Data':str(date.date()),'Resíduo':value})
            print('Nacional',per,spec,flush=True)
    df=adjusted(pd.DataFrame(rows),family_size=200)
    for col in ['p clássico','p HC3']:df['p BH '+col]=multipletests(df[col].fillna(1),method='fdr_bh')[1]
    write(df,'nacional');write(pd.DataFrame(stations),'estacionariedade');write(pd.DataFrame(criteria),'criterios');write(pd.DataFrame(co),'coeficientes');write(pd.DataFrame(residuals),'residuos_referencia');return df

def panel_new(d,key,spec):
    chunks=[]
    for uf,g in d.groupby('uf',sort=True):
        s=g.sort_values('data_base').set_index('data_base');y,x=transform(s,key,spec);dd=pd.DataFrame({'y':y})
        for l in [1,2,3,12]:dd[f'I{l}']=y.shift(l)
        for l in [1,2,3]:dd[f'D{l}']=x.shift(l)
        dd=dd.iloc[25:].dropna().astype(float);dd['uf']=uf;chunks.append(dd.reset_index().set_index(['uf','data_base']))
    dd=pd.concat(chunks).sort_index();assert dd.groupby(level=0).size().nunique()==1 and dd.index.get_level_values(0).nunique()==27
    return dd

def run_panel():
    raw=pd.read_parquet(PROC/'segunda_painel.parquet');rows=[];strows=[]
    for per,(ini,fim) in PERIODS.items():
        d=raw[raw.data_base.between(ini,fim)]
        for spec in SPECS:
            for key in EXPOS:
                common={'Período':per,'Unidade':'UF × mês','Exposição':key,'Transformação':spec,'Família':'ADEQUACAO_PAINEL','Modelo':'TWFE; lags próprios1,2,3,12; D1,2,3','Unidade efeito':'variação logarítmica percentual de I' if SPECS[spec][0] else 'pontos percentuais de I'}
                flags={'I':[],'D':[]}
                for uf,g in d.groupby('uf'):
                    s=g.sort_values('data_base').set_index('data_base');y,x=transform(s,key,spec)
                    for tag,values in [('I',y),('D',x)]:
                        st=safe_station(values);flags[tag].append(st['Estacionária']);strows.append({**common,'UF':uf,'Série':tag,**st,'Status':station_label(st)})
                dd=panel_new(d,key,spec);m=fit_panel(dd);C=dk(m,dd);cols=['D1','D2','D3'];F,pv=wald_cov(m,C,cols);v=restrict(m,cols).sum(axis=0);sm=float(v@m.params);se=float(np.sqrt(v@C@v));t=stats.t.ppf(.975,26)
                aux=dd.drop(columns='y').copy();aux['y']=m.resid.to_numpy()
                for l in [1,12]:aux[f'e{l}']=aux.y.groupby(level=0).shift(l)
                aux=aux.dropna();am=fit_panel(aux);ap=wald_cov(am,dk(am,aux),['e1','e12'])[1]
                loo=[]
                for uf in sorted(d.uf.unique()):mm=fit_panel(dd[dd.index.get_level_values(0)!=uf]);loo.append(float(v@mm.params))
                root=roots(m);fi=np.mean(flags['I']);fd=np.mean(flags['D']);infl=max(abs(np.array(loo)-sm));problems=[]
                if fi<.8:problems.append('Estacionariedade de I: menos de80% das UFs convergentes')
                if fd<.8:problems.append('Estacionariedade de D: menos de80% das UFs convergentes')
                if ap<.05:problems.append('Autocorrelação residual')
                if root>=1:problems.append('Dinâmica autorregressiva instável')
                if infl>se:problems.append('Influência material de uma UF')
                rows.append({**common,'n efetivo':int(m.nobs),'Meses efetivos':dd.index.get_level_values(1).nunique(),'Início amostra':str(dd.index.get_level_values(1).min().date()),'Fim amostra':str(dd.index.get_level_values(1).max().date()),'Proporção UF estacionária I':fi,'Proporção UF estacionária D':fd,'Raiz própria':root,'Autocorrelação p DK':ap,'LOO desvio máximo':infl,'Soma coeficientes':sm,'SE soma':se,'IC baixo':sm-t*se,'IC alto':sm+t*se,'F DK':F,'p':pv,'p DK6':wald_cov(m,dk(m,dd,6),cols)[1],'p cluster UF':wald_cov(m,cov_cluster(m,pd.factorize(dd.index.get_level_values(0))[0],use_correction=True),cols)[1],'Diagnóstico favorável':not problems,'Motivos diagnósticos':'; '.join(problems) or 'Sem indicação nos diagnósticos examinados','Limitação':'Viés dinâmico e exogeneidade não certificados; SPJ anterior preservado, não reaplicado como correção automática'})
            print('Painel',per,spec,flush=True)
    df=adjusted(pd.DataFrame(rows),family_size=32);write(df,'painel');write(pd.DataFrame(strows),'estacionariedade_uf');return df

def figures():
    import matplotlib.pyplot as plt
    r=pd.read_csv(AOUT/'nacional.csv');rows=r[(r.Exposição=='Total nacional') & r.p.notna()]
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    for ax,(per,g) in zip(axes,rows.groupby('Período',sort=False)):
        for i,(_,x) in enumerate(g.iterrows()):
            checks=[x['Estacionária I'],x['Estacionária D'],x['BG1 p']>=.05,x['BG12 p']>=.05,x['RESET p']>=.05,x['CUSUM p']>=.05,x['Raiz própria']<1,abs(x['Δ soma influência'])<=x['SE soma']]
            for j,good in enumerate(checks):ax.scatter(j,i,s=180,c='#2f8173' if good else '#c26249',marker='s')
        ax.set_yticks(range(len(g)),g.Transformação);ax.set_xticks(range(8),['I','D','BG1','BG12','RESET','CUSUM','Raiz','Influência'],rotation=45);ax.set_title(per);ax.set_xlim(-.5,7.5);ax.set_ylim(-.5,len(g)-.5)
    fig.suptitle('Referência nacional: verde = sem indicação; laranja = falha/inconclusão');fig.tight_layout();plt.show();plt.close(fig)
    for per,g in r[r.p.notna()].groupby('Período',sort=False):
        summary=g.groupby('Transformação').agg(Estimáveis=('p','size'),Diagnósticos=('Diagnóstico favorável','sum'),Sem_q0=('Adequação e utilidade','sum')).reindex(SPECS)
        ax=summary.plot.bar(figsize=(12,5),color=['#b8c6d6','#287c82','#17314d']);ax.set_title(per+' — adequação e utilidade são critérios distintos');ax.set_ylabel('Cenários');ax.tick_params(axis='x',rotation=15);plt.tight_layout();plt.show();plt.close()

def check():
    r=pd.read_csv(AOUT/'nacional.csv');p=pd.read_csv(AOUT/'painel.csv');cr=pd.read_csv(AOUT/'criterios.csv');checks=[]
    def c(name,val):
        if not val:raise AssertionError(name)
        checks.append({'Verificação':name,'Status':'passou'})
    c('200 hipóteses nacionais preservadas',len(r)==200);c('32 hipóteses painel preservadas',len(p)==32)
    for name,g in [('Nacional',r),('Painel',p)]:c('BH '+name,np.allclose(g['p BH'],multipletests(g.p.fillna(1),method='fdr_bh')[1]));c('Família '+name,(g['Família n']==len(g)).all())
    c('Amostra comum entre candidatos',cr.groupby(['Período','Exposição','Transformação'])['n comum'].nunique().eq(1).all())
    c('Datas iguais entre transformações nacionais',r[r.p.notna()].groupby(['Período','Exposição'])['Início amostra'].nunique().eq(1).all())
    c('Datas iguais entre transformações painel',p.groupby(['Período','Exposição'])['Início amostra'].nunique().eq(1).all())
    raw=pd.read_parquet(PROC/'segunda_series_completas.parquet');a=raw.iloc[:80].copy();b=a.copy();b.iloc[-1,b.columns.get_loc('I')]=99;b.iloc[-1,b.columns.get_loc('Total nacional')]=99999
    for spec in SPECS:
        X=design_new(a,'Total nacional',spec,2,2).drop(columns='y');Y=design_new(b,'Total nacional',spec,2,2).drop(columns='y');c('Sem variável contemporânea '+spec,np.allclose(X.iloc[-1],Y.iloc[-1]))
    c('Sem p na regra de diagnósticos',r[r.p.notna()].apply(lambda x:x['Diagnóstico favorável']==x['Motivos diagnósticos'].startswith('Sem indicação'),axis=1).all())
    c('Painel balanceado por transformação',p['n efetivo'].eq(p['Meses efetivos']*27).all())
    return write(pd.DataFrame(checks),'validacao')

def checkpoint_new():
    manifest={'status':'concluído','familias':{'nacional':200,'painel':32},'protocolo':sha(ROOT/'docs/adequacao_protocolo.md'),'codigo':sha(__file__),'entradas':{str(p.relative_to(ROOT)):sha(p) for p in [PROC/'segunda_series_completas.parquet',PROC/'segunda_painel.parquet']},'tabelas':{p.name:sha(p) for p in AOUT.glob('*.csv')}}
    (AOUT/'checkpoint_14.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
