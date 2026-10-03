"""Revisão DLM: auditoria e estimação. Saídas históricas em dlm/ são imutáveis."""
from pathlib import Path
import json, hashlib, os, platform, warnings
import numpy as np
import pandas as pd
from scipy import stats, linalg
from patsy import dmatrix
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.stattools import adfuller, kpss
from dlm import load_panel, exposure_columns, exposure_label, exposure_level, LABELS
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/tables/dlm_revisao'
FIG=ROOT/'outputs/figures/dlm_revisao'
CACHE=ROOT/'data/interim/dlm_revisao'
SEED=20261003
PERIODS={'Total':('2013-01-01','2024-12-01'),'Pré':('2013-01-01','2020-01-01')}
MUNICIPIOS={'AC':22,'AL':102,'AP':16,'AM':62,'BA':417,'CE':184,'DF':1,'ES':78,'GO':246,'MA':217,'MT':141,'MS':79,'MG':853,'PA':144,'PB':223,'PR':399,'PE':185,'PI':224,'RJ':92,'RN':167,'RS':497,'RO':52,'RR':15,'SC':295,'SP':645,'SE':75,'TO':139}
assert sum(MUNICIPIOS.values())==5570

def save(df,name):
 OUT.mkdir(parents=True,exist_ok=True);df.to_csv(OUT/(name+'.csv'),index=False,encoding='utf-8-sig');return df

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def analytical(code):
 c=str(int(code))
 if c.startswith(('12','13','14')):return 'Clima/hidrometeorologia'
 if c.startswith('2'):return 'Tecnológico/antrópico'
 if c.startswith('1'):return 'Natural não diretamente climático'
 return 'Código não classificado'

def masks(a,d):
 result={'total_desastres':np.ones(len(a),bool)}
 for c in exposure_columns(d)[1:]:
  key=c.split('_',1)[1];label=LABELS.get(key,key)
  result[c]=a['grupo_de_desastre' if c.startswith('grupo_') else 'descricao_tipologia'].eq(label).to_numpy()
 for label in sorted(a.classe_analitica.unique()):
  result['analitica_'+label]=a.classe_analitica.eq(label).to_numpy()
 return result

def support(d,x,events=None):
 x=np.asarray(x,float);z=pd.DataFrame({'uf':d.uf.to_numpy(),'t':d.data_base.to_numpy(),'x':x})
 s=z.groupby('uf').x.sum();s=s/s.sum() if s.sum()>0 else s*0
 tm=z.groupby('t').x.sum();tm=tm/tm.sum() if tm.sum()>0 else tm*0
 ss=s.sort_values(ascending=False);hhi=float((s*s).sum());ne=1/hhi if hhi else 0
 cells=int((x>0).sum());ufs=int(z.loc[z.x>0,'uf'].nunique());months=int(z.loc[z.x>0,'t'].nunique())
 within=float(z.groupby('uf').x.var().fillna(0).mean());top1=float(ss.iloc[0]);top2=float(ss.iloc[:2].sum())
 n_events=float(events.sum()) if events is not None else float(x.sum())
 if n_events<24 or cells<12 or ufs<5 or months<8 or within<=1e-16: status='não estimável'
 elif ne<5 or top1>.5 or top2>.8 or tm.max()>.25: status='exposição altamente concentrada'
 elif n_events>=100 and cells>=50 and ufs>=10 and months>=24 and ne>=10 and top1<=.3:status='estimável'
 else: status='estimável com ressalvas'
 return dict(eventos=n_events,soma_medida=float(x.sum()),uf_mes_positivos=cells,ufs_expostas=ufs,meses_positivos=months,top1=top1,top2=top2,hhi=hhi,n_eff=ne,hhi_temporal=float((tm*tm).sum()),top_mes=float(tm.max()),variacao_within=within,status=status,zeros=float((x==0).mean()),assimetria=float(stats.skew(x)) if np.std(x)>0 else np.nan,maximo=float(x.max()),mediana=float(np.median(x)),p95=float(np.quantile(x,.95)))

