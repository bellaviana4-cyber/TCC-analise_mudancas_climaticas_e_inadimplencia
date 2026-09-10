from __future__ import annotations

"""
Consolida os arquivos mensais do SCR/BACEN para o recorte do TCC.

Entrada
-------
data/raw/bacen/**/*.csv

Saídas
------
data/interim/scr_uf_mes_2013_2024.csv
data/interim/scr_uf_mes_2013_2024.parquet

A unidade observacional da saída é UF x mês.
Somente registros de pessoas físicas (PF) são utilizados.
"""

from pathlib import Path
import re

import numpy as np
import pandas as pd


ANO_INICIAL = 2013
ANO_FINAL = 2024

ROOT = Path(__file__).resolve().parents[1]
RAW_BACEN = ROOT / "data" / "raw" / "bacen"
INTERIM = ROOT / "data" / "interim"

ARQUIVO_CSV = INTERIM / f"scr_uf_mes_{ANO_INICIAL}_{ANO_FINAL}.csv"
ARQUIVO_PARQUET = INTERIM / f"scr_uf_mes_{ANO_INICIAL}_{ANO_FINAL}.parquet"

COLUNAS_NECESSARIAS = [
    "uf",
    "cliente",
    "carteira_ativa",
    "carteira_inadimplencia",
]


def extrair_mes_arquivo(caminho: Path) -> pd.Period | None:
    """Extrai YYYYMM do nome scrdata_YYYYMM.csv."""
    match = re.search(r"scrdata_(\d{4})(\d{2})", caminho.stem.lower())

    if not match:
        return None

    ano, mes = map(int, match.groups())

    if not 1 <= mes <= 12:
        return None

    return pd.Period(year=ano, month=mes, freq="M")


def converter_numero_ptbr(serie: pd.Series) -> pd.Series:
    """
    Converte números do formato pt-BR:
    1.234,56 -> 1234.56
    """
    return pd.to_numeric(
        serie.astype("string")
        .str.strip()
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce",
    )


def listar_arquivos() -> list[tuple[pd.Period, Path]]:
    arquivos = []

    for caminho in RAW_BACEN.rglob("*.csv"):
        periodo = extrair_mes_arquivo(caminho)

        if periodo is None:
            continue

        if ANO_INICIAL <= periodo.year <= ANO_FINAL:
            arquivos.append((periodo, caminho))

    return sorted(arquivos, key=lambda x: x[0])


def validar_cobertura(arquivos: list[tuple[pd.Period, Path]]) -> None:
    esperados = pd.period_range(
        f"{ANO_INICIAL}-01",
        f"{ANO_FINAL}-12",
        freq="M",
    )

    encontrados = pd.PeriodIndex([periodo for periodo, _ in arquivos])

    duplicados = encontrados[encontrados.duplicated()].unique()
    faltantes = esperados.difference(encontrados)

    if len(duplicados):
        raise ValueError(
            "Há mais de um arquivo para os meses: "
            + ", ".join(map(str, duplicados))
        )

    if len(faltantes):
        raise ValueError(
            "Faltam arquivos do SCR para os meses: "
            + ", ".join(map(str, faltantes))
        )


