import re
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk
from .estilos import (AMARILLO, AMARILLO_DARK, NEGRO, BLANCO, GRIS_BG,
                      GRIS_TEXTO, GRIS_BORDE, VERDE, INFO_BG,
                      APPLE_FILL, APPLE_HOVER, APPLE_SELECTED)
from .componentes import esta_en_carpeta
from ..config import MESES_A_NUMERO as _MESES_P1

_ARCHIVOS = [
    ("tiv",          "TIV",             "Transacciones del mes por agente"),
    ("maestro",      "MAESTRO CONSUMO", "Stock inicial  (MaestroStock mes anterior)"),
    ("fac_termicas", "FAC. TERMICAS",   "Agentes con factura térmica"),
    ("dsp_kyc",      "DSP / KYC",       "Flags de habilitación normativa"),
    ("com_tx_int",   "COM TX INT",      "Agentes con TX internacionales"),
    ("prisma",       "PRISMA",          "Envíos rollos Prisma"),
    ("sube",         "SUBE",            "Envíos rollos SUBE"),
    ("rollo_env",    "ROLLO (envíos)",  "Envíos rollos térmicos"),
    ("trx_sube",     "TRX SUBE",        "Transacciones SUBE"),
    ("resma_env",    "RESMA (envíos)",  "Envíos de resmas del mes"),
    ("fajas",        "FAJAS",           "Cantidad de fajas por agente"),
]

_AUTO_NOMBRES = {
    "tiv":          ["tiv_final", "tiv final", "tiv"],
    "maestro":      ["maestro_consumo_envio", "maestro consumo envio",
                     "maestro_consumo_envios", "maestro_consumo", "maestro consumo",
                     "maestro"],
    "fac_termicas": ["fac_termicas", "fac termicas", "fac-termicas", "factermicas"],
    "dsp_kyc":      ["dsp_kyc", "dsp kyc", "dsp-kyc", "dspkyc", "dsp"],
    "com_tx_int":   ["com_tx_int", "com tx int", "com-tx-int", "comtxint"],
    "prisma":       ["prisma"],
    "trx_sube":     ["trx_sube", "trx sube", "trxsube"],
    "sube":         ["sube"],
    "rollo_env":    ["rollo_env", "rollos_env", "rollo env", "rollos", "rollo"],
    "resma_env":    ["resma_env", "resma", "resmas"],
    "fajas":        ["fajas"],
}
_EXTS = {".csv", ".xlsx", ".xls"}
_LIBRO_STEM = "01_datos_v5"  # prefijo del archivo libro a auto-detectar

_TAB_LIBRO    = "  📋 Carga desde libro XLSX  "
_TAB_MULTIPLE = "  📂 Carga múltiple de archivos  "


