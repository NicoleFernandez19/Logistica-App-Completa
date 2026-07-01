import sys
import threading
import queue as q_module
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog
import pandas as pd
import customtkinter as ctk
from .estilos import (AMARILLO, AMARILLO_DARK, NEGRO, BLANCO, GRIS_BG,
                      GRIS_TEXTO, VERDE, VERDE_BG, ROJO, INFO_BG, GRIS_BORDE,
                      APPLE_FILL, APPLE_HOVER, APPLE_SELECTED)
from .componentes import TablaWidget, PanelMetrica, mostrar_dialogo
from ..config import MESES_NOMBRE as _MESES_NOMBRE

_MESES_NUMERO = {v: k for k, v in _MESES_NOMBRE.items()}

_METRICAS = [
    ("CONSUMO\nROLLOS",   "consumo_rollo"),
    ("CONSUMO\nRESMAS",   "consumo_resma"),
    ("FAJAS",             "fajas"),
    ("BOLSAS\nVERDES",    "bolsa_verde"),
    ("BOLSAS\nMAGENTA",   "bolsa_magenta"),
    ("BOLSAS\nRECOLEC.",  "bolsa_recolec"),
    ("ROLLOS\nPRISMA",    "rollo_prisma"),
    ("ROLLOS\nSUBE",      "rollo_sube"),
    ("STOCK\nROLLOS",     "stock_rollo"),
    ("STOCK\nRESMAS",     "stock_resma"),
    ("STOCK\nSUBE",       "stock_sube"),
    ("STOCK\nPRISMA",     "stock_prisma"),
]


