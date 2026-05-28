import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from .estilos import (AMARILLO, NEGRO, BLANCO, GRIS_BG, GRIS_BORDE,
                      GRIS_TEXTO, GRIS_DARK, VERDE, VERDE_BG, ROJO, ROJO_BG,
                      NARANJA, AZUL_INFO, APPLE_BAR, APPLE_HOVER, APPLE_FILL,
                      TABLA_IMPAR, aplicar_estilo_tabla, color_actual)


class TablaWidget(ctk.CTkFrame):
    """Treeview con scrollbars integrado en un CTkFrame."""
    _instancias = []

    def __init__(self, parent, columnas, anchos=None, **kwargs):
        kwargs.setdefault("fg_color", BLANCO)
        kwargs.setdefault("corner_radius", 8)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", GRIS_BORDE)
        super().__init__(parent, **kwargs)

        self._columnas = columnas
        style = ttk.Style()
        aplicar_estilo_tabla(style)

        # Scrollbars
        sb_v = ttk.Scrollbar(self, orient="vertical")
        sb_h = ttk.Scrollbar(self, orient="horizontal")
        sb_v.pack(side="right",  fill="y")
        sb_h.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(
            self,
            columns=columnas,
            show="headings",
            style="App.Treeview",
            height=7,
            yscrollcommand=sb_v.set,
            xscrollcommand=sb_h.set,
        )
        self.tree.pack(fill="both", expand=True)
        sb_v.config(command=self.tree.yview)
        sb_h.config(command=self.tree.xview)

        anchos = anchos or {}
        for col in columnas:
            w = anchos.get(col, 110)
            self.tree.heading(col, text=col, anchor="w",
                              command=lambda c=col: self._ordenar(c, False))
            self.tree.column(col, width=w, minwidth=60, anchor="w")

        self._aplicar_tags()
        self._instancias.append(self)

    def _aplicar_tags(self):
        self.tree.tag_configure("par",    background=color_actual(BLANCO))
        self.tree.tag_configure("impar",  background=color_actual(TABLA_IMPAR))
        self.tree.tag_configure("rojo",   background=color_actual(ROJO_BG),  foreground=ROJO)
        self.tree.tag_configure("verde",  background=color_actual(VERDE_BG), foreground=VERDE)

    @classmethod
    def refrescar_todas(cls):
        aplicar_estilo_tabla(ttk.Style())
        for tabla in list(cls._instancias):
            try:
                tabla._aplicar_tags()
            except tk.TclError:
                cls._instancias.remove(tabla)

    def cargar(self, filas):
        """filas: lista de tuplas con los valores en el orden de columnas."""
        self.tree.delete(*self.tree.get_children())
        for i, fila in enumerate(filas):
            tag = "par" if i % 2 == 0 else "impar"
            self.tree.insert("", "end", values=fila, tags=(tag,))

    def cargar_df(self, df, fmt_num=None):
        """Carga directamente desde un DataFrame; fmt_num: dict col→formato."""
        fmt_num = fmt_num or {}
        filas = []
        for _, row in df.iterrows():
            fila = []
            for col in self._columnas:
                val = row.get(col, "")
                if col in fmt_num and val != "":
                    try:
                        val = fmt_num[col].format(float(val))
                    except (ValueError, TypeError):
                        pass
                fila.append(val)
            filas.append(tuple(fila))
        self.cargar(filas)

    def marcar_fila(self, iid, tag):
        self.tree.item(iid, tags=(tag,))

    def _ordenar(self, col, reverso):
        datos = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            datos.sort(key=lambda t: float(t[0].replace(",", "")), reverse=reverso)
        except ValueError:
            datos.sort(reverse=reverso)
        for i, (_, k) in enumerate(datos):
            self.tree.move(k, "", i)
            tag = "par" if i % 2 == 0 else "impar"
            curr = list(self.tree.item(k, "tags"))
            curr = [t for t in curr if t not in ("par", "impar")]
            self.tree.item(k, tags=tuple(curr) + (tag,))
        self.tree.heading(col, command=lambda: self._ordenar(col, not reverso))


