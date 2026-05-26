"""
Genera los archivos Excel de prueba para el Asistente de Reposición.
Cubre todos los escenarios de cálculo:

  10001  Canal Propio  · Pendiente POSITIVA       (ROLLO 10→13→16, slope=+3)
  10002  Canal Propio  · MENDOZA · Pendiente pos  (ROLLO  8→10→12, slope=+2)
  10003  Pendiente NEGATIVA                        (ROLLO 18→14→10, slope=−4) → usa promedio
  10004  Tipo 2 → ignorado en output por metodo
  10005  Tipo 3 → ignorado en output por metodo
  10006  Tipo 4 + MENDOZA → SKU MZA en output
  10007  Tipo 5
  10008  DEP=1 → BOLSA RECOLECCION=0 en output (promedio_ajustado_dep)
  10009  DEP=1 · Pendiente positiva → BOLSA=0, ROLLO sí se envía
  10010  STOCK ROLLO muy alto → reseteo elimina por completo el pedido
  10011  SUBE y PRISMA con pendiente POSITIVA activa
  10012  MENDOZA sin canal propio → aparece SKU MZA en output
  10013  Consumo CERO → no aparece en el archivo final
  10014  Pendiente CERO (consumo estable) → usa promedio de 3 meses
  10015  SUBSEGMENTACION=3.0 → pedido proporcionalmente mayor

Ejecutar desde la raíz del proyecto:
    python Data_Test/generar_datos_prueba.py
"""
import os
import pandas as pd
from pathlib import Path

BASE_DIR   = Path(os.path.dirname(os.path.abspath(__file__)))
APP_DIR    = BASE_DIR.parent          # App_Completa/
MC_DIR     = APP_DIR / "Maestro_Consumo"   # donde viven los maestros históricos
DATA_DIR   = APP_DIR / "Data"         # archivos del Paso 1

MC_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

IDS = [10001, 10002, 10003, 10004, 10005,
       10006, 10007, 10008, 10009, 10010,
       10011, 10012, 10013, 10014, 10015]

NOMBRES = [
    "C.S. FARMACIA NORTE",    # 10001: Canal Propio + pendiente positiva
    "C.S. AGENTE MENDOZA",    # 10002: Canal Propio + MENDOZA
    "SUPER CORDOBA",          # 10003: Pendiente negativa → promedio
    "AGENTE TIPO 2",          # 10004
    "AGENTE TIPO 3",          # 10005
    "AGENTE TIPO 4 MZA",      # 10006: Tipo 4 + MENDOZA
    "AGENTE TIPO 5",          # 10007
    "DEPOSITO BUENOS AIRES",  # 10008: DEP=1 → sin bolsas
    "DEPOSITO CORDOBA",       # 10009: DEP=1 + pendiente positiva
    "ALTO STOCK ROLLOS",      # 10010: Reseteo elimina el pedido de rollos
    "SUBE Y PRISMA ACTIVOS",  # 10011: SUBE y PRISMA con pendiente positiva
    "AGENTE MENDOZA NORMAL",  # 10012: MENDOZA sin canal propio
    "CONSUMO CERO",           # 10013: Sin consumo → no aparece en output
    "PENDIENTE CERO",         # 10014: Consumo estable → promedio
    "ALTA SUBSEG",            # 10015: SUBSEGMENTACION=3.0
]

TIPOS = [1, 1, 1, 2, 3, 4, 5, 1, 1, 1, 1, 1, 1, 1, 1]
FLAGS = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

PROV = [
    "BUENOS AIRES",  # 10001
    "MENDOZA",       # 10002
    "CORDOBA",       # 10003
    "TUCUMAN",       # 10004
    "SALTA",         # 10005
    "MENDOZA",       # 10006
    "ROSARIO",       # 10007
    "BUENOS AIRES",  # 10008
    "CORDOBA",       # 10009
    "BUENOS AIRES",  # 10010
    "BUENOS AIRES",  # 10011
    "MENDOZA",       # 10012
    "CORDOBA",       # 10013
    "TUCUMAN",       # 10014
    "ROSARIO",       # 10015
]

