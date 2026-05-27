# App Reposición de Insumos — Western Union Argentina

Aplicación de escritorio para calcular el consumo mensual de insumos y generar los pedidos de reposición de agentes Western Union Argentina.

---

## Requisitos

- **Windows 10 / 11**
- **Python 3.9 o superior** — [descargar en python.org](https://www.python.org/downloads/)
  - Durante la instalación marcar **"Add python.exe to PATH"**

---

## Cómo ejecutar

1. Abrir la carpeta raíz del repositorio (donde está `Ejecutar_App_Completa.bat`)
2. Hacer doble clic en **`Ejecutar_App_Completa.bat`**

El script:
- Detecta Python automáticamente
- Crea un entorno virtual aislado en `App_Completa/.venv` (solo la primera vez)
- Instala todas las dependencias necesarias
- Abre la aplicación

No se necesita instalar nada manualmente.

---

## Estructura de carpetas de trabajo

Dentro de `App_Completa/`:

```
Data/              ← Pegar aquí los archivos del mes antes de procesar
Maestro_Consumo/   ← Maestros mensuales (input/output del Paso 2)
Data_OLD/          ← Archivos procesados (se mueven automáticamente al finalizar)
```

---

## Archivos necesarios para el Paso 1 (Consumo)

Colocar en `Data/` con cualquier nombre que contenga las palabras clave:

| Archivo | Palabras clave en el nombre |
|---|---|
| TIV | `tiv`, `tiv_final` |
| Maestro Consumo | se toma de `Maestro_Consumo/` automáticamente |
| FAC. TERMICAS | `fac_termicas`, `factermicas` |
| DSP / KYC | `dsp_kyc`, `dsp` |
| COM TX INT | `com_tx_int` |
| PRISMA (envíos) | `prisma` |
| SUBE (envíos) | `sube` |
| ROLLO (envíos) | `rollo`, `rollos` |
| TRX SUBE | `trx_sube` |
| RESMA (envíos) | `resma` |
| FAJAS | `fajas` |

Formatos soportados: `.xlsx`, `.xls`, `.csv` (separador `,` o `;`).

---

## Dependencias

Instaladas automáticamente por el `.bat`:

```
customtkinter >= 5.2.0
pandas        >= 2.0.0
numpy         >= 1.24.0
openpyxl      >= 3.1.0
xlrd          >= 2.0.0
```
