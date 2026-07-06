"""
Fixtures compartidas por generar_historico_prueba.py y test_comparacion_version_anterior.py.

Define 6 agentes de prueba (uno por cada TIPO_AGENTE 0-5, con variantes de
PROV/DEP/SUBSEGMENTACION) y funciones para armar, para un mes dado, un UNICO
libro Excel multi-hoja con el formato que realmente se carga en el Paso 1
("01_DATOS_v5.xlsx": hojas TIV, MAESTRO_CONSUMO_ENVIO, FAC TERMICAS, DSP_KYC,
COM TX INT, PRISMA, SUBE, ROLLOS, TRX_SUBE, RESMAS, FAJAS).
"""
from pathlib import Path

import pandas as pd

from app.logic.cargador import (
    cargar_tiv, cargar_maestro, cargar_fac_termicas, cargar_dsp_kyc,
    cargar_com_tx_int, cargar_prisma, cargar_sube, cargar_rollo_env,
    cargar_trx_sube, cargar_resma_env, cargar_fajas,
)
from app.logic.calculos_consumo import calcular, preparar_maestro_exportable

# ── Agentes de prueba (constantes a lo largo de los meses) ─────────────────
AGENTES = {
    "A001": dict(nombre="C.S. NORTE",           prov="BUENOS AIRES", dep=0, segmento="S1", subseg=1.0,
                 canal="Comercios",        fac=False, com=False, flag_dsp=0, flag_kyc=1,
                 mult=[0.7, 0.85, 1.0, 1.15]),   # tendencia creciente -> pendiente > 0
    "A002": dict(nombre="AGENTE SUR",           prov="BUENOS AIRES", dep=0, segmento="S1", subseg=1.2,
                 canal="Comercios",        fac=False, com=False, flag_dsp=1, flag_kyc=0,
                 mult=[1.2, 1.0, 0.8, 0.6]),     # tendencia decreciente -> pendiente <= 0
    "A003": dict(nombre="AGENTE ASISTIDO",      prov="MENDOZA",      dep=0, segmento="S2", subseg=1.0,
                 canal="Centros y Asistidos", fac=False, com=False, flag_dsp=0, flag_kyc=1,
                 mult=[1.0, 1.0, 1.0, 1.0]),     # plana -> pendiente == 0
    "A004": dict(nombre="AGENTE DEPENDIENTE",   prov="BUENOS AIRES", dep=1, segmento="S1", subseg=1.0,
                 canal="Comercios",        fac=True,  com=False, flag_dsp=0, flag_kyc=1,
                 mult=[0.5, 0.7, 0.9, 1.1]),     # TIPO 3 + DEP=1 (fajas debe dar 0)
    "A005": dict(nombre="AGENTE INTERNACIONAL", prov="MENDOZA",      dep=0, segmento="S2", subseg=0.0,
                 canal="Comercios",        fac=False, com=True,  flag_dsp=0, flag_kyc=1,
                 mult=[1.0, 1.1, 1.2, 1.3]),     # TIPO 4 + SUBSEGMENTACION vacia (debe tratarse como 1)
    "A006": dict(nombre="AGENTE FULL",          prov="BUENOS AIRES", dep=0, segmento="S3", subseg=1.0,
                 canal="Comercios",        fac=True,  com=True,  flag_dsp=1, flag_kyc=1,
                 mult=[1.3, 1.1, 0.9, 0.7]),     # TIPO 5, tendencia decreciente
}
IDS = list(AGENTES.keys())

# indices de mes usados en AGENTES[x]["mult"]: 0=M-3, 1=M-2, 2=M-1, 3=ACTUAL
MES_IDX = {"M-3": 0, "M-2": 1, "M-1": 2, "ACTUAL": 3}

BASE_IB, BASE_OB, BASE_DIB, BASE_DOB = 1200, 900, 450, 360
BASE_BP, BASE_SFA, BASE_QCASH = 9000, 150, 240
BASE_PRISMA_CI, BASE_PRISMA_CO = 600, 450
BASE_TRX_SUBE, BASE_QX_FAJAS = 3000, 400

# Sin envios: el stock queda determinado solo por el consumo historico,
# lo que fuerza a que la reposicion salga de la regresion (no quede en 0
# por sobre-stock).
ENVIO_ROLLO_FIJO = 0
ENVIO_RESMA_FIJO = 0
ENVIO_SUBE_FIJO = 0
ENVIO_PRISMA_FIJO = 0