def audit():
 for p in (OUT,FIG,CACHE):p.mkdir(parents=True,exist_ok=True)
 d=load_panel();p=ROOT/'data/processed/df_tcc_2013_2024.parquet'
 if p.exists():
  b=pd.read_parquet(p).sort_values(['uf','data_base']).reset_index(drop=True)
  for c in d.select_dtypes('number'):assert np.allclose(d[c],b[c],equal_nan=True),c
 a=pd.read_csv(ROOT/'data/raw/atlas_desastres/atlas.csv',sep=';',encoding='latin1',low_memory=False)
 dates=pd.to_datetime(a.Data_Evento,format='%d/%m/%Y',errors='coerce');invalid=int(dates.isna().sum())
 a=a.assign(date=dates,linha_original=np.arange(len(a))+2);a=a[a.date.dt.year.between(2013,2024)].copy()
 a['data_base']=a.date.dt.to_period('M').dt.to_timestamp();a['uf']=a.Sigla_UF.str.strip();a['classe_analitica']=a.Cod_Cobrade.map(analytical)
 key=['uf','Cod_IBGE_Mun','date','Cod_Cobrade'];assert not a[key].isna().any().any()
 duplicates=a.duplicated(key,keep=False)
 # Preserve lineage locally; public audit is aggregated, not raw rows.
 a.loc[duplicates].to_csv(CACHE/'duplicidades_chave.csv',index=False)
 u=a.drop_duplicates(key).copy()
 key_conflicts=a.groupby(key).agg(grupos=('grupo_de_desastre','nunique'),tipos=('descricao_tipologia','nunique'))
 assert key_conflicts[['grupos','tipos']].max().max()==1,'Chave ambígua na taxonomia: revisar manualmente'
 tax=a.groupby(['descricao_tipologia','Cod_Cobrade','classe_analitica']).agg(grupos=('grupo_de_desastre',lambda x:'; '.join(sorted(x.unique()))),registros=('uf','size')).reset_index()
 tax['observacao']=tax.apply(lambda r:'Nome não corresponde ao código de onda de calor (13310)' if r.Cod_Cobrade==13310 and r.descricao_tipologia=='Chuvas Intensas' else ('Frente fria/ZC, não código de friagem/geada' if r.Cod_Cobrade==13120 and r.descricao_tipologia=='Onda de Frio' else ('Baixa umidade (14140), não separa onda de calor' if r.Cod_Cobrade==14140 else 'Classificação analítica não atribui causalidade climática')),axis=1)
 save(tax,'taxonomia_cobrade')
 index=pd.MultiIndex.from_frame(d[['uf','data_base']]);exps={};recon=[];metrics=[];correlations=[]
 for c,mask in masks(a,d).items():
  aa=a.loc[mask];uu=u[u.linha_original.isin(aa.linha_original)]
  raw=aa.groupby(['uf','data_base']).size().reindex(index,fill_value=0).to_numpy()
  unique=uu.groupby(['uf','data_base']).size().reindex(index,fill_value=0).to_numpy()
  territory=aa.groupby(['uf','data_base']).Cod_IBGE_Mun.nunique().reindex(index,fill_value=0).to_numpy()
  prop=territory/d.uf.map(MUNICIPIOS).to_numpy()
  assert np.all(prop<=1),c
  exps[c]={'A':raw,'B':unique,'C':territory,'C_prop':prop}
  if c in d:
   assert np.array_equal(raw,d[c].to_numpy()),f'Reconciliação por UF-mês falhou: {c}'
   recon.append({'coluna':c,'atlas':int(raw.sum()),'painel':int(d[c].sum()),'max_diferenca_uf_mes':int(np.max(abs(raw-d[c]))),'ok':True})
  for per,(start,end) in PERIODS.items():
   keep=d.data_base.between(start,end).to_numpy();dd=d.loc[keep]
   for measure,x in exps[c].items():metrics.append({'periodo':per,'coluna':c,'exposicao':label(c),'nivel':level(c),'medida':measure,**support(dd,x[keep],unique[keep])})
   for m1,m2 in [('A','B'),('A','C'),('B','C'),('A','C_prop')]:
    x,y=exps[c][m1][keep],exps[c][m2][keep]
    correlations.append(dict(periodo=per,coluna=c,medida1=m1,medida2=m2,pearson=np.corrcoef(x,y)[0,1],spearman=stats.spearmanr(x,y).statistic))
 np.savez_compressed(CACHE/'exposicoes.npz',**{c+'__'+m:v for c,mm in exps.items() for m,v in mm.items()})
 save(pd.DataFrame(recon),'reconciliacao_uf_mes');save(pd.DataFrame(metrics),'suporte');save(pd.DataFrame(correlations),'correlacao_medidas')
 save(pd.DataFrame([dict(registros=len(a),ocorrencias_municipais=len(u),repeticoes_chave=len(a)-len(u),linhas_em_chaves_repetidas=int(duplicates.sum()),duplicatas_exatas=int(a.drop(columns='linha_original').duplicated().sum()),protocolos_repetidos=int(a.Protocolo_S2iD.duplicated().sum()),datas_invalidas_base_completa=invalid)]),'auditoria_resumo')
 save(pd.DataFrame({'uf':list(MUNICIPIOS),'municipios_2022':list(MUNICIPIOS.values())}),'municipios_denominador')
 # Fixed baseline 2013 credit shares; positive and normalized across UF, not observation weights.
 base=d[d.data_base.dt.year.eq(2013)].groupby('uf').carteira_ativa_total.mean();w=base/base.sum()
 save(w.rename('peso_fixo_2013').reset_index(),'pesos_credito')
 cold=a[a.descricao_tipologia.eq('Onda de Frio')]
 rows=[]
 for per,(start,end) in PERIODS.items():
  cc=cold[cold.data_base.between(start,end)]
  for uf in d.uf.unique():rows.append(dict(periodo=per,uf=uf,registros=int(cc.uf.eq(uf).sum()),participacao=float(cc.uf.eq(uf).sum()/len(cc))))
 save(pd.DataFrame(rows),'onda_frio_uf')
 return d,exps

def label(c):
 return c[10:] if c.startswith('analitica_') else exposure_label(c)
def level(c):return 'Analítica' if c.startswith('analitica_') else exposure_level(c)

def get_exps():
 z=np.load(CACHE/'exposicoes.npz');out={}
 for k in z.files:
  c,m=k.rsplit('__',1);out.setdefault(c,{})[m]=z[k]
 return out
