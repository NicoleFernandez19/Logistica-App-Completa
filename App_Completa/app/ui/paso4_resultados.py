import shutil
import threading
import queue as q_module
import sys
from datetime import datetime
from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk
from .estilos import (AMARILLO, AMARILLO_DARK, NEGRO, BLANCO, GRIS_BG,
                      GRIS_TEXTO, GRIS_BORDE, ROJO, APPLE_FILL, APPLE_HOVER)
from .componentes import TablaWidget, PanelMetrica, mostrar_dialogo
from ..config import REGLAS, AGENTES_A_EXCLUIR

_COLS_FINAL = ["ID P.F", "NOMBRE FANTASIA", "SKU", "DESCRIPCION", "CANTIDAD", "SEGMENTO"]


class Paso4Resultados(ctk.CTkFrame):
    """Paso 4: Cálculo de reposición y exportación de pedidos."""

    def __init__(self, parent, get_paths, get_maestro, get_params, get_productos,
                 get_p1_paths=None):
        super().__init__(parent, fg_color=GRIS_BG, corner_radius=0)
        self._get_paths   = get_paths
        self._get_maestro = get_maestro
        self._get_params  = get_params
        self._get_productos = get_productos
        self._get_p1_paths = get_p1_paths
        self._df_final    = None
        self._df_detallado = None
        self._q = q_module.Queue()
        self._logs = []
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Panel pre-cálculo ────────────────────────────────────────────────
        self._zona_pre = ctk.CTkFrame(self, fg_color=BLANCO, corner_radius=8,
                                      border_width=1, border_color=GRIS_BORDE)

        ctk.CTkLabel(self._zona_pre,
                     text="Archivos listos. Presione para calcular la reposición.",
                     font=("Segoe UI", 15), text_color=NEGRO).pack(pady=(20, 12), padx=48)

        ctk.CTkLabel(
            self._zona_pre,
            text="Necesidad = consumo proyectado × factor − stock actual. Canal Propio aplica el ajuste configurado.",
            font=("Segoe UI", 11), text_color=GRIS_TEXTO,
            wraplength=540,
        ).pack(pady=(0, 14), padx=48)

        self._btn_calc = ctk.CTkButton(
            self._zona_pre, text="  CALCULAR REPOSICIÓN  ",
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
        self._lbl_status.pack(pady=(4, 12))

        log_pre, self._log_pre = self._build_log_panel(
            self._zona_pre, titulo="Proceso de reposicion"
        )
        log_pre.pack(fill="x", padx=24, pady=(0, 22))
        self._logs.append(self._log_pre)

        self._zona_post = ctk.CTkFrame(self, fg_color=GRIS_BG, corner_radius=0)

        # ── Barra superior ───────────────────────────────────────────────────
        bar = ctk.CTkFrame(self._zona_post, fg_color=BLANCO, height=70, corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        ctk.CTkLabel(bar, text="Cálculo de Reposición  —  Pedidos",
                     font=("Segoe UI", 15, "bold"),
                     text_color=NEGRO).pack(side="left", padx=16)

        self._btn_exp_final = ctk.CTkButton(
            bar, text="↓  Exportar Pedidos",
            fg_color=AMARILLO, hover_color=AMARILLO_DARK,
            text_color="#FFFFFF", font=("Segoe UI", 11, "bold"),
            width=190, height=40, corner_radius=6, state="disabled",
            command=self._exportar_final,
        )
        self._btn_exp_final.pack(side="right", padx=8)

        self._btn_exp_det = ctk.CTkButton(
            bar, text="↓  Exportar Detallado",
            fg_color=APPLE_FILL, hover_color=APPLE_HOVER,
            text_color=NEGRO, font=("Segoe UI", 11),
            width=190, height=40, corner_radius=6, state="disabled",
            command=self._exportar_detallado,
        )
        self._btn_exp_det.pack(side="right", padx=4)

        self._btn_recalc = ctk.CTkButton(
            bar, text="↺  Recalcular",
            fg_color="transparent", text_color=NEGRO,
            hover_color=APPLE_HOVER, border_width=1, border_color=GRIS_BORDE,
            font=("Segoe UI", 11),
            width=130, height=40, corner_radius=6,
            command=self._mostrar_pre,
        )
        # se muestra solo después de la primera ejecución exitosa

        # ── Layout: tabla izquierda / log derecha ────────────────────────────
        body = ctk.CTkFrame(self._zona_post, fg_color=GRIS_BG, corner_radius=0)
        body.pack(fill="both", expand=True, padx=12, pady=8)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ── Panel izquierdo: KPIs + tabla + filtro ───────────────────────────
        left = ctk.CTkFrame(body, fg_color=GRIS_BG, corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.rowconfigure(2, weight=1)
        left.columnconfigure(0, weight=1)

        # ── KPIs (ocultos hasta que haya resultados) ────────────────────────
        self._zona_kpi = ctk.CTkFrame(left, fg_color="transparent",
                                      corner_radius=0)
        self._zona_kpi.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self._zona_kpi.columnconfigure((0, 1, 2, 3), weight=1)
        self._zona_kpi.grid_remove()

        self._kpi_agentes  = PanelMetrica(self._zona_kpi, "Agentes")
        self._kpi_unidades = PanelMetrica(self._zona_kpi, "Unidades totales")
        self._kpi_lineas   = PanelMetrica(self._zona_kpi, "Líneas de pedido")
        self._kpi_prom     = PanelMetrica(self._zona_kpi, "Prom. unid./agente")

        self._kpi_agentes .grid(row=0, column=0, padx=(0, 4), pady=0, sticky="ew")
        self._kpi_unidades.grid(row=0, column=1, padx=4,      pady=0, sticky="ew")
        self._kpi_lineas  .grid(row=0, column=2, padx=4,      pady=0, sticky="ew")
        self._kpi_prom    .grid(row=0, column=3, padx=(4, 0), pady=0, sticky="ew")

        # Filtro por producto
        self._build_filtro(left)

        # Tabla de resultados
        self._tbl = TablaWidget(
            left, _COLS_FINAL,
            anchos={"NOMBRE FANTASIA": 200, "DESCRIPCION": 220,
                    "ID P.F": 80, "SKU": 100, "CANTIDAD": 80},
            fg_color=GRIS_BG,
        )
        self._tbl.grid(row=2, column=0, sticky="nsew")

        # ── Panel derecho: log (Estilo macOS Light Terminal Premium) ──────────
        right = ctk.CTkFrame(body, fg_color=BLANCO, corner_radius=8,
                             border_width=1, border_color=GRIS_BORDE)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        # Barra de título macOS (3 botones de colores de Apple)
        mac_bar = ctk.CTkFrame(right, fg_color=APPLE_FILL, height=36, corner_radius=8)
        mac_bar.grid(row=0, column=0, sticky="ew")
        mac_bar.pack_propagate(False)
        
        # Separador inferior de la barra de título
        ctk.CTkFrame(mac_bar, fg_color=GRIS_BORDE, height=1, corner_radius=0).pack(side="bottom", fill="x")

        # Tres botones circulares de colores macOS
        dots = ctk.CTkFrame(mac_bar, fg_color="transparent")
        dots.pack(side="left", padx=12, pady=10)
        
        ctk.CTkFrame(dots, fg_color="#FF5F56", width=12, height=12, corner_radius=6).pack(side="left", padx=3)
        ctk.CTkFrame(dots, fg_color="#FFBD2E", width=12, height=12, corner_radius=6).pack(side="left", padx=3)
        ctk.CTkFrame(dots, fg_color="#27C93F", width=12, height=12, corner_radius=6).pack(side="left", padx=3)

        ctk.CTkLabel(mac_bar, text="Proceso de reposicion",
                     font=("Segoe UI", 11),
                     text_color=GRIS_TEXTO).pack(side="left", padx=8)

        ctk.CTkButton(
            mac_bar, text="Copiar",
            fg_color=APPLE_HOVER, hover_color=GRIS_BORDE,
            text_color=NEGRO, font=("Segoe UI", 10),
            width=60, height=22, corner_radius=5,
            command=self._copiar_log,
        ).pack(side="right", padx=12, pady=7)

        self._log = ctk.CTkTextbox(right, font=("Consolas", 11),
                                    fg_color=BLANCO, corner_radius=0,
                                    text_color=NEGRO, state="disabled",
                                    border_width=0, wrap="word")
        self._log.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))

        # Configurar tags de color del terminal de Apple (Versión Light)
        self._log.tag_config("info", foreground="#007AFF")    # Azul Apple Light
        self._log.tag_config("success", foreground="#34C759") # Verde Apple Light
        self._log.tag_config("warning", foreground="#FF9500") # Naranja Apple Light
        self._log.tag_config("error", foreground="#FF3B30")   # Rojo Apple Light
        self._logs.append(self._log)

        self._mostrar_zona("pre")

    def _build_log_panel(self, parent, titulo):
        panel = ctk.CTkFrame(parent, fg_color=BLANCO, corner_radius=8,
                             border_width=1, border_color=GRIS_BORDE)
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)

        mac_bar = ctk.CTkFrame(panel, fg_color=APPLE_FILL, height=36, corner_radius=8)
        mac_bar.grid(row=0, column=0, sticky="ew")
        mac_bar.pack_propagate(False)
        ctk.CTkFrame(mac_bar, fg_color=GRIS_BORDE, height=1, corner_radius=0).pack(side="bottom", fill="x")

        dots = ctk.CTkFrame(mac_bar, fg_color="transparent")
        dots.pack(side="left", padx=12, pady=10)
        ctk.CTkFrame(dots, fg_color="#FF5F56", width=12, height=12, corner_radius=6).pack(side="left", padx=3)
        ctk.CTkFrame(dots, fg_color="#FFBD2E", width=12, height=12, corner_radius=6).pack(side="left", padx=3)
        ctk.CTkFrame(dots, fg_color="#27C93F", width=12, height=12, corner_radius=6).pack(side="left", padx=3)

        ctk.CTkLabel(mac_bar, text=titulo,
                     font=("Segoe UI", 11),
                     text_color=GRIS_TEXTO).pack(side="left", padx=8)

        ctk.CTkButton(
            mac_bar, text="Copiar",
            fg_color=APPLE_HOVER, hover_color=GRIS_BORDE,
            text_color=NEGRO, font=("Segoe UI", 10),
            width=60, height=22, corner_radius=5,
            command=self._copiar_log,
        ).pack(side="right", padx=12, pady=7)

        log = ctk.CTkTextbox(panel, font=("Consolas", 11),
                             fg_color=BLANCO, corner_radius=0,
                             text_color=NEGRO, state="disabled",
                             border_width=0, wrap="word", height=170)
        log.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        log.tag_config("info", foreground="#007AFF")
        log.tag_config("success", foreground="#34C759")
        log.tag_config("warning", foreground="#FF9500")
        log.tag_config("error", foreground="#FF3B30")
        return panel, log

    def _build_filtro(self, parent):
        import tkinter as tk
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 6))

        ctk.CTkLabel(bar, text="Filtrar por producto:",
                     font=("Segoe UI", 11), text_color=GRIS_TEXTO).pack(
            side="left", padx=4)

        self._var_prod = tk.StringVar(value="(Todos)")
        self._cb_prod = ctk.CTkOptionMenu(
            bar, variable=self._var_prod,
            values=["(Todos)"],
            fg_color=GRIS_BG, button_color=GRIS_BG,
            button_hover_color=APPLE_HOVER, text_color=NEGRO,
            width=270, height=36,
            font=("Segoe UI", 11),
            command=self._filtrar,
        )
        self._cb_prod.pack(side="left", padx=4)

    # ── Ejecución ─────────────────────────────────────────────────────────────

    def on_mostrar(self):
        if self._df_final is None:
            self._mostrar_zona("pre")

    def _mostrar_zona(self, zona):
        if zona == "pre":
            self._zona_post.place_forget()
            self._zona_pre.place(relx=0.5, rely=0.35, anchor="center")
        else:
            self._zona_pre.place_forget()
            self._zona_post.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _copiar_log(self):
        activo = self._log_pre if self._zona_pre.winfo_ismapped() else self._log
        texto = activo.get("1.0", "end").strip()
        if texto:
            self.clipboard_clear()
            self.clipboard_append(texto)

    def _log_write(self, texto):
        tag = None
        texto_limpio = texto.strip()
        tl = texto_limpio.lower()
        if "✓" in texto_limpio or "exitosamente" in tl or "exitoso" in tl:
            tag = "success"
        elif (texto_limpio.startswith("✗") or "error" in tl
              or "falló" in tl or "no encontrado" in tl):
            tag = "error"
        elif "advertencia" in tl or "atención" in tl or "warning" in tl:
            tag = "warning"
        elif texto_limpio.startswith("Paso") or "paso" in tl or "iniciando" in tl:
            tag = "info"
            
        for log in self._logs:
            log.configure(state="normal")
            if tag:
                log.insert("end", texto + "\n", tag)
            else:
                log.insert("end", texto + "\n")
            log.see("end")
            log.configure(state="disabled")

    def _log_clear(self):
        for log in self._logs:
            log.configure(state="normal")
            log.delete("1.0", "end")
            log.configure(state="disabled")

    def _ejecutar(self):
        self._lbl_status.configure(text="", text_color=GRIS_TEXTO)
        self._btn_calc.configure(state="disabled", text="  Calculando...  ")
        self._btn_exp_final.configure(state="disabled")
        self._btn_exp_det.configure(state="disabled")
        self._zona_kpi.grid_remove()
        self._log_clear()
        self._progress.pack(pady=(0, 16))
        self._progress.start()
        self._cola_intentos = 0

        threading.Thread(target=self._hilo_reposicion, daemon=True).start()
        self.after(150, self._revisar_cola)

    def _hilo_reposicion(self):
        from ..logic.logica_reposicion import ejecutar_proceso_reposicion

        class _Writer:
            def __init__(self, q):
                self._q = q
            def write(self, msg):
                if msg.strip():
                    self._q.put(("log", msg.rstrip()))
            def flush(self):
                pass

        old_out = sys.stdout
        sys.stdout = _Writer(self._q)
        try:
            paths   = self._get_paths()
            params  = self._get_params()
            productos = self._get_productos()

            _requeridos = {
                "consumo_mes_1": "Consumo M-3",
                "consumo_mes_2": "Consumo M-2",
                "consumo_mes_3": "Consumo M-1",
                "agentes":       "Agentes Canal Propio",
            }
            faltantes = [lbl for k, lbl in _requeridos.items() if k not in paths]
            if faltantes:
                raise ValueError(
                    "Archivos faltantes para calcular la reposición:\n"
                    + "\n".join(f"  • {lbl}" for lbl in faltantes)
                )
            _nombres = {
                "maestro_actual": "Maestro Stock Actual",
                "consumo_mes_1": "Consumo M-3",
                "consumo_mes_2": "Consumo M-2",
                "consumo_mes_3": "Consumo M-1",
                "agentes": "Agentes Canal Propio",
            }
            no_existen = []
            for key, path_str in paths.items():
                if not path_str or path_str == "__GENERADO_PASO_2__":
                    continue
                if not Path(path_str).exists():
                    no_existen.append((_nombres.get(key, key), Path(path_str).name))
            if no_existen:
                detalle = "\n".join(f"  - {lbl}: {nombre}" for lbl, nombre in no_existen)
                raise ValueError(
                    "Los archivos seleccionados ya no estan disponibles en Data/.\n\n"
                    "Si este paso ya se calculo correctamente, la aplicacion los movio a Data_OLD/ "
                    "para evitar reprocesarlos por error.\n\n"
                    "Para volver a calcular, cargue un nuevo juego de archivos en el Paso 3.\n\n"
                    f"Archivos no encontrados:\n{detalle}"
                )

            maestro = self._get_maestro()
            if maestro is None:
                raise ValueError(
                    "No hay Maestro Stock disponible.\n"
                    "Complete el Paso 2 o seleccione un archivo en Paso 3 → Maestro Stock Actual."
                )

            rutas_consumos = {
                k: paths[k] for k in ("consumo_mes_1", "consumo_mes_2", "consumo_mes_3")
            }
            ruta_agentes = paths["agentes"]

            ok, msg, df_det, df_fin = ejecutar_proceso_reposicion(
                df_maestro_actual=maestro,
                rutas_consumos=rutas_consumos,
                ruta_agentes=ruta_agentes,
                parametros_calculo=params,
                productos=productos,
                reglas=REGLAS,
                agentes_excluir=AGENTES_A_EXCLUIR,
            )
            self._q.put(("done", (ok, msg, df_det, df_fin)))
        except (ValueError, KeyError) as exc:
            self._q.put(("done", (False, str(exc), None, None)))
        except Exception as exc:
            import traceback
            self._q.put(("done", (False, f"{exc}\n\n{traceback.format_exc()}", None, None)))
        finally:
            sys.stdout = old_out

    def _revisar_cola(self):
        try:
            tag, data = self._q.get_nowait()
        except q_module.Empty:
            self._cola_intentos += 1
            if self._cola_intentos > 2000:  # ~5 minutos a 150 ms por intento
                self._progress.stop()
                self._progress.pack_forget()
                self._btn_calc.configure(
                    state="normal", text="  CALCULAR REPOSICIÓN  ")
                self._lbl_status.configure(
                    text="Tiempo de espera agotado. Intente nuevamente.",
                    text_color=ROJO)
                self._log_write("\n✗ Tiempo de espera agotado. Intente nuevamente.")
                return
            self.after(150, self._revisar_cola)
            return

        if tag == "log":
            self._log_write(data)
            self.after(150, self._revisar_cola)
        elif tag == "done":
            ok, msg, df_det, df_fin = data
            self._progress.stop()
            self._progress.pack_forget()
            self._btn_calc.configure(
                state="normal", text="  CALCULAR REPOSICIÓN  ")
            if ok:
                self._df_final     = df_fin
                self._df_detallado = df_det
                self._btn_recalc.pack(side="right", padx=8)
                try:
                    self._cargar_tabla(df_fin)
                    self._actualizar_kpis(df_fin)
                except Exception as exc:
                    mostrar_dialogo(self, "error", "Error mostrando tabla", str(exc))
                productos = self._get_productos()
                self._cb_prod.configure(
                    values=["(Todos)"] + [p.get("desc_base", "") for p in productos]
                )
                self._btn_exp_final.configure(state="normal")
                self._btn_exp_det.configure(state="normal")
                self._log_write(f"\n✓ {msg}")
                self._mostrar_zona("post")
                self._archivar_data_files()
            else:
                self._lbl_status.configure(
                    text=f"Error: {msg.splitlines()[0]}", text_color=ROJO)
                self._log_write(f"\n✗ ERROR:\n{msg}")
                mostrar_dialogo(self, "error", "Error en reposición", msg[:400], copiable=True)

    def _mostrar_pre(self):
        self._mostrar_zona("pre")
        self._btn_recalc.pack_forget()
        self._btn_calc.configure(state="normal", text="  CALCULAR REPOSICIÓN  ")
        self._lbl_status.configure(text="", text_color=GRIS_TEXTO)
        self._zona_kpi.grid_remove()

    # ── Archivado Data_OLD ────────────────────────────────────────────────────

    def _archivar_data_files(self):
        """Mueve archivos de Data/ a Data_OLD/ con la fecha de procesamiento."""
        base = Path(sys.argv[0]).resolve().parent
        data_dir = base / "Data"
        data_old_dir = base / "Data_OLD"

        if not data_dir.exists():
            return

        # Recolectar todos los paths de entrada (paso1 + agentes de paso3)
        all_paths = {}
        if self._get_p1_paths:
            try:
                all_paths.update(self._get_p1_paths())
            except Exception:
                pass
        try:
            p3 = self._get_paths()
            if "agentes" in p3:
                all_paths["agentes"] = p3["agentes"]
        except Exception:
            pass

        fecha = datetime.now().strftime("%Y%m%d")
        movidos = 0

        for key, path_str in all_paths.items():
            if not path_str or path_str == "__GENERADO_PASO_2__":
                continue
            p = Path(path_str)
            try:
                p.relative_to(data_dir)
            except ValueError:
                continue  # no esta en Data/
            if not p.exists():
                continue

            data_old_dir.mkdir(exist_ok=True)
            destino = data_old_dir / f"{p.stem}_{fecha}{p.suffix}"
            contador = 1
            while destino.exists():
                destino = data_old_dir / f"{p.stem}_{fecha}_{contador}{p.suffix}"
                contador += 1
            try:
                shutil.move(str(p), str(destino))
                movidos += 1
            except Exception as exc:
                self._log_write(f"  No se pudo archivar '{p.name}': {exc}")

        if movidos:
            self._log_write(f"\nArchivados {movidos} archivo(s) en Data_OLD/ ({fecha})")

    # ── Tabla ─────────────────────────────────────────────────────────────────

    def _cargar_tabla(self, df):
        if df is None:
            return
        filas = []
        for _, r in df.iterrows():
            filas.append((
                r.get("ID P.F", ""),
                r.get("NOMBRE FANTASIA", ""),
                r.get("SKU", ""),
                r.get("DESCRIPCION", ""),
                int(r.get("CANTIDAD", 0)),
                r.get("SEGMENTO", ""),
            ))
        self._tbl.cargar(filas)

    def _filtrar(self, valor):
        if self._df_final is None:
            return
        df = self._df_final if valor == "(Todos)" else self._df_final[
            self._df_final["DESCRIPCION"] == valor
        ]
        self._cargar_tabla(df)
        self._actualizar_kpis(df)

    def _actualizar_kpis(self, df):
        if df is None or df.empty:
            self._zona_kpi.grid_remove()
            return
        agentes  = int(df["ID P.F"].nunique())
        unidades = int(df["CANTIDAD"].sum())
        lineas   = len(df)
        prom     = round(unidades / agentes, 1) if agentes else 0

        self._kpi_agentes .set(f"{agentes:,}")
        self._kpi_unidades.set(f"{unidades:,}")
        self._kpi_lineas  .set(f"{lineas:,}")
        self._kpi_prom    .set(f"{prom:,.1f}")
        self._zona_kpi.grid()

    # ── Exportar ──────────────────────────────────────────────────────────────

    def _exportar_final(self):
        if self._df_final is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            title="Guardar Pedidos de Reposición",
            initialfile="REPOSICION_FINAL.xlsx",
        )
        if not path:
            return
        try:
            self._df_final.to_excel(path, sheet_name="REPOSICION", index=False)
            mostrar_dialogo(self, "info", "Archivo exportado",
                            f"Pedidos guardados en:\n{path}")
        except Exception as exc:
            mostrar_dialogo(self, "error", "Error al exportar", str(exc))

    def _exportar_detallado(self):
        if self._df_detallado is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            title="Guardar Archivo Detallado",
            initialfile="REPOSICION_DETALLADO.xlsx",
        )
        if not path:
            return
        try:
            self._df_detallado.to_excel(path, sheet_name="DETALLE")
            mostrar_dialogo(self, "info", "Archivo exportado",
                            f"Detallado guardado en:\n{path}")
        except Exception as exc:
            mostrar_dialogo(self, "error", "Error al exportar", str(exc))

