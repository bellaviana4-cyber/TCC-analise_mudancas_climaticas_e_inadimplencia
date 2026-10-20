"""Cria notebooks de resultados executáveis e os executa sobre tabelas auditadas."""
from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient
import os
ROOT=Path(__file__).resolve().parents[1]
NB=ROOT/'notebooks';NB.mkdir(parents=True,exist_ok=True)

def m(t):return nbf.v4.new_markdown_cell(t)
def c(t):return nbf.v4.new_code_cell(t)
base="""from pathlib import Path
import os, sys, numpy as np, pandas as pd
import matplotlib.pyplot as plt
ROOT=Path.cwd()
sys.path.insert(0,str(ROOT/'src'))
if 'TCC_BASE_CSV' not in os.environ:
    os.environ['TCC_BASE_CSV']=str(ROOT/'data/processed/df_tcc_2013_2024.csv')
from analise_estadual import load, TIPOS
D=ROOT/'outputs/tables/revisao_estadual_20261019'
A=ROOT/'outputs/tables/auditoria_metodologica_20261020'
S=ROOT/'outputs/tables/sarimax_criterios_independentes_20261020'
df=load()
print(f'Painel: {len(df)} observações, {df.uf.nunique()} UFs, {df.mes_ano.nunique()} meses, {len(TIPOS)} tipologias')"""
files={}

f='34_granger_ufs_tipologias_validacao.ipynb'
cells=[m('# 34 — Causalidade de Granger por UF e tipologia\n\nAnálise nas 27 UFs, nos dois períodos, considerando as **16 tipologias da classificação operacional do Atlas**, sem agrupamentos.\n\nEsta etapa avalia **precedência preditiva**, não impacto causal. O teste F conjunto verifica se os lags do desastre agregam informação além dos lags da inadimplência. Seleção de p entre 1 e 6 por BIC; correção Benjamini–Hochberg dentro de UF × período.'),m('## 1. Leitura, transformações e verificações\n\nA dependente é `Δlog(I)` e cada tipologia é `Δlog(1+D)`. Incluímos intercepto e 11 indicadores mensais. Não rejeitar a hipótese nula de KPSS é compatível com estacionariedade, mas não constitui prova.'),c(base),m('## 2. Estimação e suporte\n\n**Para recalcular integralmente**, altere `REESTIMAR = True`. Os resultados abaixo foram executados anteriormente sobre esta mesma base e são revalidados no notebook.'),c("""REESTIMAR=False
if REESTIMAR:
    from analise_estadual import granger
    _=granger(df)
g=pd.read_csv(D/'granger_aplicacoes.csv')
assert len(g)==27*2*16
print('Aplicações',len(g),'estimáveis',int(g.status.eq('estimado').sum()),'constantes',int(g.status.eq('exposição transformada constante').sum()),'sem posto',int(g.status.eq('sem modelo de posto completo na grade').sum()))
print('Rejeições nominais',int(g.rejeicao_nominal.sum()),'corrigidas BH',int(g.rejeicao_bh.sum()))"""),m('## 3. Resultados que sobreviveram ao BH'),c("""sig=g[g.rejeicao_bh].copy()
assert len(sig)==14
print(sig[['uf','periodo','tipologia','p_lags','p','q_bh','ljungbox_p']].to_string(index=False))
print('Com rejeição do Ljung–Box:',len(sig[sig.ljungbox_p<.05]))"""),m('## 4. Correlação serial residual: intensidade e teste\n\nO Ljung–Box rejeita a hipótese nula de ausência de autocorrelação até as defasagens examinadas; p pequeno não é uma medida de magnitude. Para contextualizar, a auditoria também calcula a maior autocorrelação residual absoluta.'),c("""from auditoria_dlm_granger import auditoria_granger
ag=auditoria_granger(df)
print(ag[(ag.rejeita_BH)&(ag.p_Ljung_Box<.05)][['uf','periodo','tipologia','p_Ljung_Box','acf1','maior_acf_absoluta_1a12']].to_string(index=False))
print('Proporção de casos estimáveis sem rejeição LB:',f'{(ag.p_Ljung_Box>=.05).mean():.1%}')"""),m('## 5. Distribuição espacial das rejeições BH'),c("""counts=sig.groupby('uf').size().sort_values(ascending=False)
fig,ax=plt.subplots(figsize=(9,3))
counts.plot.bar(ax=ax)
ax.set_title('Rejeições BH de Granger por UF')
ax.set_ylabel('Quantidade de rejeições');ax.set_xlabel('UF');plt.tight_layout();plt.show()"""),m('## 6. Interpretação e alertas\n\nA evidência de precedência preditiva é localizada. Os dois casos de Alagamentos em RR rejeitam o Ljung–Box, portanto seus p-valores clássicos exigem ressalva. A seleção por BIC não entra formalmente na distribuição do teste F. Resultados de tipologias com séries idênticas não representam evidências independentes.')]
files[f]=cells

