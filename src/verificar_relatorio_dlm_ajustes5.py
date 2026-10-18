"""Dados exatos e interação do HTML final offline em desktop e mobile."""
from pathlib import Path
import re,json,argparse
import pandas as pd
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

def verify(path,screenshots=None):
 path=Path(path).resolve();html=path.read_text();A=json.loads(re.search(r'<script id="adjusted-data" type="application/json">(.*?)</script>',html,re.S).group(1));n=0
 for name in ['painel','painel_perfis','painel_candidatos','dependencia_ufs','correlacoes_ufs','nacional','nacional_perfis','nacional_candidatos','nacional_conjunto','nacional_igualdade','cobertura_nacional','controles_macro','taxonomia','taxonomia_codigos']:
  d=pd.read_csv(ROOT/'outputs/tables/dlm_ajustes5'/(name+'.csv'));assert A[name]==d.astype(object).where(pd.notna(d),None).to_dict('records');n+=1
 assert 'para apresentar à orientadora' not in html.lower();assert 'spline' not in html.lower();assert html.count('<math ')==6;n+=3
 errors=[];external=[];cases=0;downloadrows=0;dest=Path(screenshots) if screenshots else None
 if dest:dest.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as p:
  browser=p.chromium.launch(args=['--no-sandbox']);context=browser.new_context(viewport={'width':1440,'height':1050},offline=True,accept_downloads=True);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:external.append(r.url) if r.url.startswith(('http:','https:')) else None);page.goto(path.as_uri());page.wait_for_function("document.querySelector('#panel-table table')!==null")
  if dest:page.screenshot(path=str(dest/'resumo.png'))
  for per in ['Total','Pré']:
   page.select_option('#period',per)
   for level in ['Total','Grupo','Tipologia','Analítica']:
    page.select_option('#level',level);cols=page.locator('#exposure option').evaluate_all('(nodes)=>nodes.map(n=>n.value)')
    for col in cols:
     page.select_option('#exposure',col);page.click('[data-tab=Painel]')
     for L in [6,12,18]:
      page.select_option('#bandwidth',str(L));m=next((r for r in A['painel'] if r['periodo']==per and r['coluna']==col and r['L']==L),None)
      if m:
       assert page.locator('#panel-table tbody tr').count()==m['K'];assert 'q BY' in page.locator('#panel-metrics').inner_text();assert m['exposicao'] in page.locator('#panel-text').inner_text();assert page.evaluate('(v)=>f(v)',m['p_busca_BY']) in page.locator('#panel-metrics').inner_text()
      else:assert 'indisponível' in page.locator('#panel-text').inner_text()
      cases+=1
     page.click('[data-tab=Nacional]')
     for mode in (['Comum','Regimes'] if per=='Total' else ['Comum']):
      if per=='Total':page.select_option('#national-mode',mode)
      for reg in page.locator('#regime option').evaluate_all('(nodes)=>nodes.map(n=>n.value)'):
       page.select_option('#regime',reg);m=next((r for r in A['nacional'] if r['periodo']==per and r['coluna']==col and r['modo']==mode and r['regime']==reg),None)
       if m:
        assert page.locator('#national-table tbody tr').count()==m['K'];assert m['exposicao'] in page.locator('#national-text').inner_text();assert page.evaluate('(v)=>f(v)',m['p_busca_BY']) in page.locator('#national-metrics').inner_text()
       else:assert 'indisponível' in page.locator('#national-text').inner_text()
       cases+=1
     page.click('[data-tab=Granger]');assert page.locator('#view-Granger').is_visible();cases+=1
  assert set(page.evaluate('Object.keys(D)'))=={'gm','gc'};assert page.locator('#joint-cards article').count()==2;n+=2
  page.select_option('#period','Total');page.select_option('#level','Tipologia');page.select_option('#exposure','tipo_vendavais_e_ciclones');page.click('[data-tab=Nacional]');page.select_option('#national-mode','Regimes');page.select_option('#regime','Mar/2020–dez/2021')
  with page.expect_download() as info:page.click('#export')
  download=info.value;file=ROOT/'outputs/tables/dlm_ajustes5/ui_export.tmp';download.save_as(str(file));d=pd.read_csv(file,sep=';');assert len(d)==7;downloadrows=len(d);file.unlink();n+=1
  if dest:page.locator('#explore').scroll_into_view_if_needed();page.screenshot(path=str(dest/'nacional.png'))
  page.select_option('#period','Pré');page.select_option('#national-mode','Comum') if not page.locator('#national-mode').is_disabled() else None;page.select_option('#exposure','tipo_vendavais_e_ciclones');assert 'terceiro mês' in page.locator('#national-text').inner_text();n+=1
  for s in ['selic_mensal','ipca_mensal','atividade_crescimento']:page.select_option('#macro-series',s);n+=1
  page.set_viewport_size({'width':390,'height':844});page.locator('header').scroll_into_view_if_needed();assert page.evaluate('document.documentElement.scrollWidth')<=390
  if dest:page.screenshot(path=str(dest/'mobile.png'));page.locator('#explore').scroll_into_view_if_needed();page.screenshot(path=str(dest/'mobile_modelo.png'))
  n+=1;browser.close()
 assert not errors,errors;assert not external,external
 result={'verificacoes_dados_UI':n,'cenarios_interativos':cases,'erros_JS':errors,'requisicoes_externas':external,'exportacao_linhas':downloadrows,'mobile_width':390};(ROOT/'outputs/tables/dlm_ajustes5/validacao_html.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(result);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('path',nargs='?',default=str(ROOT.parent/'relatorio_granger_dlm_integrado.html'));p.add_argument('--screenshots');args=p.parse_args();verify(args.path,args.screenshots)
