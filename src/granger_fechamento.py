"""Granger condicional na equação; protocolo prévio, famílias42/126/168.

Entrada agregada conferida no checkpoint11. Não usa bases individuais nem
reestima05–14. Resultados pós-seleção BIC são apenas sensibilidade.
"""
from segunda_etapa import (ROOT, OLS, np, pd, stats, station, restrict, diag,
                           deterministics, multipletests, sha)
import json, warnings, platform, importlib.metadata

OUT = ROOT / 'outputs/tables/granger_fechamento'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = ROOT / 'outputs/tables/segunda_etapa/series_nacionais_agregadas.csv'
SOURCE_SHA = 'c613ebd61e25c05ebb4a4e0f3520c6570d673068d0b2ee2b6fc090468e1df679'
PERIODS = {'Pré-pandemia (até jan/2020)': ('2013-01-01','2020-01-01'),
           'Total (2013–2024)': ('2013-01-01','2024-12-01')}
SPECS = ['Principal sazonal fixa', 'Simples fixa com dummies',
         'Relativa sazonal fixa', 'Sazonal BIC']


def save(d, name):
    d.to_csv(OUT / (name+'.csv'), index=False, encoding='utf-8-sig')
    return d


def inputs():
    if sha(SOURCE) != SOURCE_SHA:
        raise ValueError('Série agregada diverge do checkpoint11; conferir origem antes de estimar.')
    s = pd.read_csv(SOURCE, parse_dates=['data']).set_index('data').sort_index()
    keys = ['Total nacional'] + [c for c in s if c.startswith(('Grupo |','Tipologia |'))]
    assert len(s)==144 and s.index.equals(pd.date_range('2013-01-01','2024-12-01',freq='MS'))
    assert len(keys)==21 and len([k for k in keys if k.startswith('Grupo |')])==4
    assert len([k for k in keys if k.startswith('Tipologia |')])==16
    assert np.isfinite(s[['I']+keys]).all().all() and (s[['I']+keys]>=0).all().all()
    assert (s.I>0).all()
    m=pd.read_csv(ROOT/'outputs/tables/ampliacao/classificacao_grupo_tipologia.csv')
    assert set(m.grupo_de_desastre)=={k.split(' | ')[1] for k in keys if k.startswith('Grupo |')}
    assert set(m.descricao_tipologia)=={k.split(' | ')[1] for k in keys if k.startswith('Tipologia |')}
    for prefix in ['Grupo |','Tipologia |']:
        assert s[[k for k in keys if k.startswith(prefix)]].sum(axis=1).eq(s['Total nacional']).all()
    return s, keys


def transform(s,key,spec):
    y=(100*np.log(s.I) if spec=='Relativa sazonal fixa' else s.I).diff()
    x=np.log1p(s[key]).diff()
    if spec!='Simples fixa com dummies':
        y=y.diff(12);x=x.diff(12)
    return y,x


def design(s,key,spec,p=3,q=3):
    y,x=transform(s,key,spec)
    X=deterministics(s.index) if spec=='Simples fixa com dummies' else pd.DataFrame({'const':1.},index=s.index)
    for lag in list(range(1,p+1))+[12]:X[f'I{lag}']=y.shift(lag)
    for lag in range(1,q+1):X[f'D{lag}']=x.shift(lag)
    return pd.concat([y.rename('y'),X],axis=1).iloc[25:].dropna().astype(float)


def eligible_design(d):
    n,k=len(d),d.shape[1]-1
    return n-k>=30 and n>=3*k and np.linalg.matrix_rank(d.drop(columns='y'))==k