f='35_dlm_painel_aic_bic_validacao.ipynb'
cells=[m('# 35 — DLM em painel: AIC × BIC, TWFE e perfis defasados\n\nModelo da monografia: $$Y_{i,t}=\\alpha_i+\\lambda_t+\\sum_{k=0}^{K}\\beta_k X_{i,t-k}+\\varepsilon_{i,t}.$$\n\nResposta: $Y_{it}=\\Delta\\log(I_{it})$; exposição de cada tipologia: $X_{it}=\\Delta\\log(1+D_{it})$. Uma tipologia por DLM. Efeitos fixos da UF e do mês-ano. Estimador MQO após retirada dos efeitos fixos.\n\nOs candidatos $K=1,\\ldots,24$ utilizam **uma amostra comum** por período. Seleção independente de K por AIC e BIC; aplicação das cinco hipóteses e das correções de multiplicidade.'),m('## 1. Base e transformações'),c(base),m('## 2. Horizonte K por AIC e por BIC'),c("""# Para refazer os 696 candidatos K disponíveis (29*24), marque True.
REESTIMAR=False
if REESTIMAR:
    from analise_estadual import dlm
    _=dlm(df)
sel=pd.read_csv(D/'dlm_selecao.csv')
s=sel.pivot_table(index=['periodo','tipologia'],columns='criterio',values='K').reset_index()
s['K_diferente']=s.AIC.ne(s.BIC)
print('Aplicações estimáveis',len(s),'K diferentes',int(s.K_diferente.sum()))
print('Comparações diferentes:')
print(s[s.K_diferente].to_string(index=False))"""),m('## 3. Inferência com cinco hipóteses\n\n* Contemporâneo $\\beta_0=0$; soma total $\\sum_{k=0}^K\\beta_k=0$; soma defasada $\\sum_{k=1}^K\\beta_k=0$; conjunto completo; conjunto defasado.\n* Covariâncias: cluster UF, DK regra, DK6, DK12. A banda DK é diferente do horizonte K da exposição.\n* Proteção conservadora $\\min(24p,1)$ + BH por período × critério × covariância × hipótese. Não constitui inferência seletiva exata.'),c("""h=pd.read_csv(D/'dlm_hipoteses.csv')
main=h[(h.criterio=='BIC')&(h.covariancia=='dk_regra')]
print('BIC + DK regra: rejeições protegidas',int(main.rejeicao_bh_grade.sum()))
print('Rejeições AIC + DK regra:')
print(h[(h.criterio=='AIC')&(h.covariancia=='dk_regra')&(h.rejeicao_bh_grade)][['periodo','tipologia','K','endpoint','p','q_bh_grade']].to_string(index=False))
print('Rejeições BIC + DK12:')
print(h[(h.criterio=='BIC')&(h.covariancia=='dk12')&(h.rejeicao_bh_grade)][['periodo','tipologia','K','endpoint','p','q_bh_grade']].to_string(index=False))"""),m('## 4. Auditoria de posto e condicionamento das matrizes\n\nUma rejeição de Wald com K elevado merece checagem de posto e condicionamento da covariância. Essa auditoria é numérica; não garante que a especificação seja substantivamente adequada.'),c("""from auditoria_dlm_granger import auditoria_dlm
M=auditoria_dlm(df)
print('Registros auditados:',len(M),'casos com cond X>1e3:',int(M.alerta_cond_X.sum()),'covariâncias com cond>1e6:',int(M.alerta_cond_cov.sum()),'não positivas:',int((M.n_eig_cov_nao_positivos>0).sum()))
print(M[(M.n_rejeicoes_grade_BH>0)&(M.K>=10)][['periodo','tipologia','K','covariancia','cond_X','cond_cov']].to_string(index=False))"""),m('## 5. Perfil de $\\hat\\beta_k$ e curva $C(h)=\\sum_{k=0}^h\\hat\\beta_k$\n\nOs intervalos são condicionais ao K escolhido. O somatório até K é uma **associação acumulada no horizonte modelado**, não um efeito causal de longo prazo automaticamente identificado.'),c("""from consolidar_analises_finais import dlm as construir_perfis
if not (A/'dlm_betas_por_lag.csv').exists(): construir_perfis()
P=pd.read_csv(A/'dlm_betas_por_lag.csv')
C=pd.read_csv(A/'dlm_resposta_acumulada.csv')
for per,tipo,crit in [('Pré','tipo_chuvas_intensas','AIC'),('Pré','tipo_chuvas_intensas','BIC')]:
    q=P[(P.periodo==per)&(P.tipologia==tipo)&(P.criterio==crit)&(P.covariancia=='dk_regra')].sort_values('k')
    v=C[(C.periodo==per)&(C.tipologia==tipo)&(C.criterio==crit)&(C.covariancia=='dk_regra')].sort_values('h')
    fig,ax=plt.subplots(1,2,figsize=(11,3))
    ax[0].errorbar(q.k,q.coef_beta_k,yerr=[q.coef_beta_k-q.ic95_inf,q.ic95_sup-q.coef_beta_k],fmt='o',capsize=3)
    ax[0].axhline(0,linewidth=1);ax[0].set_title(f'{crit} — β por defasagem (K={len(q)-1})');ax[0].set_xlabel('Defasagem (meses)')
    ax[1].plot(v.h,v.acum_0h,marker='o');ax[1].fill_between(v.h,v.ic95_inf,v.ic95_sup,alpha=.2)
    ax[1].axhline(0,linewidth=1);ax[1].set_title('Soma acumulada C(h)');ax[1].set_xlabel('Horizonte (meses)')
    plt.tight_layout();plt.show()"""),m('## 6. Resultados\n\nAIC e BIC selecionam K distintos em oito cenários estimáveis. O BIC escolhe K=1 em todos os 29. Não há rejeições protegidas com BIC + DK regra. Os K longos de Chuvas Intensas e Vendavais/Ciclones foram auditados numericamente; a interpretação final depende da estabilidade estatística entre inferências e do suporte dos registros.')]