class PanelMetrica(ctk.CTkFrame):
    """Tarjeta pequeña para mostrar una métrica con etiqueta y valor."""

    def __init__(self, parent, label, **kwargs):
        kwargs.setdefault("fg_color", BLANCO)
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", GRIS_BORDE)
        super().__init__(parent, **kwargs)
        self.configure(width=132, height=86)
        self.pack_propagate(False)
        self.grid_propagate(False)

        ctk.CTkFrame(self, fg_color=AMARILLO, height=3,
                     corner_radius=2).pack(fill="x", padx=12, pady=(10, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(8, 10))

        ctk.CTkLabel(body, text=label.upper(), font=("Segoe UI", 9, "bold"),
                     text_color=GRIS_TEXTO,
                     justify="left", anchor="w",
                     wraplength=108).pack(fill="x")

        self._var = tk.StringVar(value="—")
        ctk.CTkLabel(body, textvariable=self._var,
                     font=("Segoe UI", 19, "bold"),
                     text_color=NEGRO,
                     justify="left", anchor="w").pack(fill="x", pady=(5, 0))

    def set(self, value):
        self._var.set(value)


class IndicadorPasos(ctk.CTkFrame):
    """Barra de progreso de pasos al estilo wizard."""

    def __init__(self, parent, pasos, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("corner_radius", 0)
        super().__init__(parent, **kwargs)

        self._pasos    = pasos
        self._circulos = []
        self._labels   = []
        self._lineas   = []

        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(expand=True, padx=18, pady=6)

        for i, nombre in enumerate(pasos):
            if i > 0:
                ln = ctk.CTkFrame(wrap, width=112, height=2, fg_color=GRIS_BORDE)
                ln.pack(side="left", padx=2, pady=(0, 22))
                self._lineas.append(ln)

            col = ctk.CTkFrame(wrap, fg_color="transparent")
            col.pack(side="left", padx=4, pady=0)

            circle = ctk.CTkLabel(
                col, text=str(i + 1), width=34, height=34,
                corner_radius=17,
                fg_color=APPLE_FILL, text_color=GRIS_TEXTO,
                font=("Segoe UI", 12, "bold"),
            )
            circle.pack()
            self._circulos.append(circle)

            lbl = ctk.CTkLabel(col, text=nombre, font=("Segoe UI", 11),
                               text_color=GRIS_TEXTO)
            lbl.pack(pady=(6, 0))
            self._labels.append(lbl)

    def set_paso(self, paso):
        for i, (circle, lbl) in enumerate(zip(self._circulos, self._labels)):
            if i < paso:
                circle.configure(fg_color=VERDE, text_color="#FFFFFF")
                lbl.configure(text_color=VERDE, font=("Segoe UI", 11, "bold"))
            elif i == paso:
                circle.configure(fg_color=AMARILLO, text_color="#FFFFFF")
                lbl.configure(text_color=AMARILLO, font=("Segoe UI", 11, "bold"))
            else:
                circle.configure(fg_color=APPLE_FILL, text_color=GRIS_TEXTO)
                lbl.configure(text_color=GRIS_TEXTO, font=("Segoe UI", 11))

        for i, line in enumerate(self._lineas):
            line.configure(fg_color=VERDE if i < paso else GRIS_BORDE)


# ── Diálogos estilo Apple ─────────────────────────────────────────────────────

_DIALOG_CFG = {
    "error":       (ROJO,      "#FEF2F2", "x"),
    "advertencia": (NARANJA,   "#FFF7ED", "!"),
    "info":        (AZUL_INFO, "#EFF6FF",  "i"),
    "pregunta":    (GRIS_DARK, GRIS_BG,   "?"),
}


def _centrar(win, parent):
    win.update_idletasks()
    root = parent.winfo_toplevel()
    w = win.winfo_reqwidth()
    h = win.winfo_reqheight()
    x = root.winfo_rootx() + (root.winfo_width()  - w) // 2
    y = root.winfo_rooty() + (root.winfo_height() - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")
    win.deiconify()
    win.lift()
    win.focus_force()
    win.grab_set()


def _base_win(parent, ancho=500):
    win = ctk.CTkToplevel(parent)
    win.withdraw()
    win.title("")
    win.minsize(ancho, 0)
    win.resizable(False, False)
    win.configure(fg_color=BLANCO)
    return win


def _badge(parent, simbolo, color_ic, bg_ic):
    return ctk.CTkLabel(
        parent, text=simbolo, width=38, height=38,
        corner_radius=8,
        fg_color=bg_ic, text_color=color_ic,
        font=("Segoe UI", 15, "bold"),
    )


def _btn(parent, texto, comando, primario=True):
    if primario:
        return ctk.CTkButton(
            parent, text=texto, command=comando,
            fg_color=AMARILLO, text_color="#FFFFFF", hover_color="#285F88",
            width=96, height=34, corner_radius=8,
            font=("Segoe UI", 12),
        )
    return ctk.CTkButton(
        parent, text=texto, command=comando,
        fg_color="transparent", text_color=GRIS_DARK,
        hover_color=APPLE_HOVER, border_width=1, border_color=GRIS_BORDE,
        width=96, height=34, corner_radius=8,
        font=("Segoe UI", 12),
    )


def mostrar_dialogo(parent, tipo, titulo, cuerpo, *, copiable=False):
    """Diálogo informativo o de error estilo Apple.
    tipo: 'error' | 'advertencia' | 'info'
    """
    color_ic, bg_ic, simbolo = _DIALOG_CFG.get(tipo, _DIALOG_CFG["info"])

    win = _base_win(parent)

    # Cabecera
    cab = ctk.CTkFrame(win, fg_color=BLANCO)
    cab.pack(fill="x", padx=24, pady=(24, 0))
    _badge(cab, simbolo, color_ic, bg_ic).pack(side="left", anchor="n")
    ctk.CTkLabel(
        cab, text=titulo,
        font=("Segoe UI", 14, "bold"),
        text_color=NEGRO, anchor="w",
        wraplength=390, justify="left",
    ).pack(side="left", padx=12, fill="x", expand=True)

    # Cuerpo
    n_lineas = cuerpo.count("\n") + 1
    h_txt = max(72, min(220, n_lineas * 22 + 48))
    txt = ctk.CTkTextbox(
        win,
        font=("Segoe UI", 12),
        text_color=GRIS_DARK,
        fg_color=APPLE_FILL,
        corner_radius=8, border_width=0,
        wrap="word", height=h_txt,
        activate_scrollbars=True,
    )
    txt.pack(fill="x", padx=24, pady=16)
    txt.insert("1.0", cuerpo)
    txt.configure(state="disabled")

    # Botones
    bar = ctk.CTkFrame(win, fg_color=BLANCO)
    bar.pack(fill="x", padx=24, pady=(0, 24))
    if copiable:
        def _copiar():
            win.clipboard_clear()
            win.clipboard_append(cuerpo)
        _btn(bar, "Copiar", _copiar, primario=False).pack(side="left")
    _btn(bar, "Cerrar", win.destroy).pack(side="right")

    win.after(80, lambda: _centrar(win, parent))
    parent.wait_window(win)


def confirmar(parent, titulo, mensaje,
              texto_ok="Confirmar", texto_cancel="Cancelar"):
    """Diálogo de confirmación estilo Apple. Retorna True si el usuario confirma."""
    resultado = [False]
    color_ic, bg_ic, simbolo = _DIALOG_CFG["pregunta"]

    win = _base_win(parent, ancho=420)

    # Cabecera
    cab = ctk.CTkFrame(win, fg_color=BLANCO)
    cab.pack(fill="x", padx=24, pady=(24, 0))
    _badge(cab, simbolo, color_ic, bg_ic).pack(side="left", anchor="n")
    ctk.CTkLabel(
        cab, text=titulo,
        font=("Segoe UI", 14, "bold"),
        text_color=NEGRO, anchor="w",
        wraplength=320, justify="left",
    ).pack(side="left", padx=12)

    # Mensaje
    ctk.CTkLabel(
        win, text=mensaje,
        font=("Segoe UI", 12),
        text_color=GRIS_DARK,
        wraplength=372, justify="left", anchor="w",
    ).pack(fill="x", padx=24, pady=20)

    # Botones
    bar = ctk.CTkFrame(win, fg_color=BLANCO)
    bar.pack(fill="x", padx=24, pady=(0, 24))

    def _ok():
        resultado[0] = True
        win.destroy()

    _btn(bar, texto_ok,     _ok,          primario=True ).pack(side="right")
    _btn(bar, texto_cancel, win.destroy,  primario=False).pack(side="right", padx=(0, 8))

    win.after(80, lambda: _centrar(win, parent))
    parent.wait_window(win)
    return resultado[0]