STOCK_INICIAL = {"ROLLO": 0.0, "RESMA": 0.0, "SUBE": 0.0, "PRISMA": 0.0}


def _tiv_df(mes_idx):
    filas = []
    for aid, cfg in AGENTES.items():
        f = cfg["mult"][mes_idx]
        filas.append({
            "ID_PF": aid,
            "CANAL_AGENTE_AGRUP": cfg["canal"],
            "BP+TU": round(BASE_BP * f, 2),
            "TX IMT OB": round(BASE_OB * f, 2),
            "TX IMT IB": round(BASE_IB * f, 2),
            "TX DMT OB": round(BASE_DOB * f, 2),
            "TX DMT IB": round(BASE_DIB * f, 2),
            "PRISMA CI": round(BASE_PRISMA_CI * f, 2),
            "PRISMA CO": round(BASE_PRISMA_CO * f, 2),
            "TX QCASH": round(BASE_QCASH * f, 2),
            "TXS S/FAC": round(BASE_SFA * f, 2),
        })
    return pd.DataFrame(filas)


def _maestro_df(stock_ant):
    filas = []
    for aid, cfg in AGENTES.items():
        filas.append({
            "ID P.F": aid,
            "NOMBRE FANTASIA": cfg["nombre"],
            "PROV": cfg["prov"],
            "DEP": cfg["dep"],
            "SEGMENTO": cfg["segmento"],
            "SUBSEGMENTACION": cfg["subseg"],
            "STOCK ROLLO": stock_ant[aid]["ROLLO"],
            "STOCK RESMA": stock_ant[aid]["RESMA"],
            "STOCK SUBE": stock_ant[aid]["SUBE"],
            "STOCK PRISMA": stock_ant[aid]["PRISMA"],
        })
    return pd.DataFrame(filas)


def _roster_df(col, ids):
    return pd.DataFrame({col: ids})


def _dsp_kyc_df():
    return pd.DataFrame({
        "ID_PF": IDS,
        "FLAG_DSP": [AGENTES[a]["flag_dsp"] for a in IDS],
        "FLAG_KYC": [AGENTES[a]["flag_kyc"] for a in IDS],
    })


def _envio_df(cantidad):
    return pd.DataFrame({"AGENTE": IDS, "CANTIDAD": [cantidad] * len(IDS)})


def _trx_sube_df(mes_idx):
    return pd.DataFrame({
        "ID_PF": IDS,
        "TRX_SUBE": [round(BASE_TRX_SUBE * AGENTES[a]["mult"][mes_idx], 2) for a in IDS],
    })


def _fajas_df(mes_idx):
    return pd.DataFrame({
        "ID_PF": IDS,
        "Qx FAJAS": [round(BASE_QX_FAJAS * AGENTES[a]["mult"][mes_idx], 2) for a in IDS],
    })


# Nombres de hoja iguales a los que reconoce _AUTO_NOMBRES en paso1_carga.py,
# para que un libro generado asi sea auto-detectable por la app real.
def escribir_libro_paso1(path, mes_idx, stock_ant):
    """Escribe UN SOLO archivo .xlsx multi-hoja (igual formato que
    '01_DATOS_v5.xlsx', el libro que se usa de verdad para cargar el Paso 1)."""
    ids_fac = [a for a in IDS if AGENTES[a]["fac"]]
    ids_com = [a for a in IDS if AGENTES[a]["com"]]
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        _tiv_df(mes_idx).to_excel(w, sheet_name="TIV", index=False)
        _maestro_df(stock_ant).to_excel(w, sheet_name="MAESTRO_CONSUMO_ENVIO", index=False)
        _roster_df("ID_PF", ids_fac).to_excel(w, sheet_name="FAC TERMICAS", index=False)
        _dsp_kyc_df().to_excel(w, sheet_name="DSP_KYC", index=False)
        _roster_df("ID_PF", ids_com).to_excel(w, sheet_name="COM TX INT", index=False)
        _envio_df(ENVIO_PRISMA_FIJO).to_excel(w, sheet_name="PRISMA", index=False)
        _envio_df(ENVIO_SUBE_FIJO).to_excel(w, sheet_name="SUBE", index=False)
        _envio_df(ENVIO_ROLLO_FIJO).to_excel(w, sheet_name="ROLLOS", index=False)
        _trx_sube_df(mes_idx).to_excel(w, sheet_name="TRX_SUBE", index=False)
        _envio_df(ENVIO_RESMA_FIJO).to_excel(w, sheet_name="RESMAS", index=False)
        _fajas_df(mes_idx).to_excel(w, sheet_name="FAJAS", index=False)
    return path


