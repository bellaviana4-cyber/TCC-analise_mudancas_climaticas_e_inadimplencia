from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
cells=[]
def md(s):cells.append({'cell_type':'markdown','metadata':{},'source':s.splitlines(True)})
def code(s):cells.append({'cell_type':'code','metadata':{},'source':s.splitlines(True),'execution_count':None,'outputs':[]})
md('''# 22 · DLM clássico em painel: desastres e inadimplência
Isabella Viana Bambirra · Estatística/UFSCar · 06/10/2026.

Referência atual de DLM. Capítulo de metodologia orienta o desenho; dados atuais definem aplicação. Versões 16–21 continuam históricas nas branches documentadas, sem mesclar alterações experimentais. Granger não é reestimado e SARIMAX não é executado.

A pergunta é se mudanças logarítmicas nos registros estão associadas à mudança logarítmica da inadimplência no mesmo mês e nos seis meses seguintes, depois de controlar UF e mês-ano. O caráter é **exploratório**, com validade condicionada à estacionariedade, exogeneidade e estabilidade não comprovadas.''')
code('''from pathlib import Path
import sys, json
import numpy as np, pandas as pd
from threadpoolctl import threadpool_limits
ROOT=Path.cwd()
if ROOT.name=='notebooks': ROOT=ROOT.parent
assert (ROOT/'src/dlm_painel_log.py').exists(), 'Execute a partir da raiz ou de notebooks'
sys.path.insert(0,str(ROOT/'src'))
import dlm_painel_log as m
print((ROOT/'docs/dlm_painel_log_historico.json').read_text())
print('K fixo:',m.K,'; não há seleção por p, AIC/BIC ou AR')''')
md('''## 1. Decisões e teoria efetivamente aplicada
A transformação ocorre antes da diferença: $y_{it}=\\log(I_{it})-\\log(I_{i,t-1})$, $x_{it}=\\log(1+D_{it})-\\log(1+D_{i,t-1})$. Não é log da diferença.

$$y_{it}=\\alpha_i+\\lambda_t+\\sum_{k=0}^{6}\\beta_k x_{i,t-k}+\\varepsilon_{it}.$$

São 27 UFs em todas aplicações, sem ponderação. Efeitos temporais completos são uma dummy para cada mês-ano, não apenas sazonalidade. K=6 é uma janela substantiva de curto prazo, fixa antes dos resultados; associações além dela não são avaliadas. Sete coeficientes livres, sem defasagens de y. A tabela de decisões detalha razões e consequências.''')
code("print((ROOT/'docs/dlm_painel_log_protocolo.md').read_text())")
md('''## 2. Conferência de crédito e registros
Exigimos chave única, calendário completo, dados de crédito positivos e razão TI=100CI/CA. Ausência de crédito interrompe a execução. D conta linhas administrativas; protocolo e identificador físico da linha são auditados. Não se deduplica pela significância.

Total climático: selecionar diretamente COBRADE 12/13/14, sem somar grupos/tipologias sobrepostos. Geológicos, biológicos e tecnológicos ficam fora do central. Rótulos Atlas preservados nas aplicações complementares.''')
code("d,labels=m.audit()\nprint(pd.read_csv(m.OUT/'auditoria.csv').to_string(index=False))\nprint(pd.read_csv(m.OUT/'reconciliacao_atlas.csv').to_string(index=False))\nprint(pd.read_csv(m.OUT/'taxonomia.csv').to_string(index=False))")
md('''**Interpretação da auditoria:** 3.888 UF-mês, 27×144; 40.339 registros, dos quais 37.643 em COBRADE 12/13/14. As 101 repetições de chave municipal-data-código permanecem em A. Protocolos são distintos nesta fonte, mas não identificam tempestades físicas únicas. Zero significa ausência de linha na fonte reconciliada, não ausência de desastre no mundo real.

Chuvas Intensas inclui código 13310 (onda de calor); Onda de Frio inclui 13120 (frentes frias/zonas de convergência); 14140 é baixa umidade. Não atribuir esses rótulos a fenômenos físicos homogêneos nem às mudanças climáticas antropogênicas.''')
md('''## 3. Estacionariedade nas séries estaduais transformadas
ADF com intercepto e AIC dentro de limite máximo previamente definido; KPSS com intercepto e banda automática. As UFs são testadas separadamente, sem concatenar estados.

ADF: $\\Delta z_t=c+\\gamma z_{t-1}+\\sum_j\\phi_j\\Delta z_{t-j}+u_t$; $H_0:\\gamma=0$, $H_1:\\gamma<0$.

KPSS: $z_t=c+r_t+u_t$, $r_t=r_{t-1}+\\eta_t$; $H_0:\\operatorname{Var}(\\eta_t)=0$, $H_1:\\operatorname{Var}(\\eta_t)>0$.

Ambos p≥0,05 são inconclusivos. KPSS não rejeitar não comprova estacionariedade; p=0,10 é limite superior da tabela. Com tendência, a hipótese seria estacionariedade em torno da tendência, não do intercepto. Séries constantes ficam registradas como indisponíveis.''')
code("st=m.stationarity(d,labels)\nprint(st.groupby(['periodo','exposicao','classificacao']).size().to_string())\nprint(st[(st.exposicao=='inadimplencia') & (st.classificacao=='desfavorável')][['periodo','uf','ADF_p','KPSS_p','ADF_lag','KPSS_lag']].to_string(index=False))")
md('''**Interpretação:** em Δlog(I), pré: 6 favoráveis, 19 inconclusivas e 2 desfavoráveis (RO, SC); total: 18 favoráveis, 8 inconclusivas e 1 desfavorável (RO). Não alterar a transformação para obter p favorável. A evidência desfavorável impede apresentar o painel completo como validado e limita as inferências a associações exploratórias condicionais. FE/covariância robusta não corrigem raiz unitária.

Os resultados nacionais informados (ADF≈0,343 no pré e ≈0,021 no total; KPSS≥0,10) não são comprovação estadual. CIPS histórico de ΔI e cobertura é uma evidência em outras unidades/transformações, não um teste novo destas séries.''')
code("print('CIPS histórico, transformação diferente:')\nprint(pd.read_csv(ROOT/'docs/historico_dlm/cips_delta_I.csv').to_string(index=False))\nprint(pd.read_csv(ROOT/'docs/historico_dlm/cips_cobertura.csv').head(12).to_string(index=False))")
md('''## 4. Construção de lags, amostras e identificação
Diferenças e lags dentro de UF e recorte, sem meses anteriores inventados. Primeira equação ago/2013: perder 1 mês de diferença + 6 para lags em cada UF. Pré e total são sobrepostos.

MQO por FWL: remover médias de UF e de mês-ano e devolver média geral no painel balanceado. Identificação exige posto completo e variação após ambos FE. Não recorrer a pseudoinversa para declarar identificação.

Inferência CR1, 27 clusters, t26 e Wald F(r,26). DK6 usa Bartlett em scores mensais, correção finita e t(T−1)/F(r,T−1), como comparação única diante da dependência transversal. Suporte insuficiente não recebe teste.''')
code("with threadpool_limits(limits=1):\n    r=m.estimate(d,labels,st)\nprint(pd.read_csv(m.OUT/'amostras_suporte.csv').to_string(index=False))\nprint(pd.read_csv(m.OUT/'modelos.csv').to_string(index=False))")
md('''**Interpretação da amostra:** pré 2.106 observações (78×27), total 3.699 (137×27), com todas UFs. Cada janela perde 189 células no início. Categorias sem suporte não se tornam modelos estaduais ou outra metodologia.

## 5. Validação e diagnósticos
Conferir coeficientes e CR1 com MQO de dummies explícitas nas aplicações centrais; conferir DK contra implementação independente de statsmodels. Variância da soma usa $\\mathbf{1}'V\\mathbf{1}$, incluindo covariâncias. Matrizes de covariância completas são exportadas.

Ljung–Box por UF é diagnóstico residual descritivo; não substitui cluster. Correlações residuais entre UFs justificam DK. CD ingênuo após efeitos fixos temporais não fornece teste calibrado, pois a centralização temporal induz correlação. Levene é descritivo por depender de independência. Influência é medida por alavancagem e scores das UFs, sem excluir estados para obter significância.''')
code("print(pd.read_csv(m.OUT/'validacao.csv').to_string(index=False))\nprint(pd.read_csv(m.OUT/'diagnosticos.csv').to_string(index=False))\nprint(pd.read_csv(m.OUT/'autocorrelacao_uf.csv').groupby(['periodo','lag']).p.apply(lambda s:(s<.05).sum()).to_string())\nprint(pd.read_csv(m.OUT/'influencia_uf.csv').query(\"exposicao=='total_climatico'\").sort_values('share_variancia_acumulado',ascending=False).head(8).to_string(index=False))")
md('''**Limitações:** há dependência residual entre estados e variação de dispersão. A correlação média absoluta residual central é aproximadamente 0,169 no pré e 0,173 no total. DK não transforma o desenho em causal nem elimina mudanças na dinâmica. Condicionamento e correlação dos lags centrais permitem o DLM irrestrito; Almon não foi necessário.

Correções do capítulo: exogeneidade estrita deve condicionar todo o histórico de x e FE; origem natural não basta. Normalidade/homocedasticidade não são condições universais da consistência de MQO robusto. Para Almon, se futuramente necessário, $Z^{(0)}=\\sum_{k=0}^Kx_{t-k}$ e $Z^{(j)}=\\sum_{k=0}^Kk^jx_{t-k}$; $\\beta_k=\\sum_{j=0}^qa_jk^j$, $V_\\beta=BV_aB'$. Potências brutas não garantem menor correlação. Não se usa Almon nesta execução.''')
md('''## 6. Resultados e multiplicidade
Endpoints separados: β0, soma0:6, soma1:6, conjunto0:6 e conjunto1:6. BH por período × nível × covariância × endpoint; categorias indisponíveis mantêm a família com p=1 apenas para ajuste conservador. Seus testes continuam ausentes. Perfis individuais são descritivos com IC95% pontuais, não simultâneos.''')
code("print(r[r.exposicao=='total_climatico'][['periodo','covariancia','endpoint','estimate','low','high','p','q_BH']].to_string(index=False))\nprint('Todas rejeições BH por categoria:')\nprint(r[r.q_BH<.05][['periodo','rotulo','covariancia','endpoint','estimate','p','q_BH']].to_string(index=False))")
md('''**Interpretação central:** soma0:6 pré=0,002709, IC CR1 [−0,006075;0,011493], p=0,532; total=0,004372, IC [−0,001265;0,010009], p=0,123. DK6: p≈0,455/0,056. Não há rejeição central a 5%; isso não prova ausência de associação. P diferentes nas janelas sobrepostas não demonstram mudança temporal.

Movimento de Massa no total tem soma rejeitada após BH/CR1, mas não após BH/DK6. Trata-se de categoria geológica complementar fora do total climático central. Resultados conjuntos podem existir sem soma diferente de zero, por compensação entre lags. Categorias concentradas e diagnósticos desfavoráveis exigem ressalvas mesmo quando p/q são pequenos.''')
code("m.figures()\nfor per in m.PERIODS:\n    p=m.FIG/(m.slug(per)+'_total_climatico.svg')\n    emit('image/svg+xml',p.read_text())")
md('''## 7. Cenários na escala correta
βk relaciona mudança logarítmica de registros à mudança logarítmica de I no lag k, condicionada a lags e FE. Não é ponto percentual ou elasticidade simples em D.

Contraste 0→1 registro: δx=log2. Aumento persistente no nível D gera um pulso em Δlog1p(D). Pulso de um mês em D gera +log2 e depois −log2. Convoluir ambas mudanças com β, acumular em log(I) e converter $100[\\exp(\\text{resposta acumulada})-1]$. Os cenários são contrafactuais algébricos condicionais, não previsão causal de um desastre físico.''')
code("sc=pd.read_csv(m.OUT/'cenarios.csv')\nprint(sc[(sc.exposicao=='total_climatico') & (sc.covariancia=='CR1')].to_string(index=False))\nm.manifest()\nprint(json.loads((m.OUT/'manifest.json').read_text())['versoes'])")
md('''**Conclusão:** o desenho solicitado é estimável para exposições com suporte, mas permanece exploratório. O total climático não apresenta evidência robusta de associação acumulada no horizonte de seis meses nesta execução. A análise não estabelece causalidade, não atribui registros a mudanças climáticas antropogênicas e não testa ausência de efeito. Transformações iguais mantêm a definição da variável; não resolvem diagnósticos, dependência ou dinâmica instável.

Reprodução: colocar as duas entradas nos caminhos indicados no manifesto; instalar requirements-dlm-painel-log.lock.txt; executar este notebook na raiz/notebooks ou `python src/executar_notebook_painel_log.py notebooks/22_dlm_painel_diferencas_logaritmicas.ipynb`. O executor registra saídas reais em namespace Python compartilhado, sem simular execução. HTML: `python src/relatorio_dlm_painel_log.py`.''')
nb={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3'}},'nbformat':4,'nbformat_minor':5}
for i,c in enumerate(cells):c['id']='dlm-log-'+str(i)
(ROOT/'notebooks/22_dlm_painel_diferencas_logaritmicas.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1))
if __name__=='__main__':print('Notebook criado')
