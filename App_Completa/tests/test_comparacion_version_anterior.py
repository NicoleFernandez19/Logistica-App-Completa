"""
Prueba de comparacion: version anterior (script suelto en "App paso 4 anterior")
vs. Paso 3 + Paso 4 de la app actual.

A diferencia de la primera version de esta prueba, NO reprocesa los 3 meses
historicos (M-3, M-2, M-1) en cada corrida: los lee ya calculados desde
tests/datos_prueba_comparacion/paso2_export/ (generados una sola vez por
generar_historico_prueba.py). Lo unico que se procesa en cada corrida es el
mes ACTUAL, cargado desde UN SOLO libro Excel multi-hoja (igual al formato
real de Paso 1, ej. "01_DATOS_v5.xlsx"), tal como se carga en la app de
verdad.

Flujo:
  1. Toma el stock final de M-1 (ya calculado, sin recomputar) como stock de
     partida del mes ACTUAL.
  2. Genera el libro de Paso 1 del mes ACTUAL y corre el Paso 2 real sobre el
     (unica vez que se ejecuta calculos_consumo.calcular en esta prueba).
  3. Usa los archivos que devuelve el Paso 2 -- los 3 historicos ya
     calculados + el maestro actual recien calculado -- como entrada de:
       a) el script viejo (ejecutado tal cual, sin modificar, via subprocess)
       b) logica_reposicion.ejecutar_proceso_reposicion (paso 3+4 actuales)
  4. Compara ambos resultados finales (ID P.F, SKU, CANTIDAD).

No requiere pytest: se ejecuta con `python tests/test_comparacion_version_anterior.py`.
Si no existen los archivos historicos, correr antes:
    python tests/generar_historico_prueba.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from tests._datos_comunes import IDS, escribir_libro_paso1, cargar_libro_paso1, correr_paso2
from app.logic.logica_reposicion import ejecutar_proceso_reposicion
from app.config import PARAMETROS, PRODUCTOS, REGLAS

SCRIPT_VIEJO = RAIZ / "App paso 4 anterior" / "repo_con_segmento_para_eliminar_agentes_v9.2.py"
DIR_HISTORICO = Path(__file__).resolve().parent / "datos_prueba_comparacion" / "paso2_export"

# Historicos ya procesados (NO se recalculan en esta prueba)
PATH_CONSUMO_M3 = DIR_HISTORICO / "CONSUMO_ABRIL_2026.xlsx"    # mas viejo
PATH_CONSUMO_M2 = DIR_HISTORICO / "CONSUMO_MAYO_2026.xlsx"
PATH_CONSUMO_M1 = DIR_HISTORICO / "CONSUMO_JUNIO_2026.xlsx"    # mas reciente
PATH_MAESTRO_M1 = DIR_HISTORICO / "MAESTRO_CONSUMO_ENVIO_JUNIO_2026.xlsx"  # stock final de M-1


def _requerir_historico():
    faltantes = [p for p in (PATH_CONSUMO_M3, PATH_CONSUMO_M2, PATH_CONSUMO_M1, PATH_MAESTRO_M1)
                 if not p.exists()]
    if faltantes:
        raise SystemExit(
            "Faltan los archivos historicos ya procesados:\n"
            + "\n".join(f"  - {p}" for p in faltantes)
            + "\n\nCorrer primero: python tests/generar_historico_prueba.py"
        )


def main():
    _requerir_historico()

    tmp = Path(tempfile.mkdtemp(prefix="prueba_comparacion_"))
    print(f"Carpeta temporal (solo para el mes ACTUAL): {tmp}")

    # Stock de partida del mes ACTUAL = stock final de M-1, ya calculado.
    stock_m1 = pd.read_excel(PATH_MAESTRO_M1, sheet_name="MaestroStock").set_index("ID P.F")
    stock_ant = {
        aid: {
            "ROLLO":  float(stock_m1.loc[aid, "STOCK ROLLO"]),
            "RESMA":  float(stock_m1.loc[aid, "STOCK RESMA"]),
            "SUBE":   float(stock_m1.loc[aid, "STOCK SUBE"]),
            "PRISMA": float(stock_m1.loc[aid, "STOCK PRISMA"]),
        }
        for aid in IDS
    }

    # ── Unico procesamiento de esta prueba: Paso 1 (un libro) + Paso 2 del mes ACTUAL ──
    libro_actual = tmp / "01_DATOS_ACTUAL.xlsx"
    escribir_libro_paso1(libro_actual, mes_idx=3, stock_ant=stock_ant)
    paths_actual = cargar_libro_paso1(libro_actual)
    _, _, df_repo_actual = correr_paso2(paths_actual)
    print(f"  Libro de Paso 1 del mes ACTUAL: {libro_actual.name} (procesado una sola vez)")

    path_maestro_actual = tmp / "MAESTRO_CONSUMO_ENVIO_AGOSTO_2026.xlsx"
    with pd.ExcelWriter(path_maestro_actual, engine="openpyxl") as w:
        df_repo_actual.to_excel(w, sheet_name="MaestroStock", index=False)

    # ── (a) Correr la app version anterior (script intacto) ────────────────
    dir_legacy = tmp / "legacy_run"
    dir_legacy.mkdir()
    shutil.copy2(str(SCRIPT_VIEJO), str(dir_legacy / SCRIPT_VIEJO.name))
    shutil.copy2(str(PATH_CONSUMO_M3), str(dir_legacy / "CONSUMO_ABRIL_2026.xlsx"))
    shutil.copy2(str(PATH_CONSUMO_M2), str(dir_legacy / "CONSUMO_MAYO_2026.xlsx"))
    shutil.copy2(str(PATH_CONSUMO_M1), str(dir_legacy / "CONSUMO_JUNIO_2026.xlsx"))
    shutil.copy2(str(path_maestro_actual), str(dir_legacy / "MAESTRO_CONSUMO_ENVIO_AGOSTO_2026.xlsx"))

    venv_python = RAIZ / ".venv" / "Scripts" / "python.exe"
    proc = subprocess.run(
        [str(venv_python), SCRIPT_VIEJO.name],
        cwd=str(dir_legacy), capture_output=True, text=True,
    )
    if proc.returncode != 0:
        print("── stderr del script viejo ──")
        print(proc.stderr[-4000:])
    assert proc.returncode == 0, "El script de la app anterior fallo al ejecutarse."

    df_legacy = pd.read_excel(dir_legacy / "REPOSICION_CRUDO_FINAL_.xlsx")
    if "ID P.F" not in df_legacy.columns:
        df_legacy = pd.read_excel(dir_legacy / "REPOSICION_CRUDO_FINAL_.xlsx", index_col=0)
        df_legacy = df_legacy.reset_index().rename(columns={"index": "ID P.F"})
    df_legacy = df_legacy[["ID P.F", "SKU", "CANTIDAD"]]

    # ── (b) Correr Paso 3 + Paso 4 de la app actual ─────────────────────────
    ok, msg, df_detallado, df_final = ejecutar_proceso_reposicion(
        df_maestro_actual=df_repo_actual,
        rutas_consumos={
            "consumo_mes_1": str(PATH_CONSUMO_M3),   # M-3 (mas viejo)
            "consumo_mes_2": str(PATH_CONSUMO_M2),   # M-2
            "consumo_mes_3": str(PATH_CONSUMO_M1),   # M-1 (mas reciente)
        },
        ruta_agentes=None,
        parametros_calculo=PARAMETROS,
        productos=PRODUCTOS,
        reglas=REGLAS,
    )
    assert ok, f"El proceso de reposicion de la app actual fallo: {msg}"
    df_nueva = df_final[["ID P.F", "SKU", "CANTIDAD"]].copy()

    # ── Comparacion ──────────────────────────────────────────────────────────
    agg_legacy = df_legacy.groupby(["ID P.F", "SKU"], as_index=False)["CANTIDAD"].sum()
    agg_nueva  = df_nueva.groupby(["ID P.F", "SKU"], as_index=False)["CANTIDAD"].sum()

    comp = pd.merge(
        agg_legacy, agg_nueva, on=["ID P.F", "SKU"], how="outer",
        suffixes=("_ANTERIOR", "_ACTUAL"),
    ).fillna(0)
    comp["DIFERENCIA"] = comp["CANTIDAD_ACTUAL"] - comp["CANTIDAD_ANTERIOR"]

    print("\n── Comparacion ANTERIOR vs ACTUAL (por agente / SKU) ──")
    print(comp.sort_values(["ID P.F", "SKU"]).to_string(index=False))

    diffs = comp[comp["DIFERENCIA"].abs() > 1e-6]
    print(f"\nFilas comparadas: {len(comp)}. Filas con diferencia: {len(diffs)}.")

    if len(diffs) == 0:
        print("\nRESULTADO: coinciden EXACTAMENTE. La app actual (Paso 3+4) "
              "reproduce el calculo de la version anterior.")
    else:
        diffs_grandes = diffs[diffs["DIFERENCIA"].abs() > 1]
        print("\nDiferencias encontradas:")
        print(diffs.to_string(index=False))
        assert diffs_grandes.empty, (
            "Se encontraron diferencias mayores a 1 unidad entre la app anterior "
            "y la actual; revisar la logica de calculo."
        )
        print("\nRESULTADO: diferencias menores o iguales a 1 unidad (redondeo). "
              "Considerado 'muy similar'.")


if __name__ == "__main__":
    main()