def cargar_libro_paso1(path):
    """Arma el dict de rutas ('archivo::hoja') igual a como lo hace
    paso1_carga.py._libro_asignar() al cargar un libro multi-hoja."""
    path = str(path)
    return {
        "tiv":          f"{path}::TIV",
        "maestro":      f"{path}::MAESTRO_CONSUMO_ENVIO",
        "fac_termicas": f"{path}::FAC TERMICAS",
        "dsp_kyc":      f"{path}::DSP_KYC",
        "com_tx_int":   f"{path}::COM TX INT",
        "prisma":       f"{path}::PRISMA",
        "sube":         f"{path}::SUBE",
        "rollo_env":    f"{path}::ROLLOS",
        "trx_sube":     f"{path}::TRX_SUBE",
        "resma_env":    f"{path}::RESMAS",
        "fajas":        f"{path}::FAJAS",
    }


def correr_paso2(paths):
    """Corre el Paso 2 real (carga + calculo) sobre un dict de rutas
    (soporta tanto archivos sueltos como 'archivo::hoja' de un libro unico)."""
    tiv        = cargar_tiv(paths["tiv"])
    maestro    = cargar_maestro(paths["maestro"])
    fac        = cargar_fac_termicas(paths["fac_termicas"])
    dsp_kyc    = cargar_dsp_kyc(paths["dsp_kyc"])
    com_tx_int = cargar_com_tx_int(paths["com_tx_int"])
    prisma     = cargar_prisma(paths["prisma"])
    sube       = cargar_sube(paths["sube"])
    rollo_env  = cargar_rollo_env(paths["rollo_env"])
    trx        = cargar_trx_sube(paths["trx_sube"])
    resma_env  = cargar_resma_env(paths["resma_env"])
    fajas      = cargar_fajas(paths["fajas"])

    df_tiv, df_mae = calcular(
        tiv, maestro, fac, prisma, sube, trx, dsp_kyc, com_tx_int, rollo_env,
        resma_env=resma_env, fajas=fajas,
    )
    df_repo = preparar_maestro_exportable(df_tiv, df_mae)
    return df_tiv, df_mae, df_repo


def consumo_mensual_df(df_tiv):
    """Replica _construir_consumo_df de paso2_consumo.py (hoja 'Consumo Mensual':
    solo columnas de consumo, SIN stock/PROV/DEP/SEGMENTO -- es el formato que
    de verdad exporta la app para el historico M-1/M-2/M-3)."""
    cols = ["ID_PF", "FLAG_DSP_KYC", "TIPO_AGENTE", "NOMBRE_FANTASIA",
            "ROLLOS", "BOLSAS_RECOLECCION", "ROLLO_SUBE", "ROLLO_PRISMA", "RESMA", "FAJAS"]
    df = df_tiv[[c for c in cols if c in df_tiv.columns]].rename(columns={
        "ID_PF": "ID P.F", "TIPO_AGENTE": "TIPO", "NOMBRE_FANTASIA": "NOMBRE FANTASIA",
        "ROLLOS": "ROLLO", "BOLSAS_RECOLECCION": "BOLSA RECOLECCION",
        "ROLLO_SUBE": "ROLLO SUBE", "ROLLO_PRISMA": "ROLLO PRISMA",
    })
    return df


def stock_final(df_mae):
    idx = df_mae.set_index("ID_PF")
    return {
        aid: {
            "ROLLO":  float(idx.loc[aid, "STOCK_ROLLO"]),
            "RESMA":  float(idx.loc[aid, "STOCK_RESMA"]),
            "SUBE":   float(idx.loc[aid, "STOCK_SUBE"]),
            "PRISMA": float(idx.loc[aid, "STOCK_PRISMA"]),
        }
        for aid in IDS
    }