def fit(s,key,spec):
    criteria=[]
    if spec!='Sazonal BIC':
        d=design(s,key,spec)
        if not eligible_design(d):raise ValueError('GL/amostra/posto insuficiente')
        return OLS(d.y,d.drop(columns='y')).fit(),3,3,None,np.nan,criteria
    cache={}
    for p in range(1,(6 if len(s)>100 else 3)+1):
        for q in range(4):
            d=design(s,key,spec,p,q)
            if not eligible_design(d):continue
            m=OLS(d.y,d.drop(columns='y')).fit();cache[p,q]=m
            criteria.append({'p próprio':p,'q exposição':q,'n comum':len(d),'k':d.shape[1]-1,'BIC':m.bic})
    cr=pd.DataFrame(criteria)
    if cr.empty or not (cr['q exposição']>0).any():raise ValueError('Seleção inviável')
    pos=cr[cr['q exposição']>0].sort_values(['BIC','p próprio','q exposição']).iloc[0]
    best=cr.sort_values(['BIC','p próprio','q exposição']).iloc[0]
    p,q=int(pos['p próprio']),int(pos['q exposição'])
    return cache[p,q],p,q,bool(best['q exposição']==0),float(pos.BIC-best.BIC),criteria


def stationary(v):
    try:
        st=station(v)
    except (ValueError,ZeroDivisionError,OverflowError) as e:
        st={'ADF p':np.nan,'KPSS p':np.nan,'Estacionária':False,'Avisos':'Falha numérica: '+type(e).__name__}
    if st['Estacionária']:status='Compatível com estacionariedade'
    elif st.get('ADF p',np.nan)>=.05 and st.get('KPSS p',np.nan)<.05:status='Indicação de não estacionariedade'
    elif not np.isfinite(st.get('ADF p',np.nan)) or not np.isfinite(st.get('KPSS p',np.nan)):status='Inviável/falha numérica'
    else:status='Inconclusiva'
    # Preserve actionable warnings, compress repeated API-transition messages.
    msg=st.get('Avisos','')
    st['Avisos']='; '.join(t for t in ['limite tabular' if 'look-up table' in msg else '',
                                   'transição de API registrada' if 'currently returns' in msg else '',
                                   msg if msg.startswith('Falha') else ''] if t)
    st['Status']=status;st['n transformado']=int(v.notna().sum())
    st['Variância']=float(v.var())
    return st


def stability(m):
    X=pd.DataFrame(m.model.exog,index=m.model.data.row_labels,columns=m.model.exog_names)
    post=pd.Series((X.index>='2020-03-01').astype(float),index=X.index)
    X['pos_const']=post
    dynamic=[c for c in m.model.exog_names if c.startswith(('I','D'))]
    for c in dynamic:X['pos_'+c]=X[c]*post
    if len(X)-X.shape[1]<30 or len(X)<3*X.shape[1] or np.linalg.matrix_rank(X)<X.shape[1]:
        return {'Estabilidade p':np.nan,'Interação exposição p':np.nan,'Estabilidade status':'Inviável: GL/posto'}
    mm=OLS(m.model.endog,X).fit().get_robustcov_results(cov_type='HAC',maxlags=12,use_correction=True,use_t=True)
    cols=['pos_const']+['pos_'+c for c in dynamic]
    names=list(X.columns)
    def w(cs):
        R=np.zeros((len(cs),len(names)))
        for i,c in enumerate(cs):R[i,names.index(c)]=1
        C=R@mm.cov_params()@R.T
        if np.linalg.matrix_rank(C)<len(cs):return np.nan,np.nan
        r=mm.wald_test(R,use_f=True,scalar=True);return float(r.statistic),float(r.pvalue)
    F,p=w(cols);FD,pD=w(['pos_'+c for c in dynamic if c.startswith('D')])
    return {'Estabilidade F':F,'Estabilidade p':p,'Interação exposição F':FD,'Interação exposição p':pD,
            'Estabilidade GL':len(X)-X.shape[1],'Estabilidade status':'Mudança nominal' if p<.05 else 'Sem rejeição nominal' if np.isfinite(p) else 'Inconclusiva'}