def ler_mes(caminho: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(
            caminho,
            sep=";",
            encoding="utf-8-sig",
            usecols=COLUNAS_NECESSARIAS,
            dtype="string",
            low_memory=False,
        )
    except UnicodeDecodeError:
        df = pd.read_csv(
            caminho,
            sep=";",
            encoding="latin1",
            usecols=COLUNAS_NECESSARIAS,
            dtype="string",
            low_memory=False,
        )

    df.columns = df.columns.str.strip()

    ausentes = sorted(set(COLUNAS_NECESSARIAS) - set(df.columns))
    if ausentes:
        raise ValueError(
            f"{caminho.name}: colunas ausentes: {ausentes}"
        )

    return df


def processar_mes(periodo: pd.Period, caminho: Path) -> pd.DataFrame:
    df = ler_mes(caminho)

    df["uf"] = df["uf"].str.strip().str.upper()
    df["cliente"] = df["cliente"].str.strip().str.upper()

    df = df.loc[df["cliente"].eq("PF")].copy()

    df["carteira_ativa"] = converter_numero_ptbr(df["carteira_ativa"])
    df["carteira_inadimplencia"] = converter_numero_ptbr(
        df["carteira_inadimplencia"]
    )

    df["flag_mau"] = (
        df["carteira_inadimplencia"].fillna(0).gt(0).astype("int8")
    )

    agregado = (
        df.groupby("uf", as_index=False)
        .agg(
            carteira_ativa_total=("carteira_ativa", "sum"),
            carteira_inadimplencia_total=(
                "carteira_inadimplencia",
                "sum",
            ),
            qtd_registros=("cliente", "size"),
            qtd_maus=("flag_mau", "sum"),
        )
    )

    agregado["taxa_inadimplencia"] = np.where(
        agregado["carteira_ativa_total"].gt(0),
        agregado["carteira_inadimplencia_total"]
        / agregado["carteira_ativa_total"]
        * 100,
        np.nan,
    )

    agregado["pct_registros_com_inadimplencia"] = np.where(
        agregado["qtd_registros"].gt(0),
        agregado["qtd_maus"] / agregado["qtd_registros"] * 100,
        np.nan,
    )

    agregado.insert(1, "mes_ano", str(periodo))
    agregado.insert(2, "ano", periodo.year)
    agregado.insert(3, "mes", periodo.month)

    colunas = [
        "uf",
        "mes_ano",
        "ano",
        "mes",
        "carteira_ativa_total",
        "carteira_inadimplencia_total",
        "taxa_inadimplencia",
        "qtd_registros",
        "qtd_maus",
        "pct_registros_com_inadimplencia",
    ]

    return agregado[colunas]


def main() -> None:
    INTERIM.mkdir(parents=True, exist_ok=True)

    arquivos = listar_arquivos()

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo scrdata_YYYYMM.csv encontrado em {RAW_BACEN}"
        )

    validar_cobertura(arquivos)

    resultados = []

    print("=" * 68)
    print("TCC - CONSOLIDAÇÃO SCR/BACEN")
    print("=" * 68)
    print(f"Entrada: {RAW_BACEN}")
    print(f"Período: {ANO_INICIAL}-01 a {ANO_FINAL}-12")
    print(f"Arquivos: {len(arquivos)}")
    print()

    for i, (periodo, caminho) in enumerate(arquivos, start=1):
        agregado = processar_mes(periodo, caminho)
        resultados.append(agregado)

        print(
            f"[{i:03d}/{len(arquivos):03d}] {periodo} | "
            f"{agregado['uf'].nunique()} UFs | "
            f"{int(agregado['qtd_registros'].sum()):,} registros PF | "
            f"{int(agregado['qtd_maus'].sum()):,} com inadimplência"
        )

    scr = (
        pd.concat(resultados, ignore_index=True)
        .sort_values(["mes_ano", "uf"])
        .reset_index(drop=True)
    )

    n_meses = scr["mes_ano"].nunique()
    n_ufs = scr["uf"].nunique()
    duplicadas = scr.duplicated(["uf", "mes_ano"]).sum()
    esperado = 12 * (ANO_FINAL - ANO_INICIAL + 1)

    assert n_meses == esperado, (
        f"Esperados {esperado} meses, encontrados {n_meses}."
    )
    assert n_ufs == 27, f"Esperadas 27 UFs, encontradas {n_ufs}."
    assert len(scr) == esperado * 27, (
        f"Esperadas {esperado * 27} linhas, encontradas {len(scr)}."
    )
    assert duplicadas == 0, (
        f"Foram encontradas {duplicadas} chaves UF + mês duplicadas."
    )

    scr.to_csv(
        ARQUIVO_CSV,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    try:
        scr.to_parquet(ARQUIVO_PARQUET, index=False)
        parquet_ok = True
    except (ImportError, ModuleNotFoundError):
        parquet_ok = False

    print()
    print("=" * 68)
    print("VALIDAÇÃO")
    print("=" * 68)
    print(f"Linhas UF x mês: {len(scr):,}")
    print(f"Meses: {n_meses}")
    print(f"UFs: {n_ufs}")
    print(
        f"Período: {scr['mes_ano'].min()} a {scr['mes_ano'].max()}"
    )
    print(f"Chaves duplicadas: {duplicadas}")
    print()
    print("Arquivos gerados:")
    print(f"  CSV: {ARQUIVO_CSV}")

    if parquet_ok:
        print(f"  Parquet: {ARQUIVO_PARQUET}")
    else:
        print(
            "  Parquet não salvo: instale pyarrow "
            "(`python -m pip install pyarrow`)."
        )


if __name__ == "__main__":
    main()
