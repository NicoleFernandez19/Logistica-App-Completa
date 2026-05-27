import numpy as np
import pandas as pd
import os
import traceback
from functools import reduce
from pathlib import Path
from .cargador import _leer as _leer_archivo


def _redondear_con_parametro(serie, parametro):
    serie_num = pd.to_numeric(serie, errors="coerce").fillna(0)
    return np.where(
        serie_num - np.floor(serie_num) <= parametro,
        np.floor(serie_num),
        np.ceil(serie_num),
    )


def _calcular_repo_regresion(df, nombre_base, col_reseteo_key, factor_ajuste):
    col_m1 = f"{nombre_base}_m1"
    col_m2 = f"{nombre_base}_m2"
    col_m3 = f"{nombre_base}_m3"

    if not all(c in df.columns for c in [col_m1, col_m2, col_m3]):
        print(f"  ADVERTENCIA: Faltan columnas para '{nombre_base}'. Se asigna 0.")
        return pd.Series(0, index=df.index)

    promedio = (df[col_m1] + df[col_m2] + df[col_m3]) / 3
    pendiente = (
        3 * (df[col_m1] * 1 + df[col_m2] * 2 + df[col_m3] * 3)
        - 6 * (df[col_m1] + df[col_m2] + df[col_m3])
    ) / (3 * 14 - 36)
    ordenada = promedio - (pendiente * 2)
    prediccion = pendiente * 4 + ordenada

    sub = df["SUBSEGMENTACION"] if "SUBSEGMENTACION" in df.columns else 1
    col_reseteo = df[col_reseteo_key] if (col_reseteo_key and col_reseteo_key in df.columns) else 0

    repo_promedio   = (promedio   * sub * factor_ajuste) - col_reseteo
    repo_prediccion = (prediccion * sub * factor_ajuste) - col_reseteo

    return np.where(pendiente <= 0, repo_promedio, repo_prediccion)


def validar_entradas(rutas_consumos, ruta_agentes):
    """Verifica existencia de archivos. Devuelve (ok, mensaje)."""
    errores = []
    for key, path in rutas_consumos.items():
        if not path or not os.path.exists(path):
            errores.append(f"'{key}': {path or '(no seleccionado)'}")
    if not ruta_agentes or not os.path.exists(ruta_agentes):
        errores.append(f"'agentes': {ruta_agentes or '(no seleccionado)'}")
    if errores:
        return False, "Archivos no encontrados:\n" + "\n".join(errores)
    return True, "OK"


