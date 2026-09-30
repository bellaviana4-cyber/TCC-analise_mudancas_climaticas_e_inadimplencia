"""Figuras e interpretações reproduzíveis para os notebooks 07–09."""
import sys, importlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
from statsmodels.tsa.stattools import acf
from analise_categorias import *
plt.rcParams.update({'figure.dpi':90,'axes.spines.top':False,'axes.spines.right':False,'font.size':9})

def ler(nome):return pd.read_csv(TABLES/(nome+'.csv'))
def tabela(df):
    with pd.option_context('display.max_rows',None,'display.max_columns',None,'display.max_colwidth',65): display(df)

def ambiente():
    rows=[{'Pacote':'Python','Versão':sys.version.split()[0]}]
    for n in ['numpy','pandas','scipy','statsmodels','matplotlib','plotly','pyarrow','nbformat','nbclient']:
        rows.append({'Pacote':n,'Versão':importlib.import_module(n).__version__})
    return salvar(pd.DataFrame(rows),'ambiente')

def figura_est(series,key,periodo):
    ini,fim,n=PERIODOS[periodo];s=series[key].loc[ini:fim].astype(float)
    cred=key=='Inadimplência';ts=transformacoes(s,cred)
    principal=ts['Primeira diferença' if cred else 'Diferença do log'].dropna()
    saz=principal.diff(12).dropna()
    fig,ax=plt.subplots(3,2,figsize=(11,9))
    ax[0,0].plot(s.index,s,color='#187b80');ax[0,0].set_title('Nível | '+('taxa (%)' if cred else 'protocolos/mês'))
    ax[0,1].bar(range(1,13),s.groupby(s.index.month).mean(),color='#187b80');ax[0,1].set_title('Perfil médio por mês');ax[0,1].set_xticks(range(1,13))
    ax[1,0].plot(principal.index,principal,color='#a5512f');ax[1,0].set_title(f'Transformação principal | n={len(principal)}')
    ax[1,1].plot(saz.index,saz,color='#745496');ax[1,1].set_title(f'Robustez sazonal | n={len(saz)}')
    for a,x,title in [(ax[2,0],principal,'ACF da transformação principal'),(ax[2,1],saz,'ACF da robustez sazonal')]:
        if x.nunique()>1:
            av=acf(x,nlags=24,fft=False);a.vlines(range(1,25),0,av[1:]);lim=1.96/np.sqrt(len(x));a.axhline(lim,c='gray',ls='--');a.axhline(-lim,c='gray',ls='--')
        a.axvline(12,c='#c35336',ls=':');a.axhline(0,c='black',lw=.5);a.set_title(title)
    fig.suptitle(f'{key} — {periodo}',fontsize=12);fig.tight_layout()
    FIGURES.mkdir(parents=True,exist_ok=True);fig.savefig(FIGURES/f'07_{slug(key)}_{slug(periodo)}.png',dpi=90);plt.show();plt.close(fig)

def interpretar_est(st,key,periodo):
    t=st[(st.Chave==key)&(st.Período==periodo)]
    main='Primeira diferença' if key=='Inadimplência' else 'Diferença do log'
    robust='Diferença + sazonal' if key=='Inadimplência' else 'Diferença do log + sazonal'
    msgs=[]
    for tr in [main,robust]:
        r=t[t.Transformação==tr].iloc[0]
        msgs.append(f"**{tr}:** {r['Conclusão']}; ADF p={r['ADF p']:.4g}, KPSS {r['KPSS limite']} (valor tabelado {r['KPSS p']:.2g}), n={int(r['n'])}.")
    if not all(t[t.Transformação.isin([main,robust])]['Conclusão'].eq('Estacionária: convergente')):
        msgs.append('Há transformação sem convergência entre os testes. Mantemos a especificação histórica para comparação, mas a inferência correspondente é exploratória e não entra na classificação de diagnósticos favoráveis.')
    else:msgs.append('Os testes convergem nas duas transformações de referência. Isso apoia a modelagem, mas não dispensa os diagnósticos residuais nem prova estabilidade estrutural.')
    display(Markdown('\n\n'.join(msgs)))

