"""Verifica cobertura, seleção no treino, métricas e integridade dos SARIMAX."""
from pathlib import Path
import hashlib
import json
import os
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'outputs/tables/modalidades_excluidas_20261104'
os.environ['TCC_OUTPUT_DIR']=str(B/'granger')
os.environ['TCC_BASE_CSV']=str(ROOT/'data/processed/df_tcc_2013_2024.csv')
from analise_estadual import TIPOS, load
from sarimax_revisao_final import series_for_unit

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main(lags=(0,3)):
    manifest=json.loads((B/'manifesto.json').read_text(encoding='utf-8'))
    assert sha(ROOT/'data/processed/df_tcc_2013_2024.csv')==manifest['base_sha256']
    d=load();units=sorted(d.uf.unique())+['Brasil']
    # Recalcula a taxa nacional a partir dos saldos, sem usar as taxas estaduais.
    national=[]
    for per,end in [('Pré','2020-01'),('Total','2024-12')]:
        full=d[d.mes_ano<=end].groupby('mes_ano',sort=True)[['carteira_ativa_total','carteira_inadimplencia_total',*TIPOS]].sum()
        expected_y=100*np.diff(np.log(100*full.carteira_inadimplencia_total.to_numpy()/full.carteira_ativa_total.to_numpy()))
        expected_x=np.diff(np.log1p(full[TIPOS].to_numpy()),axis=0)
        y,x,counts,months=series_for_unit(d,'Brasil',per)
        assert np.allclose(y,expected_y,rtol=0,atol=1e-10)
        assert np.allclose(x,expected_x,rtol=0,atol=1e-10)
        assert np.array_equal(counts,full[TIPOS].iloc[1:].to_numpy())
        national.append(dict(periodo=per,n=len(y),max_erro_y=float(np.max(np.abs(y-expected_y))),max_erro_x=float(np.max(np.abs(x-expected_x)))))
    result=[]
    for lag in lags:
        folder=B/f'sarimax{lag}'
        from reestimar_com_exclusoes import conferir_proveniencia_checkpoints
        conferir_proveniencia_checkpoints(folder,manifest['base_sha256'])
        expected_candidates=25 if lag==0 else 22
        for per,slug,ntrain,ntest in [('Pré','pre',48,12),('Total','total',95,24)]:
            for unit in units:
                path=folder/'unidades'/slug
                r=pd.read_csv(path/f'{unit}_resumo.csv')
                c=pd.read_csv(path/f'{unit}_candidatos.csv')
                general=pd.read_csv(path/f'{unit}_geral.csv')
                baselines=pd.read_csv(path/f'{unit}_bases.csv')
                eligible_base=baselines[baselines.status.eq('estimado')].sort_values(['BIC','ordem'])
                assert len(baselines)==5 and len(eligible_base)>0
                baseline=eligible_base.iloc[0]
                assert len(r)==16 and set(r.tipologia)==set(TIPOS),(lag,per,unit,'tipologias')
                assert not r.tipologia.duplicated().any()
                assert len(c)==16*expected_candidates,(lag,per,unit,'grade incompleta')
                assert not c.duplicated(['tipologia','K']).any()
                assert set(c.K)==set(range(lag,25))
                assert len(general)==1
                assert r.n_treino.eq(ntrain).all() and r.n_teste.eq(ntest).all()
                assert np.allclose(r.bic_sarima,baseline.BIC,rtol=0,atol=1e-8)
                assert r.ordem.eq(baseline.ordem).all() and r.sazonal.eq(baseline.sazonal).all()
                assert c.n_treino_comum.eq(ntrain).all() and c.n_teste.eq(ntest).all()
                if c.status.eq('estimado').any():
                    assert c.loc[c.status.eq('estimado'),'convergiu'].astype(str).str.lower().eq('true').all()
                selected=r[r.status.eq('estimado')]
                for row in selected.itertuples():
                    candidates=c[c.tipologia.eq(row.tipologia)&c.status.eq('estimado')].sort_values(['BIC','K'])
                    assert len(candidates)>0
                    best=candidates.iloc[0]
                    assert int(row.K)==int(best.K),(lag,per,unit,row.tipologia,'K')
                    assert np.isclose(row.bic_sarimax,best.BIC,rtol=0,atol=1e-8)
                    assert int(row.n_exog)==int(row.K)-lag+1
                    assert row.rmse_sarima>0 and row.rmse_sarimax>=0
                    assert np.isclose(row.delta_BIC,row.bic_sarimax-row.bic_sarima,atol=1e-8)
                    assert np.isclose(row.melhora_rmse_pct,100*(1-row.rmse_sarimax/row.rmse_sarima),atol=1e-8)
                if general.iloc[0].status=='estimado':
                    gr=general.iloc[0]
                    assert str(gr.convergiu).lower()=='true'
                    included=gr.tipologias_incluidas.split(';')
                    assert len(set(included))==len(included)==int(gr.n_tipologias_incluidas)
                    assert set(included)<=set(TIPOS)
                    assert np.isclose(gr.delta_BIC,gr.bic_sarimax-gr.bic_sarima,atol=1e-8)
                    assert np.isclose(gr.melhora_rmse_pct,100*(1-gr.rmse_sarimax/gr.rmse_sarima),atol=1e-8)
                result.append(dict(lag_inicial=lag,periodo=per,unidade=unit,aplicacoes=16,estimados=len(selected),candidatos=len(c),passou=True))
        # Os arquivos consolidados devem conter exatamente as mesmas unidades.
        canonical=pd.read_csv(folder/'resumo.csv')
        generals=pd.read_csv(folder/'geral.csv')
        assert len(canonical)==896 and not canonical.duplicated(['periodo','unidade','tipologia']).any()
        assert len(generals)==56 and not generals.duplicated(['periodo','unidade']).any()
        summary=json.loads((folder/'resumo.json').read_text(encoding='utf-8'))
        assert summary['base_sha256']==manifest['base_sha256']
        assert summary['univariados_estimados']==int(canonical.status.eq('estimado').sum())
    if set(lags)=={0,3}:
        fields=['periodo','unidade','tipologia','n_treino','n_teste','ordem','sazonal','bic_sarima','rmse_sarima']
        left=pd.read_csv(B/'sarimax0/resumo.csv')[fields]
        right=pd.read_csv(B/'sarimax3/resumo.csv')[fields]
        paired=left.merge(right,on=fields[:3],suffixes=('_0','_3'),validate='one_to_one')
        assert len(paired)==896
        for field in ['n_treino','n_teste','ordem','sazonal']:
            assert paired[field+'_0'].eq(paired[field+'_3']).all(),field
        for field in ['bic_sarima','rmse_sarima']:
            assert np.allclose(paired[field+'_0'],paired[field+'_3'],rtol=0,atol=1e-8),field
        paired.to_csv(B/'validacao_referencia_sarimax.csv',index=False,encoding='utf-8-sig')
    suffix='' if set(lags)=={0,3} else '_lag'+'_'.join(map(str,lags))
    pd.DataFrame(result).to_csv(B/f'validacao_sarimax{suffix}.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(national).to_csv(B/f'validacao_nacional_sarimax{suffix}.csv',index=False,encoding='utf-8-sig')
    integrity=dict(base_sha256=manifest['base_sha256'],unidades_conferidas=len(result),
                   modelos_individuais_planejados=896*len(lags),modelos_gerais_planejados=56*len(lags),
                   criterios='Cobertura completa; BIC mínimo no treino entre candidatos convergentes; amostras comuns; cálculo de métricas e taxa nacional por saldos',
                   arquivos={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for lag in lags for p in sorted((B/f'sarimax{lag}').rglob('*.csv'))},
                   proveniencia_checkpoints={str(lag):json.loads((B/f'sarimax{lag}/proveniencia_checkpoints.json').read_text(encoding='utf-8')) for lag in lags},
                   codigo_sha256_lf={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_text(encoding='utf-8').encode('utf-8')).hexdigest() for p in [ROOT/'src/sarimax_por_tipologia_k0_24_20261026.py',ROOT/'src/sarimax_revisao_final.py',Path(__file__)]})
    (B/f'integridade_sarimax{suffix}.json').write_text(json.dumps(integrity,ensure_ascii=False,indent=2),encoding='utf-8')
    print('SARIMAX:',len(result),'unidades,',896*len(lags),'aplicações individuais e',56*len(lags),'gerais conferidos.')

if __name__=='__main__':main()