def ejecutar_proceso_reposicion(
    df_maestro_actual,
    rutas_consumos,
    ruta_agentes,
    parametros_calculo,
    productos,
    reglas,
    agentes_excluir=None,
):
    """
    df_maestro_actual : DataFrame preparado por preparar_maestro_exportable()
    rutas_consumos    : {'consumo_mes_1': path, 'consumo_mes_2': path, 'consumo_mes_3': path}
    ruta_agentes      : path al Excel de agentes Canal Propio
    Devuelve (success, mensaje, df_detallado, df_final)
    """
    try:
        print("Paso 1/8: Leyendo archivos de consumo histórico...")
        df_C1 = _leer_archivo(rutas_consumos["consumo_mes_1"])
        df_C2 = _leer_archivo(rutas_consumos["consumo_mes_2"])
        df_C3 = _leer_archivo(rutas_consumos["consumo_mes_3"])

        # Normalizar ID P.F en archivos históricos
        for df in [df_C1, df_C2, df_C3]:
            if "ID_PF" in df.columns and "ID P.F" not in df.columns:
                df.rename(columns={"ID_PF": "ID P.F"}, inplace=True)
            if "ID P.F" in df.columns:
                df["ID P.F"] = df["ID P.F"].astype(str).str.strip().str.replace("-", "", regex=False)

        for key, df_hist in [
            ("consumo_mes_1", df_C1),
            ("consumo_mes_2", df_C2),
            ("consumo_mes_3", df_C3),
        ]:
            if "ID P.F" not in df_hist.columns:
                nombre = Path(rutas_consumos[key]).name
                raise ValueError(
                    f"Archivo histórico '{nombre}': columna 'ID P.F' no encontrada.\n"
                    f"Columnas disponibles: {list(df_hist.columns[:20])}"
                )

        print("Paso 2/8: Leyendo archivo de agentes...")
        df_agentes = _leer_archivo(ruta_agentes)
        if df_agentes.empty or len(df_agentes.columns) == 0:
            raise ValueError(f"El archivo de agentes está vacío: '{Path(ruta_agentes).name}'")
        col_ag = next(
            (c for c in ["ID P.F", "ID_PF"] if c in df_agentes.columns),
            None,
        )
        if col_ag is None:
            raise ValueError(
                f"Archivo de agentes '{Path(ruta_agentes).name}': columna de ID no encontrada.\n"
                f"Columnas disponibles: {list(df_agentes.columns[:20])}"
            )
        lista_agentes_ajuste = (
            df_agentes[col_ag].astype(str).str.strip().str.replace("-", "", regex=False).unique().tolist()
        )

        print("Paso 3/8: Unificando datos...")
        # Normalizar el maestro actual
        df_maestro = df_maestro_actual.copy()
        if "ID_PF" in df_maestro.columns and "ID P.F" not in df_maestro.columns:
            df_maestro.rename(columns={"ID_PF": "ID P.F"}, inplace=True)
        if "ID P.F" in df_maestro.columns:
            df_maestro["ID P.F"] = df_maestro["ID P.F"].astype(str).str.strip().str.replace("-", "", regex=False)

        # Renombrar columnas de consumo histórico para evitar conflictos
        df_C1r = df_C1.rename(columns={c: f"{c}_m1" for c in df_C1.columns if c != "ID P.F"})
        df_C2r = df_C2.rename(columns={c: f"{c}_m2" for c in df_C2.columns if c != "ID P.F"})
        df_C3r = df_C3.rename(columns={c: f"{c}_m3" for c in df_C3.columns if c != "ID P.F"})

        df_consumos = reduce(
            lambda l, r: pd.merge(l, r, on="ID P.F", how="outer"),
            [df_C1r, df_C2r, df_C3r],
        )

        # Columnas del maestro para el merge
        cols_stock = [
            c for c in ["ID P.F", "PROV", "DEP", "SEGMENTO", "SUBSEGMENTACION",
                        "STOCK ROLLO", "STOCK SUBE", "STOCK PRISMA",
                        "NOMBRE FANTASIA", "TIPO"]
            if c in df_maestro.columns
        ]
        df_union = pd.merge(df_consumos, df_maestro[cols_stock], how="left", on="ID P.F")
        df_union.set_index("ID P.F", inplace=True)

        print("Paso 4/8: Limpiando datos...")
        cols_texto = [
            c for c in df_union.columns
            if "NOMBRE FANTASIA" in c or c in {"PROV", "SEGMENTO"}
        ]
        cols_numericas = [c for c in df_union.columns if c not in cols_texto]
        if cols_texto:
            df_union[cols_texto] = df_union[cols_texto].fillna("")
        if cols_numericas:
            df_union[cols_numericas] = (
                df_union[cols_numericas]
                .apply(pd.to_numeric, errors="coerce")
                .fillna(0)
            )
        # SUBSEGMENTACION se usa como multiplicador; si quedó en 0 (celda vacía),
        # usar 1 como valor neutro para no anular todas las reposiciones
        if "SUBSEGMENTACION" in df_union.columns:
            df_union["SUBSEGMENTACION"] = df_union["SUBSEGMENTACION"].where(
                df_union["SUBSEGMENTACION"] != 0, 1
            )

        print("Paso 5/8: Calculando stock ajustado...")
        for stock_col, consumo_col in [
            ("STOCK ROLLO",  "ROLLO_m3"),
            ("STOCK PRISMA", "ROLLO PRISMA_m3"),
            ("STOCK SUBE",   "ROLLO SUBE_m3"),
        ]:
            if stock_col in df_union.columns and consumo_col in df_union.columns:
                df_union[stock_col] = df_union[stock_col] - df_union[consumo_col]

        for reseteo, stock_col in [
            ("RESETEO ROLLO",  "STOCK ROLLO"),
            ("RESETEO PRISMA", "STOCK PRISMA"),
            ("RESETEO SUBE",   "STOCK SUBE"),
        ]:
            if stock_col in df_union.columns:
                df_union[reseteo] = np.where(df_union[stock_col] < 0, 0, df_union[stock_col])

        print("Paso 6/8: Calculando reposición por producto...")
        for prod in productos:
            nombre_base  = prod["nombre_base"]
            col_consumo  = prod.get("col_consumo", nombre_base)
            col_repo     = prod["col_repo"]
            metodo       = prod.get("metodo")
            factor_key   = prod.get("factor_ajuste")
            factor       = parametros_calculo.get(factor_key, 1.0) if factor_key else 1.0

            print(f"  - {nombre_base} ({metodo})")
            sub = df_union["SUBSEGMENTACION"] if "SUBSEGMENTACION" in df_union.columns else 1
            repo = pd.Series(0.0, index=df_union.index)

            if metodo == "regresion":
                col_reseteo = prod.get("col_stock_reseteo")
                repo = _calcular_repo_regresion(df_union, col_consumo, col_reseteo, factor)

            elif metodo == "promedio":
                col_m1 = f"{col_consumo}_m1"
                col_m2 = f"{col_consumo}_m2"
                col_m3 = f"{col_consumo}_m3"
                if all(c in df_union.columns for c in [col_m1, col_m2, col_m3]):
                    prom = (df_union[col_m1] + df_union[col_m2] + df_union[col_m3]) / 3
                    repo = prom * sub * factor

            elif metodo == "promedio_ajustado_dep":
                col_m1 = f"{col_consumo}_m1"
                col_m2 = f"{col_consumo}_m2"
                col_m3 = f"{col_consumo}_m3"
                if all(c in df_union.columns for c in [col_m1, col_m2, col_m3]):
                    prom = (df_union[col_m1] + df_union[col_m2] + df_union[col_m3]) / 3
                    repo_tmp = (prom * sub * factor).apply(np.ceil)
                    dep = df_union["DEP"] if "DEP" in df_union.columns else 0
                    repo = np.where(dep == 1, 0, repo_tmp)

            df_union[col_repo] = np.where(repo <= 0, 0, repo)

            param_r_key = prod.get("param_redondeo")
            if param_r_key and metodo != "promedio_ajustado_dep":
                param_r = parametros_calculo.get(param_r_key, 0.5)
                df_union[col_repo] = _redondear_con_parametro(df_union[col_repo], param_r)

        print("Paso 7/8: Aplicando reglas de negocio...")
        df_detallado = df_union.copy()

        print("Paso 8/8: Generando archivo final...")
        df_union.reset_index(inplace=True)

        # Preferir "NOMBRE FANTASIA" del maestro actual (columna sin sufijo, cubre todos los
        # agentes). Si no existe, usar la versión _m3 (histórico M-1) como respaldo.
        _col_mae  = "NOMBRE FANTASIA" if "NOMBRE FANTASIA" in df_union.columns else None
        _col_hist = next(
            (c for c in df_union.columns if "NOMBRE FANTASIA" in c and c != "NOMBRE FANTASIA"),
            None,
        )
        col_nombre = _col_mae or _col_hist

        pedidos = []
        skus_canal_propio = reglas.get("skus_ajuste_canal_propio", [])

        for prod in productos:
            col_repo = prod["col_repo"]
            cols_ext = ["ID P.F", "PROV", "SEGMENTO", col_repo]
            if col_nombre:
                cols_ext.append(col_nombre)
            if _col_hist and _col_hist not in cols_ext:
                cols_ext.append(_col_hist)

            df_p = df_union[[c for c in cols_ext if c in df_union.columns]].copy()
            ren = {col_repo: "CANTIDAD"}
            if col_nombre and col_nombre != "NOMBRE FANTASIA":
                ren[col_nombre] = "NOMBRE FANTASIA"
            df_p.rename(columns=ren, inplace=True)

            if "NOMBRE FANTASIA" in df_p.columns and _col_hist and _col_hist in df_p.columns:
                # Llenar vacíos del maestro con los nombres del histórico
                df_p["NOMBRE FANTASIA"] = df_p["NOMBRE FANTASIA"].fillna(df_p[_col_hist]).fillna("")
                df_p.drop(columns=[_col_hist], inplace=True, errors="ignore")
            elif "NOMBRE FANTASIA" not in df_p.columns:
                df_p["NOMBRE FANTASIA"] = ""

            df_p["SKU"]        = prod["sku_base"]
            df_p["DESCRIPCION"] = prod["desc_base"]

            if prod.get("prov_filter") and "PROV" in df_p.columns:
                df_p = df_p[df_p["PROV"] == prod["prov_filter"]]
            if prod.get("prov_excluir") and "PROV" in df_p.columns:
                df_p = df_p[df_p["PROV"] != prod["prov_excluir"]]

            for col in ["NOMBRE FANTASIA", "SEGMENTO"]:
                if col not in df_p.columns:
                    df_p[col] = ""
            df_p = df_p[["ID P.F", "NOMBRE FANTASIA", "SKU", "DESCRIPCION", "CANTIDAD", "SEGMENTO"]]
            pedidos.append(df_p)

        df_final = pd.concat(pedidos, ignore_index=True)
        df_final["CANTIDAD"] = df_final["CANTIDAD"].apply(np.ceil)
        df_final = df_final.dropna(subset=["CANTIDAD"])
        df_final = df_final[df_final["CANTIDAD"] > 0]

        if agentes_excluir:
            df_final = df_final[~df_final["ID P.F"].isin(agentes_excluir)]

        ajuste_cp = parametros_calculo.get("ajuste_canal_propio", 1.0)
        filtro_cp = (
            df_final["ID P.F"].isin(lista_agentes_ajuste)
            & df_final["SKU"].isin(skus_canal_propio)
        )
        df_final.loc[filtro_cp, "CANTIDAD"] = df_final.loc[filtro_cp, "CANTIDAD"].apply(
            lambda x: np.ceil(x * ajuste_cp)
        )

        print("Proceso completado exitosamente.")
        return True, "Proceso completado exitosamente.", df_detallado, df_final

    except FileNotFoundError as e:
        msg = f"Archivo no encontrado:\n{e}"
        print(msg)
        return False, msg, None, None
    except KeyError as e:
        msg = f"Columna no encontrada: {e}\n\nVerifique que los archivos tengan el formato correcto."
        print(msg)
        return False, msg, None, None
    except Exception as e:
        msg = f"Error inesperado: {type(e).__name__}: {e}\n\n{traceback.format_exc()}"
        print(msg)
        return False, msg, None, None
