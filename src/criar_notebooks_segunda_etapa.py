"""Gera narrativas e células; execução é separada, não substitui análise."""
from pathlib import Path
import nbformat as n
ROOT=Path(__file__).resolve().parents[1]
INIT="""from pathlib import Path
import sys
ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.insert(0, str(ROOT/'src'))
from segunda_etapa import *
from IPython.display import display, Markdown
import matplotlib.pyplot as plt
plt.rcParams.update({'figure.figsize':(12,5),'font.size':11})
pd.set_option('display.max_columns', 20)
def tabela(d):
    display(d.round(5))
def resumo(d):
    tabela(d.groupby(['Família','Período','Categoria resultado']).size().reset_index(name='Modelos'))
"""
def make(num,name,title,items):
    cells=[n.v4.new_markdown_cell(title),n.v4.new_markdown_cell('Esta etapa é uma extensão informada pelos resultados anteriores. Consulte `docs/segunda_etapa_protocolo.md`, registrado no GitHub antes dos testes. Precedência preditiva e associações condicionais não identificam causalidade estrutural.'),n.v4.new_code_cell(INIT)]
    for kind,txt in items:cells.append(n.v4.new_markdown_cell(txt) if kind=='md' else n.v4.new_code_cell(txt))
    nb=n.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}})
    n.write(nb,ROOT/'notebooks'/f'{num}_{name}.ipynb')
make('10','dinamica_nacional_segunda_etapa','# 10 — Dinâmica nacional: uma equação própria para a inadimplência',[
('md','## 1. Retomada sem recalcular 05–09\nA tabela anterior é lida e as hipóteses repetidas por AIC/BIC são contadas uma única vez. Os hashes das entradas são preservados. A taxa nacional é reconstruída pela razão das somas de carteiras.'),
('code',"tabela(previous())\ns=historical_series()\ntabela(s.describe().T)"),
('md','## 2. Por que ordens diferentes?\nO VAR anterior obrigava o mesmo lag nas duas equações. Aqui ΔI tem lags próprios selecionados por BIC e um termo sazonal no lag12. A exposição possui de um a três lags; médias sazonais são controladas com 11 dummies. A amostra comum impede que um candidato pareça melhor apenas por usar outras datas. O ótimo incluindo q=0 é registrado. As ordens positivas selecionadas não tornam o teste confirmatório: a incerteza pós-seleção permanece.'),
('code',"r=national()\nresumo(r)\ntabela(r[['Período','Exposição','Família','p próprio','q exposição','q0 preferido','n efetivo','p clássico','p','p BH','BG1 p','BG12 p','CUSUM p','Raiz própria','Diagnóstico favorável']])"),
('md','## 3. Estacionariedade e quebras\nADF usa H0 raiz unitária; KPSS usa H0 estacionariedade. A concordância é triagem, sem comprovação. ZA permite uma quebra endógena: sua data estimada não constitui um experimento. A janela pandêmica fixa é sensibilidade em outra família; não substitui a especificação principal por apresentar p menor.'),
('code',"tabela(read('estacionariedade_historico'))\ntabela(read('quebras'))\ntabela(read('estabilidade_interacoes'))"),
('md','## 4. Efeitos e diagnósticos\nO teste conjunto pergunta se os lags adicionam informação. A soma de coeficientes em pp por mudança de log-exposição não é uma resposta causal nem um efeito acumulado estrutural. IC HAC pontuais não incorporam seleção. Cook aponta observação influente: ela é retirada apenas em sensibilidade, não permanentemente. HAC não corrige dinâmica inadequada.'),
('code',"tabela(r[['Período','Exposição','Família','Soma coeficientes','IC baixo','IC alto','BP p','ARCH3 p','RESET p','Mês influente','Δ soma influência','Categoria resultado']])\nfigura_nacional(r)"),
('md','## 5. Comparação e decisões de robustez\nBG avalia a equação de inadimplência; Portmanteau antigo avalia o sistema. Não comparar percentuais como se fossem o mesmo teste. Toda–Yamamoto depende da triagem definida previamente. Bootstrap temporal e simulação de poder não serão usados para resgatar um modelo reprovado.'),
('code',"tabela(ty(['Total nacional'],extra=False))\ntabela(decisions())\ncheckpoint('10')"),
])
make('11','exposicao_gravidade_segunda_etapa','# 11 — Frequência, abrangência e gravidade dos desastres',[
('md','## 1. O que as medidas representam\nProtocolos medem frequência de registros; municípios distintos medem abrangência. Deslocamento e habitações medem registros de danos, sem indivíduos/imóveis únicos. Não somamos componentes a totais. Campos ausentes propagam ausência no agregado; nenhum protocolo gera zero observado. Zeros preenchidos na fonte não garantem que o dano foi investigado.'),
('code',"a,v=exposure()\ntabela(a)\ntabela(v)\ntabela(read('sobreposicoes'))\ntabela(read('monetarios'))"),
('md','## 2. Foco climático e cobertura\nO foco usa COBRADE12/13/14, mantendo o grupo e a tipologia originais. Eventos geológicos podem ser desencadeados por chuva, mas isso não está certificado em cada registro; ficam na comparação histórica. Valores monetários não entram na inferência porque o mês-base desta extração não foi confirmado; deflacioná-los novamente poderia produzir erro.'),
('code',"tabela(read('classificacao_climatica'))\ntabela(read('cobertura_ano'))\ntabela(read('cobertura_uf'))\ntabela(read('correlacao_indicadores'))\nfigura_exposicao()"),
('md','## 3. Modelos de exposição\nAplicamos a mesma regra registrada na etapa10. A família nacional preserva50 hipóteses, incluindo categorias inelegíveis com p=1 apenas no ajuste. Não recalculamos os modelos históricos, apenas completamos as oito hipóteses de exposição reservadas.'),
('code',"r=national(EXPOS,extra=True)\nresumo(r)\ntabela(r[r.Exposição.isin(EXPOS)])\nfigura_nacional(r[r.Exposição.isin(EXPOS)])"),
('md','## 4. Disponibilidade temporal\nData_Registro permite descrever atrasos, mas não reconstrói vintages de publicação e revisões. O exercício posterior de previsão é pseudo-OOS com dados revisados; não certifica uso operacional em tempo real.'),
('code',"tabela(read('disponibilidade_atlas'))\ntabela(ty(['Clima | Protocolos'],extra=True))\ntabela(decisions())\ncheckpoint('11')"),
])