def reasons(r,expanded=False):
    out=[]
    for tag in ['I','D']:
        if not r['Estacionária '+tag]:out.append('Estacionariedade '+tag+': '+r['Status '+tag])
    for col,name in [('BG1 p','Autocorrelação curta'),('BG12 p','Autocorrelação até12'),('RESET p','Forma funcional'),('CUSUM p','CUSUM')]:
        if not np.isfinite(r[col]):out.append(name+' inconclusivo')
        elif r[col]<.05:out.append(name)
    if not np.isfinite(r['Raiz própria']) or r['Raiz própria']>=1:out.append('Dinâmica instável/inconclusiva')
    if not np.isfinite(r['Δ soma influência']) or abs(r['Δ soma influência'])>r['SE soma']:out.append('Influência material/inconclusiva')
    if expanded and r['Período'].startswith('Total'):
        if not np.isfinite(r['Estabilidade p']):out.append('Estabilidade adicional inconclusiva')
        elif r['Estabilidade p']<.05:out.append('Mudança após março2020')
    return '; '.join(out) or 'Sem indicação nos critérios examinados'


def adjustment(d):
    d=d.copy()
    for fam,n in [('PRINCIPAL',42),('SENSIBILIDADES',126)]:
        ix=d.Família==fam;assert ix.sum()==n;d.loc[ix,'Família n']=n
        for method,col in [('fdr_bh','p BH'),('fdr_by','p BY'),('holm','p Holm')]:
            d.loc[ix,col]=multipletests(d.loc[ix,'p'].fillna(1),method=method)[1]
        for pc in ['p clássico','p HC3']:
            d.loc[ix,'BH '+pc]=multipletests(d.loc[ix,pc].fillna(1),method='fdr_bh')[1]
    for method,col in [('fdr_bh','p BH global168'),('fdr_by','p BY global168'),('holm','p Holm global168')]:
        d[col]=multipletests(d.p.fillna(1),method=method)[1]
    for col,out in [('Estabilidade p','Estabilidade BH84'),('Interação exposição p','Interação exposição BH84')]:
        ix=d['Período'].str.startswith('Total');assert ix.sum()==84
        d.loc[ix,out]=multipletests(d.loc[ix,col].fillna(1),method='fdr_bh')[1]
    def category(r):
        if pd.isna(r.p):return 'Não estimado'
        if r['p BH']<.05:return 'Ajustado + triagem favorável' if r['Triagem ampliada'] else 'Ajustado com limitações'
        if r.p<.05:return 'Apenas nominal'
        return 'Não significativo'
    d['Categoria resultado']=d.apply(category,axis=1)
    d['Interpretação diagnóstica']=np.where(d['Triagem ampliada'],'Triagem favorável','Limitado/inconclusivo')
    return d


