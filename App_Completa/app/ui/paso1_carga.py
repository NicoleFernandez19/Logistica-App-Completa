import re
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk
from .estilos import (AMARILLO, AMARILLO_DARK, NEGRO, BLANCO, GRIS_BG,
                      GRIS_TEXTO, GRIS_BORDE, VERDE, INFO_BG, INFO_BORDE,
                      APPLE_FILL, APPLE_HOVER)

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
    "trx_sube":     ["trx_sube", "trx sube", "trxsube"],   # antes de "sube"
    "sube":         ["sube"],
    "rollo_env":    ["rollo_env", "rollos_env", "rollo env", "rollos", "rollo"],
    "resma_env":    ["resma_env", "resma", "resmas"],
    "fajas":        ["fajas"],
}
_EXTS = {".csv", ".xlsx", ".xls"}
_MESES_P1 = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


class Paso1Carga(ctk.CTkFrame):
    """Paso 1: Selección de 11 archivos de entrada para el cálculo de consumo."""

    def __init__(self, parent, on_change):
        super().__init__(parent, fg_color=GRIS_BG, corner_radius=0)
        self._on_change = on_change
        self._paths = {}
        self._vars  = {}
        self._lbls  = {}
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

        status = ctk.CTkFrame(bar, fg_color="transparent")
        status.pack(side="left", padx=(0, 18))

        ctk.CTkLabel(status, text="archivos listos:",
                     font=("Segoe UI", 12), text_color=GRIS_TEXTO).pack(side="left")

        self._lbl_counter = ctk.CTkLabel(
            status, text="0 / 11",
            font=("Segoe UI", 14, "bold"),
            text_color=GRIS_TEXTO)
        self._lbl_counter.pack(side="left", padx=(8, 0))

        actions = ctk.CTkFrame(bar, fg_color="transparent")
        actions.pack(side="left")

        ctk.CTkButton(actions, text="Examinar",
                      fg_color=APPLE_FILL, hover_color=GRIS_BORDE,
                      text_color=NEGRO, font=("Segoe UI", 12),
                      border_width=1, border_color=GRIS_BORDE,
                      width=120, height=40, corner_radius=6,
                      command=self._examinar_archivos).pack(side="left", padx=(0, 8))

        ctk.CTkButton(actions, text="⟳  Auto-detectar",
                      fg_color=AMARILLO, hover_color=AMARILLO_DARK,
                      text_color="#FFFFFF", font=("Segoe UI", 12, "bold"),
                      width=170, height=40, corner_radius=6,
                      command=self._autodetectar).pack(side="left")

        # ── Grid de archivos ─────────────────────────────────────────────────
        guide = ctk.CTkFrame(self, fg_color=INFO_BG, height=44, corner_radius=0)
        guide.pack(fill="x")
        guide.pack_propagate(False)
        ctk.CTkLabel(
            guide,
            text="ℹ  TIV aporta el consumo del mes · Maestro define el stock inicial · Envíos y flags ajustan el stock final.",
            font=("Segoe UI", 11), text_color=GRIS_TEXTO,
        ).pack(side="left", padx=20)

        scroll = ctk.CTkScrollableFrame(self, fg_color=GRIS_BG, corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=16, pady=12)
        scroll.columnconfigure(0, weight=1, uniform="c")
        scroll.columnconfigure(1, weight=1, uniform="c")

        for idx, (key, label, desc) in enumerate(_ARCHIVOS):
            self._fila(scroll, key, label, desc, row=idx // 2, col=idx % 2)

    def _fila(self, parent, key, label, desc, row, col):
        cell = ctk.CTkFrame(parent, fg_color=BLANCO, corner_radius=8,
                            border_width=1, border_color=GRIS_BORDE)
        cell.grid(row=row, column=col, sticky="ew", padx=8, pady=6)

        top = ctk.CTkFrame(cell, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 4))

        ctk.CTkLabel(top, text=label, font=("Segoe UI", 12, "bold"),
                     text_color=NEGRO).pack(anchor="w")
        ctk.CTkLabel(top, text=desc, font=("Segoe UI", 10),
                     text_color=GRIS_TEXTO, wraplength=440,
                     justify="left").pack(anchor="w", pady=(2, 0))

        inp = ctk.CTkFrame(cell, fg_color="transparent")
        inp.pack(fill="x", padx=14, pady=(0, 12))

        var = tk.StringVar(value="Sin archivo")
        self._vars[key] = var

        lbl = ctk.CTkLabel(inp, textvariable=var,
                            fg_color=APPLE_FILL, corner_radius=6,
                            font=("Segoe UI", 11), text_color=GRIS_TEXTO,
                            anchor="w", height=38)
        lbl.pack(side="left", fill="x", expand=True)
        self._lbls[key] = lbl

        btn = ctk.CTkButton(inp, text="...", width=36, height=38,
                            fg_color=APPLE_FILL, hover_color=APPLE_HOVER,
                            text_color=NEGRO, border_width=1, border_color=GRIS_BORDE,
                            corner_radius=6,
                            command=lambda k=key: self._examinar_individual(k))
        btn.pack(side="right", padx=(8, 0))

    # ── Auto-detección ────────────────────────────────────────────────────────

    @staticmethod
    def _parsear_fecha(path):
        """Devuelve (año, mes) del nombre de archivo. (0,0) si no parsea."""
        stem = path.stem.lower()
        m = re.search(r"(?<!\d)(20\d{2})(?!\d)", stem)
        anio = int(m.group(1)) if m else 0
        # Texto en español
        for nombre, numero in _MESES_P1.items():
            if nombre in stem:
                return (anio, numero)
        # Numérico: quitar año para no confundirlo con mes
        stem_limpio = re.sub(r"20\d{2}", "", stem)
        m2 = re.search(r"(?<!\d)(\d{1,2})(?!\d)", stem_limpio)
        if m2:
            n = int(m2.group(1))
            if 1 <= n <= 12:
                return (anio, n)
        return (anio, 0)

    def _maestro_mes_anterior(self):
        """Busca en Maestro_Consumo/ el archivo del mes actual (convencion: el
        archivo se llama con el mes para el que se usa, eg. MAYO_2026 = stock
        inicial de Mayo). Acepta solo archivos cuyo nombre contiene 'maestro'."""
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
        # Prioridad 1: match exacto por fecha en el nombre
        for mes, anio in [(now.month, now.year),
                          (now.month - 1 or 12,
                           now.year if now.month > 1 else now.year - 1)]:
            for p in candidatos:
                if self._parsear_fecha(p) == (anio, mes):
                    return p
        # Prioridad 2: si no hay fecha en el nombre, el más reciente por fecha de modificación
        return max(candidatos, key=lambda p: p.stat().st_mtime)

    def _autodetectar(self):
        base = Path(sys.argv[0]).resolve().parent
        data_dir = base / "Data"
        data_dir.mkdir(exist_ok=True)

        # Maestro Consumo: siempre desde Maestro_Consumo/ (mes anterior)
        if "maestro" not in self._paths:
            p_mae = self._maestro_mes_anterior()
            if p_mae:
                self._set_path("maestro", str(p_mae), p_mae.name, auto=True)

        # Resto de archivos: Data/ primero, luego raíz
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

        # Pool mutable: cada archivo se asigna a un solo slot
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

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _examinar_archivos(self):
        base = Path(sys.argv[0]).resolve().parent
        data_dir = base / "Data"
        data_dir.mkdir(exist_ok=True)
        paths = filedialog.askopenfilenames(
            title="Seleccionar archivos de consumo",
            filetypes=[("CSV / Excel", "*.csv *.xlsx *.xls"), ("Todos", "*.*")],
            initialdir=str(data_dir),
        )
        if not paths:
            return

        pool = {Path(p).stem.lower(): Path(p) for p in paths}
        for key, nombres in _AUTO_NOMBRES.items():
            match = None
            for nombre in nombres:
                match = next(
                    (p for stem, p in pool.items() if nombre in stem),
                    None,
                )
                if match:
                    break
            if match:
                self._set_path(key, str(match), match.name, auto=False)
                pool = {s: p for s, p in pool.items() if p != match}

        self._actualizar_counter()

    def _examinar_individual(self, key):
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
        self._set_path(key, str(p), p.name, auto=False)
        self._actualizar_counter()

    def _set_path(self, key, path, nombre, auto):
        self._paths[key] = path
        self._vars[key].set(f"  {nombre}")
        color = VERDE if auto else NEGRO
        self._lbls[key].configure(text_color=color)

    def _actualizar_counter(self):
        n = len(self._paths)
        total = len(_ARCHIVOS)
        color = VERDE if n == total else (NEGRO if n > 0 else GRIS_TEXTO)
        self._lbl_counter.configure(
            text=f"{n} / {total}", text_color=color)
        self._on_change(n)

