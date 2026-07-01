import customtkinter as ctk
from tkinter import ttk

# ── Paleta moderna con marca Western Union ────────────────────────────────────
WU_YELLOW     = "#FFDD00"
WU_BLACK      = "#111111"
AMARILLO      = "#2F6F9F"
AMARILLO_DARK = "#285F88"
NEGRO         = ("#1D1D1F", "#F5F5F7")
BLANCO        = ("#FFFFFF", "#1C1C1E")
GRIS_BG       = ("#F6F6F8", "#0B0B0C")
GRIS_PANEL    = ("#FFFFFF", "#1C1C1E")
GRIS_BORDE    = ("#E5E5EA", "#2C2C2E")
GRIS_TEXTO    = ("#6E6E73", "#A1A1A6")
GRIS_DARK     = ("#424245", "#D1D1D6")
VERDE         = "#34C759"
VERDE_BG      = ("#EAF8EE", "#173A24")
ROJO          = "#FF3B30"
ROJO_BG       = ("#FFF1F0", "#3B1715")
NARANJA       = "#FF9500"
AZUL_INFO     = "#2F6F9F"
INFO_BG       = ("#F2F7FF", "#0B223A")
INFO_BORDE    = ("#D6E8FF", "#1D4F7A")
APPLE_BAR     = ("#FBFBFD", "#141416")
APPLE_HOVER   = ("#E9E9ED", "#2F2F31")
APPLE_FILL    = ("#F2F2F7", "#242426")
APPLE_SELECTED = ("#DCEAF3", "#254D6F")
TABLA_IMPAR   = ("#FAFAFC", "#202022")

FONT_SMALL = ("Segoe UI", 11)
FONT_MONO  = ("Consolas", 11)
def configurar_tema():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    ctk.set_widget_scaling(1.04)


def color_actual(color):
    if not isinstance(color, tuple):
        return color
    return color[1] if ctk.get_appearance_mode().lower() == "dark" else color[0]


def set_modo_apariencia(modo):
    ctk.set_appearance_mode(modo)


def aplicar_estilo_tabla(style: ttk.Style):
    """Aplica estilo CTk-compatible a los Treeview."""
    style.theme_use("clam")

    style.configure("App.Treeview",
        background=color_actual(BLANCO),
        foreground=color_actual(NEGRO),
        fieldbackground=color_actual(BLANCO),
        borderwidth=0,
        rowheight=32,
        font=("Segoe UI", 11),
    )
    style.configure("App.Treeview.Heading",
        background=color_actual(APPLE_FILL),
        foreground=color_actual(GRIS_DARK),
        borderwidth=0,
        relief="flat",
        font=("Segoe UI", 11, "bold"),
        padding=(8, 8),
    )
    style.map("App.Treeview",
        background=[("selected", color_actual(APPLE_SELECTED))],
        foreground=[("selected", color_actual(NEGRO))],
    )
    style.map("App.Treeview.Heading",
        background=[("active", color_actual(GRIS_BORDE))],
    )