def run():
    raw,keys=inputs();rows=[];coverage=[];stations=[];levels=[];coeff=[];criteria=[];resids=[]
    for per,(ini,fim) in PERIODS.items():
        s=raw.loc[ini:fim]
        for key in keys:
            code={'Período':per,'Exposição':key,'Nível':'Referência' if key=='Total nacional' else key.split(' | ')[0],
                  'Unidade geográfica':'Brasil','Direção':'Desastres → inadimplência'}
            ok=s[key].notna().all() and (s[key]>0).sum()>=12 and s[key].sum()>=24 and s[key].nunique()>1
            coverage.append({**code,'Meses originais':len(s),'Meses positivos':int((s[key]>0).sum()),
                             'Protocolos':int(s[key].sum()),'Ausentes':int(s[key].isna().sum()),'Variância original':s[key].var(),
                             'Elegível exposição':ok,'Motivo exposição':'' if ok else 'Rara/constante: menos12 meses positivos ou24 protocolos'})
            for lab,v in [('I',s.I),('D',s[key])]:levels.append({**code,'Série':lab,**stationary(v)})
            for spec in SPECS:
                y,x=transform(s,key,spec);sy,sx=stationary(y),stationary(x)
                for lab,v,st in [('I',y,sy),('D',x,sx)]:stations.append({**code,'Especificação':spec,'Série':lab,**st})
                row={**code,'Especificação':spec,'Família':'PRINCIPAL' if spec==SPECS[0] else 'SENSIBILIDADES',
                     'Transformação':'ΔI; Δlog(1+D)' if spec==SPECS[1] else '100Δ12Δlog(I); Δ12Δlog(1+D)' if spec==SPECS[2] else 'Δ12ΔI; Δ12Δlog(1+D)',
                     'Modelo':'ADL fixo' if spec!=SPECS[3] else 'ADL BIC condicional à seleção',
                     'Controle sazonal':'11 dummies' if spec==SPECS[1] else 'Diferença sazonal',
                     'Estacionária I':sy['Estacionária'],'Estacionária D':sx['Estacionária'],'Status I':sy['Status'],'Status D':sx['Status'],
                     'p':np.nan,'p clássico':np.nan,'p HC3':np.nan,'Triagem básica':False,'Triagem ampliada':False,
                     'Estabilidade p':np.nan,'Interação exposição p':np.nan,'Motivos':'Exposição não elegível'}
                if not ok:rows.append(row);continue
                try:m,p,q,qzero,delta,cr=fit(s,key,spec)
                except ValueError as e:row['Motivos']=str(e);rows.append(row);continue
                criteria.extend([{**code,'Especificação':spec,**r} for r in cr])
                R=restrict(m,[f'D{l}' for l in range(1,q+1)])
                hac=m.get_robustcov_results(cov_type='HAC',maxlags=12,use_correction=True,use_t=True)
                hc3=m.get_robustcov_results(cov_type='HC3',use_t=True)
                if np.linalg.matrix_rank(R@hac.cov_params()@R.T)<q:row['Motivos']='Covariância HAC degenerada';rows.append(row);continue
                dg=diag(m);ii=dg.pop('Índice influente');v=R.sum(axis=0);sm=float(v@m.params);se=float(np.sqrt(v@hac.cov_params()@v));critical=stats.t.ppf(.975,m.df_resid)
                from statsmodels.stats.diagnostic import het_breuschpagan,het_arch,breaks_cusumolsresid,linear_reset
                from statsmodels.tsa.stattools import acf
                bp=het_breuschpagan(m.resid,m.model.exog);ar=het_arch(m.resid,nlags=3)
                cu=breaks_cusumolsresid(m.resid,ddof=len(m.params));re=linear_reset(m,power=2,test_type='fitted',use_f=True,cov_type='HC3')
                dg.update({'BP LM':bp[0],'BP F':bp[2],'BP F p':bp[3],'ARCH3 LM':ar[0],'ARCH3 F':ar[2],'ARCH3 F p':ar[3],
                           'CUSUM estatística':cu[0],'RESET F':float(re.statistic),'ACF1':acf(m.resid,nlags=1,fft=False)[1]})
                keep=np.arange(m.nobs)!=ii;minus=OLS(m.model.endog[keep],m.model.exog[keep]).fit()
                for lag in [1,12]:
                    from statsmodels.stats.diagnostic import acorr_breusch_godfrey
                    bg=acorr_breusch_godfrey(m,nlags=lag);dg[f'BG{lag} LM']=bg[0];dg[f'BG{lag} F']=bg[2];dg[f'BG{lag} F p']=bg[3]
                F=hac.wald_test(R,use_f=True,scalar=True)
                row.update({**dg,'p próprio':p,'q exposição':q,'q0 preferido':qzero,'ΔBIC ótimo':delta,
                            'n efetivo':int(m.nobs),'GL':int(m.df_resid),'k':len(m.params),
                            'Início amostra':str(m.model.data.row_labels.min().date()),'Fim amostra':str(m.model.data.row_labels.max().date()),
                            'F HAC':float(F.statistic),'p':float(F.pvalue),'p clássico':float(m.wald_test(R,use_f=True,scalar=True).pvalue),
                            'p HC3':float(hc3.wald_test(R,use_f=True,scalar=True).pvalue),'Soma coeficientes':sm,'SE soma':se,
                            'IC baixo':sm-critical*se,'IC alto':sm+critical*se,'Δ soma influência':float(v@minus.params-sm),
                            'Unidade efeito':'variação logarítmica percentual de I' if spec==SPECS[2] else 'pontos percentuais de I',
                            'Estabilidade status':'Não aplicável: março2020 fora do pré'})
                if per.startswith('Total'):row.update(stability(m))
                basic=reasons(row);row['Triagem básica']=basic.startswith('Sem indicação')
                row['Motivos básicos']=basic;row['Motivos']=reasons(row,True)
                row['Triagem ampliada']=row['Motivos'].startswith('Sem indicação');rows.append(row)
                for lag in range(1,q+1):
                    j=m.model.exog_names.index(f'D{lag}');ci=hac.conf_int()[j]
                    coeff.append({**code,'Especificação':spec,'Lag':lag,'Coeficiente':m.params.iloc[j],'IC baixo':ci[0],'IC alto':ci[1]})
                if key in ['Total nacional','Tipologia | Onda de Frio'] and spec==SPECS[0]:
                    resids.extend([{**code,'Data':str(date.date()),'Resíduo':value} for date,value in m.resid.items()])
        print('Concluído',per,flush=True)
    r=adjustment(pd.DataFrame(rows));save(r,'resultados');save(pd.DataFrame(coverage),'cobertura');save(pd.DataFrame(stations),'estacionariedade')
    save(pd.DataFrame(levels),'estacionariedade_nivel');save(pd.DataFrame(coeff),'coeficientes');save(pd.DataFrame(criteria),'criterios_bic');save(pd.DataFrame(resids),'residuos_referencia')
    summary=r.groupby(['Família','Período'],sort=False).agg(Planejados=('p','size'),Estimáveis=('p','count'),
        Nominais=('p',lambda x:(x<.05).sum()),BH=('p BH',lambda x:(x<.05).sum()),BY=('p BY',lambda x:(x<.05).sum()),Holm=('p Holm',lambda x:(x<.05).sum()),
        Triagem_básica=('Triagem básica','sum'),Triagem_ampliada=('Triagem ampliada','sum')).reset_index()
    save(summary,'resumo')
    matrix=pd.DataFrame(coverage).merge(r[r.Família=='PRINCIPAL'],on=list(coverage[0])[:5],how='left',validate='one_to_one')
    save(matrix,'matriz42')
    versions=[{'Pacote':k,'Versão':importlib.metadata.version(k)} for k in ['numpy','pandas','scipy','statsmodels','matplotlib','nbformat','IPython']]
    save(pd.DataFrame([{'Pacote':'Python','Versão':platform.python_version()}]+versions),'ambiente')
    return r