files[f]=cells

f='36_sarima_sarimax_estadual_nacional_validacao.ipynb'
cells=[m('# 36 — SARIMA × SARIMAX com seleção independente no `statsmodels`\n\nAnálise principal: SARIMA e SARIMAX sazonais por UF e período, usando exógenas selecionadas **por suporte/posto no treinamento**. Análise complementar: nacional com as 16 tipologias simultaneamente, quando identificáveis.\n\nO `statsmodels` **não possui seleção automática de ordens** na classe SARIMAX. Por isso, este notebook usa uma busca explícita sobre cinco especificações sazonais, estimadas separadamente com e sem exógenas, selecionando a menor BIC convergida no treino.\n\nA previsão é condicional de um passo: usa desastres contemporâneos observados, não prevê a ocorrência futura de desastres.'),m('## 1. Verificação do painel e da disponibilidade dos resultados'),c(base),m('## 2. Execução/reexecução dos candidatos sazonais\n\nA rotina foi executada com `statsmodels`, registrando avisos, convergência e BIC por candidato. Para repetir integralmente do zero, exclua os CSVs de checkpoint e rode novamente os quatro comandos abaixo. O reprocessamento incremental não reestima combinações que já estejam salvas.\n\nO **SARIMA e SARIMAX são escolhidos separadamente** por BIC; uma comparação pareada com ordens iguais é armazenada como análise complementar.'),c("""from selecionar_sarima_sarimax_statsmodels import run
# Reprocessamento incremental seguro: preserva resultados por UF concluída.
for mode in ('nacional','estadual'):
    for period in ('Pré','Total'):
        run(mode,period)"""),m('## 3. BH global, sumários e warnings'),c("""from consolidar_analises_finais import sarimax as consolidar
consolidar()
from pathlib import Path
import json
for modo in ['estadual','nacional']:
    resumo=json.loads((S/f'{modo}_resumo_final.json').read_text())
    print(modo.upper(),resumo)
    print('Significativos após BH global:')
    cs=pd.read_csv(S/f'{modo}_significativos_BH.csv')
    print(cs[['unidade','periodo','tipologia','coef_original','p_individual','q_individual_BH_global']].to_string(index=False) if len(cs) else 'Nenhum')"""),m('## 4. Auditoria: 16 tipologias por UF versus série nacional'),c("""old=pd.read_csv(ROOT/'outputs/tables/sarimax_revisao_20261019/estadual_auditoria_posto.csv')
print(old.groupby('periodo').agg(casos=('posto_treino','size'),posto16_treino=('posto_treino',lambda x:(x==16).sum()),posto16_total=('posto_completo',lambda x:(x==16).sum())).to_string())
new=pd.concat([pd.read_csv(S/f'nacional_{period}_modelos.csv') for period in ('Pré','Total')])
print('BIC e RMSE NACIONAL:')
print(new[['periodo','ordem_sarima','ordem_sarimax','delta_BIC','rmse_sarima','rmse_sarimax','melhora_RMSE_pct','p_conjunto_condicional']].to_string(index=False))"""),m('## 5. Comparação estadual e diagnóstico Ljung–Box'),c("""st=pd.read_csv(S/'estadual_comparacao.csv')
print('Comparações estaduais:',int(st.rmse_sarimax.notna().sum()),'melhora RMSE:',int((st.melhora_RMSE_pct>0).sum()),'melhora BIC:',int((st.delta_BIC<0).sum()))
print('Rejeições do LB SARIMA:',int((st.ljungbox_sarima<.05).sum()),'SARIMAX:',int((st.ljungbox_sarimax<.05).sum()))
print('Melhorias mais expressivas:')
print(st.nlargest(10,'melhora_RMSE_pct')[['unidade','periodo','n_exog','melhora_RMSE_pct','delta_BIC']].to_string(index=False))
fig,ax=plt.subplots(figsize=(9,4))
pd.to_numeric(st.melhora_RMSE_pct,errors='coerce').dropna().hist(ax=ax,bins=15)
ax.axvline(0,linewidth=1);ax.set_title('Ganho percentual do SARIMAX no RMSE (>0 indica melhora)')
ax.set_xlabel('100 × (1 − RMSE SARIMAX / RMSE SARIMA)');ax.set_ylabel('Quantidade');plt.tight_layout();plt.show()"""),m('## 6. Warnings e convergência\n\nWarnings de inicialização AR/MA foram preservados para auditoria. Eles não significam necessariamente falha de ajuste; não convergência final, posto deficiente e rejeição Ljung–Box têm significados distintos.'),c("""for mode in ('estadual','nacional'):
    W=pd.read_csv(S/f'{mode}_warnings.csv')
    models=pd.read_csv(S/f'{mode}_comparacao.csv')
    print(mode,'candidatos com warnings',len(W),'modelos com LB SARIMAX rejeitado',int((models.ljungbox_sarimax<.05).sum()))
    print(W[['periodo','unidade','modelo','ordem','n_warnings','warnings']].head(8).to_string(index=False,max_colwidth=90))"""),m('## 7. Interpretação\n\nO modelo estadual reduzido é condicionado ao suporte das tipologias em cada UF. O nacional contém as 16 tipologias sem agrupá-las. A escolha independente por BIC pode modificar a ordem SARIMA da comparação e os resultados preditivos frente à versão que forçava a mesma ordem. Os testes individuais e conjuntos são exploratórios porque não incorporam formalmente a seleção de ordens e regressores. Nenhuma diferença de BIC positiva indica evidência favorável à complexidade adicional das exógenas.')]
files[f]=cells

for filename,cells in files.items():
    path=NB/filename
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}})
    nbclient=NotebookClient(nb,timeout=1200,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}})
    try:
        executed=nbclient.execute()
    except Exception as ex:
        nbf.write(nb,path)
        print('FALHA',filename,str(ex)[:600]);raise
    errors=[(i,o.get('ename','')) for i,cell in enumerate(executed.cells) if cell.cell_type=='code' for o in cell.get('outputs',[]) if o.output_type=='error']
    assert not errors,(filename,errors)
    nbf.write(executed,path)
    print('OK',filename,'células de código executadas:',len([c for c in cells if c.cell_type=='code']),'bytes:',path.stat().st_size,flush=True)