DEP            = [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0]
SEGMENTO       = ["A","A","B","C","A","B","A","C","B","A","A","B","C","B","A"]
SUBSEG         = [1.5, 1.0, 2.0, 1.0, 1.0, 1.5, 1.0, 2.0, 1.5, 1.0, 1.5, 2.0, 1.0, 1.5, 3.0]

# Stock de partida (para el maestro de mayo, es el stock inicial del mes)
STOCK_ROLLO    = [5,   3,  12,   4,   2,   8,   2,   6,   4, 200,   8,   5,   0,   8,   2]
STOCK_SUBE     = [0,   0,   2,   0,   0,   0,   0,   0,   0,   0,   2,   1,   0,   0,   0]
STOCK_PRISMA   = [2,   1,   4,   0,   0,   2,   0,   2,   0,   0,   3,   2,   0,   2,   0]

# Consumo mensual por producto (mes más antiguo = m1, más reciente = m3)
#                               1    2    3    4    5    6    7    8    9   10   11   12   13   14   15
CONSUMO = {
    "FEBRERO": {   # m3 (M-3, el más antiguo)
        "ROLLO":             [10,   8,  18,   6,   4,  15,   3,   8,   5,   5,  10,   9,   0,  10,   5],
        "BOLSA RECOLECCION": [ 4,   3,   6,   4,   5,   5,   3,   5,   4,   3,   4,   4,   0,   5,   3],
        "ROLLO PRISMA":      [ 1,   1,   2,   0,   0,   1,   0,   1,   0,   0,   3,   2,   0,   1,   0],
        "ROLLO SUBE":        [ 0,   0,   1,   0,   0,   0,   0,   0,   0,   0,   4,   1,   0,   0,   0],
    },
    "MARZO": {     # m2
        "ROLLO":             [13,  10,  14,   6,   6,  12,   5,   8,   8,   5,  10,  11,   0,  10,   5],
        "BOLSA RECOLECCION": [ 5,   4,   7,   4,   5,   6,   4,   5,   5,   3,   5,   5,   0,   5,   4],
        "ROLLO PRISMA":      [ 1,   1,   2,   0,   0,   1,   0,   1,   0,   0,   4,   3,   0,   1,   0],
        "ROLLO SUBE":        [ 0,   0,   1,   0,   0,   0,   0,   0,   0,   0,   5,   1,   0,   0,   0],
    },
    "ABRIL": {     # m1 (M-1, el más reciente)
        "ROLLO":             [16,  12,  10,   6,   8,   9,   7,   8,  11,   5,  10,  13,   0,  10,   5],
        "BOLSA RECOLECCION": [ 6,   5,   8,   4,   5,   7,   5,   5,   6,   3,   6,   6,   0,   5,   5],
        "ROLLO PRISMA":      [ 2,   1,   2,   0,   0,   1,   0,   1,   0,   0,   5,   4,   0,   1,   0],
        "ROLLO SUBE":        [ 0,   0,   1,   0,   0,   0,   0,   0,   0,   0,   6,   2,   0,   0,   0],
    },
}

ANIO = 2026


def _maestro_df(mes_nombre, consumo_mes):
    """Arma un DataFrame con formato MaestroStock completo (stock + consumo)."""
    d = {
        "ID P.F":          IDS,
        "NOMBRE FANTASIA": NOMBRES,
        "PROV":            PROV,
        "DEP":             DEP,
        "SEGMENTO":        SEGMENTO,
        "SUBSEGMENTACION": SUBSEG,
        "STOCK ROLLO":     STOCK_ROLLO,
        "STOCK SUBE":      STOCK_SUBE,
        "STOCK PRISMA":    STOCK_PRISMA,
        "TIPO":            TIPOS,
        "FLAG_DSP_KYC":    FLAGS,
    }
    for col, vals in consumo_mes.items():
        d[col] = vals
    return pd.DataFrame(d)


