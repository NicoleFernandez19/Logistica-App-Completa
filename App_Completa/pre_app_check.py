import importlib
import os
import subprocess
import sys
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
REQ_FILE = APP_DIR / "requirements.txt"
MIN_PYTHON = (3, 9)

REQUIRED_MODULES = {
    "customtkinter": "customtkinter",
    "pandas": "pandas",
    "numpy": "numpy",
    "openpyxl": "openpyxl",
    "xlrd": "xlrd",
    "tkinterdnd2": "tkinterdnd2",
}


def info(message):
    print(f"[INFO] {message}")


def ok(message):
    print(f"[OK]   {message}")


def warn(message):
    print(f"[WARN] {message}")


def fail(message):
    print(f"[ERROR] {message}")


def run_command(args):
    return subprocess.run(args, cwd=str(APP_DIR), check=False)


def check_python():
    version = sys.version_info[:3]
    info(f"Python detectado: {version[0]}.{version[1]}.{version[2]}")
    if version < MIN_PYTHON:
        fail(
            "La app requiere Python "
            f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]} o superior."
        )
        return False
    ok("Version de Python compatible")
    return True


def check_pip():
    result = run_command([sys.executable, "-m", "pip", "--version"])
    if result.returncode == 0:
        ok("pip disponible")
        return True

    warn("pip no esta disponible. Intentando habilitarlo con ensurepip...")
    result = run_command([sys.executable, "-m", "ensurepip", "--upgrade"])
    if result.returncode != 0:
        fail("No se pudo habilitar pip automaticamente.")
        return False

    result = run_command([sys.executable, "-m", "pip", "--version"])
    if result.returncode == 0:
        ok("pip disponible")
        return True

    fail("pip sigue sin estar disponible.")
    return False


def module_available(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def missing_modules():
    return [
        package
        for package, module_name in REQUIRED_MODULES.items()
        if not module_available(module_name)
    ]


def install_requirements():
    if not REQ_FILE.exists():
        fail(f"No se encontro requirements.txt en {REQ_FILE}")
        return False

    info("Instalando dependencias desde requirements.txt...")
    result = run_command(
        [sys.executable, "-m", "pip", "install", "-r", str(REQ_FILE)]
    )
    if result.returncode != 0:
        fail("La instalacion de dependencias fallo.")
        return False
    ok("Dependencias instaladas")
    return True


def check_dependencies():
    missing = missing_modules()
    if not missing:
        ok("Dependencias Python disponibles")
        return True

    warn("Faltan dependencias: " + ", ".join(missing))
    if not install_requirements():
        return False

    missing_after = missing_modules()
    if missing_after:
        fail(
            "Luego de instalar, siguen faltando: "
            + ", ".join(missing_after)
        )
        return False

    ok("Dependencias Python disponibles")
    return True


def check_tkinter():
    try:
        import tkinter  # noqa: F401
    except ImportError as exc:
        fail(f"tkinter no esta usable: {exc}")
        fail("Instale una distribucion normal de Python para Windows con Tcl/Tk.")
        return False
    ok("tkinter disponible")
    return True


def check_app_import():
    if str(APP_DIR) not in sys.path:
        sys.path.insert(0, str(APP_DIR))

    try:
        importlib.import_module("app.ui.ventana_principal")
    except Exception as exc:
        fail(f"No se pudo importar la app principal: {exc}")
        return False

    ok("App_Completa importable")
    return True


def ensure_runtime_dirs():
    for folder in ["Data", "Maestro_Consumo", "Data_OLD"]:
        path = APP_DIR / folder
        path.mkdir(exist_ok=True)
        ok(f"Carpeta lista: {folder}")


def main():
    print("")
    print("==============================================")
    print(" Pre-app: verificacion de App_Completa")
    print("==============================================")
    print("")

    checks = [
        check_python,
        check_pip,
        check_dependencies,
        check_tkinter,
        check_app_import,
    ]

    for check in checks:
        if not check():
            print("")
            fail("La verificacion no pudo completarse.")
            return 1
        print("")

    ensure_runtime_dirs()

    print("")
    ok("Todo listo. Se puede ejecutar App_Completa.")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    raise SystemExit(main())
