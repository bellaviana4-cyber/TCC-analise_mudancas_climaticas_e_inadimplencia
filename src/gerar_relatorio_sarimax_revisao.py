"""Relatório standalone, documentação e notebooks de resultados da revisão SARIMAX."""
from __future__ import annotations
from pathlib import Path
import pandas as pd, numpy as np, json, html
import nbformat as nbf

ROOT=Path(__file__).resolve().parents[1]
T=ROOT/'outputs/tables/sarimax_revisao_20261019'
DOC=ROOT/'docs'
REPORTS=ROOT/'outputs/reports'
for p in (DOC,REPORTS):p.mkdir(parents=True,exist_ok=True)
S=pd.read_csv(T/'estadual_comparacao_modelos.csv')
N=pd.read_csv(T/'nacional_comparacao_modelos.csv')
A=pd.read_csv(T/'estadual_auditoria_posto.csv')
AN=pd.read_csv(T/'nacional_auditoria_posto.csv')
C=pd.read_csv(T/'estadual_coeficientes.csv')
CN=pd.read_csv(T/'nacional_coeficientes.csv')
assert len(S)==54 and len(N)==2 and len(A)==54 and len(AN)==2
assert ((AN.posto_treino==16)&(AN.posto_completo==16)).all()
assert (A.query("periodo=='Pré'").posto_treino<16).all()
assert ((A.query("periodo=='Total'").posto_treino==16).sum()==1)
assert S.rmse_sarimax.notna().sum()==53
assert (S.delta_bic_treino.dropna()>0).all()
assert (N.delta_bic_treino.dropna()>0).all()

perstat=S.groupby('periodo').agg(comparaveis=('rmse_sarimax','count'),melhora_rmse=('variacao_rmse_pct',lambda x:int((x<0).sum())),mediana_rmse=('variacao_rmse_pct','median'),melhora_bic=('delta_bic_treino',lambda x:int((x<0).sum()))).reset_index()
co_sig=C[C.q_bh_global<.05]
assert len(co_sig)==2

def num(a, digits=2):
    return '—' if pd.isna(a) else f'{a:,.{digits}f}'.replace(',','X').replace('.',',').replace('X','.')

def df_table(df, cols, title_map=None):
    tr=[]
    title_map=title_map or {}
    tr.append('| '+' | '.join(title_map.get(c,c) for c in cols)+' |')
    tr.append('| '+' | '.join(['---']*len(cols))+' |')
    for _,r in df.iterrows():
        tr.append('| '+' | '.join(num(r[c]) if isinstance(r[c],(float,np.floating)) else str(r[c]) for c in cols)+' |')
    return '\n'.join(tr)

by_uf=S.pivot(index='unidade',columns='periodo',values=['n_exog_incluidas','variacao_rmse_pct']).reset_index()
by_uf.columns=['uf','n_exog_pre','n_exog_total','var_rmse_pre','var_rmse_total']
# columns is alphabetically Pré/Total for both metrics; guard explicit:
by_uf=pd.DataFrame({'uf':sorted(S.unidade.unique())})
for per,sfx in [('Pré','pre'),('Total','total')]:
    D=S[S.periodo==per].set_index('unidade').reindex(by_uf.uf)
    by_uf[f'n_exog_{sfx}']=D.n_exog_incluidas.to_numpy()
    by_uf[f'var_rmse_{sfx}']=D.variacao_rmse_pct.to_numpy()

