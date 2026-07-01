import pandas as pd


def calcular(tiv, maestro, fac_termicas, prisma_env, sube_env, trx_sube,
             dsp_kyc, com_tx_int, rollo_env, resma_env=None, fajas=None):

    # ── Enriquecer TIV ──────────────────────────────────────────────────────
    df = tiv.copy()

    df = df.merge(trx_sube[["ID_PF", "TRX_SUBE"]], on="ID_PF", how="left")
    df["TRX_SUBE"] = df["TRX_SUBE"].fillna(0)

    dsp_cols = dsp_kyc.set_index("ID_PF")[["FLAG_DSP", "FLAG_KYC"]]
    df = df.merge(dsp_cols, on="ID_PF", how="left")
    df["FLAG_DSP"] = df["FLAG_DSP"].fillna(0).astype(int)
    df["FLAG_KYC"] = df["FLAG_KYC"].fillna(0).astype(int)

    ids_fac = set(fac_termicas["ID_PF"].astype(str))
    ids_com = set(com_tx_int["ID_PF"].astype(str))
    ids_dspkyc = set(dsp_kyc["ID_PF"].astype(str))

    df["_FAC"] = df["ID_PF"].isin(ids_fac)
    df["_COM"] = df["ID_PF"].isin(ids_com)
    df["_DKY"] = df["ID_PF"].isin(ids_dspkyc)

    _tiene_canal = "CANAL_AGENTE_AGRUP" in df.columns
    if not _tiene_canal:
        print(
            "  ADVERTENCIA: columna 'CANAL_AGENTE_AGRUP' no encontrada en el TIV.\n"
            "    Los agentes 'Centros y Asistidos' quedarán clasificados como TIPO 0.\n"
            "    Verifique que el archivo TIV incluya esta columna."
        )
    else:
        valores_canal = df["CANAL_AGENTE_AGRUP"].astype(str).str.strip().unique()
        print(f"  CANAL_AGENTE_AGRUP detectada — valores únicos: {list(valores_canal)}")
        n_ca = sum(v.lower() == "centros y asistidos" for v in valores_canal
                   if v not in ("nan", ""))
        print(f"    → {n_ca} valor(es) coinciden con 'Centros y Asistidos' (sin distinguir mayúsculas)")

    def _tipo(row):
        if row["_COM"] and row["_FAC"] and row["_DKY"]:
            return 5
        if row["_COM"]:
            return 4
        if row["_FAC"]:
            return 3
        if _tiene_canal and str(row.get("CANAL_AGENTE_AGRUP", "")).strip().lower() == "centros y asistidos":
            return 2
        if row["FLAG_DSP"] == 1:
            return 1
        return 0

    df["TIPO_AGENTE"] = df.apply(_tipo, axis=1)
    conteo_tipos = df["TIPO_AGENTE"].value_counts().sort_index().to_dict()
    print(f"  Clasificación TIPO_AGENTE: {conteo_tipos}")

    df["FLAG_DSP_KYC"] = df["_DKY"].astype(int)
    df.drop(columns=["_FAC", "_COM", "_DKY"], inplace=True)

    # Garantizar columnas de transacciones; se asigna 0 si no venían en el TIV
    for _c in ["BP_TU", "TX_QCASH", "TXS_SIN_FAC", "TX_IMT_OB", "TX_IMT_IB",
               "TX_DMT_OB", "TX_DMT_IB", "PRISMA_CI", "PRISMA_CO"]:
        if _c not in df.columns:
            df[_c] = 0.0

    IB    = df["TX_IMT_IB"]
    OB    = df["TX_IMT_OB"]
    DIB   = df["TX_DMT_IB"]
    DOB   = df["TX_DMT_OB"]
    BP    = df["BP_TU"]
    SFA   = df["TXS_SIN_FAC"]
    PCI   = df["PRISMA_CI"]
    PCO   = df["PRISMA_CO"]
    SUB   = df["TRX_SUBE"]
    DSP   = df["FLAG_DSP"]
    QCASH = df["TX_QCASH"]

    BASE = (
        DIB * 49.3
        + DOB * 100.90
        + (BP - SFA) * 0.1 * 11
        + (BP - SFA) * 0.9 * 6
        + SFA * 12
        + PCO * 9.5
    )

    df["ROLLOS"] = 0.0
    m012  = df["TIPO_AGENTE"].isin([0, 1, 2])
    m3    = df["TIPO_AGENTE"] == 3
    m4_nd = (df["TIPO_AGENTE"] == 4) & (DSP == 0)
    m4_d  = (df["TIPO_AGENTE"] == 4) & (DSP == 1)
    m5_nd = (df["TIPO_AGENTE"] == 5) & (DSP == 0)
    m5_d  = (df["TIPO_AGENTE"] == 5) & (DSP == 1)

    df.loc[m012,  "ROLLOS"] = BASE[m012] / 6900 / 5
    df.loc[m3,    "ROLLOS"] = (BASE[m3]    + OB[m3]    * 20)                      / 6900 / 5
    df.loc[m4_nd, "ROLLOS"] = (BASE[m4_nd] + IB[m4_nd] * 108 + OB[m4_nd] * 116)  / 6900 / 5
    df.loc[m4_d,  "ROLLOS"] = (BASE[m4_d]  + IB[m4_d]  * 54  + OB[m4_d]  * 58)   / 6900 / 5
    df.loc[m5_nd, "ROLLOS"] = (BASE[m5_nd] + IB[m5_nd] * 108 + OB[m5_nd] * 136)  / 6900 / 5
    df.loc[m5_d,  "ROLLOS"] = (BASE[m5_d]  + IB[m5_d]  * 54  + OB[m5_d]  * 78)   / 6900 / 5

    df["BOLSAS_VERDES"] = 0.0
    m_nd = DSP == 0
    m_d  = DSP == 1
    df.loc[m_nd, "BOLSAS_VERDES"] = (IB[m_nd] * 2 + OB[m_nd] * 4 + DIB[m_nd] + DOB[m_nd]) / 100
    df.loc[m_d,  "BOLSAS_VERDES"] = (DIB[m_d] + DOB[m_d]) / 100

    df["BOLSAS_MAGENTA"] = 0.0
    m_mag = (df["FLAG_DSP"] == 1) & (df["FLAG_KYC"] == 0)
    df.loc[m_mag, "BOLSAS_MAGENTA"] = (IB[m_mag] + OB[m_mag]) / 50

    df["BOLSAS_RECOLECCION"] = df["BOLSAS_VERDES"] + df["BOLSAS_MAGENTA"]
    df["ROLLO_SUBE"]   = (SUB * 10 / 2000) / 5
    df["ROLLO_PRISMA"] = ((PCI * 4.4 * 2) / 2000) / 5

    # RESMA: solo tipos 0 y 1 imprimen en papel oficio/A4
    df["RESMA"] = 0.0
    m0_r = df["TIPO_AGENTE"] == 0
    m1_r = df["TIPO_AGENTE"] == 1
    df.loc[m0_r, "RESMA"] = (IB[m0_r] * 3   + OB[m0_r] * 5 + QCASH[m0_r]) / 500
    df.loc[m1_r, "RESMA"] = (IB[m1_r] * 1.5 + OB[m1_r] * 5 + QCASH[m1_r]) / 500

    # El repo convencional (Power BI/Excel) redondea estos valores a 3 decimales;
    # sin este redondeo aparece una variacion minima acumulada frente a la app.
    for _c in ["ROLLOS", "ROLLO_PRISMA", "ROLLO_SUBE", "BOLSAS_RECOLECCION", "RESMA"]:
        df[_c] = df[_c].round(3)

    # FAJAS: viene directo del archivo externo (Qx FAJAS / 200, redondeo al alza)
    if fajas is not None and len(fajas) > 0:
        df = df.merge(fajas[["ID_PF", "FAJAS"]], on="ID_PF", how="left")
        df["FAJAS"] = df["FAJAS"].fillna(0)
    else:
        df["FAJAS"] = 0.0

    # ── Enriquecer MAESTRO ──────────────────────────────────────────────────
    m = maestro.copy()

    for env_df, col_src, col_dst in [
        (prisma_env, "CANTIDAD", "ENVIO_PRISMA"),
        (sube_env,   "CANTIDAD", "ENVIO_SUBE"),
        (rollo_env,  "ROLLOS",   "ENVIO_ROLLO"),
    ]:
        m = m.merge(
            env_df[["AGENTE", col_src]].rename(columns={col_src: col_dst}),
            left_on="ID_PF", right_on="AGENTE", how="left"
        ).drop(columns=["AGENTE"], errors="ignore")

    if resma_env is not None:
        m = m.merge(
            resma_env[["AGENTE", "RESMAS"]].rename(columns={"RESMAS": "ENVIO_RESMA"}),
            left_on="ID_PF", right_on="AGENTE", how="left"
        ).drop(columns=["AGENTE"], errors="ignore")

    consumo = df[["ID_PF", "ROLLOS", "ROLLO_PRISMA", "ROLLO_SUBE",
                  "BOLSAS_RECOLECCION", "RESMA", "FAJAS"]].copy()
    m = m.merge(consumo, on="ID_PF", how="left")

    for c in ["ENVIO_PRISMA", "ENVIO_SUBE", "ENVIO_ROLLO", "ENVIO_RESMA",
              "ROLLOS", "ROLLO_PRISMA", "ROLLO_SUBE", "BOLSAS_RECOLECCION",
              "RESMA", "FAJAS"]:
        if c in m.columns:
            m[c] = m[c].fillna(0)
        else:
            m[c] = 0.0

    for col in ["STOCK_ROLLO_ANT", "STOCK_SUBE_ANT", "STOCK_PRISMA_ANT", "STOCK_RESMA_ANT"]:
        if col not in m.columns:
            m[col] = 0.0

    for col in ["PROV", "DEP", "SEGMENTO", "SUBSEGMENTACION"]:
        if col not in m.columns:
            m[col] = ""

    m["STOCK_ROLLO"]  = m["STOCK_ROLLO_ANT"].clip(lower=0)  + m["ENVIO_ROLLO"]  - m["ROLLOS"]
    m["STOCK_RESMA"]  = m["STOCK_RESMA_ANT"].clip(lower=0)  + m["ENVIO_RESMA"]  - m["RESMA"]
    m["STOCK_SUBE"]   = m["STOCK_SUBE_ANT"].clip(lower=0)   + m["ENVIO_SUBE"]   - m["ROLLO_SUBE"]
    m["STOCK_PRISMA"] = m["STOCK_PRISMA_ANT"].clip(lower=0) + m["ENVIO_PRISMA"] - m["ROLLO_PRISMA"]
    m["AGENTE_NEGATIVO"] = (
        (m["STOCK_ROLLO"] < 0) | (m["STOCK_RESMA"] < 0)
    ).astype(int)

    if "NOMBRE_FANTASIA" in m.columns:
        df = df.merge(m[["ID_PF", "NOMBRE_FANTASIA"]], on="ID_PF", how="left")
        df["NOMBRE_FANTASIA"] = df["NOMBRE_FANTASIA"].fillna("")

    return df, m