class Paso1Carga(ctk.CTkFrame):
    """Paso 1: Selección de 11 archivos de entrada para el cálculo de consumo."""

    def __init__(self, parent, on_change):
        super().__init__(parent, fg_color=GRIS_BG, corner_radius=0)
        self._on_change = on_change
        self._paths = {}
        self._mult_iconos = {}
        self._mult_vars   = {}
        self._mult_lbls   = {}
        self._libro_path  = None
        self._libro_mapeo = {}
        self._libro_ya_autodetectado = False
        self._build()
        self.after(200, self._autodetectar)

    def get_paths(self):
        return dict(self._paths)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Barra superior ──────────────────────────────────────────────────
        bar = ctk.CTkFrame(self, fg_color=BLANCO, height=70, corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        ctk.CTkLabel(bar, text="Archivos de entrada  —  Cálculo de Consumo",
                     font=("Segoe UI", 16, "bold"),
                     text_color=NEGRO).pack(side="left", padx=24)

        # Grupo derecho: contador + separador + botón auto-detectar
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right", padx=16)

        ctk.CTkButton(right, text="⟳  Auto-detectar",
                      fg_color=AMARILLO, hover_color=AMARILLO_DARK,
                      text_color="#FFFFFF", font=("Segoe UI", 12, "bold"),
                      width=170, height=40, corner_radius=6,
                      command=self._autodetectar).pack(side="right", padx=(8, 0))

        sep = ctk.CTkFrame(right, fg_color=GRIS_BORDE, width=1, height=36)
        sep.pack(side="right", padx=12)

        status = ctk.CTkFrame(right, fg_color="transparent")
        status.pack(side="right")
        ctk.CTkLabel(status, text="archivos listos:",
                     font=("Segoe UI", 12), text_color=GRIS_TEXTO).pack(side="left")
        self._lbl_counter = ctk.CTkLabel(
            status, text="0 / 11",
            font=("Segoe UI", 14, "bold"),
            text_color=GRIS_TEXTO)
        self._lbl_counter.pack(side="left", padx=(8, 0))

        # ── Guía informativa ────────────────────────────────────────────────
        guide = ctk.CTkFrame(self, fg_color=INFO_BG, height=44, corner_radius=0)
        guide.pack(fill="x")
        guide.pack_propagate(False)
        ctk.CTkLabel(
            guide,
            text="ℹ  TIV aporta el consumo del mes · Maestro define el stock inicial · Envíos y flags ajustan el stock final.",
            font=("Segoe UI", 11), text_color=GRIS_TEXTO,
        ).pack(side="left", padx=20)

        # ── Tabs de carga ────────────────────────────────────────────────────
        self._carga_tabs = ctk.CTkTabview(
            self,
            fg_color=BLANCO,
            segmented_button_fg_color=GRIS_BG,
            segmented_button_selected_color=APPLE_SELECTED,
            segmented_button_selected_hover_color=APPLE_SELECTED,
            segmented_button_unselected_color=GRIS_BG,
            text_color=NEGRO,
            border_width=1,
            border_color=GRIS_BORDE,
            corner_radius=8,
        )
        self._carga_tabs.pack(fill="both", expand=True, padx=16, pady=(10, 12))
        try:
            self._carga_tabs._segmented_button.configure(font=("Segoe UI", 12))
        except Exception:
            pass

        self._carga_tabs.add(_TAB_LIBRO)
        self._carga_tabs.add(_TAB_MULTIPLE)

        self._build_tab_libro(self._carga_tabs.tab(_TAB_LIBRO))
        self._build_tab_multiple(self._carga_tabs.tab(_TAB_MULTIPLE))


    # ── Tab: Carga desde libro XLSX ───────────────────────────────────────────

    def _build_tab_libro(self, tab):
        # Fila superior: selector de archivo
        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", pady=(4, 8))

        ctk.CTkLabel(top, text="Archivo:",
                     font=("Segoe UI", 11), text_color=GRIS_TEXTO,
                     width=60).pack(side="left")

        sel = ctk.CTkFrame(top, fg_color=APPLE_FILL, corner_radius=6,
                           border_width=1, border_color=GRIS_BORDE)
        sel.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._lbl_libro_archivo = ctk.CTkLabel(
            sel, text="Sin archivo seleccionado",
            font=("Segoe UI", 11), text_color=GRIS_TEXTO, anchor="w")
        self._lbl_libro_archivo.pack(side="left", fill="x", expand=True, padx=10, pady=6)

        ctk.CTkButton(sel, text="...", width=34, height=30,
                      fg_color=APPLE_FILL, hover_color=APPLE_HOVER,
                      text_color=NEGRO, border_width=1, border_color=GRIS_BORDE,
                      corner_radius=6,
                      command=self._libro_seleccionar).pack(side="right", padx=6, pady=4)

        self._btn_libro_aplicar = ctk.CTkButton(
            top, text="Aplicar",
            fg_color=AMARILLO, hover_color=AMARILLO_DARK,
            text_color="#FFFFFF", font=("Segoe UI", 12, "bold"),
            width=110, height=40, corner_radius=6, state="disabled",
            command=self._libro_aplicar)
        self._btn_libro_aplicar.pack(side="right")

        # Preview del mapeo
        self._libro_preview = ctk.CTkScrollableFrame(
            tab, fg_color=GRIS_BG, corner_radius=6,
            border_width=1, border_color=GRIS_BORDE, height=56)
        self._libro_preview.pack(fill="x", pady=(0, 6))
        self._libro_preview.columnconfigure(0, weight=1, uniform="a")
        self._libro_preview.columnconfigure(1, weight=1, uniform="a")
        self._libro_preview.columnconfigure(2, weight=1, uniform="a")

        self._lbl_libro_hint = ctk.CTkLabel(
            self._libro_preview,
            text="Seleccioná un archivo XLSX para ver el mapeo de hojas.",
            font=("Segoe UI", 10), text_color=GRIS_TEXTO)
        self._lbl_libro_hint.grid(row=0, column=0, columnspan=3, padx=12, pady=12)

    def _libro_seleccionar(self):
        import pandas as pd
        base = Path(sys.argv[0]).resolve().parent
        data_dir = base / "Data"
        data_dir.mkdir(exist_ok=True)
        path = filedialog.askopenfilename(
            title="Seleccionar libro XLSX",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Todos", "*.*")],
            initialdir=str(data_dir),
        )
        if not path:
            return
        try:
            xl = pd.ExcelFile(path, engine="openpyxl")
            hojas = xl.sheet_names
        except Exception as exc:
            messagebox.showerror("Error al leer el libro", str(exc))
            return

        p = Path(path)
        self._libro_path = path
        self._lbl_libro_archivo.configure(text=p.name, text_color=NEGRO)

        pool = {h.lower(): h for h in hojas}
        mapeo = {}
        for key, nombres in _AUTO_NOMBRES.items():
            for nombre in nombres:
                match_lower = next((k for k in pool if nombre in k), None)
                if match_lower:
                    mapeo[key] = pool[match_lower]
                    del pool[match_lower]
                    break

        self._libro_mapeo = mapeo
        self._libro_actualizar_preview(hojas)
        self._btn_libro_aplicar.configure(state="normal" if mapeo else "disabled")

    def _libro_actualizar_preview(self, todas_hojas):
        for w in self._libro_preview.winfo_children():
            w.destroy()

        asignadas = set(self._libro_mapeo.values())
        items = []
        for key, label, _ in _ARCHIVOS:
            hoja = self._libro_mapeo.get(key)
            if hoja:
                items.append((VERDE, "✓", f'{label} → "{hoja}"'))
            else:
                items.append((GRIS_TEXTO, "✗", f'{label} → —'))

        # Mostrar en 3 columnas
        for i, (color, icono, texto) in enumerate(items):
            row_f = ctk.CTkFrame(self._libro_preview, fg_color="transparent")
            row_f.grid(row=i // 3, column=i % 3, sticky="ew", padx=6, pady=2)
            ctk.CTkLabel(row_f, text=icono, font=("Segoe UI", 10, "bold"),
                         text_color=color, width=16).pack(side="left")
            ctk.CTkLabel(row_f, text=texto, font=("Segoe UI", 10),
                         text_color=color, anchor="w").pack(side="left", padx=(2, 0))

        sin_asignar = [h for h in todas_hojas if h not in asignadas]
        if sin_asignar:
            r = (len(items) + 2) // 3
            ctk.CTkLabel(self._libro_preview,
                         text="Hojas no utilizadas (no requieren acción): " + ", ".join(sin_asignar),
                         font=("Segoe UI", 9), text_color=GRIS_TEXTO).grid(
                row=r, column=0, columnspan=3, padx=8, pady=(4, 2), sticky="w")

    def _libro_aplicar(self):
        self._libro_asignar(self._libro_path, self._libro_mapeo)

    def _libro_asignar(self, source_path, mapeo):
        """Asigna las hojas a los slots. El archivo se mueve a Data_old recién después del cálculo."""
        self._libro_pendiente_archivar = source_path  # guardado para mover después
        p = Path(source_path)
        for key, hoja in mapeo.items():
            ref = f"{source_path}::{hoja}"
            self._set_path(key, ref, f"{p.name} [{hoja}]", auto=True)
        self._actualizar_counter()

    def archivar_libro(self):
        """Mueve el libro a Data_old/ después de que el cálculo fue exitoso.
        Solo archiva si el libro está dentro de Data/ (la app no debe tocar
        archivos seleccionados desde una carpeta externa del usuario)."""
        path = getattr(self, "_libro_pendiente_archivar", None)
        if not path:
            return
        p = Path(path)
        if not p.exists():
            self._libro_pendiente_archivar = None
            return
        base = Path(sys.argv[0]).resolve().parent
        data_dir = base / "Data"
        if not esta_en_carpeta(p, data_dir):
            self._libro_pendiente_archivar = None
            return
        data_old = base / "Data_old"
        data_old.mkdir(exist_ok=True)
        destino = data_old / p.name
        if destino.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            destino = data_old / f"{p.stem}_{ts}{p.suffix}"
        try:
            p.rename(destino)
        except Exception as exc:
            print(f"  ADVERTENCIA: No se pudo mover {p.name} a Data_old: {exc}")
        self._libro_pendiente_archivar = None

    # ── Tab: Carga múltiple de archivos ───────────────────────────────────────

    def _build_tab_multiple(self, tab):
        """Una fila por slot con icono de estado, nombre y botón de selección."""
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent",
                                        corner_radius=0, height=200)
        scroll.pack(fill="both", expand=True, pady=(4, 0))
        scroll.columnconfigure(0, minsize=28)   # icono ✓/–
        scroll.columnconfigure(1, minsize=185)  # nombre del slot
        scroll.columnconfigure(2, weight=1)     # archivo seleccionado
        scroll.columnconfigure(3, minsize=40)   # botón ...

        self._mult_iconos = {}
        self._mult_vars   = {}
        self._mult_lbls   = {}

        for i, (key, label, _) in enumerate(_ARCHIVOS):
            # Fondo alternado compatible con dark/light
            bg = GRIS_BG if i % 2 == 0 else APPLE_FILL

            icono = ctk.CTkLabel(scroll, text="–",
                                 fg_color=bg,
                                 font=("Segoe UI", 11, "bold"),
                                 text_color=GRIS_TEXTO, width=28)
            icono.grid(row=i, column=0, sticky="nsew", padx=(4, 0), pady=1)
            self._mult_iconos[key] = icono

            ctk.CTkLabel(scroll, text=label,
                         fg_color=bg,
                         font=("Segoe UI", 11, "bold"),
                         text_color=NEGRO, anchor="w").grid(
                row=i, column=1, sticky="nsew", padx=(4, 8), pady=1)

            var = tk.StringVar(value="Sin archivo")
            self._mult_vars[key] = var

            lbl = ctk.CTkLabel(scroll, textvariable=var,
                               fg_color=bg, corner_radius=0,
                               font=("Segoe UI", 10), text_color=GRIS_TEXTO,
                               anchor="w", height=30)
            lbl.grid(row=i, column=2, sticky="nsew", padx=(0, 4), pady=1)
            self._mult_lbls[key] = lbl

            ctk.CTkButton(scroll, text="...", width=36, height=28,
                          fg_color=APPLE_FILL, hover_color=APPLE_HOVER,
                          text_color=NEGRO, border_width=1, border_color=GRIS_BORDE,
                          corner_radius=6,
                          command=lambda k=key: self._mult_examinar(k)).grid(
                row=i, column=3, pady=1, padx=(0, 4))

    def _mult_examinar(self, key):
        base = Path(sys.argv[0]).resolve().parent
        data_dir = base / "Data"
        data_dir.mkdir(exist_ok=True)
        path = filedialog.askopenfilename(
            title=f"Seleccionar archivo para {key.upper()}",
            filetypes=[("CSV / Excel", "*.csv *.xlsx *.xls"), ("Todos", "*.*")],
            initialdir=str(data_dir),
        )
        if not path:
            return
        p = Path(path)
        # Validación visual directamente en la fila del tab
        self._mult_iconos[key].configure(text="✓", text_color=VERDE)
        self._mult_vars[key].set(f"  {p.name}")
        self._mult_lbls[key].configure(text_color=VERDE)
        self._set_path(key, str(p), p.name, auto=False)
        self._actualizar_counter()


    # ── Auto-detección ────────────────────────────────────────────────────────

    @staticmethod
    def _parsear_fecha(path):
        stem = path.stem.lower()
        m = re.search(r"(?<!\d)(20\d{2})(?!\d)", stem)
        anio = int(m.group(1)) if m else 0
        for nombre, numero in _MESES_P1.items():
            if nombre in stem:
                return (anio, numero)
        stem_limpio = re.sub(r"20\d{2}", "", stem)
        m2 = re.search(r"(?<!\d)(\d{1,2})(?!\d)", stem_limpio)
        if m2:
            n = int(m2.group(1))
            if 1 <= n <= 12:
                return (anio, n)
        return (anio, 0)

    def _maestro_mes_anterior(self):
        base = Path(sys.argv[0]).resolve().parent
        carpeta_mc = base / "Maestro_Consumo"
        if not carpeta_mc.exists():
            return None
        candidatos = [
            p for p in carpeta_mc.iterdir()
            if p.is_file() and p.suffix.lower() in _EXTS and "maestro" in p.stem.lower()
        ]
        if not candidatos:
            return None
        now = datetime.now()
        for mes, anio in [(now.month, now.year),
                          (now.month - 1 or 12,
                           now.year if now.month > 1 else now.year - 1)]:
            for p in candidatos:
                if self._parsear_fecha(p) == (anio, mes):
                    return p
        return max(candidatos, key=lambda p: p.stat().st_mtime)

    def _autodetectar(self):
        base = Path(sys.argv[0]).resolve().parent
        data_dir = base / "Data"
        data_dir.mkdir(exist_ok=True)

        # Maestro Consumo
        if "maestro" not in self._paths:
            p_mae = self._maestro_mes_anterior()
            if p_mae:
                self._set_path("maestro", str(p_mae), p_mae.name, auto=True)

        # Libro XLSX (01_DATOS_v5): detectar y aplicar directamente
        if not self._libro_ya_autodetectado:
            try:
                for p in data_dir.iterdir():
                    if p.is_file() and p.suffix.lower() in {".xlsx", ".xls"} \
                            and _LIBRO_STEM in p.stem.lower():
                        self._libro_autodetectar(p)
                        break
            except Exception:
                pass

        # Archivos individuales desde Data/ y raíz
        carpetas = [data_dir, base]
        disponibles = {}
        for carpeta in carpetas:
            try:
                for p in carpeta.iterdir():
                    if p.is_file() and p.suffix.lower() in _EXTS:
                        stem = p.stem.lower()
                        if stem not in disponibles:
                            disponibles[stem] = p
            except Exception:
                pass

        pool = dict(disponibles)
        for key, nombres in _AUTO_NOMBRES.items():
            if key == "maestro" or key in self._paths:
                continue
            match = None
            for nombre in nombres:
                match = next(
                    (p for stem, p in pool.items() if nombre in stem),
                    None,
                )
                if match:
                    break
            if match:
                self._set_path(key, str(match), match.name, auto=True)
                pool = {s: p for s, p in pool.items() if p != match}

        self._actualizar_counter()

    def _libro_autodetectar(self, p):
        """Carga y aplica automáticamente el libro XLSX, luego lo mueve a Data_old."""
        import pandas as pd
        try:
            xl = pd.ExcelFile(str(p), engine="openpyxl")
            hojas = xl.sheet_names
        except Exception:
            return

        pool = {h.lower(): h for h in hojas}
        mapeo = {}
        for key, nombres in _AUTO_NOMBRES.items():
            for nombre in nombres:
                match_lower = next((k for k in pool if nombre in k), None)
                if match_lower:
                    mapeo[key] = pool[match_lower]
                    del pool[match_lower]
                    break

        if not mapeo:
            return

        self._libro_ya_autodetectado = True
        self._libro_path  = str(p)
        self._libro_mapeo = mapeo

        # Actualizar UI del tab
        self._lbl_libro_archivo.configure(text=p.name, text_color=VERDE)
        self._libro_actualizar_preview(hojas)
        self._btn_libro_aplicar.configure(state="normal")

        self._libro_asignar(str(p), mapeo)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_path(self, key, path, nombre, auto):
        self._paths[key] = path
        color = VERDE if auto else NEGRO
        if key in self._mult_iconos:
            self._mult_iconos[key].configure(text="✓", text_color=color)
            self._mult_vars[key].set(f"  {nombre}")
            self._mult_lbls[key].configure(text_color=color)

    def _actualizar_counter(self):
        n = len(self._paths)
        total = len(_ARCHIVOS)
        color = VERDE if n == total else (NEGRO if n > 0 else GRIS_TEXTO)
        self._lbl_counter.configure(
            text=f"{n} / {total}", text_color=color)
        self._on_change(n)
