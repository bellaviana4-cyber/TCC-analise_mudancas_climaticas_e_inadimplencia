"""Notebook de reprodução, sem importar nem sobrescrever o notebook 22."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
cells=[]
def md(s):cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(True)))
def code(s):cells.append(dict(cell_type='code',metadata={},source=s.splitlines(True),execution_count=None,outputs=[]))
md(r'''# 23 · DLM em painel: escolha do horizonte por AIC
Isabella Viana Bambirra · Estatística/UFSCar · revisão solicitada em 06/10/2026.

Referência atual: escolher separadamente **K=1,...,24** por exposição e período. A versão K6 do notebook 22 permanece histórica. Granger não é reestimado; SARIMAX não é executado. O capítulo orienta o DLM clássico; os dados atuais definem recortes e unidade.

A pergunta é se mudanças logarítmicas dos registros de desastres se associam às mudanças logarítmicas da inadimplência contemporânea e nos meses seguintes, com efeitos fixos de UF e mês-ano. AIC escolhe o horizonte do ajuste; não estabelece duração física ou causalidade.''')
code('''from pathlib import Path
import sys,json
import numpy as np,pandas as pd
from threadpoolctl import threadpool_limits
ROOT=Path.cwd()
if ROOT.name=='notebooks':ROOT=ROOT.parent
sys.path.insert(0,str(ROOT/'src'))
import dlm_painel_log_aic as m
print('Candidatos: K=1,...,24; contemporâneo incluído; DK fixo em',m.DK_L)
print((ROOT/'docs/dlm_painel_log_historico.json').read_text())''')
md(r'''## 1. Desenho e regras definidas antes da execução
$$y_{it}=\Delta\log(I_{it}),\quad x_{it}=\Delta\log(1+D_{it}),\qquad y_{it}=\alpha_i+\lambda_t+\sum_{k=0}^{K^*}\beta_kx_{i,t-k}+\varepsilon_{it}.$$

27 UFs, sem ponderação; todos estados ficam nos modelos. São efeitos fixos completos de mês-ano, não 11 dummies sazonais. Sem lags de y, spline ou regime. Um modelo por exposição, sem incluir categorias sobrepostas simultaneamente.

K* minimiza o AIC na amostra comum elegível para K24. Manter essa amostra no modelo escolhido separa a mudança de K da mudança de dados. p, IC e BH usuais tratam o K selecionado como fixo e ignoram a incerteza de seleção. Não houve inferência seletiva formal; as rejeições são exploratórias. AIC gaussiano é um critério de trabalho sob dependência residual.''')
code("print((ROOT/'docs/dlm_painel_log_aic_protocolo.md').read_text())")
md('''## 2. Crédito, calendário e fonte da exposição
Conferir 27×144 células, chave única, TI=100CI/CA e carteiras positivas. Ausência não vira zero. Conferir hashes das entradas com a execução histórica antes de reusar a medida administrativa. D é contagem de linhas do Atlas, não eventos físicos únicos ou intensidade. Identificador: hash da fonte + número de linha. Agregação por Data_Evento.

Total climático selecionado uma única vez por COBRADE 12/13/14; grupos e tipologias Atlas complementares. Não somar categorias sobrepostas.''')
code('''old=json.loads((ROOT/'outputs/tables/dlm_painel_log/manifest.json').read_text())
for path,h in old['inputs'].items():
    if path.startswith('data/'):assert m.sha(ROOT/path)==h,path
d,labels=m.audit()
print(pd.read_csv(m.OUT/'auditoria.csv').to_string(index=False))
print(pd.read_csv(m.OUT/'reconciliacao_atlas.csv').to_string(index=False))
print(pd.read_csv(m.OUT/'taxonomia.csv').to_string(index=False))''')
md('''**Leitura:** contagens administrativas conciliadas preservam comparabilidade com o notebook 22. Biológicos, tecnológicos e geológicos ficam fora do central, ainda que chuva possa desencadear movimentos de massa. Rótulos Chuvas Intensas/Onda de Frio/Baixa Umidade têm ambiguidades de códigos documentadas. Isso impede atribuir todos rótulos diretamente a fenômenos climáticos homogêneos ou ao aquecimento antropogênico.''')
md(r'''## 3. Estacionariedade das séries transformadas por UF
Primeiro log, depois diferença, dentro da UF e do recorte; nunca log de uma diferença que pode ser negativa.

ADF: $\Delta z_t=c+\gamma z_{t-1}+\sum_j\phi_j\Delta z_{t-j}+u_t$, $H_0:\gamma=0$ (raiz unitária), $H_1:\gamma<0$.

KPSS: $z_t=c+r_t+u_t$, $r_t=r_{t-1}+\eta_t$, $H_0:\operatorname{Var}(\eta)=0$ (estacionariedade em torno do intercepto), $H_1:\operatorname{Var}(\eta)>0$.

ADF com intercepto/AIC; KPSS intercepto/banda auto. Ambos não rejeitar é inconclusivo; não rejeição KPSS não confirma estacionariedade. Reportar limites tabulares, constantes, lags e n. Diagnóstico sobre séries completas transformadas no recorte, não certificado específico da subamostra de seleção.''')
code('''st=m.stationarity(d,labels)
print(st.groupby(['periodo','exposicao','classificacao']).size().to_string())
print(st[(st.exposicao=='inadimplencia') & (st.classificacao=='desfavorável')][['periodo','uf','ADF_p','KPSS_p']].to_string(index=False))''')
md('''**Leitura:** Δlog(I) permanece inconclusiva em 19 UFs no pré e 8 no total; desfavorável em RO/SC no pré e RO no total. Preservar a transformação não transforma os diagnósticos em favoráveis. FE e erros robustos não corrigem raiz unitária. CIPS histórico em ΔI/cobertura e diagnóstico nacional não validam estas séries estaduais. A análise permanece exploratória.''')
md(r'''## 4. Todos os candidatos em amostra comum
$$\operatorname{AIC}(K)=n[\log(2\pi)+1+\log(\operatorname{SQR}_K/n)]+2[27+T-1+(K+1)].$$

A escala não entra na contagem, seguindo OLSResults; incluir a escala adicionaria constante 2 a todos AIC. FE são contados. Minimizar AIC separado por exposição/recorte, empate numérico 1e−8 favorece menor K; ΔAIC≤2 indica candidatos próximos, sem alterar a regra do mínimo.

Primeira equação fev/2015: perder 1 mês pela diferença e 24 pelos lags, total 675 células/recorte. Pré N=1620 (60×27), total N=3213 (119×27). Nenhum candidato recupera meses retirados. Verificar suporte tanto na janela original quanto na amostra comum, rank e condição; não usar pseudoinversa silenciosa.''')
code('''with threadpool_limits(limits=1):r=m.estimate(d,labels,st)
print(pd.read_csv(m.OUT/'selecao_K.csv').to_string(index=False))
print(pd.read_csv(m.OUT/'amostras_suporte.csv').to_string(index=False))
print(pd.read_csv(m.OUT/'candidatos_AIC.csv').query("exposicao=='total_climatico'")[['periodo','K','N','AIC','delta_AIC','selecionado','status']].to_string(index=False))''')
code('''sel=pd.read_csv(m.OUT/'selecao_K.csv')
print('Distribuição de K selecionado:')
print(sel.groupby(['periodo','K']).size().to_string())
print('Candidatos próximos não certificam um único horizonte:')
print(sel[['periodo','rotulo','K','K_delta_AIC_ate2','fronteira','status']].to_string(index=False))''')
md('''**Interpretação:** K pode diferir entre desastres e períodos, mas não precisa. K1/K24 são limites da grade, não duração comprovada; no limite superior o horizonte pode estar truncado. Somatórios com K distintos são associações acumuladas em horizontes distintos. A seleção é pelo ajuste, jamais pelo menor p.''')
md('''## 5. Validação independente e diagnósticos
CR1 por UF, correção G/(G−1)×(n−1)/(n−p_total), t26/Wald F(r,26). DK6, scores mensais/Bartlett, n/(n−p_total), t(T−1)/F(r,T−1). A banda DK6 é fixa e diferente de K do DLM. Cluster por UF não resolve dependência transversal.

Comparar FWL com dummies explícitas nas centrais (K selecionado e extremos 1/24), incluindo AIC, β e CR1; DK com statsmodels. Covariância da soma inclui todos elementos. Condicionamento, VIF, correlação dos lags, influência, autocorrelação e dependência residual são registrados, sem excluir UFs pelo p.''')
code('''print(pd.read_csv(m.OUT/'validacao.csv').to_string(index=False))
print(pd.read_csv(m.OUT/'diagnosticos.csv').to_string(index=False))
print(pd.read_csv(m.OUT/'influencia_uf.csv').query("exposicao=='total_climatico'").sort_values('share_variancia_acumulado',ascending=False).head(8).to_string(index=False))''')
md('''**Leitura dos diagnósticos:** testes residuais são descritivos e não certificam a regressão. CD ingênuo sob efeitos temporais não é calibrado; Levene pressupõe independência. Poucas UFs efetivamente expostas e K longos podem fragilizar testes conjuntos (25 coeficientes em K24 versus 27 clusters). DK não corrige exogeneidade, seleção de K ou estacionariedade.''')
md(r'''## 6. Associações contemporâneas, defasadas e acumuladas
Reportar β0, soma0K, soma1K, conjuntos0K/1K, perfis e IC95% pontuais. $\operatorname{Var}(c'\hat\beta)=c'\hat Vc$, não soma dos erros padrão. BH por período×nível×covariância×endpoint; indisponíveis ficam na família apenas como p=1 no ajuste, sem p observado fictício. BH não remove seleção AIC.''')
code('''print(r[r.exposicao=='total_climatico'][['periodo','K','covariancia','endpoint','estimate','low','high','p','q_BH']].to_string(index=False))
print('Todas rejeições BH, sem selecionar apenas favoráveis:')
print(r[r.q_BH<.05][['periodo','K','rotulo','covariancia','endpoint','estimate','p','q_BH']].to_string(index=False))
for per in m.PERIODS:
    z=r[(r.periodo==per)&(r.exposicao=='total_climatico')&(r.endpoint=='soma0K')]
    for row in z.itertuples():
        print(f'{per}, K={row.K}, {row.covariancia}: associação acumulada={row.estimate:.6f}, IC95%=[{row.low:.6f},{row.high:.6f}], p={row.p:.6f}, q={row.q_BH:.6f}. '+('Rejeição exploratória a 5%, ignorando a seleção de K.' if row.q_BH<.05 else 'Sem rejeição a 5%.'))''')
md('''**Interpretação:** sinal não basta para afirmar associação; não rejeição não prova ausência. Conjunto pode rejeitar e soma não, porque sinais opostos se compensam. Sensibilidade CR1/DK e suporte devem acompanhar p e q. P distintos em janelas sobrepostas não demonstram mudança temporal. Resultados usuais após seleção continuam exploratórios; não houve inferência seletiva formal.''')
md('''## 7. Perfis e cenários na escala correta
β mede associação entre mudanças logarítmicas, não pontos percentuais ou elasticidade simples em D. C(h) soma β até h: resposta acumulada em log(I) a um pulso unitário em Δlog1p(D). Bandas pontuais, não simultâneas.

Aumento persistente 0→1 registro: pulso log2 na diferença. Pulso de um mês em D: +log2 seguido de −log2. Resposta é convolução com β; acumular em log(I), converter por 100[exp(resposta)−1]. São cenários algébricos condicionais, não previsão causal de desastre físico.''')
code('''m.figures()
for per in m.PERIODS:
    emit('image/svg+xml',(m.FIG/(m.slug(per)+'_total_climatico.svg')).read_text())
print(pd.read_csv(m.OUT/'cenarios.csv').query("exposicao=='total_climatico' and covariancia=='CR1'").to_string(index=False))
m.manifest()
print(json.loads((m.OUT/'manifest.json').read_text())['versoes'])''')
md('''**Revisão de suporte e testes conjuntos:** Onda de Frio pré foi bloqueada pela regra de suporte contemporâneo (4 UFs); em K24 suas regressoras alcançam 6 UFs e têm posto completo, sem garantir inferência confiável. Regra original mantida. Covariâncias CR1 padronizadas dos testes conjuntos têm condição aproximada 37.463 em Calor/Baixa Umidade total, 13.312 em Chuvas Intensas total e 8.627 no pré. P muito pequeno não constitui evidência conclusiva; 27 UFs não são igualmente informativas. Mantém-se a especificação nos casos inconclusivos com não rejeição KPSS, documentando também os casos desfavoráveis.''')
md('''## 8. Conclusão e reprodução
A escolha de K é específica da exposição e recorte, na mesma amostra entre candidatos. O ganho é ampliar o horizonte sem impô-lo igualmente a todos desastres; o custo é perder meses e introduzir incerteza de seleção não incorporada aos IC usuais. O painel é estimável quando há suporte e rank, mas não é apresentado como validado. Associação temporal, precedência preditiva de Granger e causalidade são conceitos diferentes.

Exogeneidade estrita condiciona todo histórico de x e FE; origem natural não garante causalidade. Normalidade/homocedasticidade não são condições universais da consistência de MQO robusto. Almon não foi necessário; fórmulas corretas Z0=Σx e Zj=Σk^j x, β=Ba, Vβ=BV_aB′ ficam no protocolo histórico, com correções incorporadas ao capítulo.

Entradas nos caminhos do manifesto; instalar requirements-dlm-painel-log.lock.txt. Executar `python src/executar_notebook_painel_log.py notebooks/23_dlm_painel_selecao_aic_1a24.ipynb`, depois `python src/relatorio_dlm_painel_log_aic.py` e `python src/verificar_dlm_painel_log_aic.py`. O executor usa compile/exec em namespace compartilhado, com stdout e figuras reais, sem simular saídas. O notebook 22 e seus resultados ficam preservados.''')
for i,c in enumerate(cells):
 c['id']='dlm-aic-'+str(i)
 if c['cell_type']=='markdown':c['source']=[line.replace('\\\\','\\') for line in c['source']]
nb=dict(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3'}},nbformat=4,nbformat_minor=5)
(ROOT/'notebooks/23_dlm_painel_selecao_aic_1a24.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1))
