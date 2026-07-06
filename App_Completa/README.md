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

## Flujo de la app (4 pasos)

1. **Consumo** — cargar los 11 archivos del mes (ver tabla abajo) y calcular el consumo por agente.
2. **Cálculo de Consumo** — revisar métricas y tablas de resultado; se guarda automáticamente el MaestroStock del mes en `Maestro_Consumo/`.
3. **Reposición** — cargar el maestro actual + 3 meses históricos y ajustar parámetros/productos si hace falta.
4. **Pedidos** — calcular la reposición y exportar `REPOSICION_FINAL.xlsx` (pedido) y `REPOSICION_DETALLADO.xlsx` (todas las columnas intermedias del cálculo).

Documentación completa de la lógica de cálculo, reglas de negocio y formatos de archivo: [`docs/APP_REPOSICION.md`](../docs/APP_REPOSICION.md). Casos de prueba funcionales: [`docs/CASOS_DE_PRUEBA.md`](../docs/CASOS_DE_PRUEBA.md).

---

## Carpeta `backup/`

Contiene la versión anterior de la app: un script suelto (`repo_con_segmento_para_eliminar_agentes_v9.2.py`) que hacía manualmente lo que hoy automatizan los Pasos 3 y 4. Se conserva como referencia histórica, no como fuente de verdad — ver ["Comparación con el script legacy"](../docs/APP_REPOSICION.md#comparación-con-el-script-legacy-backuprepo_con_segmento_para_eliminar_agentes_v92py) en la documentación completa para un caso concreto donde ese script dio resultados incorrectos por no normalizar el tipo de dato del ID de agente entre archivos.

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