class Paso2Consumo(ctk.CTkFrame):
    """Paso 2: Cálculo de consumo mensual + vista de resultados."""

    def __init__(self, parent, get_paths, on_calculado):
        super().__init__(parent, fg_color=GRIS_BG, corner_radius=0)
        self._get_paths   = get_paths
        self._on_calculado = on_calculado
        self._df_tiv     = None
        self._df_maestro = None
        self._q          = q_module.Queue()
        self._run_id     = 0
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Panel pre-cálculo ────────────────────────────────────────────────
        self._zona_pre = ctk.CTkFrame(self, fg_color=BLANCO, corner_radius=8,
                                      border_width=1, border_color=GRIS_BORDE)

        ctk.CTkLabel(self._zona_pre,
                     text="Archivos listos. Presione para calcular el consumo mensual.",
                     font=("Segoe UI", 15), text_color=NEGRO).pack(pady=(20, 12), padx=48)

        ctk.CTkLabel(
            self._zona_pre,
            text="Fórmula:  Stock final = Stock inicial + Envíos del mes − Consumo calculado",
            font=("Segoe UI", 11), text_color=GRIS_TEXTO,
            wraplength=540,
        ).pack(pady=(0, 14), padx=48)

        mes_frame = ctk.CTkFrame(self._zona_pre, fg_color="transparent")
        mes_frame.pack(pady=(0, 14))
        ctk.CTkLabel(mes_frame, text="Mes de la repo:",
                     font=("Segoe UI", 12), text_color=NEGRO).pack(side="left", padx=(0, 8))
        # Por defecto el mes anterior: el consumo que se calcula siempre es el del
        # mes recien cerrado, no el mes calendario en curso.
        now = datetime.now()
        mes_default = now.month - 1 or 12
        anio_default = now.year if now.month > 1 else now.year - 1
        self._var_mes_repo = tk.StringVar(value=_MESES_NOMBRE[mes_default])
        ctk.CTkOptionMenu(mes_frame, variable=self._var_mes_repo, values=list(_MESES_NOMBRE.values()),
                          fg_color=GRIS_BG, button_color=GRIS_BG,
                          button_hover_color=APPLE_HOVER, text_color=NEGRO,
                          width=150, height=32, font=("Segoe UI", 12)).pack(side="left", padx=(0, 8))
        self._var_anio_repo = tk.StringVar(value=str(anio_default))
        ctk.CTkEntry(mes_frame, textvariable=self._var_anio_repo,
                     width=70, height=32, font=("Segoe UI", 12)).pack(side="left")

        self._btn_calc = ctk.CTkButton(
            self._zona_pre, text="  CALCULAR CONSUMO  ",
            fg_color=AMARILLO, hover_color=AMARILLO_DARK,
            text_color="#FFFFFF", font=("Segoe UI", 15, "bold"),
            width=320, height=54, corner_radius=8,
            command=self._ejecutar,
        )
        self._btn_calc.pack(pady=(0, 8))

        self._progress = ctk.CTkProgressBar(self._zona_pre, mode="indeterminate",
                                             height=6, corner_radius=3,
                                             fg_color=APPLE_FILL,
                                             progress_color=AMARILLO,
                                             width=320)

        self._lbl_status = ctk.CTkLabel(
            self._zona_pre, text="",
            font=("Segoe UI", 12), text_color=GRIS_TEXTO)
        self._lbl_status.pack(pady=(4, 20))

        self._zona_pre.place(relx=0.5, rely=0.38, anchor="center")

        # ── Panel post-cálculo ───────────────────────────────────────────────
        self._zona_post = ctk.CTkFrame(self, fg_color=GRIS_BG, corner_radius=0)

        # Sub-barra
        bar = ctk.CTkFrame(self._zona_post, fg_color=BLANCO, height=70,
                           corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        ctk.CTkLabel(bar, text="Cálculo de Consumo  —  Resultados del mes",
                     font=("Segoe UI", 15, "bold"),
                     text_color=NEGRO).pack(side="left", padx=16)

        ctk.CTkButton(bar, text="↺  Recalcular",
                      fg_color="transparent", text_color=NEGRO,
                      hover_color=APPLE_HOVER, border_width=1, border_color=GRIS_BORDE,
                      font=("Segoe UI", 11),
                      width=130, height=40, corner_radius=6,
                      command=self._volver_a_calcular).pack(side="right", padx=8)

        ctk.CTkButton(bar, text="↓  Exportar MaestroStock",
                      fg_color=AMARILLO, hover_color=AMARILLO_DARK,
                      text_color="#FFFFFF", font=("Segoe UI", 11, "bold"),
                      width=220, height=40, corner_radius=6,
                      command=self._exportar).pack(side="right", padx=8)

        ctk.CTkButton(bar, text="↓  Descargar Consumo",
                      fg_color="transparent", text_color=NEGRO,
                      hover_color=APPLE_HOVER, border_width=1, border_color=GRIS_BORDE,
                      font=("Segoe UI", 11),
                      width=180, height=40, corner_radius=6,
                      command=self._exportar_consumo).pack(side="right", padx=8)

        # Métricas
        met = ctk.CTkFrame(self._zona_post, fg_color="transparent",
                           corner_radius=0)
        met.pack(fill="x", padx=12, pady=(10, 4))
        self._mvar = {}
        self._met_panels = {}
        for label, key in _METRICAS:
            p = PanelMetrica(met, label)
            p.pack(side="left", expand=True, fill="x", padx=4, pady=4)
            self._mvar[key] = p
            self._met_panels[key] = p

        self._lbl_neg = ctk.CTkLabel(
            self._zona_post, text="",
            font=("Segoe UI", 12), text_color=GRIS_TEXTO)
        self._lbl_neg.pack(anchor="e", padx=20, pady=(0, 4))

        # Tabs
        self._tabs = ctk.CTkTabview(self._zona_post, fg_color=BLANCO,
                                     segmented_button_fg_color=GRIS_BG,
                                     segmented_button_selected_color=APPLE_SELECTED,
                                     segmented_button_selected_hover_color=APPLE_SELECTED,
                                     segmented_button_unselected_color=GRIS_BG,
                                     text_color=NEGRO)
        self._tabs.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        try:
            self._tabs._segmented_button.configure(font=("Segoe UI", 12))
        except Exception:
            pass

        self._tabs.add("  Consumo Mensual  ")
        self._tabs.add("  Maestro Stock  ")
        self._tabs.add("  Reconciliación  ")
        self._tabs.add("  Sin TIV  ")
        self._tabs.add("  Sin Maestro  ")

        self._build_tab_consumo()
        self._build_tab_stock()
        self._build_tab_recon()
        self._build_tab_sin_tiv()
        self._build_tab_sin_mae()

    def _build_tab_consumo(self):
        tab = self._tabs.tab("  Consumo Mensual  ")
        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(bar, text="Filtrar canal:",
                     font=("Segoe UI", 11), text_color=GRIS_TEXTO).pack(side="left", padx=4)
        self._var_canal = tk.StringVar(value="(Todos)")
        self._cb_canal = ctk.CTkOptionMenu(
            bar, variable=self._var_canal, values=["(Todos)"],
            fg_color=GRIS_BG, button_color=GRIS_BG,
            button_hover_color=APPLE_HOVER, text_color=NEGRO,
            width=205, height=36,
            font=("Segoe UI", 11),
            command=self._filtrar_consumo,
        )
        self._cb_canal.pack(side="left", padx=4)
        ctk.CTkLabel(
            bar,
            text="Consumo mensual normalizado por agente y producto.",
            font=("Segoe UI", 11), text_color=GRIS_TEXTO,
        ).pack(side="left", padx=14)

        cols = ["ID P.F", "FLAG DSP", "TIPO", "NOMBRE FANTASIA",
                "CANAL", "PROV", "ROLLO", "BOLSA RECOL.", "ROLLO SUBE", "ROLLO PRISMA",
                "RESMA", "FAJAS"]
        anchos = {"NOMBRE FANTASIA": 180, "CANAL": 140, "ID P.F": 80}
        self._tbl_consumo = TablaWidget(tab, cols, anchos, fg_color=GRIS_BG)
        self._tbl_consumo.pack(fill="both", expand=True)

    def _build_tab_stock(self):
        tab = self._tabs.tab("  Maestro Stock  ")
        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 6))
        self._var_negs = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(bar, text="Mostrar solo negativos",
                        variable=self._var_negs, font=("Segoe UI", 11),
                        text_color=NEGRO, fg_color=AMARILLO,
                        hover_color=AMARILLO_DARK,
                        command=self._filtrar_stock).pack(side="left", padx=4)
        ctk.CTkLabel(
            bar,
            text="Stock final = stock anterior + envios - consumo.",
            font=("Segoe UI", 11), text_color=GRIS_TEXTO,
        ).pack(side="left", padx=14)

        cols = ["ID P.F", "NOMBRE FANTASIA", "PROV", "DEP",
                "SEGMENTO", "SUBSEG.", "STOCK ROLLO", "STOCK RESMA",
                "STOCK SUBE", "STOCK PRISMA", "⚠"]
        anchos = {"NOMBRE FANTASIA": 180, "ID P.F": 80, "⚠": 40}
        self._tbl_stock = TablaWidget(tab, cols, anchos, fg_color=GRIS_BG)
        self._tbl_stock.pack(fill="both", expand=True)

    def _build_tab_recon(self):
        tab = self._tabs.tab("  Reconciliación  ")
        cols = ["ID P.F", "NOMBRE FANTASIA", "CANAL",
                "C.ROLLO", "ENV.ROLLO", "ST.ROLLO ANT",
                "ST.ROLLO FINAL", "C.SUBE", "ENV.SUBE",
                "ST.SUBE ANT", "ST.SUBE FINAL",
                "C.PRISMA", "ENV.PRISMA", "ST.PRISMA ANT",
                "ST.PRISMA FINAL"]
        anchos = {"NOMBRE FANTASIA": 160, "CANAL": 130, "ID P.F": 80}
        ctk.CTkLabel(tab, text="Comparacion por producto entre consumo, envios y stock resultante.",
                     font=("Segoe UI", 11), text_color=GRIS_TEXTO).pack(anchor="w", padx=4)
        self._tbl_recon = TablaWidget(tab, cols, anchos, fg_color=GRIS_BG)
        self._tbl_recon.pack(fill="both", expand=True, pady=(4, 0))

    def _build_tab_sin_tiv(self):
        tab = self._tabs.tab("  Sin TIV  ")
        ctk.CTkLabel(tab, text="Agentes en Maestro sin transacciones este mes",
                     font=("Segoe UI", 11), text_color=GRIS_TEXTO).pack(anchor="w", padx=4)
        cols = ["ID P.F", "NOMBRE FANTASIA", "PROV", "SEGMENTO"]
        anchos = {"NOMBRE FANTASIA": 200, "ID P.F": 80}
        self._tbl_sin_tiv = TablaWidget(tab, cols, anchos, fg_color=GRIS_BG)
        self._tbl_sin_tiv.pack(fill="both", expand=True, pady=(4, 0))

    def _build_tab_sin_mae(self):
        tab = self._tabs.tab("  Sin Maestro  ")
        ctk.CTkLabel(tab, text="Agentes con transacciones sin registro en el Maestro",
                     font=("Segoe UI", 11), text_color=GRIS_TEXTO).pack(anchor="w", padx=4)
        cols = ["ID P.F", "NOMBRE FANTASIA", "CANAL", "PROV"]
        anchos = {"NOMBRE FANTASIA": 200, "CANAL": 140, "ID P.F": 80}
        self._tbl_sin_mae = TablaWidget(tab, cols, anchos, fg_color=GRIS_BG)
        self._tbl_sin_mae.pack(fill="both", expand=True, pady=(4, 0))

    # ── Ejecución ─────────────────────────────────────────────────────────────

    def on_mostrar(self):
        """Llamado cuando este paso se hace visible."""
        if self._df_maestro is None:
            self._mostrar_zona("pre")

    def _mostrar_zona(self, zona):
        if zona == "pre":
            self._zona_post.place_forget()
            self._zona_pre.place(relx=0.5, rely=0.35, anchor="center")
        else:
            self._zona_pre.place_forget()
            self._zona_post.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _volver_a_calcular(self):
        self._df_tiv = None
        self._df_maestro = None
        self._btn_calc.configure(state="normal", text="  CALCULAR CONSUMO  ")
        self._progress.stop()
        self._progress.pack_forget()
        self._lbl_status.configure(text="")
        self._mostrar_zona("pre")

    def _mostrar_advertencias(self, advertencias):
        texto = "\n\n──────────\n\n".join(advertencias)
        mostrar_dialogo(self, "advertencia", "Advertencias del cálculo", texto,
                        copiable=True)

    def _ejecutar(self):
        self._btn_calc.configure(state="disabled", text="  Calculando...  ")
        self._lbl_status.configure(text="")
        self._progress.pack(pady=(0, 8))
        self._progress.start()
        self.update_idletasks()
        self._cola_intentos = 0
        self._run_id += 1
        threading.Thread(target=self._hilo_calculo, args=(self._run_id,), daemon=True).start()
        self.after(150, self._revisar_cola)

    def _hilo_calculo(self, run_id):
        try:
            from ..logic.cargador import (
                cargar_tiv, cargar_maestro, cargar_fac_termicas,
                cargar_dsp_kyc, cargar_com_tx_int,
                cargar_prisma, cargar_sube, cargar_rollo_env, cargar_trx_sube,
                cargar_resma_env, cargar_fajas,
            )
            from ..logic.calculos_consumo import calcular, preparar_maestro_exportable

            paths = self._get_paths()
            _obligatorios = {
                "tiv": "TIV", "maestro": "Maestro Consumo",
                "fac_termicas": "FAC. TERMICAS", "dsp_kyc": "DSP / KYC",
                "com_tx_int": "COM TX INT", "prisma": "PRISMA",
                "sube": "SUBE", "rollo_env": "ROLLO (envíos)", "trx_sube": "TRX SUBE",
                "resma_env": "RESMA (envíos)", "fajas": "FAJAS",
            }
            faltantes = [lbl for k, lbl in _obligatorios.items() if k not in paths]
            if faltantes:
                raise ValueError(
                    "Archivos no seleccionados:\n"
                    + "\n".join(f"  • {lbl}" for lbl in faltantes)
                )

            def _ruta_archivo(p):
                """Extrae la ruta del archivo descartando ::NombreHoja si lo tiene."""
                return p.rsplit("::", 1)[0] if "::" in p else p

            no_existen = [
                (lbl, paths[k]) for k, lbl in _obligatorios.items()
                if k in paths and not Path(_ruta_archivo(paths[k])).exists()
            ]
            if no_existen:
                detalle = "\n".join(
                    f"  • {lbl}: {_ruta_archivo(p)}" for lbl, p in no_existen
                )
                raise ValueError(
                    "Los siguientes archivos ya no se encuentran en su ubicación original.\n"
                    "Puede que hayan sido movidos o eliminados.\n"
                    "Por favor, vuelva al Paso 1 y selecciónelos nuevamente:\n\n"
                    + detalle
                )

            tiv        = cargar_tiv(paths["tiv"])
            maestro    = cargar_maestro(paths["maestro"])
            fac        = cargar_fac_termicas(paths["fac_termicas"])
            dsp_kyc    = cargar_dsp_kyc(paths["dsp_kyc"])
            com_tx_int = cargar_com_tx_int(paths["com_tx_int"])
            prisma     = cargar_prisma(paths["prisma"])
            sube       = cargar_sube(paths["sube"])
            rollo_env  = cargar_rollo_env(paths["rollo_env"])
            trx        = cargar_trx_sube(paths["trx_sube"])
            resma_env  = cargar_resma_env(paths["resma_env"]) if "resma_env" in paths else None
            fajas      = cargar_fajas(paths["fajas"]) if "fajas" in paths else None

            advertencias = []
            if "CANAL_AGENTE_AGRUP" not in tiv.columns:
                advertencias.append(
                    "La columna 'CANAL_AGENTE_AGRUP' no se encontró en el archivo TIV.\n\n"
                    "Los agentes 'Centros y Asistidos' quedarán clasificados como TIPO 0, "
                    "lo que puede afectar el cálculo de RESMAS.\n\n"
                    "Verifique que el archivo TIV exportado incluya esta columna."
                )

            df_tiv, df_mae = calcular(
                tiv, maestro, fac, prisma, sube, trx,
                dsp_kyc, com_tx_int, rollo_env,
                resma_env=resma_env, fajas=fajas,
            )

            if "CANAL_AGENTE_AGRUP" in tiv.columns:
                n_tipo2 = int((df_tiv["TIPO_AGENTE"] == 2).sum())
                if n_tipo2 == 0:
                    col_ca = "CANAL_AGENTE_AGRUP"
                    ca_mask = (
                        df_tiv[col_ca].astype(str).str.strip().str.lower()
                        == "centros y asistidos"
                    ) if col_ca in df_tiv.columns else None

                    valor_existe = ca_mask is not None and ca_mask.any()
                    if not valor_existe:
                        valores = (
                            tiv["CANAL_AGENTE_AGRUP"]
                            .dropna()
                            .astype(str)
                            .str.strip()
                            .unique()
                            .tolist()
                        )
                        advertencias.append(
                            "La columna 'CANAL_AGENTE_AGRUP' está presente en el TIV "
                            "pero ningún valor coincide exactamente con 'Centros y Asistidos'.\n\n"
                            f"Valores encontrados: {valores}\n\n"
                            "Verifique que el archivo TIV contenga ese valor tal como está escrito."
                        )

            df_repo = preparar_maestro_exportable(df_tiv, df_mae)
            self._q.put((run_id, "ok", (df_tiv, df_mae, df_repo, advertencias)))
        except (ValueError, KeyError) as exc:
            self._q.put((run_id, "error", str(exc)))
        except FileNotFoundError as exc:
            ruta = exc.filename if exc.filename else str(exc)
            self._q.put((run_id, "error",
                f"No se encontró el archivo:\n  {ruta}\n\n"
                "El archivo puede haber sido movido o eliminado.\n"
                "Vuelva al Paso 1 y selecciónelo nuevamente."
            ))
        except Exception as exc:
            import traceback
            self._q.put((run_id, "error", f"{exc}\n\n{traceback.format_exc()}"))

    def _revisar_cola(self):
        try:
            run_id, msg, data = self._q.get_nowait()
        except q_module.Empty:
            self._cola_intentos += 1
            if self._cola_intentos > 2000:  # ~5 minutos a 150 ms por intento
                self._btn_calc.configure(state="normal", text="  CALCULAR CONSUMO  ")
                self._lbl_status.configure(
                    text="Tiempo de espera agotado. Intente nuevamente.",
                    text_color=ROJO,
                )
                return
            self.after(150, self._revisar_cola)
            return

        if run_id != self._run_id:
            # Resultado de un calculo anterior ya abandonado por timeout; se descarta
            # para que no pise el resultado del calculo actual.
            self._revisar_cola()
            return

        self._progress.stop()
        self._progress.pack_forget()
        if msg == "ok":
            df_tiv, df_mae, df_repo, advertencias = data
            self._df_tiv     = df_tiv
            self._df_maestro = df_mae
            self._df_repo    = df_repo
            self._on_calculado(df_tiv, df_mae, df_repo)
            try:
                self._poblar_tablas(df_tiv, df_mae)
                self._mostrar_metricas(df_tiv, df_mae)
            except Exception as exc:
                mostrar_dialogo(self, "error", "Error mostrando resultados", str(exc))
            self._mostrar_zona("post")
            self._btn_calc.configure(state="normal",
                                     text="  CALCULAR CONSUMO  ")
            self._auto_guardar()
            if advertencias:
                self._mostrar_advertencias(advertencias)
        else:
            self._btn_calc.configure(state="normal",
                                     text="  CALCULAR CONSUMO  ")
            self._lbl_status.configure(text=f"Error: {data.splitlines()[0]}",
                                       text_color=ROJO)
            mostrar_dialogo(self, "error", "Error en el cálculo", data, copiable=True)

    # ── Mostrar resultados ────────────────────────────────────────────────────

    def _mostrar_metricas(self, t, m):
        f = lambda v: f"{v:,.1f}"
        self._mvar["consumo_rollo"].set(f(t["ROLLOS"].sum()))
        self._mvar["consumo_resma"].set(f(t["RESMA"].sum() if "RESMA" in t.columns else 0))
        self._mvar["fajas"].set(f(t["FAJAS"].sum() if "FAJAS" in t.columns else 0))
        self._mvar["bolsa_verde"].set(f(t["BOLSAS_VERDES"].sum()))
        self._mvar["bolsa_magenta"].set(f(t["BOLSAS_MAGENTA"].sum()))
        self._mvar["bolsa_recolec"].set(f(t["BOLSAS_RECOLECCION"].sum()))
        self._mvar["rollo_prisma"].set(f(t["ROLLO_PRISMA"].sum()))
        self._mvar["rollo_sube"].set(f(t["ROLLO_SUBE"].sum()))
        self._mvar["stock_rollo"].set(f(m["STOCK_ROLLO"].sum()))
        self._mvar["stock_resma"].set(f(m["STOCK_RESMA"].sum() if "STOCK_RESMA" in m.columns else 0))
        self._mvar["stock_sube"].set(f(m["STOCK_SUBE"].sum()))
        self._mvar["stock_prisma"].set(f(m["STOCK_PRISMA"].sum()))

        neg = int(m["AGENTE_NEGATIVO"].sum())
        n_a = len(t)
        self._lbl_neg.configure(
            text=f"{n_a:,} agentes procesados  ·  {neg:,} con stock negativo",
            text_color=ROJO if neg > 0 else VERDE,
        )

    def _poblar_tablas(self, t, m):
        self._t = t
        self._m = m

        # Consumo
        self._canales = sorted(
            t["CANAL_AGENTE_AGRUP"].dropna().unique().tolist()
            if "CANAL_AGENTE_AGRUP" in t.columns else []
        )
        self._cb_canal.configure(values=["(Todos)"] + self._canales)
        self._cargar_consumo(t)

        # Stock
        self._cargar_stock(m, solo_neg=False)

        # Reconciliación
        self._cargar_recon(t, m)

        # Sin TIV / Sin Maestro
        tiv_ids = set(t["ID_PF"].astype(str))
        mae_ids = set(m["ID_PF"].astype(str))

        sin_tiv = m[~m["ID_PF"].astype(str).isin(tiv_ids)].copy()
        filas_sin_tiv = [
            (r.get("ID_PF", ""), r.get("NOMBRE_FANTASIA", ""),
             r.get("PROV", ""), r.get("SEGMENTO", ""))
            for _, r in sin_tiv.iterrows()
        ]
        self._tbl_sin_tiv.cargar(filas_sin_tiv)

        sin_mae = t[~t["ID_PF"].astype(str).isin(mae_ids)].copy()
        filas_sin_mae = [
            (r.get("ID_PF", ""), r.get("NOMBRE_FANTASIA", ""),
             r.get("CANAL_AGENTE_AGRUP", ""), r.get("PROVINCIA", ""))
            for _, r in sin_mae.iterrows()
        ]
        self._tbl_sin_mae.cargar(filas_sin_mae)

    def _cargar_consumo(self, t):
        fmt = "{:,.2f}"
        filas = []
        for _, r in t.iterrows():
            filas.append((
                r.get("ID_PF", ""),
                r.get("FLAG_DSP", ""),
                r.get("TIPO_AGENTE", ""),
                r.get("NOMBRE_FANTASIA", ""),
                r.get("CANAL_AGENTE_AGRUP", ""),
                r.get("PROVINCIA", r.get("PROV", "")),
                fmt.format(r.get("ROLLOS", 0)),
                fmt.format(r.get("BOLSAS_RECOLECCION", 0)),
                fmt.format(r.get("ROLLO_SUBE", 0)),
                fmt.format(r.get("ROLLO_PRISMA", 0)),
                fmt.format(r.get("RESMA", 0)),
                fmt.format(r.get("FAJAS", 0)),
            ))
        self._tbl_consumo.cargar(filas)

    def _filtrar_consumo(self, valor):
        if not hasattr(self, "_t"):
            return
        if valor == "(Todos)" or "CANAL_AGENTE_AGRUP" not in self._t.columns:
            t = self._t
        else:
            t = self._t[self._t["CANAL_AGENTE_AGRUP"] == valor]
        self._cargar_consumo(t)

    def _cargar_stock(self, m, solo_neg):
        fmt = "{:,.2f}"
        tree = self._tbl_stock.tree
        self._tbl_stock.tree.delete(*tree.get_children())
        i = 0
        for _, r in m.iterrows():
            neg = int(r.get("AGENTE_NEGATIVO", 0))
            if solo_neg and neg == 0:
                continue
            tag_base = "par" if i % 2 == 0 else "impar"
            tag = "rojo" if neg else tag_base
            fila = (
                r.get("ID_PF", ""),
                r.get("NOMBRE_FANTASIA", ""),
                r.get("PROV", ""),
                r.get("DEP", ""),
                r.get("SEGMENTO", ""),
                r.get("SUBSEGMENTACION", ""),
                fmt.format(r.get("STOCK_ROLLO", 0)),
                fmt.format(r.get("STOCK_RESMA", 0)),
                fmt.format(r.get("STOCK_SUBE", 0)),
                fmt.format(r.get("STOCK_PRISMA", 0)),
                "⚠ SÍ" if neg else "OK",
            )
            tree.insert("", "end", values=fila, tags=(tag,))
            i += 1

    def _filtrar_stock(self):
        if hasattr(self, "_m"):
            self._cargar_stock(self._m, solo_neg=self._var_negs.get())

    def _cargar_recon(self, t, m):
        fmt = "{:,.2f}"
        t_cols = [c for c in ["ID_PF", "NOMBRE_FANTASIA", "CANAL_AGENTE_AGRUP",
                               "ROLLOS", "ROLLO_SUBE", "ROLLO_PRISMA"] if c in t.columns]
        m_cols = [c for c in ["ID_PF", "ENVIO_ROLLO", "ENVIO_SUBE", "ENVIO_PRISMA",
                               "STOCK_ROLLO_ANT", "STOCK_SUBE_ANT", "STOCK_PRISMA_ANT",
                               "STOCK_ROLLO", "STOCK_SUBE", "STOCK_PRISMA"] if c in m.columns]
        merged = t[t_cols].merge(m[m_cols], on="ID_PF", how="left")
        num_cols = merged.select_dtypes(include="number").columns
        merged[num_cols] = merged[num_cols].fillna(0)
        if "NOMBRE_FANTASIA" in merged.columns:
            merged["NOMBRE_FANTASIA"] = merged["NOMBRE_FANTASIA"].fillna("")
        if "CANAL_AGENTE_AGRUP" in merged.columns:
            merged["CANAL_AGENTE_AGRUP"] = merged["CANAL_AGENTE_AGRUP"].fillna("")
        filas = []
        for _, r in merged.iterrows():
            filas.append((
                r.get("ID_PF", ""),
                r.get("NOMBRE_FANTASIA", ""),
                r.get("CANAL_AGENTE_AGRUP", ""),
                fmt.format(r.get("ROLLOS", 0)),
                fmt.format(r.get("ENVIO_ROLLO", 0)),
                fmt.format(r.get("STOCK_ROLLO_ANT", 0)),
                fmt.format(r.get("STOCK_ROLLO", 0)),
                fmt.format(r.get("ROLLO_SUBE", 0)),
                fmt.format(r.get("ENVIO_SUBE", 0)),
                fmt.format(r.get("STOCK_SUBE_ANT", 0)),
                fmt.format(r.get("STOCK_SUBE", 0)),
                fmt.format(r.get("ROLLO_PRISMA", 0)),
                fmt.format(r.get("ENVIO_PRISMA", 0)),
                fmt.format(r.get("STOCK_PRISMA_ANT", 0)),
                fmt.format(r.get("STOCK_PRISMA", 0)),
            ))
        self._tbl_recon.cargar(filas)

    # ── Exportar ──────────────────────────────────────────────────────────────

    def _construir_consumo_df(self):
        t = self._df_tiv
        consumo_cols = ["ID_PF", "FLAG_DSP_KYC", "TIPO_AGENTE", "NOMBRE_FANTASIA",
                        "ROLLOS", "BOLSAS_RECOLECCION", "ROLLO_SUBE", "ROLLO_PRISMA",
                        "RESMA", "FAJAS"]
        consumo = t[[c for c in consumo_cols if c in t.columns]].copy()
        consumo = consumo.rename(columns={
            "ID_PF": "ID P.F", "TIPO_AGENTE": "TIPO",
            "NOMBRE_FANTASIA": "NOMBRE FANTASIA",
            "ROLLOS": "ROLLO", "BOLSAS_RECOLECCION": "BOLSA RECOLECCION",
            "ROLLO_SUBE": "ROLLO SUBE", "ROLLO_PRISMA": "ROLLO PRISMA",
        })
        return consumo

    def _write_export_workbook(self, path):
        t, m = self._df_tiv, self._df_maestro

        consumo = self._construir_consumo_df()

        stock_cols = ["ID_PF", "NOMBRE_FANTASIA", "PROV", "DEP",
                      "SEGMENTO", "SUBSEGMENTACION",
                      "STOCK_ROLLO", "STOCK_RESMA", "STOCK_SUBE", "STOCK_PRISMA"]
        stock = m[[c for c in stock_cols if c in m.columns]].copy()
        stock = stock.rename(columns={
            "ID_PF": "ID P.F", "NOMBRE_FANTASIA": "NOMBRE FANTASIA",
            "STOCK_ROLLO": "STOCK ROLLO", "STOCK_RESMA": "STOCK RESMA",
            "STOCK_SUBE": "STOCK SUBE", "STOCK_PRISMA": "STOCK PRISMA",
        })

        t_cols = [c for c in ["ID_PF", "NOMBRE_FANTASIA", "CANAL_AGENTE_AGRUP",
                               "ROLLOS", "ROLLO_SUBE", "ROLLO_PRISMA"] if c in t.columns]
        m_cols = [c for c in ["ID_PF", "ENVIO_ROLLO", "ENVIO_SUBE", "ENVIO_PRISMA",
                               "STOCK_ROLLO_ANT", "STOCK_SUBE_ANT", "STOCK_PRISMA_ANT",
                               "STOCK_ROLLO", "STOCK_SUBE", "STOCK_PRISMA"] if c in m.columns]
        recon = t[t_cols].merge(m[m_cols], on="ID_PF", how="left")

        tiv_ids = set(t["ID_PF"].astype(str))
        mae_ids = set(m["ID_PF"].astype(str))
        sin_tiv = m[~m["ID_PF"].astype(str).isin(tiv_ids)]
        sin_mae = t[~t["ID_PF"].astype(str).isin(mae_ids)]

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df_repo = getattr(self, "_df_repo", None)
            if df_repo is not None:
                df_repo.to_excel(writer, sheet_name="MaestroStock", index=False)
            consumo.to_excel(writer, sheet_name="Consumo Mensual", index=False)
            stock.to_excel(writer,   sheet_name="Maestro Stock",   index=False)
            recon.to_excel(writer,   sheet_name="Reconciliacion",  index=False)
            sin_tiv.to_excel(writer, sheet_name="Sin TIV",         index=False)
            sin_mae.to_excel(writer, sheet_name="Sin Maestro",     index=False)

    def _destino_maestro(self):
        """Nombra el archivo con el mes SIGUIENTE al mes de la repo elegido en el selector,
        ya que este MaestroStock es el stock de partida para la repo del mes que viene."""
        mes_repo = _MESES_NUMERO.get(self._var_mes_repo.get(), datetime.now().month)
        try:
            anio_repo = int(self._var_anio_repo.get())
        except ValueError:
            anio_repo = datetime.now().year
        mes_siguiente = mes_repo + 1
        anio_siguiente = anio_repo
        if mes_siguiente > 12:
            mes_siguiente = 1
            anio_siguiente += 1
        nombre = f"MAESTRO_CONSUMO_ENVIO_{_MESES_NOMBRE[mes_siguiente]}_{anio_siguiente}.xlsx"
        carpeta = Path(sys.argv[0]).resolve().parent / "Maestro_Consumo"
        carpeta.mkdir(exist_ok=True)
        return carpeta / nombre

    def _auto_guardar(self):
        """Guarda en Maestro_Consumo/. Si ya existe el archivo del mes, lo renombra como _anterior."""
        if self._df_tiv is None:
            return
        destino = self._destino_maestro()
        if destino.exists():
            import shutil
            backup = destino.with_name(destino.stem + "_anterior" + destino.suffix)
            try:
                shutil.copy2(str(destino), str(backup))
            except Exception:
                pass
        try:
            self._write_export_workbook(str(destino))
            self._lbl_status.configure(
                text=f"Guardado: Maestro_Consumo/{destino.name}",
                text_color=VERDE,
            )
        except Exception as exc:
            self._lbl_status.configure(
                text=f"Error al guardar: {exc}",
                text_color=ROJO,
            )

    def _ejecutar_exportacion(self, accion, mensaje_ok):
        """Corre `accion` (que escribe el archivo) y muestra el resultado en un dialogo."""
        try:
            accion()
            mostrar_dialogo(self, "info", "Archivo exportado", mensaje_ok)
        except Exception as exc:
            mostrar_dialogo(self, "error", "Error al exportar", str(exc))

    def _exportar(self):
        """Botón manual: sobreescribe sin preguntar y muestra confirmación."""
        if self._df_tiv is None:
            return
        destino = self._destino_maestro()
        self._ejecutar_exportacion(
            lambda: self._write_export_workbook(str(destino)),
            f"MaestroStock guardado en:\nMaestro_Consumo/{destino.name}",
        )

    def _exportar_consumo(self):
        """Descarga únicamente la tabla de Consumo Mensual, en un archivo aparte."""
        if self._df_tiv is None:
            return
        now = datetime.now()
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            title="Guardar Consumo Mensual",
            initialfile=f"CONSUMO_MENSUAL_{now.strftime('%Y%m')}.xlsx",
        )
        if not path:
            return
        self._ejecutar_exportacion(
            lambda: self._construir_consumo_df().to_excel(path, sheet_name="Consumo Mensual", index=False),
            f"Consumo mensual guardado en:\n{path}",
        )

