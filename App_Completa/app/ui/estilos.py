import customtkinter as ctk
from tkinter import ttk

# ── Paleta Western Union ──────────────────────────────────────────────────────
AMARILLO      = "#FFDD00"
AMARILLO_DARK = "#E6C800"
NEGRO         = "#1A1A1A"
BLANCO        = "#FFFFFF"
GRIS_BG       = "#F5F5F7"
GRIS_PANEL    = "#FFFFFF"
GRIS_BORDE    = "#D1D5DB"
GRIS_TEXTO    = "#6B7280"
GRIS_DARK     = "#1F2937"
VERDE         = "#16A34A"
VERDE_BG      = "#DCFCE7"
ROJO          = "#DC2626"
ROJO_BG       = "#FEE2E2"
NARANJA       = "#EA580C"
AZUL_INFO     = "#2563EB"
INFO_BG       = "#F1F5F9"
INFO_BORDE    = "#CBD5E1"

# Fuentes
FONT_TITLE   = ("Segoe UI", 22, "bold")
FONT_HEADING = ("Segoe UI", 15, "bold")
FONT_BODY    = ("Segoe UI", 13)
FONT_SMALL   = ("Segoe UI", 11)
FONT_MONO    = ("Consolas", 11)


def configurar_tema():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    ctk.set_widget_scaling(1.08)


def aplicar_estilo_tabla(style: ttk.Style):
    """Aplica estilo CTk-compatible a los Treeview."""
    style.theme_use("clam")

    style.configure("App.Treeview",
        background=BLANCO,
        foreground=NEGRO,
        fieldbackground=BLANCO,
        borderwidth=0,
        rowheight=34,
        font=("Segoe UI", 11),
    )
    style.configure("App.Treeview.Heading",
        background=GRIS_BG,
        foreground=GRIS_DARK,
        borderwidth=0,
        relief="flat",
        font=("Segoe UI", 11, "bold"),
        padding=(8, 8),
    )
    style.map("App.Treeview",
        background=[("selected", AMARILLO)],
        foreground=[("selected", NEGRO)],
    )
    style.map("App.Treeview.Heading",
        background=[("active", GRIS_BORDE)],
    )
