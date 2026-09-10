from __future__ import annotations

"""
Prepara o Atlas Digital de Desastres para o recorte do TCC.

Entrada
-------
data/raw/atlas_desastres/*.csv

Saídas
------
data/interim/atlas_eventos_2013_2024.parquet
data/interim/atlas_eventos_2013_2024.csv
data/interim/atlas_uf_mes_2013_2024.parquet
data/interim/atlas_uf_mes_2013_2024.csv

A base agregada possui uma linha por UF x mês.
"""

from pathlib import Path
import re
import unicodedata

import pandas as pd


ANO_INICIAL = 2013
ANO_FINAL = 2024

ROOT = Path(__file__).resolve().parents[1]
RAW_ATLAS = ROOT / "data" / "raw" / "atlas_desastres"
INTERIM = ROOT / "data" / "interim"

EVENTOS_CSV = INTERIM / f"atlas_eventos_{ANO_INICIAL}_{ANO_FINAL}.csv"
EVENTOS_PARQUET = INTERIM / f"atlas_eventos_{ANO_INICIAL}_{ANO_FINAL}.parquet"
AGG_CSV = INTERIM / f"atlas_uf_mes_{ANO_INICIAL}_{ANO_FINAL}.csv"
AGG_PARQUET = INTERIM / f"atlas_uf_mes_{ANO_INICIAL}_{ANO_FINAL}.parquet"

COLUNAS = [
    "Sigla_UF",
    "regiao",
    "Data_Evento",
    "descricao_tipologia",
    "grupo_de_desastre",
]


def normalizar_rotulo(valor: object) -> str:
    texto = str(valor).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_") or "sem_informacao"


def localizar_atlas() -> Path:
    arquivos = sorted(RAW_ATLAS.glob("*.csv"))

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum CSV do Atlas foi encontrado em {RAW_ATLAS}"
        )

    if len(arquivos) > 1:
        nomes = "\n".join(f"  - {p.name}" for p in arquivos)
        raise ValueError(
            "Há mais de um CSV na pasta do Atlas. "
            "Deixe apenas o arquivo consolidado que será utilizado:\n"
            + nomes
        )

    return arquivos[0]


def ler_atlas(caminho: Path) -> pd.DataFrame:
    erros = []

    for encoding in ("latin1", "utf-8-sig", "utf-8"):
        try:
            return pd.read_csv(
                caminho,
                sep=";",
                encoding=encoding,
                usecols=COLUNAS,
                low_memory=False,
            )
        except (UnicodeDecodeError, ValueError) as exc:
            erros.append(f"{encoding}: {exc}")

    raise ValueError(
        "Não foi possível ler o Atlas com as configurações esperadas.\n"
        + "\n".join(erros)
    )


def main() -> None:
    INTERIM.mkdir(parents=True, exist_ok=True)

    caminho = localizar_atlas()
    atlas = ler_atlas(caminho)

    atlas = atlas.rename(columns={"Sigla_UF": "uf"})

    atlas["uf"] = (
        atlas["uf"].astype("string").str.strip().str.upper()
    )

    atlas["Data_Evento"] = pd.to_datetime(
        atlas["Data_Evento"],
        dayfirst=True,
        errors="coerce",
    )

    atlas["grupo_de_desastre"] = (
        atlas["grupo_de_desastre"]
        .astype("string")
        .str.strip()
        .fillna("Sem informação")
    )

    atlas["descricao_tipologia"] = (
        atlas["descricao_tipologia"]
        .astype("string")
        .str.strip()
        .fillna("Sem informação")
    )

    atlas = atlas.dropna(subset=["uf", "Data_Evento"]).copy()

    atlas["ano"] = atlas["Data_Evento"].dt.year.astype("int16")
    atlas["mes"] = atlas["Data_Evento"].dt.month.astype("int8")
    atlas["mes_ano"] = (
        atlas["Data_Evento"].dt.to_period("M").astype(str)
    )

    atlas = atlas.loc[
        atlas["ano"].between(ANO_INICIAL, ANO_FINAL)
    ].copy()

    atlas = (
        atlas.sort_values(["Data_Evento", "uf"])
        .reset_index(drop=True)
    )

    grupos = atlas.assign(
        categoria=atlas["grupo_de_desastre"].map(normalizar_rotulo)
    )

    pivot_grupo = (
        grupos.groupby(["uf", "mes_ano", "categoria"])
        .size()
        .unstack(fill_value=0)
        .add_prefix("grupo_")
        .reset_index()
    )
    pivot_grupo.columns.name = None

    tipos = atlas.assign(
        categoria=atlas["descricao_tipologia"].map(normalizar_rotulo)
    )

    pivot_tipo = (
        tipos.groupby(["uf", "mes_ano", "categoria"])
        .size()
        .unstack(fill_value=0)
        .add_prefix("tipo_")
        .reset_index()
    )
    pivot_tipo.columns.name = None

    agregado = pivot_grupo.merge(
        pivot_tipo,
        on=["uf", "mes_ano"],
        how="outer",
        validate="one_to_one",
    ).fillna(0)

    colunas_grupo = [
        c for c in agregado.columns if c.startswith("grupo_")
    ]
    colunas_tipo = [
        c for c in agregado.columns if c.startswith("tipo_")
    ]

    for coluna in colunas_grupo + colunas_tipo:
        agregado[coluna] = agregado[coluna].astype("int64")

    agregado["total_desastres"] = agregado[colunas_grupo].sum(axis=1)

    agregado["ano"] = (
        agregado["mes_ano"].str.slice(0, 4).astype("int16")
    )
    agregado["mes"] = (
        agregado["mes_ano"].str.slice(5, 7).astype("int8")
    )

    agregado = (
        agregado.sort_values(["mes_ano", "uf"])
        .reset_index(drop=True)
    )

    total_original = len(atlas)
    total_agregado = int(agregado["total_desastres"].sum())
    duplicadas = agregado.duplicated(["uf", "mes_ano"]).sum()

    assert total_original == total_agregado, (
        "A contagem de eventos mudou durante a agregação."
    )
    assert duplicadas == 0, (
        "Há duplicidades na chave UF + mês-ano do Atlas agregado."
    )

    atlas.to_csv(
        EVENTOS_CSV,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )
    agregado.to_csv(
        AGG_CSV,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    parquet_ok = True
    try:
        atlas.to_parquet(EVENTOS_PARQUET, index=False)
        agregado.to_parquet(AGG_PARQUET, index=False)
    except (ImportError, ModuleNotFoundError):
        parquet_ok = False

    print("=" * 68)
    print("TCC - PREPARAÇÃO DO ATLAS DIGITAL DE DESASTRES")
    print("=" * 68)
    print(f"Arquivo: {caminho.name}")
    print(f"Eventos {ANO_INICIAL}–{ANO_FINAL}: {total_original:,}")
    print(f"UFs: {atlas['uf'].nunique()}")
    print(
        f"Período: {atlas['mes_ano'].min()} a "
        f"{atlas['mes_ano'].max()}"
    )
    print(f"Linhas agregadas UF x mês com evento: {len(agregado):,}")
    print(f"Duplicidades UF + mês: {duplicadas}")
    print(f"Total após agregação: {total_agregado:,}")
    print()
    print("Arquivos gerados:")
    print(f"  {EVENTOS_CSV}")
    print(f"  {AGG_CSV}")

    if parquet_ok:
        print(f"  {EVENTOS_PARQUET}")
        print(f"  {AGG_PARQUET}")
    else:
        print(
            "  Parquet não salvo: instale pyarrow "
            "(`python -m pip install pyarrow`)."
        )


if __name__ == "__main__":
    main()
