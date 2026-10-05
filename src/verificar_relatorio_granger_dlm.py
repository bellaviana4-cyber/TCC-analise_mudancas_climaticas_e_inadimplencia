"""Validação sem reestimar Granger/DLM: integridade, filtros e navegador offline."""
from pathlib import Path
import argparse, json, re
import numpy as np
from playwright.sync_api import sync_playwright
import relatorio_granger_dlm as report

def verify(path, screenshot_dir=None):
 path=Path(path).resolve();content=path.read_text();d=json.loads(re.search(r'<script id="report-data" type="application/json">(.*?)</script>',content,re.S).group(1));fresh=report.load()
 assert d==fresh,'HTML diverge das tabelas/escala atuais'
 assert '<script src=' not in content and 'cdn.' not in content,'Dependência externa essencial'
 assert len(d['gm'])==42 and len(d['m'])==552
 assert len([r for r in d['national'] if r['q_global_p_acumulado']<.05])==4
 assert len([r for r in d['national'] if r['q_global_p_conjunto']<.05])==10
 # Propriedade de soma e identidade entre C10 final e contraste acumulado.
 for acc in [r for r in d['cr'] if r['endpoint']=='acumulado']:
  key=lambda r:all(r[k]==acc[k] for k in ['periodo','coluna','especificacao','K'])
  curve=sorted([r for r in d['cr'] if key(r) and r['endpoint'].startswith('beta_')],key=lambda r:int(r['endpoint'].split('_')[-1]))
  assert np.isclose(sum(r['estimate'] for r in curve),acc['estimate'],atol=2e-8,rtol=1e-8)
  final=next(r for r in d['cr'] if key(r) and r['endpoint']=='C_'+str(acc['K']))
  for k in ['estimate','low','high','se']:
   assert np.isclose(final[k],acc[k],atol=2e-8,rtol=1e-8),(acc['id'],k)
 checked=0;errors=[];external=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':1440,'height':1050},accept_downloads=True,offline=True)
  page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:external.append(r.url) if r.url.startswith(('http:','https:')) else None)
  page.goto(path.as_uri());page.wait_for_function("document.querySelector('#dCoefficients table')!==null")
  page.click('[data-tab=dlm]')
  for period in ['Total','Pré']:
   page.select_option('#period',period)
   for level in ['Total','Grupo','Tipologia','Analítica']:
    page.select_option('#level',level)
    cols=page.locator('#exposure option').evaluate_all('(nodes)=>nodes.map(n=>n.value)')
    for col in cols:
     page.select_option('#exposure',col);page.select_option('#spec','Principal');page.select_option('#K','10')
     state=page.evaluate("""()=>({selected:$('selected').textContent,g:$('gText').textContent,d:$('dText').textContent,n:$('nText').textContent,beta:$('betaCaption').textContent,c:$('cCaption').textContent,station:$('stationText').textContent})""")
     name=next(r['exposicao'] for r in d['m'] if r['coluna']==col)
     assert name in state['selected'] and name.split(' | ')[-1] in state['station'],(period,col,state,errors)
     has=any(r['coluna']==col and r['periodo']==period and r['especificacao']=='Principal' and r['K']==10 for r in d['m'])
     if has:
      assert 'sem spline' in state['d'] and 'CR2' in state['d'] and 'CR2' in state['beta']
      # Valores plotados e rótulos de inferência provenientes da mesma linha.
      acc=next(r for r in d['cr'] if r['periodo']==period and r['coluna']==col and r['especificacao']=='Principal' and r['endpoint']=='acumulado')
      expected=page.evaluate('(x)=>f(x)',acc['p']);assert 'p='+expected in state['d']
     else:assert 'não estimável' in state['d']
     checked+=1
  # Grade K e desenhos: rótulos devem mudar, sem IC CR2 inventado para K<10.
  page.select_option('#period','Total');page.select_option('#level','Total')
  for k in range(1,11):
   page.select_option('#K',str(k));txt=page.locator('#betaCaption').inner_text()
   assert ('CR1S' if k<10 else 'CR2') in txt
  for spec in ['Com contemporâneo','Delta X']:
   page.select_option('#spec',spec);assert page.locator('#K').is_disabled();assert page.locator('#K').input_value()=='10'
  page.select_option('#spec','Principal');page.select_option('#level','Tipologia');page.select_option('#exposure','tipo_granizo')
  assert '0,00026873' in page.locator('#gText').inner_text()
  page.click('[data-tab=granger]');assert page.locator('#granger').is_visible() and not page.locator('#dlm').is_visible()
  if screenshot_dir:
   dest=Path(screenshot_dir);dest.mkdir(parents=True,exist_ok=True);page.locator('#explorar').scroll_into_view_if_needed();page.screenshot(path=str(dest/'granger_granizo.png'))
  page.select_option('#exposure','tipo_onda_de_frio');page.click('[data-tab=dlm]');assert page.locator('#dlm').is_visible()
  if screenshot_dir:page.locator('#dlm').scroll_into_view_if_needed();page.screenshot(path=str(dest/'dlm_frio.png'))
  page.click('[data-tab=national]');assert page.locator('#national').is_visible()
  if screenshot_dir:page.locator('#national').scroll_into_view_if_needed();page.screenshot(path=str(dest/'nacional_frio.png'))
  with page.expect_download() as download:page.click('#export')
  if screenshot_dir:download.value.save_as(str(dest/'exportacao_teste.csv'))
  assert download.value.suggested_filename.endswith('.csv')
  page.select_option('#exposure','tipo_onda_de_calor_e_baixa_umidade');page.select_option('#period','Pré')
  assert 'não estimável' in page.locator('#dText').inner_text()
  assert not errors,errors;assert not external,external
  browser.close()
 return {'status':'aprovado','combinacoes_periodo_nivel_exposicao':checked,'horizontes_testados':10,'desenhos_testados':3,'erros_javascript':errors,'requisicoes_externas':external,'exportacao':'aprovada','comparacao_fontes':'identidade exata do payload','contrastes':'soma beta e C final/IC conferidos'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('html');p.add_argument('--screenshots');args=p.parse_args();print(json.dumps(verify(args.html,args.screenshots),indent=2,ensure_ascii=False))