def figures(r):
    import matplotlib.pyplot as plt
    main=r[(r.Família=='PRINCIPAL')&r.p.notna()]
    for per,g in main.groupby('Período',sort=False):
        fig,ax=plt.subplots(figsize=(11,8));y=np.arange(len(g));ax.errorbar(g['Soma coeficientes'],y,
            xerr=[g['Soma coeficientes']-g['IC baixo'],g['IC alto']-g['Soma coeficientes']],fmt='o',capsize=3,color='#237b80')
        ax.axvline(0,color='gray');ax.set_yticks(y,g.Exposição);ax.set_xlabel('Soma dos lags: pp por Δ12Δlog(1+D); IC95% HAC pontual');ax.set_title(per+' — principal fixa, associação condicional')
        plt.tight_layout();plt.show();plt.close(fig)
    z=r.groupby(['Especificação','Período']).agg(Favoráveis=('Triagem ampliada','sum')).unstack().fillna(0)
    z.plot.bar(figsize=(11,5));plt.ylabel('Cenários com triagem ampliada favorável');plt.xticks(rotation=15);plt.tight_layout();plt.show();plt.close()


def checkpoint():
    from executar_granger_fechamento import notebook_source
    d={'status':'executado','etapa':15,'entradas':{str(SOURCE.relative_to(ROOT)):sha(SOURCE),
        'outputs/tables/ampliacao/classificacao_grupo_tipologia.csv':sha(ROOT/'outputs/tables/ampliacao/classificacao_grupo_tipologia.csv')},
       'codigo':{p:sha(ROOT/p) for p in ['src/granger_fechamento.py','src/segunda_etapa.py','src/verificar_granger_fechamento.py','src/executar_granger_fechamento.py','src/executar_notebooks_categorias.py']},
       'notebook_codigo':notebook_source(),
       'protocolo':sha(ROOT/'docs/granger_fechamento_protocolo.md'),
       'tabelas':{p.name:sha(p) for p in sorted(OUT.glob('*.csv'))}}
    (OUT/'checkpoint_15.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
