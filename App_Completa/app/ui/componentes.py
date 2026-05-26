import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from .estilos import (AMARILLO, NEGRO, BLANCO, GRIS_BG, GRIS_BORDE,
                      GRIS_TEXTO, GRIS_DARK, VERDE, VERDE_BG, ROJO, ROJO_BG,
                      FONT_SMALL, aplicar_estilo_tabla)


class TablaWidget(ctk.CTkFrame):
    """Treeview con scrollbars integrado en un CTkFrame."""

    def __init__(self, parent, columnas, anchos=None, **kwargs):
        kwargs.setdefault("fg_color", BLANCO)
        kwargs.setdefault("corner_radius", 10)
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
            self.tree.heading(col, text=col,
                              command=lambda c=col: self._ordenar(c, False))
            self.tree.column(col, width=w, minwidth=60, anchor="w")

        self.tree.tag_configure("par",    background=BLANCO)
        self.tree.tag_configure("impar",  background="#F8FAFC")
        self.tree.tag_configure("rojo",   background=ROJO_BG,  foreground=ROJO)
        self.tree.tag_configure("verde",  background=VERDE_BG, foreground=VERDE)

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
        self.configure(width=128)

        ctk.CTkLabel(self, text=label, font=("Segoe UI", 10),
                     text_color=GRIS_TEXTO,
                     justify="center", wraplength=124).pack(pady=(14, 4))

        self._var = tk.StringVar(value="—")
        ctk.CTkLabel(self, textvariable=self._var,
                     font=("Segoe UI", 18, "bold"),
                     text_color=NEGRO,
                     justify="center").pack(pady=(0, 14))

    def set(self, value):
        self._var.set(value)


class IndicadorPasos(ctk.CTkFrame):
    """Barra de progreso de pasos al estilo wizard."""

    def __init__(self, parent, pasos, **kwargs):
        kwargs.setdefault("fg_color", NEGRO)
        super().__init__(parent, **kwargs)

        self._pasos    = pasos
        self._circulos = []
        self._labels   = []
        self._lineas   = []

        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(expand=True)

        for i, nombre in enumerate(pasos):
            if i > 0:
                ln = ctk.CTkFrame(wrap, width=100, height=2, fg_color="#555555")
                ln.pack(side="left", pady=0)
                self._lineas.append(ln)

            col = ctk.CTkFrame(wrap, fg_color="transparent")
            col.pack(side="left", padx=8, pady=10)

            circle = ctk.CTkLabel(
                col, text=str(i + 1), width=40, height=40,
                corner_radius=20,
                fg_color="#444444", text_color="#888888",
                font=("Segoe UI", 12, "bold"),
            )
            circle.pack()
            self._circulos.append(circle)

            lbl = ctk.CTkLabel(col, text=nombre, font=("Segoe UI", 10),
                               text_color="#888888")
            lbl.pack()
            self._labels.append(lbl)

    def set_paso(self, paso):
        for i, (circle, lbl) in enumerate(zip(self._circulos, self._labels)):
            if i < paso:
                circle.configure(fg_color=VERDE, text_color=BLANCO)
                lbl.configure(text_color=VERDE)
            elif i == paso:
                circle.configure(fg_color=AMARILLO, text_color=NEGRO)
                lbl.configure(text_color=AMARILLO)
            else:
                circle.configure(fg_color="#444444", text_color="#888888")
                lbl.configure(text_color="#888888")
