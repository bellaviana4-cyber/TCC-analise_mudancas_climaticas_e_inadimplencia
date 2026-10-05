"""Snapshot oficial SGS para controles mensais; sem interpolação e sem atualização silenciosa."""
from pathlib import Path
import urllib.request,urllib.parse,json,hashlib,datetime
import pandas as pd,numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/tables/dlm_ajustes5'
SERIES={'selic_mensal':4390,'ipca_mensal':433,'ibc_br_sa':24364}
def fetch():
 OUT.mkdir(parents=True,exist_ok=True);frame=pd.DataFrame(index=pd.date_range('2012-01-01','2024-12-01',freq='MS'));metadata=[]
 for name,code in SERIES.items():
  url=f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados?'+urllib.parse.urlencode({'formato':'json','dataInicial':'01/01/2012','dataFinal':'31/12/2024'});p=OUT/f'sgs_{code}_snapshot.json'
  if not p.exists():
   with urllib.request.urlopen(url,timeout=45) as response:raw=response.read()
   json.loads(raw);p.write_bytes(raw)
  raw=p.read_bytes();records=json.loads(raw);data=pd.DataFrame(records);data['t']=pd.to_datetime(data.data,format='%d/%m/%Y');assert not data.t.duplicated().any();values=pd.to_numeric(data.valor,errors='raise');frame[name]=pd.Series(values.to_numpy(),index=data.t).reindex(frame.index);assert frame[name].notna().all();metadata.append({'serie':name,'SGS':code,'fonte':url,'sha256':hashlib.sha256(raw).hexdigest(),'observacoes':len(data),'extraido_em_UTC':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),'periodicidade':'mensal','snapshot':'revisão disponível na extração; não vintage histórico'})
 assert frame.ibc_br_sa.gt(0).all();frame['atividade_crescimento']=100*np.log(frame.ibc_br_sa).diff()
 for name in ['selic_mensal','ipca_mensal','atividade_crescimento']:frame[name+'_lag1']=frame[name].shift(1)
 relevant=frame.loc['2013-01-01':'2024-12-01'];assert relevant.notna().all().all() and len(relevant)==144
 relevant.rename_axis('data').to_csv(OUT/'controles_macro.csv',encoding='utf-8-sig');(OUT/'controles_fontes.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2));return relevant
if __name__=='__main__':print(fetch().describe())
