import os
import pandas as pd


def validar_rutas(rutas):
    missing = [k for k, path in rutas.items() if not path or not os.path.exists(path)]
    if missing:
        return False, f"Faltan archivos o rutas inválidas: {', '.join(missing)}"
    return True, "Rutas válidas"


def leer_archivo(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path, dtype=str, encoding="utf-8-sig")


def cargar_consumo(path):
    return leer_archivo(path)


def cargar_agentes(path):
    return leer_archivo(path)
