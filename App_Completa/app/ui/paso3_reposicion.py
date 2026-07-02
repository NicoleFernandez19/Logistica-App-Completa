import re
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from .componentes import TablaWidget, mostrar_dialogo, confirmar
from .estilos import (AMARILLO, AMARILLO_DARK, NEGRO, BLANCO, GRIS_BG,
                      GRIS_TEXTO, GRIS_BORDE, VERDE, INFO_BG, INFO_BORDE,
                      APPLE_FILL, APPLE_HOVER, APPLE_SELECTED)
from ..config import PARAMETROS, PRODUCTOS, MESES_A_NUMERO as _MESES
from ..logic.cargador import cargar_consumo_mes


_ARCHIVOS_REPO = [
    ("maestro_actual", "Maestro Stock Actual",
     "Stock de partida. Sin archivo, usa el del Paso 2."),
    ("consumo_mes_1", "Consumo M-3", "MaestroStock de hace 3 meses"),
    ("consumo_mes_2", "Consumo M-2", "MaestroStock de hace 2 meses"),
    ("consumo_mes_3", "Consumo M-1", "MaestroStock del mes anterior"),
    ("agentes", "Agentes Canal", "Listado de agentes Canal Propio"),
]

_EXTS = {".csv", ".xlsx", ".xls"}

_PRODUCT_COLS = ["Base", "Repo", "Método", "SKU", "Descripción"]


