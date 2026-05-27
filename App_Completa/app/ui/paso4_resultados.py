import shutil
import threading
import queue as q_module
import sys
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk
from .estilos import (AMARILLO, AMARILLO_DARK, NEGRO, BLANCO, GRIS_BG,
                      GRIS_TEXTO, GRIS_BORDE)
from .componentes import TablaWidget
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
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Barra superior ───────────────────────────────────────────────────
        bar = ctk.CTkFrame(self, fg_color=BLANCO, height=70, corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        ctk.CTkLabel(bar, text="Cálculo de Reposición  —  Pedidos",
                     font=("Segoe UI", 15, "bold"),
                     text_color=NEGRO).pack(side="left", padx=16)

        self._btn_exp_final = ctk.CTkButton(
            bar, text="↓  Exportar Pedidos",
            fg_color=AMARILLO, hover_color=AMARILLO_DARK,
            text_color=NEGRO, font=("Segoe UI", 11, "bold"),
            width=190, height=40, corner_radius=6, state="disabled",
            command=self._exportar_final,
        )
        self._btn_exp_final.pack(side="right", padx=8)

        self._btn_exp_det = ctk.CTkButton(
            bar, text="↓  Exportar Detallado",
            fg_color=GRIS_BG, hover_color=GRIS_BG,
            text_color=NEGRO, font=("Segoe UI", 11),
            width=190, height=40, corner_radius=6, state="disabled",
            command=self._exportar_detallado,
        )
        self._btn_exp_det.pack(side="right", padx=4)

        # ── Layout: tabla izquierda / log derecha ────────────────────────────
        body = ctk.CTkFrame(self, fg_color=GRIS_BG, corner_radius=0)
        body.pack(fill="both", expand=True, padx=12, pady=8)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ── Panel izquierdo: botón + tabla ───────────────────────────────────
        left = ctk.CTkFrame(body, fg_color=GRIS_BG, corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        # Zona pre-cálculo
        self._zona_pre = ctk.CTkFrame(left, fg_color=BLANCO, corner_radius=8)
        self._zona_pre.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ctk.CTkLabel(self._zona_pre,
                     text="Archivos listos. Presione para calcular la reposición.",
                     font=("Segoe UI", 15), text_color=NEGRO).pack(pady=(18, 12))

        ctk.CTkLabel(
            self._zona_pre,
            text="Necesidad = consumo proyectado * factor - stock actual. Canal Propio aplica el ajuste configurado.",
            font=("Segoe UI", 11), text_color=GRIS_TEXTO,
            wraplength=680,
        ).pack(pady=(0, 12))

        self._btn_calc = ctk.CTkButton(
            self._zona_pre, text="  CALCULAR REPOSICIÓN  ",
            fg_color=AMARILLO, hover_color=AMARILLO_DARK,
            text_color=NEGRO, font=("Segoe UI", 15, "bold"),
            width=320, height=54, corner_radius=8,
            command=self._ejecutar,
        )
        self._btn_calc.pack(pady=(0, 8))

        # Barra de progreso (oculta inicialmente, dentro de _zona_pre)
        self._progress = ctk.CTkProgressBar(self._zona_pre, mode="indeterminate",
                                             height=6, corner_radius=3,
                                             fg_color="#E2E8F0",
                                             progress_color=AMARILLO,
                                             width=320)

        # Tabla de resultados
        self._tbl = TablaWidget(
            left, _COLS_FINAL,
            anchos={"NOMBRE FANTASIA": 200, "DESCRIPCION": 220,
                    "ID P.F": 80, "SKU": 100, "CANTIDAD": 80},
            fg_color=GRIS_BG,
        )
        self._tbl.grid(row=1, column=0, sticky="nsew")

        # Filtro por producto
        self._build_filtro(left)

        # ── Panel derecho: log ───────────────────────────────────────────────
        right = ctk.CTkFrame(body, fg_color=BLANCO, corner_radius=10,
                             border_width=1, border_color=GRIS_BORDE)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Log del proceso",
                     font=("Segoe UI", 11, "bold"),
                     text_color=NEGRO).grid(row=0, column=0,
                                             sticky="w", padx=10, pady=6)

        self._log = ctk.CTkTextbox(right, font=("Consolas", 11),
                                    fg_color=GRIS_BG, corner_radius=0,
                                    text_color=GRIS_TEXTO, state="disabled")
        self._log.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))

    def _build_filtro(self, parent):
        import tkinter as tk
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=2, column=0, sticky="ew", pady=(6, 0))

        ctk.CTkLabel(bar, text="Filtrar por producto:",
                     font=("Segoe UI", 11), text_color=GRIS_TEXTO).pack(
            side="left", padx=4)

        self._var_prod = tk.StringVar(value="(Todos)")
        self._cb_prod = ctk.CTkOptionMenu(
            bar, variable=self._var_prod,
            values=["(Todos)"],
            fg_color=GRIS_BG, button_color=GRIS_BG,
            button_hover_color="#E2E8F0", text_color=NEGRO,
            width=270, height=36,
            font=("Segoe UI", 11),
            command=self._filtrar,
        )
        self._cb_prod.pack(side="left", padx=4)

    # ── Ejecución ─────────────────────────────────────────────────────────────

    def on_mostrar(self):
        pass

    def _log_write(self, texto):
        self._log.configure(state="normal")
        self._log.insert("end", texto + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _log_clear(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _ejecutar(self):
        self._btn_calc.configure(state="disabled", text="  Calculando...  ")
        self._btn_exp_final.configure(state="disabled")
        self._btn_exp_det.configure(state="disabled")
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
            maestro = self._get_maestro()
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
                try:
                    self._cargar_tabla(df_fin)
                except Exception as exc:
                    messagebox.showerror("Error mostrando tabla", str(exc))
                productos = self._get_productos()
                self._cb_prod.configure(
                    values=["(Todos)"] + [p.get("desc_base", "") for p in productos]
                )
                self._btn_exp_final.configure(state="normal")
                self._btn_exp_det.configure(state="normal")
                self._log_write(f"\n✓ {msg}")
                self._archivar_data_files()
            else:
                self._log_write(f"\n✗ ERROR:\n{msg}")
                messagebox.showerror("Error en reposición", msg[:400])

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
            messagebox.showinfo("Exportado", f"Pedidos guardados en:\n{path}")
        except Exception as exc:
            messagebox.showerror("Error al exportar", str(exc))

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
            messagebox.showinfo("Exportado", f"Detallado guardado en:\n{path}")
        except Exception as exc:
            messagebox.showerror("Error al exportar", str(exc))
