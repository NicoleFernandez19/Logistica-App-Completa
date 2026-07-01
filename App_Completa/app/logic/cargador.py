import math
from pathlib import Path

import pandas as pd


def _leer(path):
    # Soporte para "ruta.xlsx::NombreHoja" (libro multi-hoja cargado desde Paso 1)
    sheet_name = 0  # default: primera hoja (igual que antes)
    path_str = str(path)
    if "::" in path_str:
        path_str, sheet_name = path_str.rsplit("::", 1)
        path = Path(path_str)

    with open(path, "rb") as fh:
        firma = fh.read(4)
    ext = str(path).rsplit(".", 1)[-1].lower() if "." in str(path) else ""
    es_zip = firma == b"PK\x03\x04"
    es_ole = firma[:4] == b"\xD0\xCF\x11\xE0"
    if ext == "xlsx" or es_zip:
        df = pd.read_excel(path, dtype=str, engine="openpyxl", sheet_name=sheet_name)
    elif ext == "xls" or es_ole:
        try:
            df = pd.read_excel(path, dtype=str, engine="xlrd", sheet_name=sheet_name)
        except Exception:
            df = pd.read_excel(path, dtype=str, engine="openpyxl", sheet_name=sheet_name)
    else:
        ultimo_error = None
        df = None
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
            try:
                df = pd.read_csv(path, dtype=str, encoding=encoding)
                # Si hay solo una columna o el parser falla, el separador es ";" (Excel argentino)
                # En ese formato la coma es separador decimal, no de miles
                if len(df.columns) <= 1:
                    df = pd.read_csv(path, dtype=str, encoding=encoding, sep=";")
                    df.attrs["decimal_coma"] = True
                break
            except pd.errors.ParserError:
                try:
                    df = pd.read_csv(path, dtype=str, encoding=encoding, sep=";")
                    df.attrs["decimal_coma"] = True
                    break
                except Exception:
                    pass
            except UnicodeDecodeError as exc:
                ultimo_error = exc
        if df is None:
            raise ultimo_error
    # Guardia: pd.read_excel devuelve dict solo con sheet_name=None o lista
    if isinstance(df, dict):
        print(f"  DIAGNOSTICO _leer: path={str(path)!r} sheet_name={sheet_name!r}")
        print(f"  Hojas disponibles: {list(df.keys())}")
        if isinstance(sheet_name, str) and sheet_name in df:
            df = df[sheet_name]
        elif isinstance(sheet_name, str):
            # Buscar coincidencia case-insensitive
            match = next((k for k in df if k.strip().lower() == sheet_name.strip().lower()), None)
            if match:
                print(f"  Match case-insensitive: '{sheet_name}' → '{match}'")
                df = df[match]
            else:
                raise ValueError(
                    f"Hoja '{sheet_name}' no encontrada en el archivo.\n"
                    f"Hojas disponibles: {list(df.keys())}"
                )
        else:
            df = next(iter(df.values()))
    df.columns = df.columns.str.strip().str.upper()
    return df


def _num(df, cols):
    # En CSVs con separador ";" (formato argentino/europeo) la coma es decimal, no miles
    decimal_coma = df.attrs.get("decimal_coma", False)
    for c in cols:
        if c in df.columns:
            s = df[c].astype(str).str.strip()
            if decimal_coma:
                # Formato argentino: punto=miles ("1.234"), coma=decimal ("3,468" → 3.468)
                s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            elif s.str.contains(',', na=False).any():
                muestra = s[s.str.contains(',', na=False)].head(30)
                # Coma como miles: TODOS los valores con coma deben tener exactamente 3 dígitos
                # Usar .all() evita que un valor decimal (ej: "1,5") sea mal tratado como "15"
                es_miles = muestra.str.match(r'^\d{1,3}(,\d{3})+$').all()
                if es_miles:
                    s = s.str.replace(',', '', regex=False)
                else:
                    # Coma como decimal: "1.234,56" → "1234.56"
                    s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df[c] = pd.to_numeric(s, errors="coerce").fillna(0)
    return df


def _strip_id(s):
    return s.astype(str).str.strip().str.replace("-", "", regex=False)


def _validar(df, cols, path):
    """Lanza ValueError descriptivo si alguna columna requerida no está en el DataFrame."""
    faltantes = [c for c in cols if c not in df.columns]
    if not faltantes:
        return
    nombre = Path(path).name
    disponibles = list(df.columns[:30])
    raise ValueError(
        f"Archivo '{nombre}': columna(s) requeridas no encontradas: {faltantes}\n"
        f"Columnas disponibles en el archivo: {disponibles}"
    )


