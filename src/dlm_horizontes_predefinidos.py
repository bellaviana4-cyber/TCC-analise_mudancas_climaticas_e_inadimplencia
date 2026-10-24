"""Sensibilidade do DLM com horizontes comuns, sem seleção de K por AIC.

Mantém o DLM finito irrestrito, efeitos fixos de UF e mês-ano e a amostra
comum original. K=12 é o horizonte substantivo de referência (um ano);
K=6 é uma sensibilidade. Como estes horizontes foram propostos após inspecionar
os resultados, a análise é exploratória, não uma pré-especificação genuína.

Ajusta Holm sobre as 16 tipologias planejadas × dois horizontes de K para
evitar reportar seletivamente o horizonte com valor-p mais favorável.
Também confere qual seria a escolha por AIC caso K=0 estivesse na grade.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/processed/df_tcc_2013_2024.csv"
EXPECTED_HASH = "46f4f8408f5f6a809de2601b5c313ea52ee5992ed5a65ede5246c57d28767e36"
OUT = ROOT / "outputs/tables/dlm_horizontes_fixos_20261024"
SELECT = ROOT / "outputs/tables/revisao_defasagens_20261024/dlm_dois_menores_aic.csv"
HORIZONS = (6, 12)
BANDS = ("dk_regra", "dk6", "dk12")
ENDPOINTS = ("beta0", "soma0K", "soma1K", "conjunto0K", "conjunto1K")


def demean(a):
    return a - a.mean(axis=0, keepdims=True) - a.mean(axis=1, keepdims=True) + a.mean()


def fit_panel(x: np.ndarray, y: np.ndarray, k: int):
    G, TT = x.shape
    months = np.arange(25, TT)
    T = len(months)
    X = np.stack([x[:, months - lag] for lag in range(k + 1)], axis=2)
    X = (X - X.mean(axis=0, keepdims=True)
           - X.mean(axis=1, keepdims=True)
           + X.mean(axis=(0, 1), keepdims=True)).reshape(G*T, k+1)
    yy = demean(y[:, months]).reshape(G*T)
    if np.linalg.matrix_rank(X) != k+1:
        raise ValueError(f"Matriz singular no horizonte {k}")
    b = np.linalg.lstsq(X, yy, rcond=None)[0]
    e = yy - X @ b
    rss = float(e@e)
    n = len(yy)
    ptotal = G+T-1+(k+1)
    aic = n * (np.log(2*np.pi)+1+np.log(rss/n)) + 2*ptotal
    return dict(X=X, b=b, e=e, rss=rss, aic=float(aic), G=G, T=T, n=n, ptotal=ptotal)


def dk_cov(f, label: str):
    G,T,n = f["G"],f["T"],f["n"]
    L = int(np.floor(4*(T/100)**(2/9))) if label == "dk_regra" else int(label[2:])
    X = f["X"].reshape(G,T,-1)
    E = f["e"].reshape(G,T)
    bread = np.linalg.pinv(f["X"].T@f["X"], hermitian=True)
    score = np.einsum("gtk,gt->tk", X, E)
    meat = score.T@score
    for lag in range(1, min(L+1,T)):
        cross = score[lag:].T@score[:-lag]
        meat += (1-lag/(L+1))*(cross+cross.T)
    cov = n/(n-f["ptotal"])*bread@meat@bread
    return (cov+cov.T)/2,L


def contrast(beta, V, c, dof):
    effect = float(c@beta)
    variance = float(c@V@c)
    if not np.isfinite(variance) or variance <= 0:
        return dict(estimativa=effect, erro_padrao=np.nan, p=np.nan)
    se = float(np.sqrt(variance))
    p = float(2*stats.t.sf(abs(effect/se),dof))
    return dict(estimativa=effect, erro_padrao=se, p=p)


def holm(p):
    """Holm step-down, incluindo posições reservadas às tipologias ausentes."""
    p = np.asarray(p,float)
    order=np.argsort(p,kind="stable")
    adj=np.maximum.accumulate(np.minimum(1.,(len(p)-np.arange(len(p)))*p[order]))
    result=np.empty_like(p)
    result[order]=adj
    return result


def run():
    assert hashlib.sha256(BASE.read_bytes()).hexdigest()==EXPECTED_HASH
    selected = pd.read_csv(SELECT, encoding="utf-8-sig")
    candidates = pd.read_csv(ROOT / "outputs/tables/revisao_estadual_20261019/dlm_candidatos.csv",encoding="utf-8-sig")
    df = pd.read_csv(BASE, sep=";", encoding="utf-8-sig").sort_values(["uf","mes_ano"])
    assert len(df)==3888 and df.uf.nunique()==27 and df.mes_ano.nunique()==144
    df["y"] = df.groupby("uf").taxa_inadimplencia.transform(lambda s:np.log(s).diff())
    results=[]; k0_results=[]
    for per in ("Pré","Total"):
        d = df[df.mes_ano<=("2020-01" if per=="Pré" else "2024-12")].copy()
        units = sorted(d.uf.unique())
        G,T = len(units),d.mes_ano.nunique()
        y = np.stack([d.loc[d.uf.eq(u),"y"].to_numpy(float) for u in units])
        for sel in selected.loc[selected.periodo.eq(per)].itertuples(index=False):
            tip = sel.tipologia
            d["x"] = d.groupby("uf")[tip].transform(lambda s:np.log1p(s).diff())
            x = np.stack([d.loc[d.uf.eq(u),"x"].to_numpy(float) for u in units])
            k0 = fit_panel(x,y,0)
            k0_results.append(dict(periodo=per,tipologia=tip,
                                   K_AIC_original=int(sel.K_menor_AIC),
                                   AIC_K0=k0["aic"], AIC_K_original=float(sel.AIC_1),
                                   delta_AIC_K0_menos_original=k0["aic"]-float(sel.AIC_1),
                                   K0_seria_preferido=bool(k0["aic"]<float(sel.AIC_1))))
            for k in HORIZONS:
                f = fit_panel(x,y,k)
                saved = candidates.loc[(candidates.periodo==per)&(candidates.tipologia==tip)&(candidates.K==k),"AIC"]
                assert len(saved)==1 and np.isclose(f["aic"],float(saved.iloc[0]),atol=1e-7), (per,tip,k)
                for band in BANDS:
                    cov,L = dk_cov(f,band)
                    individual=[contrast(f["b"],cov,np.eye(k+1)[j],f["T"]-1)
                                for j in range(k+1)]
                    for endpoint in ENDPOINTS:
                        if endpoint=="beta0":
                            z=individual[0]; multip=1
                        elif endpoint=="soma0K":
                            z=contrast(f["b"],cov,np.ones(k+1),f["T"]-1);multip=1
                        elif endpoint=="soma1K":
                            z=contrast(f["b"],cov,np.r_[0,np.ones(k)],f["T"]-1);multip=1
                        else:
                            start=0 if endpoint=="conjunto0K" else 1
                            # União conservadora, sem inverter V de dimensão alta.
                            z=dict(estimativa=np.nan,erro_padrao=np.nan,
                                   p=float(np.nanmin([v["p"] for v in individual[start:]])))
                            multip=k+1-start
                        results.append(dict(periodo=per,tipologia=tip,K=k,criterio="fixado sem otimização",
                                            AIC=f["aic"],N=f["n"],banda=band,L=L,
                                            endpoint=endpoint,multiplicador_conjunto=multip,
                                            p_conjunto_ajustado=min(1.,z["p"]*multip),**z))
    a=pd.DataFrame(results);a["p_holm_32"] = np.nan
    for keys,g in a.groupby(["periodo","banda","endpoint"]):
        p=np.r_[g.p_conjunto_ajustado.fillna(1).to_numpy(),np.ones(32-len(g))]
        a.loc[g.index,"p_holm_32"] = holm(p)[:len(g)]
    a["rejeita_5pct"] = a.p_holm_32.lt(.05)
    k0=pd.DataFrame(k0_results)
    assert len(k0)==29 and len(a)==29*2*3*5
    resumo=a.groupby(["K","banda"]).agg(hipoteses=("p","count"),
             rejeicoes_nominais=("p",lambda z:int((z<.05).sum())),
             rejeicoes_apos_ajuste=("rejeita_5pct","sum")).reset_index()
    OUT.mkdir(parents=True,exist_ok=True)
    for name,frame in [("inferencia.csv",a),("k0_comparacao_aic.csv",k0),
                       ("resumo_inferencia.csv",resumo)]:
        frame.to_csv(OUT/name,index=False,encoding="utf-8-sig")
    info=dict(modelo="DLM painel TWFE irrestrito; Delta log I ~ Delta log(1+D) com K fixo",
              horizontes=list(HORIZONS), regra="K=12 de referência e K=6 de sensibilidade, sem otimizar K por AIC",
              denominador="amostra comum original que começa em 2015-02 devido à grade histórica K<=24",
              inferencia="DK regra (principal), DK6 e DK12; min-p e Bonferroni para conjuntos; Holm entre 16 tipologias × dois K",
              advertencia="horizontes escolhidos após observar o estudo; inferência exploratória; sem garantia seletiva formal",
              estimaveis=len(k0),k0_preferidos=int(k0.K0_seria_preferido.sum()),
              k1_que_iriam_para_0=int((k0.K_AIC_original.eq(1)&k0.K0_seria_preferido).sum()),
              base_sha256=EXPECTED_HASH)
    (OUT/"resumo.json").write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding="utf-8")
    print("K0 venceria",info["k0_preferidos"],"/",len(k0),"; dos K=1:",info["k1_que_iriam_para_0"])
    print(resumo.to_string(index=False))
    print("Rejeicoes:")
    print(a.loc[a.rejeita_5pct,["periodo","tipologia","K","banda","endpoint","p_holm_32"]].to_string(index=False))


if __name__=="__main__":
    run()