md=f'''# Revisão SARIMA versus SARIMAX — TCC (19/10/2026)

## Objetivos e base

A análise principal compara SARIMA sazonal e SARIMAX sazonal em **27 UFs × 2 períodos**, com tipologias exógenas escolhidas **apenas por suporte e estimabilidade no treino**. A complementar compara SARIMA e SARIMAX na **série nacional**, com **as 16 tipologias simultaneamente**, após testar posto e condicionamento.

A fonte é a base consolidada mensal `df_tcc_2013_2024.csv`; SHA-256 **46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36**. 27 UFs × 144 meses = 3.888 linhas. Sem reauditoria dos registros individuais do Atlas. Os nomes das 16 tipologias vêm da taxonomia administrativa; nem todas correspondem exclusivamente a fenômenos climáticos.

## Verificação anterior à alteração (16 exógenas, UF por UF)

O sistema original usava 16 colunas `Δlog(1+D)` simultâneas em cada UF e período. O posto da matriz de treino foi **inferior a 16 nas 27 UFs pré-pandemia e em 26 das 27 UFs no período total**. Apenas **MG/Total** teve posto 16 no treino, embora MG, MS, RS, SC e SP tenham posto 16 na amostra total. Isso demonstra não identificação dos 16 coeficientes em 53 das 54 comparações de treinamento; a sazonalidade ARMA não cria variação onde uma exógena é constante nem resolve colinearidade exata.

**Não confundir:** um software pode retornar parâmetros em matriz singular por regularização numérica ou escolha arbitrária; esses parâmetros não seriam individualmente identificados por variação da amostra. Não se deve interpretar tais estimativas como 16 efeitos separados defensáveis.

## Modelo e procedimento comum

- Resposta estadual: `y_it = 100 Δlog(taxa_inadimplencia_it)` (143 valores no período completo). Resposta nacional: `100 Δlog(100 × Σ carteira_inadimplente / Σ carteira_ativa)`. **Não se usa média aritmética das taxas estaduais.**
- Exposição estadual: `x_it = Δlog(1 + registros_tipologia_it)`; exposição nacional: primeiro **somar os registros** de cada tipologia entre UFs, depois aplicar `Δlog(1 + soma)`. Nunca somar as séries log-diferenciadas estaduais.
- A sazonalidade anual é obrigatória no grid. Modelos candidatos no treino: ARMA `(0,0,0)`, `(1,0,0)`, `(0,0,1)` e `(1,0,1)` com sazonal `(1,0,0,12)`, mais `(1,0,0) × (0,0,1,12)`. `d=D=0` porque a transformação log-diferença já foi feita externamente.
- Seleção do modelo de referência: preferir candidatos convergidos sem rejeição de Ljung–Box 12 a 5%; minimizar BIC entre eles. Sem candidato que passe, utilizar menor BIC convergido com ressalva. A escolha é feita **apenas no treino** e a ordem é mantida igual no par SARIMA/SARIMAX.
- Período pré: treino fevereiro/2013–janeiro/2019, 72 observações; teste fevereiro/2019–janeiro/2020, 12. Período completo: treino fevereiro/2013–dezembro/2022, 119; teste janeiro/2023–dezembro/2024, 24.
- Previsões de **um passo à frente**, sem reestimar parâmetros no teste, atualizando o filtro com inadimplência passada efetivamente observada. As `x_t` de desastres são contemporâneas e conhecidas no teste: trata-se de **previsão condicional**, não previsão em tempo real anterior ao desastre.
- No SARIMAX, as colunas são padronizadas com médias/desvios calculados **somente no treino**, para favorecer a otimização. Coeficientes originais são reconstruídos dividindo pelo desvio do treino.
- Critérios de comparação: RMSE/MAE no teste; BIC no treino com a mesma ordem ARMA; LR conjunto (qui-quadrado com gl igual ao número de exógenas, **exploratório**, pois há seleção prévia); Ljung–Box; p individuais, BH por modelo e BH global na família estadual. O BIC penaliza naturalmente regressores adicionais.

## Análise principal — redução estadual pré-definida

Para cada UF/período, sobre a **amostra de treino exclusivamente**: (1) manter tipologias com **pelo menos três meses de ocorrência positiva**; (2) ordenar por número de meses com ocorrência e ordem original da taxonomia para desempate; (3) acrescentar sequencialmente apenas colunas não constantes e independentes; (4) descartar candidato que leve a número de condição > 1.000 após padronização; (5) limitar a no máximo **9 exógenas no pré** ou **12 no total**, por parcimônia. Esse limite adicional significa que nem toda variável estimável entra automaticamente: ele é declarado, não ocultado, e **não utiliza o p-valor nem o teste para seleção**.

São **53 de 54** comparações possíveis: DF pré ficou sem exógena que atingisse suporte mínimo. Dos 53 SARIMAX estaduais comparáveis, **14 tiveram RMSE menor** e **39 tiveram RMSE maior** do que o SARIMA sazonal pareado. **Nenhum dos 53 melhorou o BIC no treino.** A mediana de variação percentual de RMSE (SARIMAX versus SARIMA) foi de **+{num(S.variacao_rmse_pct.median())}%**: positiva significa pior desempenho do SARIMAX.

{df_table(perstat,['periodo','comparaveis','melhora_rmse','mediana_rmse','melhora_bic'],{'periodo':'Período','comparaveis':'Comparáveis','melhora_rmse':'SARIMAX melhor no RMSE','mediana_rmse':'Mediana Δ RMSE (%)','melhora_bic':'SARIMAX melhor no BIC'})}

O Ljung–Box 12 não rejeitou a 5% em **41 dos 53 SARIMAX** estaduais comparáveis. Logo, os demais precisam de ressalva de especificação residual. Nenhuma das 53 hipóteses conjuntas de exógenas foi rejeitada após BH entre modelos. Duas associações individuais sobreviveram BH global (395 testes de coeficientes): **Enxurradas em Pernambuco, pré e total** (coeficientes positivos), mas seus modelos pioraram o BIC e o RMSE e os testes conjuntos não sobreviveram BH. Além disso, há seleção de modelo prévia e testes condicionais: não atribuir causalidade e não interpretar esses dois achados como robustez geral.

### Comparação de cada UF

Δ RMSE = 100 × (RMSE do SARIMAX / RMSE do SARIMA − 1). Valores **negativos** indicam melhora do SARIMAX.

{df_table(by_uf,['uf','n_exog_pre','var_rmse_pre','n_exog_total','var_rmse_total'],{'uf':'UF','n_exog_pre':'Exógenas pré','var_rmse_pre':'Δ RMSE pré (%)','n_exog_total':'Exógenas total','var_rmse_total':'Δ RMSE total (%)'})}

## Análise complementar — Brasil (16 variáveis simultâneas)

A matriz de 16 exposições nacionais apresentou posto **16/16 no treino e na amostra completa** nos dois períodos, com números de condição do treino de **{num(AN.iloc[0].cond_treino)}** (pré) e **{num(AN.iloc[1].cond_treino)}** (total). As duas especificações SARIMAX com 16 exógenas e sazonalidade anual convergiram.

{df_table(N,['periodo','n_exog_incluidas','rmse_sarima','rmse_sarimax','variacao_rmse_pct','delta_bic_treino','p_conjunto_treino','lb_sarimax_treino'],{'periodo':'Período','n_exog_incluidas':'Exógenas','rmse_sarima':'RMSE SARIMA','rmse_sarimax':'RMSE SARIMAX','variacao_rmse_pct':'Δ RMSE (%)','delta_bic_treino':'Δ BIC treino','p_conjunto_treino':'p LR','lb_sarimax_treino':'p Ljung–Box'})}

**No nacional, o SARIMAX piorou o RMSE em ambos os períodos** e teve BIC maior; os testes conjuntos não rejeitaram, e ambos os SARIMAX apresentaram autocorrelação residual pelo Ljung–Box a 5%. Portanto, as 16 exógenas são *identificáveis* nessa série, mas **não trouxeram ganho preditivo ou de parcimônia nas especificações estimadas**.

## Conclusão metodológica

A série nacional permite identificar as 16 tipologias juntas, mas, com as ordens sazonais testadas e estas amostras, não sustenta superioridade do SARIMAX. Por UF, a redução por suporte permite 53 análises pareadas; a inclusão de desastres só reduz RMSE em 14 casos e eleva o BIC em todos. Não rejeição de hipóteses não demonstra ausência de efeito econômico; modelos condicionais, multiplicidade, informação esparsa, classificação administrativa e diagnóstico residual impedem conclusões causais.

## Arquivos e reprodução

- Script único de estimação: `src/sarimax_revisao_final.py`.
- Gerador de relatório/notebooks: `src/gerar_relatorio_sarimax_revisao.py`.
- Notebooks: `32_sarimax_estadual_tipologias_estimaveis.ipynb` e `33_sarimax_nacional_16_tipologias.ipynb`.
- Tabelas: `outputs/tables/sarimax_revisao_20261019/` (auditoria, seleção, coeficientes, previsões agregadas, comparações, resumos).
- Relatório offline: `outputs/reports/relatorio_sarimax_revisao_20261019.html`.

Com a base já processada no caminho padrão (não versionada, por privacidade e volume), executar:

```bash
python src/sarimax_revisao_final.py nacional
python src/sarimax_revisao_final.py estadual
python src/gerar_relatorio_sarimax_revisao.py
```

Se a base estiver em outro caminho, usar `TCC_BASE_CSV` apontando ao arquivo com o SHA acima. Reexecutar primeiro o SARIMA/SARIMAX se a base mudar. A inferência após seleção de ordens e regressoras não foi formalmente ajustada; BH controla apenas a multiplicidade das famílias de testes identificadas.
'''
(DOC/'sarimax_revisao_estadual_nacional_20261019.md').write_text(md,encoding='utf-8')

