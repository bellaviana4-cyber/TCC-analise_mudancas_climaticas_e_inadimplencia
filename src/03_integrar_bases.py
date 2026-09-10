from __future__ import annotations

"""
Integra SCR/BACEN e Atlas Digital de Desastres.

Entradas
--------
data/interim/scr_uf_mes_2013_2024.parquet (ou CSV)
data/interim/atlas_uf_mes_2013_2024.parquet (ou CSV)

Saídas
------
data/processed/df_tcc_2013_2024.parquet
data/processed/df_tcc_2013_2024.csv

A unidade observacional final é UF x mês, totalizando
144 meses x 27 UFs = 3.888 observações.
"""

from pathlib import Path

import pandas as pd


ANO_INICIAL = 2013
ANO_FINAL = 2024

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"

SCR_PARQUET = INTERIM / f"scr_uf_mes_{ANO_INICIAL}_{ANO_FINAL}.parquet"
SCR_CSV = INTERIM / f"scr_uf_mes_{ANO_INICIAL}_{ANO_FINAL}.csv"

ATLAS_PARQUET = INTERIM / f"atlas_uf_mes_{ANO_INICIAL}_{ANO_FINAL}.parquet"
ATLAS_CSV = INTERIM / f"atlas_uf_mes_{ANO_INICIAL}_{ANO_FINAL}.csv"

FINAL_PARQUET = PROCESSED / f"df_tcc_{ANO_INICIAL}_{ANO_FINAL}.parquet"
FINAL_CSV = PROCESSED / f"df_tcc_{ANO_INICIAL}_{ANO_FINAL}.csv"

REGIOES = {
    "AC": "Norte", "AM": "Norte", "AP": "Norte", "PA": "Norte",
    "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste",
    "MA": "Nordeste", "PB": "Nordeste", "PE": "Nordeste",
    "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste",
    "MS": "Centro-Oeste", "MT": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste",
    "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}


def ler_base(parquet: Path, csv: Path) -> pd.DataFrame:
    if parquet.exists():
        try:
            return pd.read_parquet(parquet)
        except (ImportError, ModuleNotFoundError):
            pass

    if csv.exists():
        return pd.read_csv(csv, sep=";")

    raise FileNotFoundError(
        f"Base não encontrada. Esperado: {parquet.name} ou {csv.name}"
    )


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)

    scr = ler_base(SCR_PARQUET, SCR_CSV)
    atlas = ler_base(ATLAS_PARQUET, ATLAS_CSV)

    scr["uf"] = scr["uf"].astype("string").str.strip().str.upper()
    scr["mes_ano"] = scr["mes_ano"].astype("string").str.strip()

    atlas["uf"] = atlas["uf"].astype("string").str.strip().str.upper()
    atlas["mes_ano"] = atlas["mes_ano"].astype("string").str.strip()

    assert scr.duplicated(["uf", "mes_ano"]).sum() == 0, (
        "O SCR possui duplicidades em UF + mês."
    )
    assert atlas.duplicated(["uf", "mes_ano"]).sum() == 0, (
        "O Atlas possui duplicidades em UF + mês."
    )

    scr["regiao"] = scr["uf"].map(REGIOES)

    if scr["regiao"].isna().any():
        ufs = sorted(scr.loc[scr["regiao"].isna(), "uf"].unique())
        raise ValueError(f"UFs sem região definida: {ufs}")

    colunas_desastre = [
        c for c in atlas.columns
        if c.startswith("grupo_")
        or c.startswith("tipo_")
        or c == "total_desastres"
    ]

    atlas_merge = atlas[
        ["uf", "mes_ano"] + colunas_desastre
    ].copy()

    final = scr.merge(
        atlas_merge,
        on=["uf", "mes_ano"],
        how="left",
        validate="one_to_one",
    )

    final[colunas_desastre] = (
        final[colunas_desastre]
        .fillna(0)
        .astype("int64")
    )

    final["data_base"] = pd.to_datetime(
        final["mes_ano"] + "-01",
        errors="raise",
    )

    final = (
        final.sort_values(["data_base", "uf"])
        .reset_index(drop=True)
    )

    n_meses = final["mes_ano"].nunique()
    n_ufs = final["uf"].nunique()
    duplicadas = final.duplicated(["uf", "mes_ano"]).sum()
    esperado_meses = 12 * (ANO_FINAL - ANO_INICIAL + 1)
    esperado_linhas = esperado_meses * 27

    assert n_meses == esperado_meses, (
        f"Esperados {esperado_meses} meses; encontrados {n_meses}."
    )
    assert n_ufs == 27, f"Esperadas 27 UFs; encontradas {n_ufs}."
    assert len(final) == esperado_linhas, (
        f"Esperadas {esperado_linhas} linhas; encontradas {len(final)}."
    )
    assert duplicadas == 0, (
        f"Encontradas {duplicadas} chaves UF + mês duplicadas."
    )

    final.to_csv(
        FINAL_CSV,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    try:
        final.to_parquet(FINAL_PARQUET, index=False)
        parquet_ok = True
    except (ImportError, ModuleNotFoundError):
        parquet_ok = False

    print("=" * 68)
    print("TCC - INTEGRAÇÃO SCR/BACEN + ATLAS")
    print("=" * 68)
    print(f"Período: {final['mes_ano'].min()} a {final['mes_ano'].max()}")
    print(f"Meses: {n_meses}")
    print(f"UFs: {n_ufs}")
    print(f"Linhas: {len(final):,}")
    print(f"Duplicidades UF + mês: {duplicadas}")
    print(f"Eventos associados: {int(final['total_desastres'].sum()):,}")
    print()
    print("Arquivos gerados:")
    print(f"  CSV: {FINAL_CSV}")

    if parquet_ok:
        print(f"  Parquet: {FINAL_PARQUET}")
    else:
        print(
            "  Parquet não salvo: instale pyarrow "
            "(`python -m pip install pyarrow`)."
        )


if __name__ == "__main__":
    main()
