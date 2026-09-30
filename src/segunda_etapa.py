"""Extensão informada: regras em docs/segunda_etapa_protocolo.md. Sem entradas individuais publicadas."""
from pathlib import Path
import hashlib, json, warnings, sys
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.api import OLS
from statsmodels.stats.diagnostic import acorr_breusch_godfrey, het_breuschpagan, het_arch, breaks_cusumolsresid, linear_reset
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.sandwich_covariance import cov_nw_groupsum, cov_cluster
from statsmodels.tsa.stattools import adfuller, kpss, zivot_andrews, acf
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/tables/segunda_etapa';OUT.mkdir(parents=True,exist_ok=True)
PROC=ROOT/'data/processed';PROC.mkdir(parents=True,exist_ok=True)
PERIODS={'Total (2013–2024)':('2013-01-01','2024-12-01'), 'Pré-pandemia (até jan/2020)':('2013-01-01','2020-01-01')}
EXPOS=['Clima | Protocolos','Clima | Municípios','Clima | Deslocamento','Clima | Habitações']
SEED=20260930

def save(df,name):
    df.to_csv(OUT/(name+'.csv'),index=False,encoding='utf-8-sig');return df

def read(name):return pd.read_csv(OUT/(name+'.csv'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def checkpoint(stage):
    files=list(OUT.glob('*.csv'))
    manifest={'etapa':stage,'status':'executada','entradas':{p.name:sha(p) for p in [PROC/'df_tcc_2013_2024.parquet',next((ROOT/'data/raw/atlas_desastres').glob('*.csv'))]},'protocolo':sha(ROOT/'docs/segunda_etapa_protocolo.md'),'codigo':sha(__file__),'tabelas':{p.name:sha(p) for p in files}}
    (OUT/f'checkpoint_{stage}.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))

def credit():
    d=pd.read_parquet(PROC/'df_tcc_2013_2024.parquet');d['data_base']=pd.to_datetime(d.data_base)
    assert len(d)==3888 and not d.duplicated(['uf','data_base']).any()
    d['I']=100*d.carteira_inadimplencia_total/d.carteira_ativa_total
    return d

def historical_series():
    d=credit();g=d.groupby('data_base');s=g[['carteira_ativa_total','carteira_inadimplencia_total']].sum()
    s=pd.DataFrame({'I':100*s.carteira_inadimplencia_total/s.carteira_ativa_total})
    s['Total nacional']=g.total_desastres.sum()
    # Use mapping from existing original categories, never rename source categories.
    from analise_categorias import slug
    m=pd.read_csv(ROOT/'outputs/tables/ampliacao/classificacao_grupo_tipologia.csv')
    for col,nivel,pref in [('grupo_de_desastre','Grupo','grupo_'),('descricao_tipologia','Tipologia','tipo_')]:
        for cat in sorted(m[col].unique()):s[nivel+' | '+cat]=g[pref+slug(cat)].sum()
    assert len(s)==144 and len(s.columns)==22
    s.to_parquet(PROC/'segunda_series_historicas.parquet');return s

def previous():
    d=pd.read_csv(ROOT/'outputs/tables/ampliacao/granger_selecionados.csv');u=d[d['Direção']=='Desastres → inadimplência'].drop_duplicates(['Período','Chave','Especificação','Direção','Defasagem']);z=u[u.p<.05]
    vals=[len(u),len(z),int((u['p BH']<.05).sum()),int((z['Portmanteau p']<.05).sum()),int(z['Diagnóstico favorável'].sum())]
    assert vals==[235,29,0,18,4]
    return save(pd.DataFrame({'Métrica':['Hipóteses distintas','Rejeições nominais','Rejeições BH','Nominais com autocorrelação sistema','Nominais com triagem favorável'],'Valor':vals}),'comparacao_anterior')

def station(x,det='c'):
    x=pd.Series(x).dropna()
    if len(x)<30 or x.nunique()<2:return {'ADF p':np.nan,'KPSS p':np.nan,'Estacionária':False,'Avisos':'curta/constante'}
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter('always');a=adfuller(x,regression=det,autolag='BIC',maxlag=min(12,len(x)//4));k=kpss(x,regression=det,nlags='auto')
    return {'ADF estatística':a[0],'ADF p':a[1],'ADF lag':a[2],'ADF n':a[3],'KPSS estatística':k[0],'KPSS p':k[1],'KPSS lag':k[2],'KPSS limite':'>=0.10' if k[1]==.1 else '<=0.01' if k[1]==.01 else 'interpolado','Estacionária':bool(a[1]<.05 and k[1]>=.05),'Avisos':' | '.join(str(w.message) for w in ws)}

def deterministics(index,pandemic=False):
    X=pd.DataFrame({'const':1.},index=index)
    for m in range(2,13):X[f'mes{m}']=(index.month==m).astype(float)
    if pandemic:X['pandemia']=((index>='2020-03-01')&(index<='2021-02-01')).astype(float)
    return X

def design(raw,key,p,q,pandemic=False,start=12):
    y=raw.I.diff();x=np.log1p(raw[key]).diff();X=deterministics(raw.index,pandemic)
    for l in list(range(1,p+1))+[12]:X[f'I{l}']=y.shift(l)
    for l in range(1,q+1):X[f'D{l}']=x.shift(l)
    # First difference consumes one month; common start means 12 transformed lags.
    mask=np.arange(len(raw))>=start+1
    dd=pd.concat([y.rename('y'),X],axis=1).loc[mask].dropna()
    return dd.y.astype(float),dd.drop(columns='y').astype(float)

def select(raw,key,pandemic=False):
    mx=6 if len(raw)>100 else 3;rows=[];cache={}
    for p in range(1,mx+1):
        for q in range(4):
            y,X=design(raw,key,p,q,pandemic);n,k=X.shape
            if n-k<30 or n<3*k or np.linalg.matrix_rank(X)<k:continue
            model=OLS(y,X).fit();cache[p,q]=model
            rows.append({'p próprio':p,'q exposição':q,'n comum':n,'k':k,'AIC':model.aic,'BIC':model.bic})
    ct=pd.DataFrame(rows)
    if ct.empty or not (ct['q exposição']>0).any():raise ValueError('Graus de liberdade/design')
    z=ct[ct['q exposição']>0].sort_values(['BIC','p próprio','q exposição']).iloc[0]
    opt=ct.sort_values(['BIC','p próprio','q exposição']).iloc[0]
    return cache[int(z['p próprio']),int(z['q exposição'])],ct,bool(opt['q exposição']==0),int(z['p próprio']),int(z['q exposição'])

def restrict(model,cols):
    R=np.zeros((len(cols),len(model.params)))
    for j,c in enumerate(cols):R[j,model.model.exog_names.index(c)]=1
    return R

def roots(model):
    co=np.zeros(12)
    for l in range(1,13):co[l-1]=model.params.get(f'I{l}',0)
    A=np.vstack([co,np.hstack([np.eye(11),np.zeros((11,1))])]);return max(abs(np.linalg.eigvals(A)))

def diag(model):
    r={'BG1 p':acorr_breusch_godfrey(model,nlags=1)[1],'BG12 p':acorr_breusch_godfrey(model,nlags=12)[1],'BP p':het_breuschpagan(model.resid,model.model.exog)[1],'ARCH3 p':het_arch(model.resid,nlags=3)[1],'CUSUM p':breaks_cusumolsresid(model.resid,ddof=len(model.params))[1],'RESET p':linear_reset(model,power=2,test_type='fitted',use_f=True,cov_type='HC3').pvalue,'ACF12':acf(model.resid,nlags=12,fft=False)[12],'Raiz própria':roots(model)}
    inf=model.get_influence();i=int(np.argmax(inf.cooks_distance[0]));r.update({'Cook máximo':inf.cooks_distance[0][i],'Mês influente':str(model.model.data.row_labels[i].date()),'Índice influente':i})
    return r

def adjusted(df,pcol='p',family_size=None):
    n=family_size or len(df);vals=df[pcol].fillna(1).to_numpy();vals=np.r_[vals,np.ones(n-len(vals))]
    df['Família n']=n
    for method,col in [('fdr_bh','p BH'),('fdr_by','p BY'),('holm','p Holm')]:df[col]=multipletests(vals,method=method)[1][:len(df)]
    return df

def classify(r):
    if pd.isna(r.get('p')):return 'Excluído / inviável'
    if not r.get('Diagnóstico favorável',False):return 'Diagnósticos inadequados ou inconclusivos'
    if r.get('p BH',1)<.05:return 'Ajustado + diagnósticos favoráveis'
    if r['p']<.05:return 'Apenas nominal'
    return 'Não significativo'

def national(keys=None,extra=False):
    raw=pd.read_parquet(PROC/('segunda_series_completas.parquet' if extra else 'segunda_series_historicas.parquet'))
    keys=keys or [c for c in raw if c!='I'];rows=[];criteria=[];coeff=[];st=[];breaks=[];sens=[]
    for per,(ini,fim) in PERIODS.items():
        s=raw.loc[ini:fim]
        for key in keys:
            common={'Período':per,'Unidade':'Brasil','Exposição':key,'Indicador':'Protocolos' if key not in EXPOS else key.split(' | ')[1],'Transformação':'ΔI; Δlog(1+exposição)','Família':'NACIONAL','Modelo':'ADL BIC + 11 dummies + I12'}
            sy=station(s.I.diff());sx=station(np.log1p(s[key]).diff())
            for lab,rr in [('ΔI',sy),('Δlog exposição',sx)]:st.append({**common,'Série':lab,**rr})
            if key=='Total nacional':
                for det in ['c','ct']:
                    with warnings.catch_warnings(record=True):
                        za=zivot_andrews(s.I,trim=.15,maxlag=6,regression=det,autolag='BIC')
                    breaks.append({'Período':per,'Determinística':det,'ZA estatística':za[0],'ZA p':za[1],'ZA lag':za[3],'Quebra estimada':str(s.index[za[4]].date()),'Nota':'H0 raiz unitária; data estimada não prova ruptura causal'})
            if s[key].isna().any() or (s[key]>0).sum()<12 or s[key].sum()<24:
                rows.append({**common,'p':np.nan,'Diagnóstico favorável':False,'Motivo':'Ausentes/constante/rara'});continue
            for pan in [False,True] if len(s)>100 else [False]:
                try:model,ct,qzero,p,q=select(s,key,pan)
                except ValueError as e:
                    rows.append({**common,'p':np.nan,'Diagnóstico favorável':False,'Motivo':str(e)});continue
                cc={**common,'Família':'DETERMINISTICAS' if pan else 'NACIONAL','Modelo':common['Modelo']+(' + janela pandemia' if pan else ''),'p próprio':p,'q exposição':q,'q0 preferido':qzero,'n efetivo':int(model.nobs),'GL':int(model.df_resid),'Início amostra':str(model.model.data.row_labels.min().date()),'Fim amostra':str(model.model.data.row_labels.max().date())}
                criteria.extend([{**cc,**a} for a in ct.to_dict('records')])
                cols=[f'D{l}' for l in range(1,q+1)];R=restrict(model,cols);hac=model.get_robustcov_results(cov_type='HAC',maxlags=12,use_correction=True,use_t=True);hc=model.get_robustcov_results(cov_type='HC3',use_t=True)
                f=model.wald_test(R,use_f=True,scalar=True);rh=hac.wald_test(R,use_f=True,scalar=True)
                dg=diag(model);ii=dg.pop('Índice influente');keep=np.arange(model.nobs)!=ii;minus=OLS(model.model.endog[keep],model.model.exog[keep]).fit()
                v=R.sum(axis=0);sm=float(v@model.params);se=float(np.sqrt(v@hac.cov_params()@v));critical=stats.t.ppf(.975,model.df_resid);delta=float(v@minus.params-sm)
                good=sy['Estacionária'] and sx['Estacionária'] and dg['BG1 p']>=.05 and dg['BG12 p']>=.05 and dg['CUSUM p']>=.05 and dg['RESET p']>=.05 and dg['Raiz própria']<1 and not qzero and abs(delta)<=se
                rows.append({**cc,**dg,'F clássico':float(f.statistic),'p clássico':float(f.pvalue),'F HAC':float(rh.statistic),'p':float(rh.pvalue),'p HC3':float(hc.wald_test(R,use_f=True,scalar=True).pvalue),'Soma coeficientes':sm,'SE soma':se,'IC baixo':sm-critical*se,'IC alto':sm+critical*se,'Unidade efeito':'pp de ΔI por unidade de Δlog exposição; soma de lags, não IRF','Soma sem mês influente':sm+delta,'Δ soma influência':delta,'Estacionária I':sy['Estacionária'],'Estacionária D':sx['Estacionária'],'Diagnóstico favorável':bool(good),'Motivo':''})
                for l in cols:
                    i=model.model.exog_names.index(l);ci=hac.conf_int()[i];coeff.append({**cc,'Termo':l,'Coeficiente':model.params[l],'IC baixo':ci[0],'IC alto':ci[1],'p lag HAC':hac.pvalues[i]})
                if key=='Total nacional' and not pan:
                    X=pd.DataFrame(model.model.exog,index=model.model.data.row_labels,columns=model.model.exog_names);post=(X.index>='2020-03-01').astype(float)
                    for c in ['I1']+cols:X['pos_'+c]=X[c]*post
                    if len(s)>100:
                        mm=OLS(model.model.endog,X).fit();tt=mm.get_robustcov_results(cov_type='HAC',maxlags=12,use_correction=True).wald_test(restrict(mm,['pos_'+c for c in ['I1']+cols]),use_f=True,scalar=True)
                        sens.append({**cc,'Estabilidade pós-março2020 p':float(tt.pvalue),'Nota':'interações limitadas, diagnóstico exploratório'})
    rr=pd.DataFrame(rows)
    tag='exposicao' if extra else 'historico'
    save(rr,'nacional_'+tag+'_bruto');save(pd.DataFrame(criteria),'criterios_'+tag);save(pd.DataFrame(coeff),'coeficientes_'+tag);save(pd.DataFrame(st),'estacionariedade_'+tag)
    if breaks:save(pd.DataFrame(breaks),'quebras')
    if sens:save(pd.DataFrame(sens),'estabilidade_interacoes')
    combine_national();checkpoint('11' if extra else '10');return read('nacional')

def combine_national():
    parts=[read('nacional_historico_bruto')]
    if (OUT/'nacional_exposicao_bruto.csv').exists():parts.append(read('nacional_exposicao_bruto'))
    allr=pd.concat(parts,ignore_index=True);result=[]
    for fam,n in [('NACIONAL',50),('DETERMINISTICAS',25)]:
        g=allr[allr.Família==fam].copy();g=adjusted(g,family_size=n)
        for pc,suf in [('p clássico','clássico'),('p HC3','HC3')]:
            if pc in g:g['p BH '+suf]=multipletests(np.r_[g[pc].fillna(1),np.ones(n-len(g))],method='fdr_bh')[1][:len(g)]
        result.append(g)
    z=pd.concat(result,ignore_index=True);z['Categoria resultado']=z.apply(classify,axis=1);save(z,'nacional')


def atlas():
    a=pd.read_csv(next((ROOT/'data/raw/atlas_desastres').glob('*.csv')),sep=';',encoding='latin1',low_memory=False)
    a['date']=pd.to_datetime(a.Data_Evento,format='%d/%m/%Y');a=a[a.date.dt.year.between(2013,2024)].copy();a['mes']=a.date.dt.to_period('M').dt.to_timestamp();a['uf']=a.Sigla_UF.str.strip();a['code']=a.Cod_Cobrade.astype(str).str.replace(r'\.0$','',regex=True).str.zfill(5)
    a['clima']=a.code.str[:2].isin(['12','13','14']);a['subito']=a.code.str[:2].isin(['12','13']);a['seca']=a.code.isin(['14110','14120'])
    return a

def exposure():
    a=atlas();grid=credit().set_index(['uf','data_base']).sort_index();idx=grid.index
    old=pd.read_csv(ROOT/'outputs/tables/ampliacao/auditoria.csv');assert sha(next((ROOT/'data/raw/atlas_desastres').glob('*.csv')))==old.iloc[0]['Resultado']
    fields=['DH_DESABRIGADOS','DH_DESALOJADOS','DM_Uni Habita Danificadas','DM_Uni Habita Destruidas','PEPR_total_privado'];audit=[];annual=[]
    for c in fields+[x for x in a if x.startswith('PEPR_') and '(R$)' in x]:
        orig=a[c].astype('string');num=pd.to_numeric(orig.str.replace('.','',regex=False).str.replace(',','.',regex=False) if orig.str.contains(',',na=False).any() else orig,errors='coerce');bad=a[c].notna()&num.isna();a[c]=num
        audit.append({'Campo':c,'Registros':len(a),'Ausentes':num.isna().sum(),'Conversão inválida':bad.sum(),'Negativos':(num<0).sum(),'Zeros informados':(num==0).sum(),'Mediana':num.median(),'Q99':num.quantile(.99),'Máximo':num.max(),'Participação máximo':num.max()/num.sum() if num.sum()>0 else np.nan})
        for year,g in a.groupby(a.date.dt.year):annual.append({'Ano':year,'Campo':c,'Cobertura':g[c].notna().mean(),'Zeros':(g[c]==0).mean(),'Soma reportada':g[c].sum(min_count=1)})
        if bad.any() or (num<0).any():raise ValueError('Campo inválido '+c)
    a['deslocamento']=a[['DH_DESABRIGADOS','DH_DESALOJADOS']].sum(axis=1,min_count=2)
    a['habitacoes']=a[['DM_Uni Habita Danificadas','DM_Uni Habita Destruidas']].sum(axis=1,min_count=2)
    cl=a[a.clima];cov=[];ufcov=[];out=pd.DataFrame(index=idx);keys=['uf','mes']
    out[EXPOS[0]]=cl.groupby(keys).size().reindex(idx,fill_value=0)
    out[EXPOS[1]]=cl.groupby(keys).Cod_IBGE_Mun.nunique().reindex(idx,fill_value=0)
    for c,key in [('deslocamento',EXPOS[2]),('habitacoes',EXPOS[3])]:
        gr=cl.groupby(keys)[c];z=gr.sum(min_count=1);missing=gr.apply(lambda x:x.isna().any());z.loc[missing]=np.nan
        out[key]=z.reindex(idx);has=cl.groupby(keys).size().reindex(idx,fill_value=0)>0;out.loc[~has,key]=0
        cov.append({'Exposição':key,'Cobertura protocolos':cl[c].notna().mean(),'Cobertura células':out[key].notna().mean(),'Meses nacionais completos':int(out[key].groupby(level=1).apply(lambda x:x.notna().all()).sum()),'Zeros não distinguíveis de omissão':'zeros mantidos como reportados; completude real não certificada','Elegível':bool(cl[c].notna().mean()>=.95 and out[key].notna().mean()>=.95 and out[key].groupby(level=1).apply(lambda x:x.notna().all()).all())})
        for uf,g in cl.groupby('uf'):ufcov.append({'UF':uf,'Exposição':key,'Cobertura protocolos':g[c].notna().mean(),'Total registros':len(g)})
    for mask,name,field in [(a.subito,'Súbitos | Municípios','Cod_IBGE_Mun'),(a.seca,'Seca | Protocolos',None)]:
        g=a[mask].groupby(keys);out[name]=(g[field].nunique() if field else g.size()).reindex(idx,fill_value=0)
    out['I']=grid.I;out.reset_index().to_parquet(PROC/'segunda_painel.parquet',index=False)
    national=pd.read_parquet(PROC/'segunda_series_historicas.parquet')
    for key in out.columns:
        if key=='I':continue
        national[key]=out[key].groupby(level=1).apply(lambda v:v.sum() if v.notna().all() else np.nan)
    national.to_parquet(PROC/'segunda_series_completas.parquet')
    classified=a.groupby(['code','grupo_de_desastre','descricao_tipologia','clima','subito','seca']).size().reset_index(name='Protocolos');save(classified,'classificacao_climatica')
    private=[x for x in a if x.startswith('PEPR_') and '(R$)' in x];components=a[private].sum(axis=1,min_count=len(private));dif=a.PEPR_total_privado-components
    save(pd.DataFrame([{'Campo':'PEPR_total_privado','Registros comparáveis':dif.notna().sum(),'Diferenças acima R$1':(dif.abs()>1).sum(),'Diferença máxima':dif.abs().max(),'Inferência':'Excluído: mês-base/correção desta versão não confirmados; não deflacionado novamente'}]),'monetarios')
    reg=pd.to_datetime(a.Data_Registro,format='%d/%m/%Y',errors='coerce');delay=(reg-a.date).dt.days
    save(pd.DataFrame([{'n':len(a),'Data registro ausente/inválida':reg.isna().sum(),'Registro anterior ao evento':(delay<0).sum(),'Mediana dias':delay.median(),'Q90 dias':delay.quantile(.9),'Q99 dias':delay.quantile(.99),'Proporção registrado depois mês evento':(reg.dt.to_period('M')>a.date.dt.to_period('M')).mean(),'Limitação':'Data registro não é vintage de publicação/revisão; pseudo-OOS revisado'}]),'disponibilidade_atlas')
    save(pd.DataFrame(audit),'auditoria_exposicao');save(pd.DataFrame(annual),'cobertura_ano');save(pd.DataFrame(cov),'viabilidade_exposicao');save(pd.DataFrame(ufcov),'cobertura_uf');save(national.reset_index().rename(columns={'data_base':'data'}),'series_nacionais_agregadas')
    save(national[EXPOS].corr().rename_axis('Indicador').reset_index(),'correlacao_indicadores')
    # Aggregate consistency and overlap warning only, no protocol exports.
    save(pd.DataFrame([{'Deslocamento ambos campos positivos':int(((cl.DH_DESABRIGADOS>0)&(cl.DH_DESALOJADOS>0)).sum()),'Habitações ambos campos positivos':int(((cl['DM_Uni Habita Danificadas']>0)&(cl['DM_Uni Habita Destruidas']>0)).sum()),'Nota':'Não é possível certificar pessoas/imóveis únicos entre protocolos; não somar aos totais'}]),'sobreposicoes')
    return read('auditoria_exposicao'),read('viabilidade_exposicao')

def figura_nacional(r):
    import matplotlib.pyplot as plt
    for per,g in r[r.Família=='NACIONAL'].groupby('Período'):
        g=g.dropna(subset=['Soma coeficientes']);fig,ax=plt.subplots(figsize=(11,max(4,.36*len(g))))
        y=np.arange(len(g));ax.errorbar(g['Soma coeficientes'],y,xerr=[g['Soma coeficientes']-g['IC baixo'],g['IC alto']-g['Soma coeficientes']],fmt='o',color='#216477',capsize=3)
        ax.axvline(0,color='gray');ax.set_yticks(y,g.Exposição);ax.set_xlabel('Soma dos coeficientes (pp por unidade de Δlog exposição); IC95% HAC pontual');ax.set_title(per+' — ADL; associações condicionais');fig.tight_layout();plt.show();plt.close(fig)

def figura_exposicao():
    import matplotlib.pyplot as plt
    s=pd.read_parquet(PROC/'segunda_series_completas.parquet');fig,axes=plt.subplots(4,1,figsize=(12,10),sharex=True)
    for ax,key in zip(axes,EXPOS):ax.plot(s.index,s[key],color='#216477');ax.set_title(key);ax.grid(alpha=.2)
    fig.suptitle('Medidas climáticas nacionais — escalas distintas; registros, não pessoas únicas');fig.tight_layout();plt.show();plt.close(fig)

def ty(keys,extra=False):
    from statsmodels.tsa.api import VAR
    s=pd.read_parquet(PROC/('segunda_series_completas.parquet' if extra else 'segunda_series_historicas.parquet'));nr=read('nacional');rows=[]
    for key in keys:
        for per,(ini,fim) in PERIODS.items():
            base={'Período':per,'Exposição':key,'Família':'TY','d_max':1,'p':np.nan,'Diagnóstico favorável':False}
            z=nr[(nr.Exposição==key)&(nr.Período==per)&(nr.Família=='NACIONAL')].iloc[0]
            if not bool(z.get('Estacionária I',False)) or not bool(z.get('Estacionária D',False)) or z.get('BG1 p',0)<.05 or z.get('BG12 p',0)<.05 or z.get('Raiz própria',2)>=1:
                rows.append({**base,'Motivo':'Gate: integração/dinâmica ADL inadequada ou inconclusiva; TY não usado para resgate'});continue
            raw=s.loc[ini:fim];yy=pd.DataFrame({'I':raw.I,'D':np.log1p(raw[key])}).astype(float);mx=6 if len(raw)>100 else 3;ex=deterministics(raw.index).drop(columns='const');cs=[]
            for k in range(1,mx+1):
                # All candidate VARs share target dates starting at mx+1.
                mm=VAR(yy.iloc[mx+1-k:],exog=ex.iloc[mx+1-k:]).fit(k,trend='c');cs.append((mm.bic,k))
            k=min(cs)[1];model=VAR(yy,exog=ex).fit(k+1,trend='c');port=model.test_whiteness(nlags=12,adjusted=True)
            X=deterministics(yy.index)
            for l in range(1,k+2):
                X[f'I{l}']=yy.I.shift(l);X[f'D{l}']=yy.D.shift(l)
            dd=pd.concat([yy.I.rename('y'),X],axis=1).iloc[k+1:];m=OLS(dd.y,dd.drop(columns='y')).fit();R=restrict(m,[f'D{l}' for l in range(1,k+1)]);w=m.wald_test(R,use_f=False,scalar=True)
            rows.append({**base,'k':k,'Lags totais':k+1,'Restrições':'D1..Dk, sem restringir lag adicional','Wald chi2':float(w.statistic),'p':float(w.pvalue),'n efetivo':int(m.nobs),'Portmanteau p':float(port.pvalue),'Diagnóstico favorável':bool(port.pvalue>=.05),'Motivo':'Robustez em níveis: integração limite I(1); raízes unitárias não avaliadas como instabilidade estacionária'})
    if extra and (OUT/'ty.csv').exists():rows=read('ty').drop(columns=['p BH','p BY','p Holm','Família n','Categoria resultado'],errors='ignore').to_dict('records')+rows
    r=adjusted(pd.DataFrame(rows),family_size=4);r['Categoria resultado']=r.apply(classify,axis=1);return save(r,'ty')

def decisions():
    r=read('nacional');fav=r[(r.Família=='NACIONAL')&r['Diagnóstico favorável']]
    return save(pd.DataFrame([{'Procedimento':'Bootstrap temporal H0','Decisão':'Não aplicado','Justificativa':'Teste condicional à seleção; bootstrap defensável exigiria reexecutar seleção e validar dinâmica. Não usado como correção automática dos modelos reprovados.'},{'Procedimento':'Simulação de poder','Decisão':'Não aplicada','Justificativa':'Não atribuir tamanho/poder confiável a um DGP escolhido de modelos com diagnóstico inadequado; intervalos e OOS explicitam incerteza.'},{'Procedimento':'Controles econômicos adicionais','Decisão':'Não incluídos','Justificativa':'Não disponíveis na entrada com cobertura oficial compatível; choques comuns no painel não substituem confundidores específicos de UF.'},{'Procedimento':'GMM','Decisão':'Não aplicado','Justificativa':'N=27,T longo; evitar proliferação de instrumentos. Persistência modelada diretamente; sensibilidade SPJ verifica viés, sem promessa de eliminá-lo.'}]),'decisoes')