# Notebooks documentam e permitem reproduzir as verificações já executadas.
def notebook(mode):
    label='estadual' if mode=='estadual' else 'nacional'
    title='SARIMAX estadual — tipologias estimáveis' if label=='estadual' else 'SARIMAX nacional — 16 tipologias simultâneas'
    nb=nbf.v4.new_notebook()
    nb.metadata.kernelspec={'display_name':'Python 3','language':'python','name':'python3'}
    nb.cells=[nbf.v4.new_markdown_cell(f'# {title}\n\nEsta análise foi executada no script `src/sarimax_revisao_final.py`. O notebook examina e interpreta as saídas salvas. Para reestimar os modelos, execute o script conforme a seção de reprodução. As seleções não utilizam a amostra de teste.'),
              nbf.v4.new_markdown_cell('## 1. Protocolo de estimação\n\nResposta: `100 Δlog(I)`. Exógenas: `Δlog(1+D)`. SARIMA e SARIMAX usam a mesma ordem e sazonalidade anual `s=12` no par; a escolha é feita no treino. Avaliação condicional de um passo com `x_t` conhecida.'),
              nbf.v4.new_code_cell("from pathlib import Path\nimport pandas as pd, numpy as np, json\nroot=Path.cwd()\nif not (root/'outputs'/'tables').exists(): root=root.parent\ntables=root/'outputs'/'tables'/'sarimax_revisao_20261019'\n"),
              nbf.v4.new_code_cell(f"df=pd.read_csv(tables/'{label}_comparacao_modelos.csv')\naudit=pd.read_csv(tables/'{label}_auditoria_posto.csv')\ncoef=pd.read_csv(tables/'{label}_coeficientes.csv')\nsummary=json.loads((tables/'{label}_resumo.json').read_text(encoding='utf-8'))\nprint('Resumo:', summary)\nprint('Postos originais:', audit.groupby('periodo')[['posto_treino','posto_completo']].agg(['min','max']).to_string())"),
              nbf.v4.new_markdown_cell('## 2. Resultados e comparação\n\nΔ RMSE negativo indica melhora do SARIMAX. BIC comparado apenas para modelos ajustados no mesmo treino.'),
              nbf.v4.new_code_cell("cols=['periodo','unidade','n_exog_incluidas','sazonal','rmse_sarima','rmse_sarimax','variacao_rmse_pct','delta_bic_treino','p_conjunto_treino','q_conjunto_bh','lb_sarimax_treino']\nprint(df[cols].to_string(index=False))\nprint('Modelos comparáveis:',df.rmse_sarimax.notna().sum(),'Melhora RMSE:',(df.variacao_rmse_pct<0).sum(),'Melhora BIC:',(df.delta_bic_treino<0).sum())"),
              nbf.v4.new_markdown_cell('## 3. Evidências e limites\n\nOs p-valores são condicionais à seleção do modelo e não representam causalidade. Os regressors `x_t` contemporâneos são conhecidos no teste; a previsão é condicional. Verificar o Ljung–Box e a família de multiplicidade ao interpretar efeitos individuais.'),
              nbf.v4.new_code_cell("if 'q_bh_global' in coef.columns:\n    print(coef.loc[coef.q_bh_global<.05,['periodo','unidade','tipologia','coef_original','p','q_bh_global']].to_string(index=False))\nelse: print('Sem coeficientes elegíveis ao BH global')"),
              nbf.v4.new_markdown_cell(f'## 4. Reprodução integral\n\nNo terminal do projeto: `python src/sarimax_revisao_final.py {label}`. Consulte `docs/sarimax_revisao_estadual_nacional_20261019.md` para definições, seleção de suporte, limitações e conclusões.')]
    # Preencher outputs com o conteúdo REAL lido dos CSVs, sem fingir execução do notebook.
    namespace={'Path':Path,'pd':pd,'np':np,'json':json,'print':print}
    import io,contextlib
    count=0
    for c in nb.cells:
        if c.cell_type!='code':continue
        count+=1
        cap=io.StringIO()
        with contextlib.redirect_stdout(cap):exec(c.source,namespace)
        c.execution_count=count
        c.outputs=[nbf.v4.new_output('stream',name='stdout',text=cap.getvalue())] if cap.getvalue() else []
    return nb

