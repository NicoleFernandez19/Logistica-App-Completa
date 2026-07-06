"""
Prueba de integracion: verifica la regla de negocio

    "El mes mas anterior (M-1) al Maestro de Stock del Paso 3 debe ser el
    Consumo Mensual, y ambos (Maestro de Stock actual + Consumo M-1) deben
    poder salir de la MISMA corrida de Paso 2 (mismo archivo exportado)."

Simula 4 corridas mensuales consecutivas de Paso 2 (calculos_consumo.calcular +
preparar_maestro_exportable), exporta cada una a un .xlsx multi-hoja igual que
_write_export_workbook en paso2_consumo.py, y luego usa esos 4 archivos como
entrada del Paso 3 (maestro_actual + consumo_mes_1/2/3) para correr
logica_reposicion.ejecutar_proceso_reposicion.

No requiere pytest: se ejecuta con `python test_vinculo_paso2_paso3.py`.
"""
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.logic.calculos_consumo import calcular, preparar_maestro_exportable
from app.logic.logica_reposicion import ejecutar_proceso_reposicion
from app.config import PARAMETROS, PRODUCTOS, REGLAS

AGENTES = ["A001", "A002", "A003"]


def _tiv(ib, ob, prisma_co):
    """TIV con transacciones que crecen mes a mes (IB/OB/PRISMA_CO parametrizables)."""
    return pd.DataFrame({
        "ID_PF": AGENTES,
        "BP_TU": [100, 200, 300],
        "TX_IMT_OB": [ob, ob + 5, ob + 10],
        "TX_IMT_IB": [ib, ib + 5, ib + 10],
        "TX_DMT_OB": [10, 10, 10],
        "TX_DMT_IB": [10, 10, 10],
        "PRISMA_CI": [5, 5, 5],
        "PRISMA_CO": [prisma_co, prisma_co, prisma_co],
        "TX_QCASH": [0, 0, 0],
        "TXS_SIN_FAC": [0, 0, 0],
    })


def _maestro(stock_rollo_ant):
    return pd.DataFrame({
        "ID_PF": AGENTES,
        "NOMBRE_FANTASIA": ["Agente Uno", "Agente Dos", "Agente Tres"],
        "PROV": ["BUENOS AIRES", "BUENOS AIRES", "MENDOZA"],
        "DEP": [0, 0, 0],
        "SEGMENTO": ["S1", "S1", "S2"],
        "SUBSEGMENTACION": [1, 1, 1],
        "STOCK_ROLLO_ANT": [stock_rollo_ant] * 3,
    })


def _envio(cantidad, col="CANTIDAD"):
    return pd.DataFrame({"AGENTE": AGENTES, col: [cantidad] * 3})


def _vacio(cols):
    return pd.DataFrame({c: [] for c in cols})


def _correr_paso2(mes_idx, ib, ob, prisma_co, stock_rollo_ant):
    """Simula una corrida de Paso 2 y devuelve el DataFrame combinado
    (equivalente a la hoja 'MaestroStock', primera hoja del export real)."""
    tiv = _tiv(ib, ob, prisma_co)
    maestro = _maestro(stock_rollo_ant)
    fac_termicas = _vacio(["ID_PF"])
    dsp_kyc = pd.DataFrame({"ID_PF": AGENTES, "FLAG_DSP": [0, 0, 0], "FLAG_KYC": [0, 0, 0]})
    com_tx_int = _vacio(["ID_PF"])
    prisma_env = _envio(0)
    sube_env = _envio(0)
    trx_sube = pd.DataFrame({"ID_PF": AGENTES, "TRX_SUBE": [0, 0, 0]})
    rollo_env = _envio(200, col="ROLLOS")
    resma_env = pd.DataFrame({"AGENTE": AGENTES, "RESMAS": [50, 50, 50]})
    fajas = pd.DataFrame({"ID_PF": AGENTES, "FAJAS": [0, 0, 0]})

    df_tiv, df_mae = calcular(
        tiv, maestro, fac_termicas, prisma_env, sube_env, trx_sube,
        dsp_kyc, com_tx_int, rollo_env, resma_env=resma_env, fajas=fajas,
    )
    df_repo = preparar_maestro_exportable(df_tiv, df_mae)
    return df_tiv, df_mae, df_repo


