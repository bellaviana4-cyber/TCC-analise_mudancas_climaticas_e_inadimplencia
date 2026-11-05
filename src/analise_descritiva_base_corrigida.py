"""Reproduz tabelas e figuras descritivas a partir do painel agregado auditado."""
from pathlib import Path
import hashlib,json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'outputs/tables/modalidades_excluidas_20261104'
FIG=ROOT/'outputs/figures/modalidades_excluidas_20261104'
LABELS=dict(zip(
    ['alagamentos','chuvas_intensas','doencas_infecciosas','enxurradas','erosao','estiagem_e_seca','granizo','incendio_florestal','inundacoes','movimento_de_massa','onda_de_calor_e_baixa_umidade','onda_de_frio','outros','rompimento_colapso_de_barragens','tornado','vendavais_e_ciclones'],
    ['Alagamentos','Chuvas Intensas','Doenças Infecciosas','Enxurradas','Erosão','Estiagem e Seca','Granizo','Incêndio Florestal','Inundações','Movimento de Massa','Onda de Calor e Baixa Umidade','Onda de Frio','Outros','Rompimento/Colapso de Barragens','Tornado','Vendavais e Ciclones']))

def save(fig,name):
    fig.tight_layout()
    fig.savefig(FIG/(name+'.png'),bbox_inches='tight')
    plt.close(fig)

def main():
    base=ROOT/'data/processed/df_tcc_2013_2024.csv'
    expected=json.loads((B/'manifesto.json').read_text(encoding='utf-8'))['base_sha256']
    assert hashlib.sha256(base.read_bytes()).hexdigest()==expected
    d=pd.read_csv(base,sep=';')
    assert len(d)==3888 and not d.duplicated(['uf','mes_ano']).any()
    FIG.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':120,'savefig.dpi':180})
    national=d.groupby('mes_ano')[['carteira_ativa_total','carteira_inadimplencia_total','total_desastres']].sum()
    national['taxa']=100*national.carteira_inadimplencia_total/national.carteira_ativa_total
    national.index=pd.to_datetime(national.index)
    annual=d.groupby('ano')[['carteira_ativa_total','carteira_inadimplencia_total','total_desastres']].sum()
    annual['taxa']=100*annual.carteira_inadimplencia_total/annual.carteira_ativa_total
    regional=d.groupby('regiao').total_desastres.sum().sort_values(ascending=False)
    regional.to_csv(B/'descritiva_regioes.csv',header=['registros'])
    annual.to_csv(B/'descritiva_anual.csv')
    national.to_csv(B/'descritiva_nacional_mensal.csv')
    groups=d[[c for c in d if c.startswith('grupo_')]].sum().sort_values(ascending=False)
    types=d[[c for c in d if c.startswith('tipo_')]].sum().sort_values()
    fig,ax=plt.subplots(figsize=(9,4))
    groups.rename(index=lambda x:x.replace('grupo_','').capitalize()).plot.bar(ax=ax,color='#247b8a',rot=0)
    ax.set_ylabel('Registros municipais');ax.set_title('Desastres por grupo — Brasil, 2013–2024');save(fig,'grupos_2013_2024')
    fig,ax=plt.subplots(figsize=(10,6))
    types.rename(index=lambda x:LABELS[x.removeprefix('tipo_')]).plot.barh(ax=ax,color='#247b8a')
    ax.set_xlabel('Registros municipais');ax.set_title('Desastres por tipologia — Brasil, 2013–2024');save(fig,'tipologias_2013_2024')
    fig,ax=plt.subplots(figsize=(9,4));regional.plot.bar(ax=ax,color='#247b8a',rot=0)
    ax.set_ylabel('Registros municipais');save(fig,'regioes_2013_2024')
    fig,axes=plt.subplots(9,3,figsize=(11,16),sharex=True)
    for ax,(uf,g) in zip(axes.flat,d.groupby('uf')):
        g=g.sort_values('mes_ano');ax.plot(pd.to_datetime(g.mes_ano),g.taxa_inadimplencia,lw=1,color='#247b8a')
        ax.set_title(uf,fontsize=10);ax.tick_params(labelsize=7)
    fig.suptitle('Taxa de inadimplência PF por UF (%) — três modalidades excluídas',y=1.002);save(fig,'uf_2013_2024')
    fig,ax=plt.subplots(figsize=(10,4))
    for reg,g in d.groupby('regiao'):
        g=g.groupby('mes_ano')[['carteira_ativa_total','carteira_inadimplencia_total']].sum()
        ax.plot(pd.to_datetime(g.index),100*g.carteira_inadimplencia_total/g.carteira_ativa_total,label=reg,lw=1.3)
    ax.set_ylabel('Taxa de inadimplência (%)');ax.legend(ncol=3,fontsize=8);save(fig,'inad_regiao_2013_2024')
    fig,ax=plt.subplots(figsize=(10,4));ax.plot(national.index,national.taxa,color='#176c83',label='Inadimplência')
    ax.set_ylabel('Taxa de inadimplência (%)',color='#176c83')
    other=ax.twinx();other.bar(national.index,national.total_desastres,width=20,color='#bd7844',alpha=.3)
    other.set_ylabel('Registros municipais');save(fig,'nacional_2013_2024')
    order=d.groupby('uf').taxa_inadimplencia.median().sort_values(ascending=False).index
    fig,ax=plt.subplots(figsize=(10,4))
    ax.boxplot([d.loc[d.uf.eq(u),'taxa_inadimplencia'] for u in order],tick_labels=order,showfliers=False)
    ax.set_ylabel('Taxa de inadimplência (%)');ax.tick_params(axis='x',labelsize=8);save(fig,'boxplot_2013_2024')
    granger=B/'granger/granger_aplicacoes.csv'
    if granger.exists():
        g=pd.read_csv(granger);counts=g.p_lags.dropna().astype(int).value_counts().reindex(range(1,7),fill_value=0).sort_index()
        fig,ax=plt.subplots(figsize=(8,3));ax.bar(counts.index,counts.values,color='#247b8a')
        ax.set_xticks(range(1,7));ax.set_xlabel('Defasagens selecionadas pelo BIC (meses)');ax.set_ylabel('Modelos');save(fig,'granger_defasagens')
    print('Tabelas e figuras descritivas reproduzidas a partir do painel corrigido.')

if __name__=='__main__':main()
