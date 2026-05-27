import sys
import os

# Asegurar que el directorio de la app esté en el path
_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

# Auto-instalar dependencias si faltan
_DEPS = ["customtkinter", "pandas", "openpyxl", "numpy", "xlrd"]
_missing = []
for dep in _DEPS:
    try:
        __import__(dep)
    except ImportError:
        _missing.append(dep)

if _missing:
    import subprocess
    print(f"Instalando dependencias faltantes: {', '.join(_missing)}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + _missing)
    except subprocess.CalledProcessError:
        print(
            "Error al instalar dependencias. Ejecute manualmente:\n"
            f"  pip install {' '.join(_missing)}"
        )
        sys.exit(1)
    print("Dependencias instaladas. Reiniciando...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

from app.ui.ventana_principal import VentanaPrincipal

if __name__ == "__main__":
    app = VentanaPrincipal()
    app.mainloop()
