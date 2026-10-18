"""Verificação da seleção, estimativas e preservação de fontes históricas."""
from pathlib import Path
import numpy as np
import pandas as pd
import json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/tables/dlm_selecionado'
def verify():
 checks=0
 for name in ['painel','nacional']:
  m=pd.read_csv(OUT/(name+'.csv'));grid=pd.read_csv(OUT/(name+'_candidatos.csv'));pr=pd.read_csv(OUT/(name+'_perfis.csv'))
  assert len(m)==46 and not m.duplicated(['periodo','coluna']).any();checks+=2
  for row in m.itertuples():
   candidates=grid[(grid.periodo==row.periodo)&(grid.coluna==row.coluna)];assert candidates.N.nunique()==1 and candidates.N.iloc[0]==row.N
   order=['BIC','K'] if name=='painel' else ['BIC','n_params','K','p_proprio'];candidates=candidates.assign(n_params=candidates.K+candidates.p_proprio);best=candidates.sort_values(order).iloc[0];assert best.K==row.K and best.p_proprio==row.p_proprio
   z=pr[(pr.periodo==row.periodo)&(pr.coluna==row.coluna)].sort_values('lag');assert z.lag.tolist()==list(range(1,row.K+1));assert np.isclose(z.beta.sum(),row.estimate,atol=1e-8);assert np.allclose(z[['C','C_low','C_high']].iloc[-1],[row.estimate,row.low,row.high],atol=1e-8);checks+=5
  assert m.q.between(0,1).all() and m.q_joint.dropna().between(0,1).all();checks+=1
  if name=='painel':assert m.singular_boot.eq(0).all();checks+=1
 rec=pd.read_csv(OUT/'reconciliacao_cr2.csv');assert len(rec)==5 and rec.aprovado.all() and rec.max_diferenca.max()<1e-7;checks+=1
 cov=pd.read_csv(OUT/'cobertura.csv');assert len(cov)==96 and (cov.status=='estimado').sum()==92;checks+=1
 result={'status':'aprovado','verificacoes':checks,'familias_planejadas':48,'modelos_painel':46,'modelos_nacional':46,'reconciliacoes_CR2_com_R':5,'inferência':'condicional à seleção, não ajustada para K/p'};(OUT/'validacao.json').write_text(json.dumps(result,indent=2,ensure_ascii=False));return result
if __name__=='__main__':print(json.dumps(verify(),indent=2,ensure_ascii=False))