class Paso3Reposicion(ctk.CTkFrame):
    """Paso 3: archivos historicos, parametros y productos de reposicion."""

    def __init__(self, parent, get_maestro, on_change):
        super().__init__(parent, fg_color=GRIS_BG, corner_radius=0)
        self._get_maestro = get_maestro
        self._on_change = on_change
        self._paths = {}
        self._vars = {}
        self._lbls = {}
        self._param_vars = {}
        self._productos = [p.copy() for p in PRODUCTOS]
        self._search_var = tk.StringVar()
        self._build()
        self.after(300, self._autodetectar)

    def get_paths(self):
        paths = dict(self._paths)
        if "maestro_actual" not in paths and self._get_maestro() is not None:
            paths["maestro_actual"] = "__GENERADO_PASO_2__"
        return paths

    def get_maestro_actual(self):
        path = self._paths.get("maestro_actual")
        if path:
            return cargar_consumo_mes(path)
        return self._get_maestro()

    def get_params(self):
        params = dict(PARAMETROS)
        for key, var in self._param_vars.items():
            try:
                params[key] = float(var.get())
            except ValueError:
                pass
        return params

    def get_productos(self):
        return [p.copy() for p in self._productos]

    def _build(self):
        self._tabs = ctk.CTkTabview(
            self,
            fg_color=BLANCO,
            segmented_button_fg_color=GRIS_BG,
            segmented_button_selected_color=APPLE_SELECTED,
            segmented_button_selected_hover_color=APPLE_SELECTED,
            segmented_button_unselected_color=GRIS_BG,
            text_color=NEGRO,
            anchor="nw",
        )
        self._tabs.pack(fill="both", expand=True, padx=20, pady=14)
        try:
            self._tabs._segmented_button.configure(font=("Segoe UI", 12))
        except Exception:
            pass
        self._tabs.add("  Archivos  ")
        self._tabs.add("  Productos  ")
        self._tabs.add("  Parametros  ")

        self._build_tab_archivos()
        self._build_tab_productos()
        self._build_tab_parametros()

    def _build_tab_archivos(self):
        tab = self._tabs.tab("  Archivos  ")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        guide = self._guide(
            tab,
            "Maestro actual: stock de partida para calcular la necesidad. "
            "M-3, M-2 y M-1: consumo de los tres meses anteriores para proyectar por regresion o promedio. "
            "Agentes Canal: lista para aplicar el ajuste de Canal Propio.",
        )
        guide.grid(row=0, column=0, sticky="ew", pady=(2, 8))

        scroll = ctk.CTkScrollableFrame(tab, fg_color=GRIS_BG, corner_radius=8)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.columnconfigure(0, weight=1)

        row = self._build_toolbar(scroll, 0)
        for key, label, desc in _ARCHIVOS_REPO:
            row = self._fila_archivo(scroll, key, label, desc, row)
        self._actualizar_estado_maestro()
        self._actualizar_status()

        nav = ctk.CTkFrame(tab, fg_color="transparent")
        nav.grid(row=2, column=0, sticky="e", pady=(6, 0))
        ctk.CTkButton(
            nav, text="Productos  →",
            fg_color=AMARILLO, hover_color=AMARILLO_DARK,
            text_color="#FFFFFF", font=("Segoe UI", 11, "bold"),
            width=150, height=34, corner_radius=6,
            command=lambda: self._tabs.set("  Productos  "),
        ).pack(padx=4)

    def _build_tab_productos(self):
        tab = self._tabs.tab("  Productos  ")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        guide = self._guide(
            tab,
            "Define que articulos se reponen, que columna historica se usa como consumo y que metodo aplica el Paso 4. "
            "Cada producto genera una fila en el pedido final.",
        )
        guide.grid(row=0, column=0, sticky="ew", pady=(2, 8))

        box = ctk.CTkFrame(tab, fg_color=GRIS_BG, corner_radius=8)
        box.grid(row=1, column=0, sticky="nsew")
        box.columnconfigure(0, weight=1)
        box.rowconfigure(1, weight=1)
        self._build_productos(box)

        nav = ctk.CTkFrame(tab, fg_color="transparent")
        nav.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        ctk.CTkButton(
            nav, text="←  Archivos",
            fg_color=APPLE_FILL, hover_color=APPLE_HOVER,
            text_color=NEGRO, font=("Segoe UI", 11),
            width=140, height=34, corner_radius=6,
            command=lambda: self._tabs.set("  Archivos  "),
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            nav, text="Parametros  →",
            fg_color=AMARILLO, hover_color=AMARILLO_DARK,
            text_color="#FFFFFF", font=("Segoe UI", 11, "bold"),
            width=150, height=34, corner_radius=6,
            command=lambda: self._tabs.set("  Parametros  "),
        ).pack(side="right", padx=4)

    def _build_tab_parametros(self):
        tab = self._tabs.tab("  Parametros  ")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        guide = self._guide(
            tab,
            "Regresion: si el consumo de 3 meses crece, se proyecta el 4to mes; si es estable o baja, se usa el promedio.  "
            "Necesidad = consumo proyectado × SUBSEGMENTACION × factor − stock disponible.  "
            "Redondeo: decimal ≤ umbral → abajo, > umbral → arriba.  "
            "Canal Propio: la cantidad calculada se multiplica por su factor adicional.",
        )
        guide.grid(row=0, column=0, sticky="ew", pady=(2, 8))

        scroll = ctk.CTkScrollableFrame(tab, fg_color=GRIS_BG, corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.columnconfigure(0, weight=1)
        self._build_params(scroll, 0)

        nav = ctk.CTkFrame(tab, fg_color="transparent")
        nav.grid(row=2, column=0, sticky="w", pady=(6, 0))
        ctk.CTkButton(
            nav, text="←  Productos",
            fg_color=APPLE_FILL, hover_color=APPLE_HOVER,
            text_color=NEGRO, font=("Segoe UI", 11),
            width=140, height=34, corner_radius=6,
            command=lambda: self._tabs.set("  Productos  "),
        ).pack(side="left", padx=4)

    def _guide(self, parent, text):
        box = ctk.CTkFrame(parent, fg_color=INFO_BG, corner_radius=8,
                           border_width=1, border_color=INFO_BORDE)
        ctk.CTkLabel(
            box, text=f"ℹ  {text}", font=("Segoe UI", 11),
            text_color=GRIS_TEXTO, anchor="w", justify="left",
            wraplength=680,
        ).pack(fill="x", padx=14, pady=10)
        return box

    def _build_toolbar(self, parent, row):
        bar = ctk.CTkFrame(parent, fg_color=BLANCO, corner_radius=8,
                           border_width=1, border_color=GRIS_BORDE)
        bar.grid(row=row, column=0, sticky="ew", padx=8, pady=(8, 6))
        bar.columnconfigure(4, weight=1)

        ctk.CTkLabel(bar, text="Archivos de reposicion",
                     font=("Segoe UI", 12, "bold"),
                     text_color=NEGRO).grid(row=0, column=0, padx=(14, 8), pady=10)
        self._lbl_detect = ctk.CTkLabel(
            bar, text="archivos: pendiente",
            font=("Segoe UI", 11), text_color=GRIS_TEXTO)
        self._lbl_detect.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=10)
        ctk.CTkButton(bar, text="Examinar",
                      fg_color=APPLE_FILL, hover_color=APPLE_HOVER,
                      text_color=NEGRO, font=("Segoe UI", 12),
                      border_width=1, border_color=GRIS_BORDE,
                      width=120, height=40, corner_radius=6,
                      command=self._examinar_archivos).grid(row=0, column=2, padx=4, pady=10)
        ctk.CTkButton(bar, text="⟳  Auto-detectar",
                      fg_color=AMARILLO, hover_color=AMARILLO_DARK,
                      text_color="#FFFFFF", font=("Segoe UI", 12, "bold"),
                      width=170, height=40, corner_radius=6,
                      command=self._autodetectar).grid(row=0, column=3, padx=4, pady=10)
        return row + 1

    def _fila_archivo(self, parent, key, label, desc, row):
        cell = ctk.CTkFrame(parent, fg_color=BLANCO, corner_radius=8,
                            border_width=1, border_color=GRIS_BORDE)
        cell.grid(row=row, column=0, sticky="ew", padx=8, pady=4)

        top = ctk.CTkFrame(cell, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(top, text=label, font=("Segoe UI", 12, "bold"),
                     text_color=NEGRO).pack(anchor="w")
        ctk.CTkLabel(top, text=desc, font=("Segoe UI", 10),
                     text_color=GRIS_TEXTO, wraplength=520,
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

        return row + 1

    def _build_params(self, parent, row):
        grid = ctk.CTkFrame(parent, fg_color=BLANCO, corner_radius=8,
                            border_width=1, border_color=GRIS_BORDE)
        grid.grid(row=row, column=0, sticky="ew", padx=8, pady=8)

        params_def = [
            ("redondeo_rollos", "Redondeo rollos", "Umbral de fraccion para redondear hacia arriba o abajo"),
            ("redondeo_rollos_prisma", "Redondeo Prisma", "Umbral de fraccion para redondear Prisma"),
            ("redondeo_rollos_sube", "Redondeo SUBE", "Umbral de fraccion para redondear SUBE"),
            ("redondeo_resma", "Redondeo Resma", "Umbral de fraccion para redondear Resma"),
            ("ajuste_canal_propio", "Ajuste Canal Propio", "Factor de reduccion para agentes Canal Propio"),
        ]

        for i, (key, label, desc) in enumerate(params_def):
            r, c = divmod(i, 2)
            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=r, column=c, padx=18, pady=14, sticky="ew")
            grid.columnconfigure(c, weight=1)

            ctk.CTkLabel(cell, text=label, font=("Segoe UI", 12, "bold"),
                         text_color=NEGRO, anchor="w").pack(fill="x")
            ctk.CTkLabel(cell, text=desc, font=("Segoe UI", 10),
                         text_color=GRIS_TEXTO, anchor="w",
                         wraplength=380).pack(fill="x")

            var = tk.StringVar(value=str(PARAMETROS.get(key, "")))
            self._param_vars[key] = var
            ctk.CTkEntry(cell, textvariable=var, width=118, height=36,
                         font=("Segoe UI", 12)).pack(anchor="w", pady=(6, 0))

    def _build_productos(self, parent):
        tools = ctk.CTkFrame(parent, fg_color=BLANCO, corner_radius=8,
                             border_width=1, border_color=GRIS_BORDE)
        tools.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        tools.columnconfigure(1, weight=1)

        ctk.CTkLabel(tools, text="Buscar:",
                     font=("Segoe UI", 11), text_color=GRIS_TEXTO).grid(
            row=0, column=0, padx=(12, 6), pady=10)
        search = ctk.CTkEntry(tools, textvariable=self._search_var,
                              width=300, height=36, font=("Segoe UI", 11))
        search.grid(row=0, column=1, sticky="w", pady=10)
        search.bind("<KeyRelease>", lambda _e: self._populate_productos())

        ctk.CTkButton(tools, text="Anadir",
                      fg_color=AMARILLO, hover_color=AMARILLO_DARK,
                      text_color="#FFFFFF", font=("Segoe UI", 11),
                      width=100, height=36,
                      command=self._add_producto).grid(row=0, column=2, padx=4, pady=10)
        ctk.CTkButton(tools, text="Editar",
                      fg_color=APPLE_FILL, hover_color=APPLE_HOVER,
                      text_color=NEGRO, font=("Segoe UI", 11),
                      width=100, height=36,
                      command=self._edit_producto).grid(row=0, column=3, padx=4, pady=10)
        ctk.CTkButton(tools, text="Eliminar",
                      fg_color=APPLE_FILL, hover_color=APPLE_HOVER,
                      text_color=NEGRO, font=("Segoe UI", 11),
                      width=100, height=36,
                      command=self._remove_producto).grid(row=0, column=4, padx=4, pady=10)
        ctk.CTkButton(tools, text="Restaurar",
                      fg_color=APPLE_FILL, hover_color=APPLE_HOVER,
                      text_color=NEGRO, font=("Segoe UI", 11),
                      width=112, height=36,
                      command=self._reset_productos).grid(row=0, column=5, padx=(4, 12), pady=10)

        self._tbl_productos = TablaWidget(
            parent, _PRODUCT_COLS,
            anchos={"Base": 150, "Repo": 180, "Método": 150,
                    "SKU": 110, "Descripción": 360},
            fg_color=GRIS_BG,
        )
        self._tbl_productos.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._populate_productos()

    def on_mostrar(self):
        self._actualizar_estado_maestro()
        self._actualizar_status()

    def _ready_count(self):
        return len(self.get_paths())

    def _actualizar_estado_maestro(self):
        if "maestro_actual" not in self._vars:
            return
        if "maestro_actual" in self._paths:
            return
        df = self._get_maestro()
        if df is not None:
            self._vars["maestro_actual"].set(
                f"  Generado en Paso 2 ({len(df):,} agentes)"
            )
            self._lbls["maestro_actual"].configure(text_color=VERDE)
        else:
            self._vars["maestro_actual"].set("Sin archivo")
            self._lbls["maestro_actual"].configure(text_color=GRIS_TEXTO)

    def _actualizar_status(self):
        if not hasattr(self, "_lbl_detect"):
            return
        paths = self.get_paths()
        # Contamos solo los archivos requeridos (los 4 primeros)
        requeridos = [k for k, _, _ in _ARCHIVOS_REPO if k != "agentes"]
        n_req = sum(1 for k in requeridos if k in paths)
        total_req = len(requeridos)
        
        self._lbl_detect.configure(
            text=f"archivos requeridos: {n_req} / {total_req}",
            text_color=VERDE if n_req == total_req else GRIS_TEXTO,
        )
        self._on_change(n_req)

    def _set_path(self, key, path, auto=False):
        self._paths[key] = path
        self._vars[key].set(f"  {Path(path).name}")
        self._lbls[key].configure(text_color=VERDE if auto else NEGRO)
        self._actualizar_status()

    def _mes_numero(self, stem):
        """Extrae el mes (1-12) de un stem de archivo. Soporta texto y número."""
        # Texto en español
        for nombre, numero in _MESES.items():
            if nombre in stem:
                return numero
        # Numérico: eliminar el año (4 dígitos) para no confundirlo con mes
        stem_limpio = re.sub(r"20\d{2}", "", stem)
        m = re.search(r"(?<!\d)(\d{1,2})(?!\d)", stem_limpio)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 12:
                return n
        return 0

    def _fecha_archivo(self, path):
        """Devuelve (año, mes) para ordenar. (0, 0) si no se puede parsear."""
        stem = path.stem.lower()
        m = re.search(r"(?<!\d)(20\d{2})(?!\d)", stem)
        anio = int(m.group(1)) if m else 0
        mes  = self._mes_numero(stem)
        return (anio, mes)

    def _autodetectar(self):
        base = Path(sys.argv[0]).resolve().parent

        # ── 1. Buscar en Maestro_Consumo por mes/año exacto ──────────────────
        carpeta_mc = base / "Maestro_Consumo"
        por_fecha = {}          # {(año, mes): Path}
        if carpeta_mc.exists():
            for p in carpeta_mc.iterdir():
                if p.is_file() and p.suffix.lower() in _EXTS:
                    fecha = self._fecha_archivo(p)
                    if fecha[0] > 0 and fecha[1] > 0:
                        por_fecha[fecha] = p

        if por_fecha:
            now = datetime.now()
            ma, mm = now.year, now.month

            # Solo archivos con "maestro" en el nombre son elegibles como maestro_actual.
            # Los archivos CONSUMO_*.xlsx son solo historial de consumo, no stock maestro.
            por_fecha_maestro = {
                k: v for k, v in por_fecha.items()
                if "maestro" in v.stem.lower()
            }

            # maestro_actual: paso2 en memoria tiene prioridad absoluta.
            # Solo asignar archivo si paso2 no generó nada en esta sesión.
            if "maestro_actual" not in self._paths and self._get_maestro() is None:
                if por_fecha_maestro:
                    clave_actual = (ma, mm)
                    p_actual = por_fecha_maestro.get(clave_actual) or por_fecha_maestro[
                        max(por_fecha_maestro.keys())
                    ]
                    self._set_path("maestro_actual", str(p_actual), auto=True)

            # consumo M-1, M-2, M-3: mes actual − 1, − 2, − 3
            for key, delta in zip(
                ("consumo_mes_3", "consumo_mes_2", "consumo_mes_1"),
                (1, 2, 3),
            ):
                if key not in self._paths:
                    m = mm - delta
                    a = ma
                    while m <= 0:
                        m += 12
                        a -= 1
                    p = por_fecha.get((a, m))
                    if p:
                        self._set_path(key, str(p), auto=True)

        # ── 2. Buscar agentes en Data/ (y fallback a carpeta raiz) ──────────
        data_dir = base / "Data"
        data_dir.mkdir(exist_ok=True)
        carpetas = [data_dir, base]

        consumos, maestros, agentes = [], [], []
        for carpeta in carpetas:
            try:
                for p in carpeta.iterdir():
                    stem = p.stem.lower()
                    if not p.is_file() or p.suffix.lower() not in _EXTS:
                        continue
                    if "consumo" in stem and "maestro" not in stem:
                        consumos.append(p)
                    elif "maestro" in stem and ("stock" in stem or "consumo" in stem):
                        maestros.append(p)
                    elif "agente" in stem:
                        agentes.append(p)
            except Exception:
                pass

        # Fallback: si Maestro_Consumo estaba vacío, usar carpeta normal
        if not por_fecha:
            maestros.sort(key=self._fecha_archivo, reverse=True)
            if maestros and "maestro_actual" not in self._paths and self._get_maestro() is None:
                self._set_path("maestro_actual", str(maestros[0]), auto=True)
            for key, p in zip(
                ("consumo_mes_3", "consumo_mes_2", "consumo_mes_1"),
                maestros[1:4],
            ):
                if key not in self._paths:
                    self._set_path(key, str(p), auto=True)

        consumos.sort(key=lambda p: (self._fecha_archivo(p), p.name.lower()))
        for key, p in zip(("consumo_mes_1", "consumo_mes_2", "consumo_mes_3"), consumos[:3]):
            if key not in self._paths:
                self._set_path(key, str(p), auto=True)

        if agentes and "agentes" not in self._paths:
            self._set_path("agentes", str(sorted(agentes, key=lambda p: p.name.lower())[0]), auto=True)

        self._actualizar_estado_maestro()
        self._actualizar_status()

    def _examinar_archivos(self):
        base = Path(sys.argv[0]).resolve().parent
        idir = base / "Data"
        idir.mkdir(exist_ok=True)
        paths = filedialog.askopenfilenames(
            title="Seleccionar archivos de reposicion",
            filetypes=[("CSV / Excel", "*.csv *.xlsx *.xls"), ("Todos", "*.*")],
            initialdir=str(idir),
        )
        if not paths:
            return

        archivos = [Path(p) for p in paths]
        agentes = [p for p in archivos if "agente" in p.stem.lower()]
        candidatos = [p for p in archivos if p not in agentes]

        if agentes:
            self._set_path("agentes", str(sorted(agentes, key=lambda p: p.name.lower())[0]), auto=False)

        ordenados = sorted(
            candidatos,
            key=lambda p: (self._fecha_archivo(p), p.name.lower()),
        )
        if ordenados:
            # Si hay 4 o más archivos, el más reciente suele ser el maestro actual.
            historial = ordenados
            if len(ordenados) >= 4:
                actual = ordenados[-1]
                self._set_path("maestro_actual", str(actual), auto=False)
                historial = ordenados[:-1]
            elif any("maestro" in p.stem.lower() and "stock" in p.stem.lower() for p in ordenados):
                actual = next(
                    p for p in reversed(ordenados)
                    if "maestro" in p.stem.lower() and "stock" in p.stem.lower()
                )
                self._set_path("maestro_actual", str(actual), auto=False)
                historial = [p for p in ordenados if p != actual]

            for key, p in zip(("consumo_mes_1", "consumo_mes_2", "consumo_mes_3"), historial[-3:]):
                self._set_path(key, str(p), auto=False)

        self._actualizar_estado_maestro()
        self._actualizar_status()

    def _examinar_individual(self, key):
        base = Path(sys.argv[0]).resolve().parent
        idir = base / "Data"
        idir.mkdir(exist_ok=True)
        path = filedialog.askopenfilename(
            title=f"Seleccionar archivo para {key.upper()}",
            filetypes=[("CSV / Excel", "*.csv *.xlsx *.xls"), ("Todos", "*.*")],
            initialdir=str(idir),
        )
        if not path:
            return
        self._set_path(key, path, auto=False)

    def _populate_productos(self):
        term = self._search_var.get().strip().lower()
        tree = self._tbl_productos.tree
        tree.delete(*tree.get_children())

        for idx, prod in enumerate(self._productos):
            values = (
                prod.get("nombre_base", ""),
                prod.get("col_repo", ""),
                prod.get("metodo", ""),
                prod.get("sku_base", ""),
                prod.get("desc_base", ""),
            )
            if term and not any(term in str(v).lower() for v in values):
                continue
            tag = "par" if len(tree.get_children()) % 2 == 0 else "impar"
            tree.insert("", "end", iid=str(idx), values=values, tags=(tag,))

    def _selected_product_index(self):
        item = self._tbl_productos.tree.focus()
        if not item:
            mostrar_dialogo(self, "advertencia", "Sin selección",
                            "Seleccione un producto de la lista.")
            return None
        return int(item)

    def _add_producto(self):
        dialog = ProductDialog(self)
        if dialog.result:
            self._productos.append(dialog.result)
            self._populate_productos()

    def _edit_producto(self):
        idx = self._selected_product_index()
        if idx is None:
            return
        dialog = ProductDialog(self, self._productos[idx])
        if dialog.result:
            self._productos[idx] = dialog.result
            self._populate_productos()

    def _remove_producto(self):
        idx = self._selected_product_index()
        if idx is None:
            return
        if confirmar(self, "Eliminar producto",
                     "¿Desea eliminar el producto seleccionado?",
                     texto_ok="Eliminar", texto_cancel="Cancelar"):
            self._productos.pop(idx)
            self._populate_productos()

    def _reset_productos(self):
        if confirmar(self, "Restaurar productos",
                     "¿Restaurar la lista de productos por defecto?\nSe perderán los cambios actuales.",
                     texto_ok="Restaurar", texto_cancel="Cancelar"):
            self._productos = [p.copy() for p in PRODUCTOS]
            self._search_var.set("")
            self._populate_productos()


class ProductDialog(ctk.CTkToplevel):
    """Dialogo simple para alta/edicion de productos."""

    _FIELDS = [
        ("nombre_base", "Nombre Base", "entry"),
        ("col_repo", "Columna Repo", "entry"),
        ("metodo", "Método", ["regresion", "promedio", "promedio_ajustado_dep"]),
        ("factor_ajuste", "Clave Factor Ajuste", "entry"),
        ("param_redondeo", "Clave Umbral Redondeo", "entry"),
        ("col_stock_reseteo", "Columna Reseteo Stock", "entry"),
        ("sku_base", "SKU Base", "entry"),
        ("desc_base", "Descripción", "entry"),
        ("col_consumo", "Columna Consumo", "entry"),
        ("prov_filter", "Solo Provincia", "entry"),
        ("prov_excluir", "Excluir Provincia", "entry"),
    ]

    def __init__(self, parent, product_data=None):
        super().__init__(parent)
        self.withdraw()
        self.transient(parent)
        self.title("Editar Producto" if product_data else "Anadir Producto")
        self.configure(fg_color=GRIS_BG)
        self.result = None
        self._vars = {}

        body = ctk.CTkFrame(self, fg_color=BLANCO, corner_radius=8)
        body.pack(fill="both", expand=True, padx=14, pady=14)

        # Campos con scroll propio: en pantallas chicas la lista de campos no
        # entra completa y sin esto quedaban tapados el resto de campos o los
        # botones Guardar/Cancelar, sin forma de llegar a ellos.
        scroll = ctk.CTkScrollableFrame(body, fg_color=BLANCO, corner_radius=0,
                                        width=480,
                                        height=min(420, 48 * len(self._FIELDS)))
        scroll.pack(fill="both", expand=True, padx=0, pady=(0, 6))
        scroll.columnconfigure(1, weight=1)

        data = product_data or {}
        for i, (key, label, widget_type) in enumerate(self._FIELDS):
            ctk.CTkLabel(scroll, text=label, font=("Segoe UI", 11),
                         text_color=NEGRO).grid(row=i, column=0, sticky="w",
                                                 padx=12, pady=6)
            var = tk.StringVar(value="" if data.get(key) is None else str(data.get(key, "")))
            self._vars[key] = var
            if isinstance(widget_type, list):
                if not var.get():
                    var.set(widget_type[0])
                widget = ctk.CTkOptionMenu(scroll, variable=var, values=widget_type,
                                           width=290, height=36,
                                           font=("Segoe UI", 11))
                # El metodo de calculo es parte del modelo del producto: al editar uno
                # ya existente se bloquea para evitar cambiarlo por error. Al agregar
                # un producto nuevo (product_data=None) queda libre para elegir.
                if key == "metodo" and product_data is not None:
                    widget.configure(state="disabled")
            else:
                widget = ctk.CTkEntry(scroll, textvariable=var, width=360, height=36,
                                      font=("Segoe UI", 11))
            widget.grid(row=i, column=1, sticky="ew", padx=12, pady=6)
            if key == "metodo" and product_data is not None:
                ctk.CTkLabel(scroll, text="No editable en productos existentes",
                             font=("Segoe UI", 9), text_color=GRIS_TEXTO).grid(
                    row=i, column=2, sticky="w", padx=(0, 12))

        # Barra de acciones fija, fuera del area con scroll: siempre visible.
        actions = ctk.CTkFrame(body, fg_color="transparent")
        actions.pack(fill="x", pady=(6, 4))
        ctk.CTkButton(actions, text="Guardar",
                      fg_color=AMARILLO, hover_color=AMARILLO_DARK,
                      text_color="#FFFFFF", font=("Segoe UI", 11, "bold"),
                      width=125, height=38,
                      command=self._save).pack(side="left", padx=(12, 6))
        ctk.CTkButton(actions, text="Cancelar",
                      fg_color=APPLE_FILL, hover_color=APPLE_HOVER,
                      text_color=NEGRO, font=("Segoe UI", 11),
                      width=125, height=38,
                      command=self.destroy).pack(side="left", padx=6)

        self.update_idletasks()
        pantalla_w = self.winfo_screenwidth()
        pantalla_h = self.winfo_screenheight()
        w = min(self.winfo_reqwidth(), int(pantalla_w * 0.9))
        h = min(self.winfo_reqheight(), int(pantalla_h * 0.85))
        x = max(0, min(parent.winfo_rootx() + 120, pantalla_w - w))
        y = max(0, min(parent.winfo_rooty() + 80, pantalla_h - h))
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.deiconify()
        self.lift()
        self.focus_force()
        self.grab_set()
        self.wait_window()

    def _save(self):
        required = ["nombre_base", "col_repo", "metodo", "sku_base", "desc_base"]
        for key in required:
            if not self._vars[key].get().strip():
                mostrar_dialogo(self, "error", "Campo requerido",
                                f"Complete el campo '{key}'.")
                return

        result = {}
        for key, _, _ in self._FIELDS:
            value = self._vars[key].get().strip()
            if not value:
                continue
            if key == "sku_base":
                try:
                    value = int(value)
                except ValueError:
                    mostrar_dialogo(self, "error", "SKU inválido",
                                    f"El SKU debe ser un número entero.\nValor ingresado: '{value}'")
                    return
            result[key] = value

        self.result = result
        self.destroy()