def preparar_maestro_exportable(df_tiv, df_maestro):
    """
    Combina los DataFrames de consumo y stock en un único DataFrame
    con el formato esperado por logica_reposicion (columnas con espacio).
    Este archivo sirve como MaestroStock para el módulo de Reposición.
    """
    # Base: columnas del maestro
    cols_mae = ["ID_PF", "NOMBRE_FANTASIA", "PROV", "DEP", "SEGMENTO", "SUBSEGMENTACION",
                "STOCK_ROLLO", "STOCK_RESMA", "STOCK_SUBE", "STOCK_PRISMA"]
    m = df_maestro[[c for c in cols_mae if c in df_maestro.columns]].copy()

    # Garantizar columnas descriptivas aunque no vengan del maestro
    for col in ["PROV", "DEP", "SEGMENTO", "SUBSEGMENTACION"]:
        if col not in m.columns:
            m[col] = ""

    # Agregar consumos desde df_tiv
    consumo_cols = ["ID_PF", "TIPO_AGENTE", "FLAG_DSP_KYC",
                    "ROLLOS", "BOLSAS_RECOLECCION", "ROLLO_SUBE", "ROLLO_PRISMA",
                    "RESMA", "FAJAS"]
    tiv_sub = df_tiv[[c for c in consumo_cols if c in df_tiv.columns]].copy()
    m = m.merge(tiv_sub, on="ID_PF", how="left")

    # Renombrar a formato con espacio (compatibilidad con logica_reposicion)
    m = m.rename(columns={
        "ID_PF":              "ID P.F",
        "NOMBRE_FANTASIA":    "NOMBRE FANTASIA",
        "STOCK_ROLLO":        "STOCK ROLLO",
        "STOCK_RESMA":        "STOCK RESMA",
        "STOCK_SUBE":         "STOCK SUBE",
        "STOCK_PRISMA":       "STOCK PRISMA",
        "ROLLOS":             "ROLLO",
        "BOLSAS_RECOLECCION": "BOLSA RECOLECCION",
        "ROLLO_SUBE":         "ROLLO SUBE",
        "ROLLO_PRISMA":       "ROLLO PRISMA",
        "TIPO_AGENTE":        "TIPO",
    })

    # Rellenar NaN en columnas numéricas
    num_cols = ["STOCK ROLLO", "STOCK RESMA", "STOCK SUBE", "STOCK PRISMA",
                "ROLLO", "BOLSA RECOLECCION", "ROLLO PRISMA", "ROLLO SUBE",
                "RESMA", "FAJAS"]
    for c in num_cols:
        if c in m.columns:
            m[c] = m[c].fillna(0)

    return m
