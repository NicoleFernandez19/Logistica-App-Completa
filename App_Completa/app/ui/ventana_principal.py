import customtkinter as ctk
from .estilos import configurar_tema, NEGRO, AMARILLO, AMARILLO_DARK, BLANCO, GRIS_BG
from .componentes import IndicadorPasos

_PASOS = ["Archivos\nConsumo", "Consumo", "Archivos\nReposición", "Pedidos"]
_N_CONSUMO     = 11  # archivos requeridos en paso 1
_N_REPOSICION  = 5   # maestro actual + 3 historicos + agentes


class VentanaPrincipal(ctk.CTk):
    def __init__(self):
        configurar_tema()
        super().__init__()

        self.title("Western Union  —  Reposición de Insumos  Argentina")
        self.geometry("1420x880")
        self.minsize(1180, 760)
        self.configure(fg_color=NEGRO)
        self.state("zoomed")

        # ── Estado compartido entre pasos ────────────────────────────────────
        self._df_tiv      = None   # resultado de calcular()
        self._df_maestro  = None   # resultado de calcular()
        self._df_maestro_repo = None  # preparar_maestro_exportable()

        self._paso_actual = 0

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
        h = ctk.CTkFrame(self, fg_color=NEGRO, height=66, corner_radius=0)
        h.pack(fill="x")
        h.pack_propagate(False)

        # Línea amarilla inferior
        ctk.CTkFrame(h, fg_color=AMARILLO, height=3, corner_radius=0).pack(
            side="bottom", fill="x")

        ctk.CTkLabel(h, text="WESTERN UNION",
                     font=("Segoe UI", 20, "bold"),
                     text_color=AMARILLO).pack(side="left", padx=20, pady=8)
        ctk.CTkLabel(h, text="Reposición de Insumos  ·  Argentina",
                     font=("Segoe UI", 12),
                     text_color="#CCCCCC").pack(side="left", padx=4)

    # ── Indicador de pasos ────────────────────────────────────────────────────

    def _build_indicador(self):
        bar = ctk.CTkFrame(self, fg_color=NEGRO, height=86, corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        ctk.CTkFrame(bar, fg_color="#333333", height=1,
                     corner_radius=0).pack(side="bottom", fill="x")

        self._indicador = IndicadorPasos(bar, _PASOS, fg_color="transparent")
        self._indicador.place(relx=0.5, rely=0.5, anchor="center")

    # ── Footer con navegación ─────────────────────────────────────────────────

    def _build_footer(self):
        foot = ctk.CTkFrame(self, fg_color=NEGRO, height=76, corner_radius=0)
        foot.pack(fill="x", side="bottom")
        foot.pack_propagate(False)
        ctk.CTkFrame(foot, fg_color="#333333", height=1,
                     corner_radius=0).pack(side="top", fill="x")

        self._btn_ant = ctk.CTkButton(
            foot, text="← Anterior",
            fg_color="#2D2D2D", hover_color="#404040",
            text_color=BLANCO, font=("Segoe UI", 12),
            width=150, height=46, corner_radius=6,
            command=self._anterior,
        )
        self._btn_ant.pack(side="left", padx=20, pady=12)

        self._btn_sig = ctk.CTkButton(
            foot, text="Siguiente →",
            fg_color=AMARILLO, hover_color=AMARILLO_DARK,
            text_color=NEGRO, font=("Segoe UI", 12, "bold"),
            width=180, height=46, corner_radius=6,
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
                                    fg_color="#1A1A1A", text_color="#555555")
        else:
            self._btn_ant.configure(state="normal",
                                    fg_color="#2D2D2D", text_color=BLANCO)

        # Botón Siguiente
        if n == 0:
            loaded = len(self._p1.get_paths())
            if loaded == _N_CONSUMO:
                self._btn_sig.configure(
                    state="normal", fg_color=AMARILLO,
                    text_color=NEGRO, text="Siguiente →")
            else:
                self._btn_sig.configure(
                    state="disabled", fg_color="#333333",
                    text_color="#666666",
                    text=f"Cargar archivos  ({loaded}/{_N_CONSUMO})")

        elif n == 1:
            if self._df_maestro_repo is not None:
                self._btn_sig.configure(
                    state="normal", fg_color=AMARILLO,
                    text_color=NEGRO, text="Ir a Reposición →")
            else:
                self._btn_sig.configure(
                    state="disabled", fg_color="#333333",
                    text_color="#666666", text="Calcular consumo primero")

        elif n == 2:
            loaded = len(self._p3.get_paths())
            if loaded == _N_REPOSICION:
                self._btn_sig.configure(
                    state="normal", fg_color=AMARILLO,
                    text_color=NEGRO, text="Calcular Pedidos →")
            else:
                self._btn_sig.configure(
                    state="disabled", fg_color="#333333",
                    text_color="#666666",
                    text=f"Cargar archivos  ({loaded}/{_N_REPOSICION})")

        else:
            self._btn_sig.configure(
                state="disabled", fg_color="#333333",
                text_color="#666666", text="Finalizado")

    # ════════════════════════════════════════════════════════════════════════
    # Callbacks entre pasos
    # ════════════════════════════════════════════════════════════════════════

    def _on_archivos_consumo_change(self, n_loaded):
        if self._paso_actual == 0:
            self._actualizar_nav()

    def _on_consumo_calculado(self, df_tiv, df_maestro, df_maestro_repo):
        self._df_tiv = df_tiv
        self._df_maestro = df_maestro
        self._df_maestro_repo = df_maestro_repo
        if self._paso_actual == 1:
            self._actualizar_nav()

    def _on_archivos_repo_change(self, n_loaded):
        if self._paso_actual == 2:
            self._actualizar_nav()
