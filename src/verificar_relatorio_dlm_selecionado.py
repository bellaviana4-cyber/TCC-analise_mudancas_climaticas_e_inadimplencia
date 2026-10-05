"""Valida dados, filtros, desenhos, exportação e abertura offline do HTML atual."""
from pathlib import Path
import argparse,json,re
import pandas as pd
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

def verify_baseline(path,screenshots=None):
 path=Path(path).resolve();html=path.read_text()
 data=json.loads(re.search(r'<script id="selected-data" type="application/json">(.*?)</script>',html,re.S).group(1))
 for name in ['painel','nacional','painel_perfis','nacional_perfis','painel_candidatos','nacional_candidatos','cobertura']:
  df=pd.read_csv(ROOT/'outputs/tables/dlm_selecionado'/f'{name}.csv')
  assert data[name]==df.astype(object).where(pd.notna(df),None).to_dict('records'),name
 for name in ['nacional_diagnosticos','nacional_influencia','nacional_estabilidade','painel_conferencia']:
  df=pd.read_csv(ROOT/'outputs/tables/revisao_integrada'/f'{name}.csv')
  assert data['review_'+name]==df.astype(object).where(pd.notna(df),None).to_dict('records')
 assert len(data['painel'])==len(data['nacional'])==46
 assert len([r for r in data['nacional'] if r['q']<.05])==3
 assert len([r for r in data['painel'] if r['q']<.05])==0
 errors=[];external=[];checked=0
 dest=Path(screenshots) if screenshots else None
 if dest:dest.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as p:
  browser=p.chromium.launch(args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':1440,'height':1050},offline=True,accept_downloads=True)
  page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('request',lambda r:external.append(r.url) if r.url.startswith(('http:','https:')) else None)
  page.goto(path.as_uri());page.wait_for_function("document.querySelector('#sel-panel-table table')!==null")
  if dest:page.screenshot(path=str(dest/'resumo.png'))
  assert page.locator('#historical-report').count()==0
  assert set(page.evaluate('Object.keys(D)'))=={'gm','gc'}
  assert 'Por que usar bootstrap no painel?' in html
  for period in ['Total','Pré']:
   page.select_option('#sel-period',period)
   for level in ['Total','Grupo','Tipologia','Analítica']:
    page.select_option('#sel-level',level)
    cols=page.locator('#sel-exposure option').evaluate_all('(nodes)=>nodes.map(n=>n.value)')
    for col in cols:
     page.select_option('#sel-exposure',col)
     for name,key,prefix in [('Painel','painel','sel-panel'),('Nacional','nacional','sel-national')]:
      page.click(f'[data-current-tab={name}]')
      assert page.locator('#selected-'+name).is_visible()
      m=next((r for r in data[key] if r['periodo']==period and r['coluna']==col),None)
      text=page.locator('#'+prefix+'-text').inner_text()
      if m:
       metrics=page.locator('#'+prefix+'-metrics').inner_text()
       assert f"1–{m['K']} meses" in metrics
       assert 'q = '+page.evaluate('(v)=>f(v)',m['q']) in metrics
       assert m['exposicao'] in text and 'condicional' in text.lower()
       assert page.locator('#'+prefix+'-table tbody tr').count()==m['K']
       if key=='painel':assert 'q bootstrap acumulado='+page.evaluate('(v)=>f(v)',m['q_boot']) in text
      else:assert 'Não há modelo estimável' in text
     checked+=1
  assert checked==48
  for col in [r['coluna'] for r in data['nacional'] if r['q']<.05]:
   page.click(f'[data-selected-jump="{col}"]')
   assert page.locator('#sel-exposure').input_value()==col
   assert page.locator('#selected-Nacional').is_visible()
   assert 'permanece significativo' in page.locator('#sel-national-text').inner_text()
  if dest:
   page.locator('#current-explore').scroll_into_view_if_needed();page.screenshot(path=str(dest/'nacional.png'))
  with page.expect_download() as download:page.click('#sel-export')
  exported=download.value.path();df=pd.read_csv(exported,sep=';',encoding='utf-8-sig')
  assert len(df)==2 and set(df.desenho)=={'Painel','Nacional'}
  page.select_option('#sel-period','Pré');page.select_option('#sel-level','Tipologia');page.select_option('#sel-exposure','tipo_alagamentos');page.click('[data-current-tab=Painel]')
  assert '1–6 meses' in page.locator('#sel-panel-metrics').inner_text()
  if dest:
   page.locator('#sel-panel-beta').scroll_into_view_if_needed();page.screenshot(path=str(dest/'painel_alagamentos.png'))
   page.set_viewport_size({'width':390,'height':844});page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(dest/'mobile.png'))
   assert page.evaluate('document.documentElement.scrollWidth')<=390
  assert not errors,errors;assert not external,external;browser.close()
 return dict(status='aprovado',combinacoes=checked,desenhos=2,modelos=92,payload='identidade exata com CSV',exportacao='aprovada',erros_javascript=errors,requisicoes_externas=external)

def verify(path,screenshots=None):
 from verificar_relatorio_dlm_ajustes5 import verify as current
 return current(path,screenshots)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('html');p.add_argument('--screenshots');a=p.parse_args()
 print(json.dumps(verify(a.html,a.screenshots),ensure_ascii=False,indent=2))