for mode,nm in [('estadual','32_sarimax_estadual_tipologias_estimaveis.ipynb'),('nacional','33_sarimax_nacional_16_tipologias.ipynb')]:
    nb=notebook(mode)
    p=ROOT/'notebooks'/nm;p.parent.mkdir(parents=True,exist_ok=True);nbf.write(nb,p)
    nbf.validate(nb)

# Relatório HTML offline com filtros interativos e dados incorporados.
def rec(df):
    return json.loads(df.replace({np.nan:None}).to_json(orient='records',force_ascii=False))
data={'estaduais':rec(S),'nacionais':rec(N),'auditoria_estado':rec(A),'auditoria_brasil':rec(AN),
      'coef_estado':rec(C),'coef_brasil':rec(CN),'summary_estado':json.loads((T/'estadual_resumo.json').read_text()),
      'summary_brasil':json.loads((T/'nacional_resumo.json').read_text())}
serialized=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
h=f'''<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SARIMAX | TCC — revisão final estadual e nacional</title>
<style>
:root{{--nav:#162239;--ink:#1d293b;--text:#34435a;--muted:#66768b;--pink:#a64175;--bg:#f6f8fc;--border:#e1e6ef;--blue:#3457a4}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;font:15px/1.64 system-ui,-apple-system,'Segoe UI',Arial,sans-serif;color:var(--ink);background:var(--bg)}}
nav{{position:fixed;left:0;top:0;bottom:0;width:246px;background:var(--nav);padding:28px 14px;z-index:4;overflow:auto}}nav b{{color:white;font-size:17px;display:block;margin:3px 10px 27px;line-height:1.35}}nav a{{display:block;color:#c6cee0;text-decoration:none;padding:11px 12px;border-radius:9px;margin:2px 0;font-size:13px}}nav a:hover,nav a.active{{background:#304264;color:white}}nav .foot{{color:#8192b0;font-size:11px;padding:18px 12px}}
main{{margin-left:246px}}section{{max-width:1440px;margin:0 auto;padding:48px clamp(22px,5vw,78px) 85px}}section h2{{font-size:30px;margin:0 0 9px;letter-spacing:-.5px}}section h3{{margin:27px 0 12px;font-size:19px}}p{{color:var(--text);max-width:1040px}}.cover{{max-width:none;background:linear-gradient(136deg,#101a2b 14%,#25395c 55%,#693153);color:white;min-height:94vh;display:flex;flex-direction:column;justify-content:center;padding-left:clamp(28px,8vw,130px)}}.cover h1{{font-size:clamp(38px,4.5vw,68px);line-height:1.14;letter-spacing:-1.3px;max-width:850px;margin:14px 0 20px}}.cover p{{color:#dae1ed;font-size:17px;max-width:690px}}.eyebrow{{letter-spacing:2.5px;text-transform:uppercase;color:#dc9eb9;font-size:12px;font-weight:700}}.chip{{display:inline-block;background:#ffffff15;border:1px solid #ffffff30;padding:6px 12px;border-radius:99px;font-size:12px;margin:8px 8px 0 0}}.lede{{font-size:16px;color:var(--muted);margin:0 0 27px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(178px,1fr));gap:15px;margin:27px 0}}.stat{{background:white;border:1px solid var(--border);border-radius:14px;padding:22px;box-shadow:0 4px 24px #21324a08}}.stat strong{{display:block;font-size:34px;letter-spacing:-1px}}.stat span{{color:var(--muted);font-size:12px}}.panel{{border:1px solid var(--border);background:white;padding:22px;border-radius:14px;margin:20px 0}}.panel h3{{margin-top:0}}.boxnote{{border-left:3px solid var(--pink);padding:13px 18px;background:#fdf3f8;border-radius:0 9px 9px 0;color:var(--text);margin:20px 0}}.split{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.filters{{display:flex;gap:11px;flex-wrap:wrap;align-items:center;margin:10px 0 18px}}select,input{{font:inherit;border:1px solid #bfc9db;border-radius:8px;background:white;padding:9px 12px;color:var(--ink)}}label{{color:var(--muted);font-size:12px;font-weight:700}}.tablewrap{{overflow:auto;border:1px solid var(--border);border-radius:12px;background:white}}table{{width:100%;border-collapse:collapse;font-size:12.5px;min-width:720px}}th{{background:#eaf0f9;font-weight:700;text-align:left;white-space:nowrap;position:sticky;top:0}}th,td{{padding:9px 12px;border-bottom:1px solid #edf0f5}}td.num{{font-variant-numeric:tabular-nums;white-space:nowrap}}tr:hover td{{background:#fafcff}}.good{{color:#147a56;font-weight:700}}.bad{{color:#ac4d67;font-weight:700}}.small{{font-size:12px;color:var(--muted)}}.barrow{{display:grid;grid-template-columns:74px 1fr 70px;gap:12px;align-items:center;margin:8px 0;font-size:12px}}.track{{height:10px;background:#e9edf4;position:relative;border-radius:8px;overflow:hidden}}.bar{{position:absolute;top:0;bottom:0;background:var(--pink);border-radius:4px}}.bar.green{{background:#399e7b}}.empty{{color:var(--muted);padding:35px;text-align:center}}.call{{font-weight:750;font-size:20px;color:#172d4a}}.steps{{counter-reset:s}}.step{{position:relative;padding:13px 16px 13px 60px;border-left:2px solid #d5e0ec;margin-left:18px}}.step:before{{counter-increment:s;content:counter(s);position:absolute;left:-19px;top:13px;border-radius:100%;background:#344c74;color:white;width:35px;height:35px;display:grid;place-items:center}}.mobile{{display:none}}@media(max-width:900px){{nav{{transform:translateX(-246px);transition:.25s}}nav.show{{transform:translateX(0)}}main{{margin-left:0}}section{{padding:28px 20px 65px}}.split{{grid-template-columns:1fr}}.mobile{{display:block;position:fixed;right:14px;top:14px;z-index:10;background:var(--nav);color:white;border:0;padding:10px;border-radius:8px}}.cover{{padding:60px 25px}}}}
</style></head><body><button class="mobile" onclick="document.querySelector('nav').classList.toggle('show')">☰ Menu</button>
<nav><b>SARIMAX<br>Revisão metodológica</b><a href="#capa">Capa</a><a href="#metodo">Protocolo</a><a href="#auditoria">Auditoria 16 exógenas</a><a href="#estadual">Análise estadual</a><a href="#nacional">Análise nacional</a><a href="#coef">Coeficientes e testes</a><a href="#conclusao">Conclusões</a><a href="#reproducao">Reprodução</a><div class="foot">TCC · 19 de outubro de 2026<br>27 UFs | 16 tipologias | s=12</div></nav>
<main>
<section class="cover" id="capa"><span class="eyebrow">TCC · desastres e inadimplência</span><h1>Quando incluir desastres melhora um modelo sazonal de inadimplência?</h1><p>Comparação controlada entre SARIMA e SARIMAX, por UF e no Brasil, após verificar que a inclusão simultânea de 16 exógenas estaduais não é identificável em quase todos os treinamentos.</p><div><span class="chip">54 cenários estaduais</span><span class="chip">2 séries nacionais</span><span class="chip">Teste cronológico</span><span class="chip">Sazonalidade anual obrigatória</span></div></section>
<section id="metodo"><h2>Metodologia</h2><p class="lede">Os modelos usam a mesma dinâmica temporal em cada par, distinguindo o ganho das variáveis climáticas da captura de padrões autorregressivos e sazonais.</p><div class="steps"><div class="step"><b>Resposta</b><p><code>100 Δlog(I)</code> por UF; no Brasil, <code>I = 100 ΣCI / ΣCA</code>, ponderada pelo saldo da carteira e não pela média simples estadual.</p></div><div class="step"><b>Regressores</b><p><code>Δlog(1+D)</code> para cada tipologia. No Brasil, os registros são somados primeiro e a transformação é calculada depois.</p></div><div class="step"><b>Sazonalidade anual</b><p>São avaliados cinco candidatos parcimoniosos, sempre com SARIMA sazonal anual: AR(12) ou MA(12), <code>d=D=0</code> após diferença externa.</p></div><div class="step"><b>Sem vazamento</b><p>Seleção do modelo, suporte e padronização feitos somente no treino. Pré: 72 meses de treino +12 de teste. Total: 119 de treino +24 de teste.</p></div><div class="step"><b>Comparação e inferência</b><p>BIC de treino, RMSE/MAE de teste, Ljung–Box, LR conjunto e BH. Previsão condicional de um passo com desastres contemporâneos observados.</p></div></div><div class="boxnote">A série de exposição contemporânea em t é fornecida ao SARIMAX na avaliação. Portanto, o ganho de RMSE mede previsão condicional e <b>não</b> antevisão de desastres futuros. Os testes são exploratórios depois da escolha das ordens.</div></section>
<section id="auditoria"><h2>Antes da modelagem: por que a especificação original falhou?</h2><p class="lede">A sazonalidade não corrige a ausência de variação dos desastres numa UF. Para estimar 16 coeficientes separados, a matriz de 16 regressoras precisa de posto 16 já no treino.</p><div class="grid"><div class="stat"><strong>0 / 27</strong><span>Posto 16 estadual no treino pré-pandemia</span></div><div class="stat"><strong>1 / 27</strong><span>Posto 16 estadual no treino completo (MG)</span></div><div class="stat"><strong>16 / 16</strong><span>Posto nacional no treino de ambos os períodos</span></div><div class="stat"><strong>5,18–7,96</strong><span>Condição bruta da matriz nacional no treino</span></div></div><div class="panel"><div class="filters"><label>Período <select id="auditPeriod"><option value="Pré">Pré-pandemia</option><option value="Total">Período completo</option></select></label></div><div id="auditTable"></div></div><div class="boxnote">Confirmação: os 16 coeficientes não são identificáveis nos demais treinamentos. A especificação nacional completa, porém, passou nos critérios iniciais de posto e condicionamento — foi, por isso, efetivamente ajustada.</div></section>
<section id="estadual"><h2>Principal: SARIMA × SARIMAX estadual</h2><p class="lede">As tipologias foram escolhidas exclusivamente pelo suporte no treinamento (≥3 meses positivos), independência linear, condição padronizada ≤1.000 e limite de 9 regressoras no pré ou 12 no total. Não houve seleção por significância.</p><div class="grid"><div class="stat"><strong>53 / 54</strong><span>Pares estaduais comparáveis</span></div><div class="stat"><strong>14 / 53</strong><span>SARIMAX melhora RMSE</span></div><div class="stat"><strong>0 / 53</strong><span>SARIMAX melhora BIC</span></div><div class="stat"><strong>+7,19%</strong><span>Mediana do Δ RMSE: piora relativa</span></div></div><div class="split"><div class="panel"><h3>Variação do RMSE por UF</h3><div class="filters"><label>Período <select id="statePeriod"><option value="Pré">Pré-pandemia</option><option value="Total">Período completo</option></select></label><label>Ordenar <select id="stateSort"><option value="asc">Maior melhora SARIMAX</option><option value="desc">Maior piora SARIMAX</option></select></label></div><div id="bars"></div></div><div class="panel"><h3>Leitura dos resultados</h3><p class="call">A inclusão das tipologias não se mostrou superior de forma generalizada.</p><p>As diferenças negativas no RMSE indicam ganhos locais de previsão condicional. Contudo, todos os SARIMAX estaduais apresentaram BIC maior do que o SARIMA de referência.</p><p>DF pré-pandemia: nenhuma variável atingiu suporte mínimo. Para as 53 comparações restantes, 41 SARIMAX não tiveram rejeição Ljung–Box a 5% no treino.</p><div class="boxnote">BIC e RMSE respondem a questões diferentes: parcimônia/adequação no treino e erro preditivo condicional em meses futuros.</div></div></div><div class="panel"><h3>Comparação detalhada — 27 UFs</h3><div class="filters"><label>Período <select id="tablePeriod"><option value="Pré">Pré-pandemia</option><option value="Total">Período completo</option></select></label><label>Localizar UF <input id="searchUf" placeholder="Ex.: MG, Pernambuco" maxlength="30"></label></div><div id="stateTable"></div></div></section>
<section id="nacional"><h2>Complementar: SARIMAX nacional com 16 exógenas</h2><p class="lede">Ao agregar os registros por tipologia e ponderar a inadimplência pelas carteiras, o treino nacional tem posto 16 e condicionamento moderado nos dois períodos. As 16 regressoras entraram simultaneamente no modelo sazonal.</p><div class="grid"><div class="stat"><strong>2 / 2</strong><span>SARIMAX com 16 exógenas convergiram</span></div><div class="stat"><strong>+29,01%</strong><span>Δ RMSE pré-pandemia (piora)</span></div><div class="stat"><strong>+10,58%</strong><span>Δ RMSE completo (piora)</span></div><div class="stat"><strong>0 / 2</strong><span>Testes conjuntos BH significativos</span></div></div><div class="panel"><h3>Resultados nacionais comparáveis</h3><div id="nationalTable"></div></div><div class="boxnote">A identificabilidade do modelo nacional foi confirmada, mas sua adequação não: o BIC e o RMSE pioraram nos dois períodos, e o Ljung–Box rejeitou ausência de autocorrelação residual em ambos os SARIMAX.</div></section>
<section id="coef"><h2>Inferência: coeficientes e hipóteses</h2><p class="lede">Separar rejeição pontual de uma variável, relevância conjunta das exógenas e ganho preditivo. Essas três questões não são equivalentes.</p><div class="grid"><div class="stat"><strong>395</strong><span>Coeficientes exógenos avaliados nos modelos estaduais</span></div><div class="stat"><strong>2</strong><span>Coeficientes estaduais com BH global &lt;5%</span></div><div class="stat"><strong>0</strong><span>Testes conjuntos com BH estadual &lt;5%</span></div><div class="stat"><strong>0</strong><span>Coeficientes nacionais com BH global &lt;5%</span></div></div><div class="panel"><h3>Associações individuais que sobreviveram ao BH global</h3><p>Foram identificadas duas associações positivas com <strong>Enxurradas, em Pernambuco</strong>, uma no pré-pandemia e outra no completo. Mas os modelos correspondentes <b>pioraram</b> BIC e RMSE, e as hipóteses conjuntas não sobreviveram a BH.</p><div id="coeftable"></div></div><div class="boxnote">Os p-valores de coeficientes são condicionais à seleção de ordem e de regressores; não incorporam inferência pós-seleção exata. Não devem ser interpretados como prova causal ou confirmação isolada de efeitos robustos.</div></section>
<section id="conclusao"><h2>Conclusão</h2><p class="call">Foi possível executar as duas estratégias propostas, mas os dados não sustentam que o SARIMAX seja geralmente melhor que o SARIMA.</p><div class="split"><div class="panel"><h3>Estadual</h3><p>Após reduzir tipologias usando apenas informação de treino, 53 comparações foram possíveis. A melhora do RMSE ocorreu em 14, porém nenhum SARIMAX superou o SARIMA pelo BIC. A redução resolveu a estimabilidade, mas não produziu vantagem geral.</p></div><div class="panel"><h3>Nacional</h3><p>As 16 tipologias puderam ser incluídas simultaneamente em ambos os períodos, com posto completo e convergência. Em contrapartida, BIC e RMSE pioraram e houve sinais de autocorrelação residual nos modelos.</p></div></div><p>Os achados não comprovam ausência de impactos de desastres, nem permitem conclusão causal. Há esparsidade, classificação de eventos administrativos heterogênea, seleção de modelo, ausência de desastres futuros conhecidos para previsão operacional e limitações de adequação dos resíduos.</p></section>
<section id="reproducao"><h2>Reprodutibilidade</h2><p>A análise usa somente o painel mensal consolidado com SHA-256 documentado, sem republicar as bases originais. Código, auditoria, comparações e coeficientes estão organizados no GitHub.</p><div class="panel"><code>python src/sarimax_revisao_final.py nacional<br>python src/sarimax_revisao_final.py estadual<br>python src/gerar_relatorio_sarimax_revisao.py</code><p class="small">Todos os gráficos e tabelas desta página são incorporados ao HTML; o arquivo funciona offline.</p></div></section></main>
<script>const DATA={serialized};const $=x=>document.getElementById(x);const f=(v,k=2)=>v===null||v===undefined||!Number.isFinite(+v)?'—':Number(v).toLocaleString('pt-BR',{{minimumFractionDigits:k,maximumFractionDigits:k}});const good=v=>v<0?'good':'bad';
function table(container,columns,rows){{if(!rows.length){{$(container).innerHTML='<p class="empty">Nenhum resultado no filtro.</p>';return}}let out='<div class="tablewrap"><table><thead><tr>'+columns.map(c=>'<th>'+c[1]+'</th>').join('')+'</tr></thead><tbody>';for(const r of rows){{out+='<tr>'+columns.map(c=>{{let v=r[c[0]];let view=typeof v==='number'?f(v,c[2]??2):(v===null||v===undefined?'—':String(v));return '<td class="'+(c[0].includes('variacao')?'num '+(v<0?'good':'bad'):'num')+'">'+view+'</td>'}}).join('')+'</tr>'}}$(container).innerHTML=out+'</tbody></table></div>'}}
function stateTable(){{let p=$('tablePeriod').value;let q=$('searchUf').value.toUpperCase().trim();let rows=DATA.estaduais.filter(x=>x.periodo===p&&x.unidade.toUpperCase().includes(q));table('stateTable',[['unidade','UF'],['n_exog_incluidas','Nº exógenas',0],['ordem','ARMA'],['sazonal','Sazonal'],['rmse_sarima','RMSE SARIMA',3],['rmse_sarimax','RMSE SARIMAX',3],['variacao_rmse_pct','Δ RMSE (%)',2],['delta_bic_treino','Δ BIC',2],['lb_sarimax_treino','p Ljung–Box',3]],rows)}}
function audit(){{let p=$('auditPeriod').value;let rows=DATA.auditoria_estado.filter(x=>x.periodo===p);table('auditTable',[['unidade','UF'],['posto_treino','Posto no treino',0],['posto_completo','Posto amostra total',0],['n_constantes_treino','Colunas constantes treino',0]],rows)}}
function bars(){{let p=$('statePeriod').value;let rows=DATA.estaduais.filter(x=>x.periodo===p&&x.variacao_rmse_pct!==null).sort((a,b)=>$('stateSort').value==='asc'?a.variacao_rmse_pct-b.variacao_rmse_pct:b.variacao_rmse_pct-a.variacao_rmse_pct);let scale=Math.max(...rows.map(x=>Math.abs(x.variacao_rmse_pct)),5);$('bars').innerHTML=rows.map(x=>'<div class="barrow"><b>'+x.unidade+'</b><div class="track"><span class="bar '+(x.variacao_rmse_pct<0?'green':'')+'" style="left:0;width:'+Math.max(1,Math.abs(x.variacao_rmse_pct)/scale*100).toFixed(2)+'%"></span></div><span class="'+good(x.variacao_rmse_pct)+'">'+f(x.variacao_rmse_pct,1)+'%</span></div>').join('')}}
function national(){{table('nationalTable',[['periodo','Período'],['posto_exog_treino','Posto selecionadas',0],['rmse_sarima','RMSE SARIMA',3],['rmse_sarimax','RMSE SARIMAX',3],['variacao_rmse_pct','Δ RMSE (%)'],['delta_bic_treino','Δ BIC'],['p_conjunto_treino','p teste conjunto',3],['lb_sarimax_treino','p Ljung–Box',3]],DATA.nacionais)}}
function coef(){{let rows=DATA.coef_estado.filter(x=>x.q_bh_global!==null&&x.q_bh_global<.05);table('coeftable',[['periodo','Período'],['unidade','UF'],['tipologia','Tipologia'],['coef_original','Coeficiente'],['p','p individual',5],['q_bh_global','q BH global',4]],rows)}}
for(const id of ['statePeriod','stateSort'])$(id).addEventListener('change',bars);for(const id of ['tablePeriod','searchUf'])$(id).addEventListener('input',stateTable);$('auditPeriod').addEventListener('change',audit);document.querySelectorAll('nav a').forEach(e=>e.addEventListener('click',()=>document.querySelector('nav').classList.remove('show')));audit();stateTable();bars();national();coef();</script></body></html>'''
(REPORTS/'relatorio_sarimax_revisao_20261019.html').write_text(h,encoding='utf-8')
print('docs',len(md),'html',len(h),'notebooks',[(p.name,p.stat().st_size) for p in (ROOT/'notebooks').glob('3[23]*')])