def main():
    print("Generando archivos de prueba...")
    print()

    # ── Archivos históricos en Maestro_Consumo/ ───────────────────────────────
    # Cada archivo tiene el formato MaestroStock completo (stock + consumo del mes).
    # Son los mismos que genera paso2 en una ejecución real.
    for mes_nombre, consumo_data in CONSUMO.items():
        df = _maestro_df(mes_nombre, consumo_data)
        filename = f"MAESTRO_CONSUMO_ENVIO_{mes_nombre}_{ANIO}.xlsx"
        path = MC_DIR / filename
        df.to_excel(path, index=False)
        print(f"  OK  Maestro_Consumo/{filename}  ({len(df)} agentes)")

    # ── Maestro bootstrap de Mayo (stock de partida para el mes actual) ───────
    # Simula el que genera paso2; mismo formato que los meses anteriores.
    # Solo se escribe si no existe (paso2 lo genera con datos reales).
    mayo_path = MC_DIR / f"MAESTRO_CONSUMO_ENVIO_MAYO_{ANIO}.xlsx"
    if not mayo_path.exists():
        df_mayo = _maestro_df("MAYO", CONSUMO["ABRIL"])  # usa consumo de abril como placeholder
        df_mayo.to_excel(mayo_path, index=False)
        print(f"  OK  Maestro_Consumo/MAESTRO_CONSUMO_ENVIO_MAYO_{ANIO}.xlsx  ({len(df_mayo)} agentes, generado)")
    else:
        print(f"  --  Maestro_Consumo/MAESTRO_CONSUMO_ENVIO_MAYO_{ANIO}.xlsx  (ya existe, conservado)")

    # ── Eliminar archivos CONSUMO_*.xlsx obsoletos de Maestro_Consumo/ ───────
    for p in MC_DIR.glob("CONSUMO_*.xlsx"):
        p.unlink()
        print(f"  DEL {p.name}  (reemplazado por MAESTRO_CONSUMO_ENVIO_*)")

    # ── Agentes Canal Propio → Data/ ─────────────────────────────────────────
    df_agentes = pd.DataFrame({"ID P.F": [10001, 10002]})
    ag_path = DATA_DIR / "Agentes.xlsx"
    df_agentes.to_excel(ag_path, index=False)
    print(f"  OK  Data/Agentes.xlsx  (agentes canal propio: 10001, 10002)")

    print()
    print("-" * 64)
    print("Resultados esperados en el output (referencia de validacion):")
    print("-" * 64)
    print("  10001  ROLLOS: regresion mes 4, luego -18% (canal propio)")
    print("  10002  ROLLOS: SKU 9001222101 (MZA) + -18% (canal propio)")
    print("  10003  ROLLOS: usa promedio (pendiente negativa)")
    print("  10008  BOLSAS: 0 en output (DEP=1)")
    print("  10009  BOLSAS: 0 en output (DEP=1), ROLLOS si se calculan")
    print("  10010  ROLLOS: 0 en output (stock 200 absorbe el pedido)")
    print("  10011  SUBE y PRISMA: aparecen en output con cantidades > 0")
    print("  10012  ROLLOS: SKU 9001222101 (Mendoza)")
    print("  10013  No aparece en el output final (todo consumo = 0)")
    print("  10014  ROLLOS: usa promedio (pendiente = 0)")
    print("  10015  Cantidades ~2x las de un agente con SUBSEG=1.5 similar")
    print("-" * 64)
    print()
    print("Archivos de prueba generados correctamente.")
    print(f"  Maestro_Consumo/ -> {len(CONSUMO)+1} archivos MAESTRO_CONSUMO_ENVIO_*")
    print(f"  Data/            -> Agentes.xlsx")


if __name__ == "__main__":
    main()