def _escribir_export(path, df_tiv, df_mae, df_repo):
    """Replica _write_export_workbook de paso2_consumo.py: la hoja 'MaestroStock'
    (combinada, stock + consumo) va SIEMPRE primera -> es la que se lee por
    defecto (sheet_name=0) sin importar si el archivo se usa como maestro_actual
    o como historico M-1/M-2/M-3."""
    consumo_cols = ["ID_PF", "TIPO_AGENTE", "NOMBRE_FANTASIA", "ROLLOS",
                    "BOLSAS_RECOLECCION", "ROLLO_SUBE", "ROLLO_PRISMA", "RESMA", "FAJAS"]
    consumo = df_tiv[[c for c in consumo_cols if c in df_tiv.columns]].rename(columns={
        "ID_PF": "ID P.F", "TIPO_AGENTE": "TIPO", "NOMBRE_FANTASIA": "NOMBRE FANTASIA",
        "ROLLOS": "ROLLO", "BOLSAS_RECOLECCION": "BOLSA RECOLECCION",
        "ROLLO_SUBE": "ROLLO SUBE", "ROLLO_PRISMA": "ROLLO PRISMA",
    })
    stock_cols = ["ID_PF", "NOMBRE_FANTASIA", "PROV", "DEP", "SEGMENTO",
                  "SUBSEGMENTACION", "STOCK_ROLLO", "STOCK_RESMA", "STOCK_SUBE", "STOCK_PRISMA"]
    stock = df_mae[[c for c in stock_cols if c in df_mae.columns]].rename(columns={
        "ID_PF": "ID P.F", "NOMBRE_FANTASIA": "NOMBRE FANTASIA",
        "STOCK_ROLLO": "STOCK ROLLO", "STOCK_RESMA": "STOCK RESMA",
        "STOCK_SUBE": "STOCK SUBE", "STOCK_PRISMA": "STOCK PRISMA",
    })
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df_repo.to_excel(writer, sheet_name="MaestroStock", index=False)
        consumo.to_excel(writer, sheet_name="Consumo Mensual", index=False)
        stock.to_excel(writer, sheet_name="Maestro Stock", index=False)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="prueba_vinculo_"))
    print(f"Carpeta temporal: {tmp}")

    # 4 corridas mensuales consecutivas con transacciones DISTINTAS entre si,
    # para poder distinguir sin ambiguedad que datos vinieron de que mes.
    corridas = {}
    parametros_mes = {
        "M-3": dict(ib=10, ob=10, prisma_co=1, stock_rollo_ant=50),
        "M-2": dict(ib=20, ob=20, prisma_co=2, stock_rollo_ant=40),
        "M-1": dict(ib=30, ob=30, prisma_co=3, stock_rollo_ant=30),
        "ACTUAL": dict(ib=40, ob=40, prisma_co=4, stock_rollo_ant=20),
    }
    for mes_idx, (etiqueta, params) in enumerate(parametros_mes.items()):
        df_tiv, df_mae, df_repo = _correr_paso2(mes_idx, **params)
        path = tmp / f"MAESTRO_CONSUMO_ENVIO_{etiqueta}.xlsx"
        _escribir_export(path, df_tiv, df_mae, df_repo)
        corridas[etiqueta] = dict(path=path, df_tiv=df_tiv, df_mae=df_mae, df_repo=df_repo)
        print(f"  Corrida '{etiqueta}' exportada -> {path.name}")

    # ── Paso 3: maestro_actual = corrida ACTUAL, historicos M-1/M-2/M-3 ────────
    rutas_consumos = {
        "consumo_mes_3": str(corridas["M-1"]["path"]),   # clave interna "M-1" en la UI
        "consumo_mes_2": str(corridas["M-2"]["path"]),
        "consumo_mes_1": str(corridas["M-3"]["path"]),
    }
    df_maestro_actual = corridas["ACTUAL"]["df_repo"]

    ok, msg, df_detallado, df_final = ejecutar_proceso_reposicion(
        df_maestro_actual=df_maestro_actual,
        rutas_consumos=rutas_consumos,
        ruta_agentes=None,
        parametros_calculo=PARAMETROS,
        productos=PRODUCTOS,
        reglas=REGLAS,
    )

    assert ok, f"El proceso de reposicion fallo: {msg}"
    print("OK: ejecutar_proceso_reposicion no genero errores.")

    # ── Verificaciones puntuales ────────────────────────────────────────────
    fila = df_detallado.loc["A001"]

    consumo_rollo_m1_esperado = float(
        corridas["M-1"]["df_repo"].set_index("ID P.F").loc["A001", "ROLLO"]
    )
    stock_rollo_actual_esperado = float(
        corridas["ACTUAL"]["df_repo"].set_index("ID P.F").loc["A001", "STOCK ROLLO"]
    )

    assert "ROLLO_m3" in fila.index, (
        "No se encontro la columna ROLLO_m3: el archivo M-1 no aporto datos de "
        "consumo mensual (revisar que la hoja leida por defecto sea 'MaestroStock')."
    )
    valor_leido = float(fila["ROLLO_m3"])
    assert abs(valor_leido - consumo_rollo_m1_esperado) < 1e-6, (
        f"El consumo M-1 (ROLLO_m3={valor_leido}) no coincide con el Consumo "
        f"Mensual de esa corrida ({consumo_rollo_m1_esperado}). "
        "Esto indicaria que Paso 3 esta leyendo la hoja equivocada del archivo."
    )
    print(f"OK: ROLLO_m3 (consumo M-1) = {valor_leido} == Consumo Mensual de esa corrida.")

    valor_stock = float(fila["STOCK ROLLO"]) + valor_leido  # el codigo resta ROLLO_m3 al stock (linea 189 logica_reposicion.py)
    assert abs(valor_stock - stock_rollo_actual_esperado) < 1e-6, (
        f"El STOCK ROLLO del maestro actual ({valor_stock}) no coincide con el "
        f"stock final de la corrida ACTUAL ({stock_rollo_actual_esperado})."
    )
    print(f"OK: STOCK ROLLO del maestro actual coincide con la corrida ACTUAL ({stock_rollo_actual_esperado}).")

    assert abs(consumo_rollo_m1_esperado - stock_rollo_actual_esperado) > 1e-6, (
        "Los valores de consumo M-1 y stock actual son iguales por casualidad; "
        "la prueba no podria detectar si se esta leyendo la hoja incorrecta."
    )

    print("\nTODAS LAS VERIFICACIONES PASARON.")
    print("Confirmado: el Maestro de Stock actual y el Consumo M-1 usados en el "
          "Paso 3 se obtienen correctamente de la misma hoja combinada "
          "('MaestroStock') que exporta el Paso 2 en cada corrida.")


if __name__ == "__main__":
    main()