def cargar_tiv(path):
    df = _leer(path)
    if df.empty:
        raise ValueError(f"Archivo '{Path(path).name}': sin datos (0 filas).")
    _validar(df, ["ID_PF"], path)
    df["ID_PF"] = _strip_id(df["ID_PF"])
    n_antes = len(df)
    df = df.drop_duplicates(subset="ID_PF")
    if len(df) < n_antes:
        print(f"  ADVERTENCIA: {Path(path).name}: {n_antes - len(df)} ID_PF duplicados eliminados.")
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
    _cols_tx = ["BP_TU", "TX_IMT_OB", "TX_IMT_IB", "TX_DMT_OB", "TX_DMT_IB"]
    if not any(c in df.columns for c in _cols_tx):
        raise ValueError(
            f"Archivo '{Path(path).name}': ninguna columna de transacciones reconocida.\n"
            f"Esperadas (al menos una de): {_cols_tx}\n"
            f"Columnas disponibles: {list(df.columns)}"
        )
    return df


def cargar_maestro(path):
    df = _leer(path)
    if df.empty:
        raise ValueError(f"Archivo '{Path(path).name}': sin datos (0 filas).")
    df = df.rename(columns={"ID P.F": "ID_PF"})
    _validar(df, ["ID_PF"], path)
    df["ID_PF"] = _strip_id(df["ID_PF"])
    n_antes = len(df)
    df = df.drop_duplicates(subset="ID_PF")
    if len(df) < n_antes:
        print(f"  ADVERTENCIA: {Path(path).name}: {n_antes - len(df)} ID_PF duplicados eliminados.")
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
        "STOCK RESMA":               "STOCK_RESMA_ANT",
        "STOCK_RESMA":               "STOCK_RESMA_ANT",
        "STOCK_RESMA_MES ANTERIOR":  "STOCK_RESMA_ANT",
    })
    # Eliminar duplicados de columna ANTES de _num para evitar que df[col] retorne DataFrame
    df = df.loc[:, ~df.columns.duplicated(keep="first")]
    _num(df, ["STOCK_ROLLO_ANT", "STOCK_SUBE_ANT", "STOCK_PRISMA_ANT", "STOCK_RESMA_ANT"])
    return df


def cargar_fac_termicas(path):
    df = _leer(path)
    _validar(df, ["ID_PF"], path)
    df["ID_PF"] = _strip_id(df["ID_PF"])
    return df


def cargar_dsp_kyc(path):
    df = _leer(path)
    _validar(df, ["ID_PF", "FLAG_DSP", "FLAG_KYC"], path)
    df["ID_PF"] = _strip_id(df["ID_PF"])
    n_antes = len(df)
    df = df.drop_duplicates(subset="ID_PF")
    if len(df) < n_antes:
        print(f"  ADVERTENCIA: {Path(path).name}: {n_antes - len(df)} ID_PF duplicados eliminados.")
    _num(df, ["FLAG_DSP", "FLAG_KYC"])
    return df


def cargar_com_tx_int(path):
    df = _leer(path)
    _validar(df, ["ID_PF"], path)
    df["ID_PF"] = _strip_id(df["ID_PF"])
    return df


def cargar_rollo_env(path):
    df = _leer(path)
    _validar(df, ["AGENTE", "CANTIDAD"], path)
    df["AGENTE"] = _strip_id(df["AGENTE"])
    df = df.rename(columns={"CANTIDAD": "ROLLOS"})
    _num(df, ["ROLLOS"])
    df = df.groupby("AGENTE", as_index=False)["ROLLOS"].sum()
    return df


def cargar_prisma(path):
    df = _leer(path)
    _validar(df, ["AGENTE", "CANTIDAD"], path)
    df["AGENTE"] = _strip_id(df["AGENTE"])
    _num(df, ["CANTIDAD"])
    df = df.groupby("AGENTE", as_index=False)["CANTIDAD"].sum()
    return df


def cargar_sube(path):
    df = _leer(path)
    _validar(df, ["AGENTE", "CANTIDAD"], path)
    df["AGENTE"] = _strip_id(df["AGENTE"])
    _num(df, ["CANTIDAD"])
    df = df.groupby("AGENTE", as_index=False)["CANTIDAD"].sum()
    return df


def cargar_trx_sube(path):
    df = _leer(path)
    _validar(df, ["ID_PF", "TRX_SUBE"], path)
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


def cargar_resma_env(path):
    df = _leer(path)
    _validar(df, ["AGENTE", "CANTIDAD"], path)
    df["AGENTE"] = _strip_id(df["AGENTE"])
    df = df.rename(columns={"CANTIDAD": "RESMAS"})
    _num(df, ["RESMAS"])
    df = df.groupby("AGENTE", as_index=False)["RESMAS"].sum()
    return df


def cargar_fajas(path):
    df = _leer(path)
    _validar(df, ["ID_PF", "QX FAJAS"], path)
    df["ID_PF"] = _strip_id(df["ID_PF"])
    _num(df, ["QX FAJAS"])
    df = df.groupby("ID_PF", as_index=False)["QX FAJAS"].sum()
    df["FAJAS"] = df["QX FAJAS"].apply(lambda x: math.ceil(x / 200) if x > 0 else 0)
    return df


def cargar_agentes(path):
    """Lee el archivo de agentes para ajuste Canal Propio."""
    df = _leer(path)
    if "ID_PF" in df.columns and "ID P.F" not in df.columns:
        df = df.rename(columns={"ID_PF": "ID P.F"})
    return df