def figura_granger(r,l,key,periodo):
    fig,axes=plt.subplots(1,3,figsize=(13,4),sharey=True)
    for ax,spec in zip(axes,SPECS):
        sub=l[(l.Chave==key)&(l.Período==periodo)&(l.Especificação==spec)]
        for dr,col in [(DIRECOES[0][0],'#187b80'),(DIRECOES[1][0],'#b1603c')]:
            z=sub[sub.Direção==dr];ax.plot(z.Defasagem,z.p,marker='.',label=dr,c=col)
        ax.axhline(.05,ls='--',c='gray');ax.set_title(spec.replace(': ',':\n'));ax.set_xlabel('Defasagem (meses)');ax.set_ylim(-.02,1.02)
    axes[0].set_ylabel('p-valor original');axes[0].legend(fontsize=7)
    fig.suptitle(f'{key} — {periodo}');fig.tight_layout();fig.savefig(FIGURES/f'granger_{slug(key)}_{slug(periodo)}.png',dpi=90);plt.show();plt.close(fig)

def interpretar_granger(r,key,periodo):
    t=r[(r.Chave==key)&(r.Período==periodo)]
    if t.empty:return
    texts=[]
    for spec in SPECS:
        a=t[(t.Especificação==spec)&(t.Direção==DIRECOES[0][0])]
        vals=[]
        for _,v in a.iterrows():vals.append(f"{v['Critério']}: lag {int(v['Defasagem'])}, p={v['p']:.4g}, BH={v['p BH']:.4g}, n={int(v['n efetivo'])}"+(' (ótimo incluindo zero: 0)' if v['Zero preferido'] else ''))
        texts.append('**'+spec+'** — '+'; '.join(vals)+'.')
    p=t[t.Direção==DIRECOES[0][0]];rev=t[t.Direção==DIRECOES[1][0]]
    texts.append(f"Na direção principal, {int(p['Significativo nominal'].sum())}/{len(p)} linhas de critério têm significância nominal e {int(p['Significativo BH'].sum())}/{len(p)} permanecem após BH. Na reversa, são {int(rev['Significativo nominal'].sum())} nominais e {int(rev['Significativo BH'].sum())} após BH. Linhas AIC/BIC coincidentes não são testes independentes.")
    bad=t[t['Portmanteau p']<.05]
    texts.append(f"Há rejeição do diagnóstico de ruído branco em {len(bad)}/{len(t)} linhas; {int(t['Pico sazonal'].sum())} sinalizam pico residual no lag 12. Esses alertas limitam a leitura dos F clássicos; HC3/HAC são sensibilidades, não reparos da dinâmica.")
    if (t['Estacionariedade I']!='Estacionária: convergente').any():texts.append('Neste recorte, a estacionariedade da inadimplência transformada não tem confirmação conjunta. Os testes Granger são exploratórios; a ausência de rejeição do ADF não demonstra não estacionariedade, mas a limitação impede uma conclusão robusta.')
    texts.append('Não rejeitar H0 não demonstra ausência de efeito. Rejeitar o teste conjunto tampouco indica sinal positivo, efeito causal estrutural ou validação preditiva fora da amostra.')
    display(Markdown('\n\n'.join(texts)))

def consistencia(r):
    rows=[]
    for (key,direction),g in r.groupby(['Chave','Direção']):
        bothcrit=g.groupby(['Período','Especificação'])['Significativo BH'].agg(['sum','count'])
        bothspec=g.groupby(['Período','Critério'])['Significativo BH'].agg(['sum','count'])
        bothperiod=g.groupby(['Especificação','Critério'])['Significativo BH'].agg(['sum','count'])
        rows.append({'Chave':key,'Nível':g.iloc[0]['Nível'],'Categoria':g.iloc[0]['Categoria'],'Direção':direction,'Linhas nominais':int(g['Significativo nominal'].sum()),'Linhas BH':int(g['Significativo BH'].sum()),'Linhas BY':int((g['p BY']<.05).sum()),'AIC e BIC significativos no mesmo cenário':bool(((bothcrit['sum']==2)&(bothcrit['count']==2)).any()),'Três especificações significativas no mesmo período/critério':bool(((bothspec['sum']==3)&(bothspec['count']==3)).any()),'Dois períodos significativos na mesma especificação/critério':bool(((bothperiod['sum']==2)&(bothperiod['count']==2)).any()),'Linhas BH com diagnósticos favoráveis':int(g['Evidência com diagnósticos favoráveis'].sum())})
    return salvar(pd.DataFrame(rows),'consistencia')
