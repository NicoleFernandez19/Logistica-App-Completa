import customtkinter as ctk
try:
    from tkinterdnd2 import TkinterDnD
    _DND_DISPONIBLE = True
except ImportError:
    TkinterDnD = None
    _DND_DISPONIBLE = False
from .estilos import (configurar_tema, set_modo_apariencia,
                      NEGRO, AMARILLO, AMARILLO_DARK,
                      BLANCO, GRIS_BG, GRIS_BORDE, GRIS_TEXTO,
                      APPLE_BAR, APPLE_HOVER, APPLE_FILL, APPLE_SELECTED,
                      WU_BLACK, WU_YELLOW)
from .componentes import IndicadorPasos, TablaWidget, mostrar_dialogo

_PASOS = ["Archivos", "Consumo", "Reposicion", "Pedidos"]
_N_CONSUMO     = 11  # archivos requeridos en paso 1
_N_REPOSICION  = 4   # maestro actual + 3 historicos (agentes es opcional)

_Base = (TkinterDnD.DnDWrapper, ctk.CTk) if _DND_DISPONIBLE else (ctk.CTk,)


class VentanaPrincipal(*_Base):
    """Ventana raiz. Si tkinterdnd2 esta disponible, habilita arrastrar y
    soltar archivos desde el explorador (ver componentes.registrar_drop)."""

    def __init__(self):
        configurar_tema()
        super().__init__()
        if _DND_DISPONIBLE:
            self.TkdndVersion = TkinterDnD._require(self)

        self.title("Western Union - Reposicion de Insumos")
        self.geometry("1420x880")
        self.minsize(1180, 760)
        self.configure(fg_color=GRIS_BG)
        # Maximizar recien despues de que la ventana termine de dibujarse:
        # si se hace en el mismo __init__, el recalculo de escala por DPI
        # que hace CustomTkinter poco despues del arranque puede "deshacer"
        # el estado zoomed, y se ve la ventana agrandarse y luego achicarse.
        self.after(10, lambda: self.state("zoomed"))

        # ── Estado compartido entre pasos ────────────────────────────────────
        self._df_tiv      = None   # resultado de calcular()
        self._df_maestro  = None   # resultado de calcular()
        self._df_maestro_repo = None  # preparar_maestro_exportable()

        self._paso_actual = 0
        self._modo_var = ctk.StringVar(value="Dia")

        self._build()
        self._ir_paso(0)

    # ════════════════════════════════════════════════════════════════════════
    # Layout principal
    # ════════════════════════════════════════════════════════════════════════

    def _build(self):
        self._build_header()
        self._build_indicador()

        # Área de contenido
        self._content = ctk.CTkFrame(self, fg_color=GRIS_BG, corner_radius=0)
        self._content.pack(fill="both", expand=True)

        # Importar pasos aquí para evitar importaciones circulares
        from .paso1_carga import Paso1Carga
        from .paso2_consumo import Paso2Consumo
        from .paso3_reposicion import Paso3Reposicion
        from .paso4_resultados import Paso4Resultados

        self._p1 = Paso1Carga(self._content,
                               on_change=self._on_archivos_consumo_change)
        self._p2 = Paso2Consumo(self._content,
                                 get_paths=lambda: self._p1.get_paths(),
                                 on_calculado=self._on_consumo_calculado)
        self._p3 = Paso3Reposicion(self._content,
                                    get_maestro=lambda: self._df_maestro_repo,
                                    on_change=self._on_archivos_repo_change)
        self._p4 = Paso4Resultados(self._content,
                                    get_paths=lambda: self._p3.get_paths(),
                                    get_maestro=lambda: self._p3.get_maestro_actual(),
                                    get_params=lambda: self._p3.get_params(),
                                    get_productos=lambda: self._p3.get_productos(),
                                    get_p1_paths=lambda: self._p1.get_paths())
        self._pages = [self._p1, self._p2, self._p3, self._p4]

        self._build_footer()

    # ── Header ───────────────────────────────────────────────────────────────

    def _build_header(self):
        h = ctk.CTkFrame(self, fg_color=APPLE_BAR, height=78, corner_radius=0)
        h.pack(fill="x")
        h.pack_propagate(False)

        # Separador inferior
        ctk.CTkFrame(h, fg_color=GRIS_BORDE, height=1, corner_radius=0).pack(
            side="bottom", fill="x")

        brand = ctk.CTkFrame(h, fg_color="transparent")
        brand.pack(side="left", padx=22, pady=11)

        logo = ctk.CTkFrame(brand, fg_color=WU_BLACK, width=172, height=48,
                            corner_radius=10, border_width=1,
                            border_color=GRIS_BORDE)
        logo.pack(side="left")
        logo.pack_propagate(False)

        ctk.CTkLabel(
            logo, text="WESTERN UNION",
            font=("Segoe UI", 16, "bold"),
            text_color=WU_YELLOW,
        ).pack(expand=True)

        brand_text = ctk.CTkFrame(brand, fg_color="transparent")
        brand_text.pack(side="left", padx=14)
        ctk.CTkLabel(brand_text, text="Reposicion de Insumos",
                     font=("Segoe UI", 15, "bold"),
                     text_color=NEGRO).pack(anchor="w")
        ctk.CTkLabel(brand_text, text="Argentina",
                     font=("Segoe UI", 11),
                     text_color=GRIS_TEXTO).pack(anchor="w", pady=(2, 0))

        self._modo_selector = ctk.CTkSegmentedButton(
            h,
            values=["Dia", "Noche"],
            variable=self._modo_var,
            command=self._cambiar_modo,
            fg_color=APPLE_FILL,
            selected_color=APPLE_SELECTED,
            selected_hover_color=APPLE_SELECTED,
            unselected_color=APPLE_FILL,
            unselected_hover_color=APPLE_HOVER,
            text_color=NEGRO,
            width=156,
            height=36,
            corner_radius=18,
            font=("Segoe UI", 11),
        )
        self._modo_selector.pack(side="right", padx=22, pady=16)

    # ── Indicador de pasos ────────────────────────────────────────────────────

    def _build_indicador(self):
        bar = ctk.CTkFrame(self, fg_color=APPLE_BAR, height=88, corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        ctk.CTkFrame(bar, fg_color=GRIS_BORDE, height=1, corner_radius=0).pack(
            side="bottom", fill="x")

        self._indicador = IndicadorPasos(bar, _PASOS)
        self._indicador.place(relx=0.5, rely=0.48, anchor="center")

    # ── Footer con navegación ─────────────────────────────────────────────────

    def _build_footer(self):
        foot = ctk.CTkFrame(self, fg_color=GRIS_BG, height=70, corner_radius=0)
        foot.pack(fill="x", side="bottom")
        foot.pack_propagate(False)

        self._btn_ant = ctk.CTkButton(
            foot, text="← Anterior",
            fg_color=APPLE_FILL, hover_color=APPLE_HOVER,
            text_color=NEGRO, font=("Segoe UI", 12),
            border_width=1, border_color=GRIS_BORDE,
            width=150, height=42, corner_radius=21,
            command=self._anterior,
        )
        self._btn_ant.pack(side="left", padx=20, pady=12)

        self._btn_sig = ctk.CTkButton(
            foot, text="Siguiente →",
            fg_color=AMARILLO, hover_color=AMARILLO_DARK,
            text_color="#FFFFFF", font=("Segoe UI", 12, "bold"),
            width=180, height=42, corner_radius=21,
            command=self._siguiente,
        )
        self._btn_sig.pack(side="right", padx=20, pady=12)

    # ════════════════════════════════════════════════════════════════════════
    # Navegación
    # ════════════════════════════════════════════════════════════════════════

    def _ir_paso(self, n):
        for p in self._pages:
            p.pack_forget()
        self._pages[n].pack(fill="both", expand=True)
        self._paso_actual = n
        self._indicador.set_paso(n)
        self._actualizar_nav()

        # Notificar al paso que es visible
        if hasattr(self._pages[n], "on_mostrar"):
            self._pages[n].on_mostrar()

    def _anterior(self):
        if self._paso_actual > 0:
            self._ir_paso(self._paso_actual - 1)

    def _siguiente(self):
        if self._paso_actual < len(self._pages) - 1:
            self._ir_paso(self._paso_actual + 1)

    def _actualizar_nav(self):
        n = self._paso_actual

        # Botón Anterior
        if n == 0:
            self._btn_ant.configure(state="disabled",
                                    fg_color=APPLE_FILL, text_color=GRIS_BORDE)
        else:
            self._btn_ant.configure(state="normal",
                                    fg_color=APPLE_FILL, text_color=NEGRO)

        # Botón Siguiente
        if n == 0:
            loaded = len(self._p1.get_paths())
            if loaded == _N_CONSUMO:
                self._btn_sig.configure(
                    state="normal", fg_color=AMARILLO,
                    text_color="#FFFFFF", text="Siguiente →")
            else:
                self._btn_sig.configure(
                    state="disabled", fg_color=APPLE_FILL,
                    text_color=GRIS_TEXTO,
                    text=f"Cargar archivos  ({loaded}/{_N_CONSUMO})")

        elif n == 1:
            if self._df_maestro_repo is not None:
                self._btn_sig.configure(
                    state="normal", fg_color=AMARILLO,
                    text_color="#FFFFFF", text="Ir a Reposición →")
            else:
                self._btn_sig.configure(
                    state="disabled", fg_color=APPLE_FILL,
                    text_color=GRIS_TEXTO, text="Calcular consumo primero")

        elif n == 2:
            loaded = len(self._p3.get_paths())
            if loaded >= _N_REPOSICION:
                self._btn_sig.configure(
                    state="normal", fg_color=AMARILLO,
                    text_color="#FFFFFF", text="Calcular Pedidos →")
            else:
                self._btn_sig.configure(
                    state="disabled", fg_color=APPLE_FILL,
                    text_color=GRIS_TEXTO,
                    text=f"Cargar archivos  ({loaded}/{_N_REPOSICION})")

        else:
            self._btn_sig.configure(
                state="disabled", fg_color=APPLE_FILL,
                text_color=GRIS_TEXTO, text="Finalizado")

    # ════════════════════════════════════════════════════════════════════════
    # Callbacks entre pasos
    # ════════════════════════════════════════════════════════════════════════

    def _cambiar_modo(self, valor):
        set_modo_apariencia("dark" if valor == "Noche" else "light")
        TablaWidget.refrescar_todas()
        self._actualizar_nav()

    def _on_archivos_consumo_change(self, n_loaded):
        if self._paso_actual == 0:
            self._actualizar_nav()

    def _on_consumo_calculado(self, df_tiv, df_maestro, df_maestro_repo):
        self._df_tiv = df_tiv
        self._df_maestro = df_maestro
        self._df_maestro_repo = df_maestro_repo
        # Mover el libro XLSX a Data_old ahora que el cálculo fue exitoso
        try:
            self._p1.archivar_libro()
        except Exception as exc:
            mostrar_dialogo(
                self, "advertencia", "No se pudo archivar el libro",
                f"El consumo se calculó correctamente, pero el archivo de origen no se "
                f"pudo mover a Data_old (¿está abierto en Excel?):\n\n{exc}",
            )
        if self._paso_actual == 1:
            self._actualizar_nav()

    def _on_archivos_repo_change(self, n_loaded):
        if self._paso_actual == 2:
            self._actualizar_nav()
