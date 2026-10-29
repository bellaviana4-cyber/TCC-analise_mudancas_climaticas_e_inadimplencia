from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "tables" / "dlm"


def verify():
    r = pd.read_csv(OUT / "resultados_sintese.csv")
    a = pd.read_csv(OUT / "estimabilidade.csv")
    v = pd.read_csv(OUT / "validacao_atlas.csv")
    checks = [
        ("Atlas reconciliado", bool(v.ok.all())),
        ("42 cenários planejados", len(a) == 42),
        ("40 modelos estimados", len(r) == 40),
        ("K pertence à grade", bool(r.K.isin([3, 6, 9, 12]).all())),
        ("K=3 selecionado nesta execução", bool((r.K == 3).all())),
        ("q-values válidos", bool(r[["q_p_acumulado", "q_p_conjunto"]].apply(lambda s: s.between(0, 1).all()).all())),
        ("Intervalos ordenados", bool((r.ci95_low <= r.efeito_acumulado).all() and (r.efeito_acumulado <= r.ci95_high).all())),
        ("Único acumulado FDR é Onda de Frio pré", r.loc[r.q_p_acumulado < .05, "exposicao"].tolist() == ["Tipologia | Onda de Frio"]),
    ]
    out = pd.DataFrame(checks, columns=["verificacao", "passou"])
    assert out.passou.all(), out[~out.passou]
    return out


if __name__ == "__main__":
    print(verify().to_string(index=False))
