"""
Genera UNA SOLA VEZ los datos historicos de prueba (M-3, M-2, M-1) y los deja
guardados en tests/datos_prueba_comparacion/paso2_export/, para que
test_comparacion_version_anterior.py los reutilice sin volver a correr Paso 1/2.

Para cada mes historico guarda dos archivos (ambos son, en definitiva, la
misma corrida de Paso 2 -- solo cambia que columnas se recortan):
  - MAESTRO_CONSUMO_ENVIO_<MES>.xlsx : hoja "MaestroStock" combinada
    (stock + consumo), igual a lo que hoy exporta el Paso 2 real. Sirve para
    "encadenar" el stock inicial del mes siguiente sin recalcular nada.
  - CONSUMO_<MES>.xlsx : solo la hoja "Consumo Mensual" (sin stock), en el
    formato que espera el script de la app anterior.

Tambien guarda, por separado, el LIBRO de Paso 1 (unico archivo multi-hoja)
que hubiera generado cada mes historico -- por si se quiere auditar de donde
salen esos numeros -- aunque el test de comparacion NO lo vuelve a leer.

Se corre a mano, rara vez:
    python tests/generar_historico_prueba.py
"""
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from tests._datos_comunes import (
    IDS, STOCK_INICIAL, escribir_libro_paso1, cargar_libro_paso1,
    correr_paso2, consumo_mensual_df, stock_final,
)

DIR_SALIDA = Path(__file__).resolve().parent / "datos_prueba_comparacion"
DIR_LIBROS = DIR_SALIDA / "libros_paso1_historico"
DIR_EXPORT = DIR_SALIDA / "paso2_export"

NOMBRE_MES = {"M-3": "ABRIL_2026", "M-2": "MAYO_2026", "M-1": "JUNIO_2026"}
HOJA_CONSUMO_MES = {"M-3": "CONSUMO_MENSUAL", "M-2": "CONSUMO_MENSUAL", "M-1": "Consumo Mensual"}


def main():
    DIR_LIBROS.mkdir(parents=True, exist_ok=True)
    DIR_EXPORT.mkdir(parents=True, exist_ok=True)

    stock_ant = {aid: dict(STOCK_INICIAL) for aid in IDS}

    for etiqueta, mes_idx in [("M-3", 0), ("M-2", 1), ("M-1", 2)]:
        nombre_mes = NOMBRE_MES[etiqueta]
        libro = DIR_LIBROS / f"01_DATOS_{etiqueta}_{nombre_mes}.xlsx"
        escribir_libro_paso1(libro, mes_idx, stock_ant)

        paths = cargar_libro_paso1(libro)
        df_tiv, df_mae, df_repo = correr_paso2(paths)

        path_maestro = DIR_EXPORT / f"MAESTRO_CONSUMO_ENVIO_{nombre_mes}.xlsx"
        with pd.ExcelWriter(path_maestro, engine="openpyxl") as w:
            df_repo.to_excel(w, sheet_name="MaestroStock", index=False)

        path_consumo = DIR_EXPORT / f"CONSUMO_{nombre_mes}.xlsx"
        with pd.ExcelWriter(path_consumo, engine="openpyxl") as w:
            consumo_mensual_df(df_tiv).to_excel(w, sheet_name=HOJA_CONSUMO_MES[etiqueta], index=False)

        stock_ant = stock_final(df_mae)
        print(f"{etiqueta} ({nombre_mes}): libro={libro.name}  "
              f"-> {path_maestro.name}, {path_consumo.name}")

    # Guarda tambien el stock final de M-1, que es el que necesita el mes
    # ACTUAL como stock de partida (test_comparacion_version_anterior.py lo
    # lee directamente de MAESTRO_CONSUMO_ENVIO_JUNIO_2026.xlsx, no hace
    # falta un archivo aparte).
    print("\nListo. Datos historicos (M-3, M-2, M-1) generados en:")
    print(f"  {DIR_EXPORT}")
    print("test_comparacion_version_anterior.py ya puede reusarlos sin reprocesar.")


if __name__ == "__main__":
    main()
