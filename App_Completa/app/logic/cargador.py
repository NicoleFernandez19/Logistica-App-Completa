import pandas as pd


def _leer(path):
    with open(path, "rb") as fh:
        firma = fh.read(4)
    ext = str(path).rsplit(".", 1)[-1].lower() if "." in str(path) else ""
    es_zip = firma == b"PK\x03\x04"
    es_ole = firma[:4] == b"\xD0\xCF\x11\xE0"
    if ext == "xlsx" or (es_zip and ext not in ("csv",)):
        return pd.read_excel(path, dtype=str, engine="openpyxl")
    if ext == "xls" or es_ole:
        try:
            return pd.read_excel(path, dtype=str, engine="xlrd")
        except Exception:
            return pd.read_excel(path, dtype=str, engine="openpyxl")
    ultimo_error = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return pd.read_csv(path, dtype=str, encoding=encoding)
        except UnicodeDecodeError as exc:
            ultimo_error = exc
    raise ultimo_error


def _num(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


def _strip_id(s):
    return s.astype(str).str.strip().str.replace("-", "", regex=False)


def cargar_tiv(path):
    df = _leer(path)
    df["ID_PF"] = _strip_id(df["ID_PF"])
    df = df.drop_duplicates(subset="ID_PF")
    df = df.rename(columns={
        "BP + TU":   "BP_TU",
        "BP+TU":     "BP_TU",
        "TX QCASH":  "TX_QCASH",
        "TXS S/FAC": "TXS_SIN_FAC",
        "TX IMT OB": "TX_IMT_OB",
        "TX IMT IB": "TX_IMT_IB",
        "TX DMT OB": "TX_DMT_OB",
        "TX DMT IB": "TX_DMT_IB",
        "PRISMA CI":  "PRISMA_CI",
        "PRISMA CO":  "PRISMA_CO",
    })
    _num(df, ["BP_TU", "TX_QCASH", "TXS_SIN_FAC", "TX_IMT_OB", "TX_IMT_IB",
              "TX_DMT_OB", "TX_DMT_IB", "PRISMA_CI", "PRISMA_CO"])
    return df


def cargar_maestro(path):
    df = _leer(path)
    df = df.rename(columns={"ID P.F": "ID_PF"})
    df["ID_PF"] = _strip_id(df["ID_PF"])
    df = df.drop_duplicates(subset="ID_PF")
    df = df.rename(columns={
        "NOMBRE FANTASIA":           "NOMBRE_FANTASIA",
        "STOCK ROLLO":               "STOCK_ROLLO_ANT",
        "STOCK SUBE":                "STOCK_SUBE_ANT",
        "STOCK PRISMA":              "STOCK_PRISMA_ANT",
        "STOCK_SUBE":                "STOCK_SUBE_ANT",
        "STOCK_PRISMA":              "STOCK_PRISMA_ANT",
        "STOCK_ROLLO_MES ANTERIOR":  "STOCK_ROLLO_ANT",
        "STOCK_SUBE_MES ANTERIOR":   "STOCK_SUBE_ANT",
        "STOCK_PRISMA_MES ANTERIOR": "STOCK_PRISMA_ANT",
    })
    _num(df, ["STOCK_ROLLO_ANT", "STOCK_SUBE_ANT", "STOCK_PRISMA_ANT"])
    return df


def cargar_fac_termicas(path):
    df = _leer(path)
    df["ID_PF"] = _strip_id(df["ID_PF"])
    return df


def cargar_dsp_kyc(path):
    df = _leer(path)
    df["ID_PF"] = _strip_id(df["ID_PF"])
    df = df.drop_duplicates(subset="ID_PF")
    _num(df, ["FLAG_DSP", "FLAG_KYC"])
    return df


def cargar_com_tx_int(path):
    df = _leer(path)
    df["ID_PF"] = _strip_id(df["ID_PF"])
    return df


def cargar_rollo_env(path):
    df = _leer(path)
    df["AGENTE"] = _strip_id(df["AGENTE"])
    df = df.rename(columns={"CANTIDAD": "ROLLOS"})
    _num(df, ["ROLLOS"])
    return df


def cargar_prisma(path):
    df = _leer(path)
    df["AGENTE"] = _strip_id(df["AGENTE"])
    _num(df, ["CANTIDAD"])
    return df


def cargar_sube(path):
    df = _leer(path)
    df["AGENTE"] = _strip_id(df["AGENTE"])
    _num(df, ["CANTIDAD"])
    return df


def cargar_trx_sube(path):
    df = _leer(path)
    df["ID_PF"] = _strip_id(df["ID_PF"])
    _num(df, ["TRX_SUBE"])
    df = df.groupby("ID_PF", as_index=False)["TRX_SUBE"].sum()
    return df


def cargar_consumo_mes(path):
    """Lee un archivo MaestroStock de meses anteriores para usar en reposición."""
    df = _leer(path)
    if "ID_PF" in df.columns and "ID P.F" not in df.columns:
        df = df.rename(columns={"ID_PF": "ID P.F"})
    if "ID P.F" in df.columns:
        df["ID P.F"] = df["ID P.F"].astype(str).str.strip().str.replace("-", "", regex=False)
    return df


def cargar_agentes(path):
    """Lee el archivo de agentes para ajuste Canal Propio."""
    df = _leer(path)
    if "ID_PF" in df.columns and "ID P.F" not in df.columns:
        df = df.rename(columns={"ID_PF": "ID P.F"})
    return df
