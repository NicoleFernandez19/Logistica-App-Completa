# App Reposición de Insumos — Western Union Argentina

## Descripción general

Aplicación de escritorio (Python / CustomTkinter) que automatiza el cálculo mensual de consumo de insumos de los agentes Western Union Argentina y genera los pedidos de reposición para el mes siguiente. Reemplaza el proceso manual en Power BI / Excel.

---

## Estructura del proyecto

```
App_Completa/
├── main.pyw                  # Punto de entrada
├── pre_app_check.py          # Verificación de dependencias al arrancar
├── requirements.txt
├── Data/                     # Archivos de entrada del mes (se archivan al finalizar)
├── Data_OLD/                 # Histórico de archivos procesados
├── Data_Test/                # Datos de prueba
├── Maestro_Consumo/          # Maestros mensuales (input y output del Paso 2)
└── app/
    ├── config.py             # Parámetros, reglas y productos configurables
    ├── logic/
    │   ├── cargador.py       # Lectura y normalización de todos los archivos
    │   ├── calculos_consumo.py  # Fórmulas de consumo (replica Power BI)
    │   └── logica_reposicion.py # Regresión lineal y cálculo de pedidos
    └── ui/
        ├── ventana_principal.py  # Ventana raíz, navegación entre pasos
        ├── paso1_carga.py        # Paso 1: carga de archivos de consumo
        ├── paso2_consumo.py      # Paso 2: cálculo y visualización de consumo
        ├── paso3_reposicion.py   # Paso 3: archivos históricos y parámetros
        ├── paso4_resultados.py   # Paso 4: cálculo y exportación de pedidos
        ├── componentes.py        # Widgets reutilizables (tabla, métrica, pasos)
        └── estilos.py            # Paleta de colores y tema Western Union
```

---

## Flujo de trabajo (4 pasos)

### Paso 1 — Archivos de Consumo

El usuario carga 11 archivos de entrada. La app auto-detecta los archivos desde la carpeta `Data/` y el maestro desde `Maestro_Consumo/`.

| Clave | Nombre en UI | Contenido |
|---|---|---|
| `tiv` | TIV | Transacciones del mes por agente |
| `maestro` | MAESTRO CONSUMO | Stock inicial (MaestroStock mes anterior) |
| `fac_termicas` | FAC. TERMICAS | Agentes con factura térmica |
| `dsp_kyc` | DSP / KYC | Flags de habilitación normativa |
| `com_tx_int` | COM TX INT | Agentes con TX internacionales |
| `prisma` | PRISMA | Envíos de rollos Prisma |
| `sube` | SUBE | Envíos de rollos SUBE |
| `rollo_env` | ROLLO (envíos) | Envíos de rollos térmicos |
| `trx_sube` | TRX SUBE | Transacciones SUBE |
| `resma_env` | RESMA (envíos) | Envíos de resmas del mes |
| `fajas` | FAJAS | Cantidad de fajas por agente |

El botón **Siguiente** se habilita únicamente cuando los 11 archivos están cargados.

### Paso 2 — Cálculo de Consumo

Ejecuta las fórmulas de consumo sobre los archivos del Paso 1 y muestra métricas y tablas de resultado. Al terminar, guarda automáticamente el MaestroStock en `Maestro_Consumo/MAESTRO_CONSUMO_ENVIO_{MES}_{AÑO}.xlsx`.

**Métricas mostradas:** Consumo Rollos, Consumo Resmas, Fajas, Bolsas Verdes, Bolsas Magenta, Bolsas Recolección, Rollos Prisma, Rollos SUBE, Stock Rollos, Stock Resmas, Stock SUBE, Stock Prisma.

**Pestañas de resultado:**
- **Consumo Mensual** — consumo normalizado por agente (filtrable por canal)
- **Maestro Stock** — stock final por agente (filtro de negativos)
- **Reconciliación** — consumo vs. envíos vs. stock por producto
- **Sin TIV** — agentes en maestro sin transacciones en el mes
- **Sin Maestro** — agentes con transacciones sin registro en el maestro

### Paso 3 — Archivos de Reposición

Tres pestañas:

**Archivos:** Carga el maestro actual (o usa el generado en Paso 2) + 3 meses históricos (M-1, M-2, M-3) + archivo de agentes Canal Propio. Auto-detección desde `Maestro_Consumo/` por mes/año.

**Productos:** Lista editable de productos a reponer. Cada producto define:
- Columna de consumo histórico base
- Método de cálculo (regresión / promedio / promedio ajustado por DEP)
- Factor de ajuste y umbral de redondeo
- SKU y descripción para el pedido
- Filtros opcionales por provincia (incluir / excluir)

**Parámetros:** Valores numéricos configurables para el cálculo (factor ajuste rollos, umbrales de redondeo, ajuste Canal Propio).

### Paso 4 — Pedidos

Ejecuta el cálculo de reposición en un hilo separado y muestra el resultado en tabla. Permite filtrar por producto. Exporta:
- **Pedidos finales** (`REPOSICION_FINAL.xlsx`) — una fila por agente/SKU con cantidad redondeada
- **Detallado** (`REPOSICION_DETALLADO.xlsx`) — todas las columnas intermedias del cálculo

Al terminar mueve los archivos de `Data/` a `Data_OLD/` con fecha del procesamiento.

---

## Lógica de cálculo de consumo (`calculos_consumo.py`)

### Clasificación de agentes (TIPO\_AGENTE)

| TIPO | Condición |
|---|---|
| 5 | COM TX INT + FAC TERMICA + DSP/KYC |
| 4 | COM TX INT |
| 3 | FAC TERMICA |
| 2 | Canal "Centros y Asistidos" |
| 1 | FLAG\_DSP == 1 |
| 0 | Resto |

### Fórmula BASE (común a todos los tipos)

```
BASE = DMT_IB×49.3 + DMT_OB×100.90
     + (BP_TU − TXS_SIN_FAC)×0.1×11
     + (BP_TU − TXS_SIN_FAC)×0.9×6
     + TXS_SIN_FAC×12
     + PRISMA_CO×9.5
```

### ROLLOS por tipo

| TIPO | DSP | Fórmula |
|---|---|---|
| 0,1,2 | — | BASE / 6900 / 5 |
| 3 | — | (BASE + OB×20) / 6900 / 5 |
| 4 | 0 | (BASE + IB×108 + OB×116) / 6900 / 5 |
| 4 | 1 | (BASE + IB×54 + OB×58) / 6900 / 5 |
| 5 | 0 | (BASE + IB×108 + OB×136) / 6900 / 5 |
| 5 | 1 | (BASE + IB×54 + OB×78) / 6900 / 5 |

### Otros consumos

```
BOLSAS_VERDES      (DSP=0) = (IB×2 + OB×4 + DMT_IB + DMT_OB) / 100
BOLSAS_VERDES      (DSP=1) = (DMT_IB + DMT_OB) / 100
BOLSAS_MAGENTA     (DSP=1, KYC=0) = (IB + OB) / 50
BOLSAS_RECOLECCION = BOLSAS_VERDES + BOLSAS_MAGENTA

ROLLO_SUBE   = (TRX_SUBE × 10 / 2000) / 5
ROLLO_PRISMA = (PRISMA_CI × 4.4 × 2 / 2000) / 5

RESMA (TIPO 0) = (IB×3 + OB×5 + QCASH) / 500
RESMA (TIPO 1) = (IB×1.5 + OB×5 + QCASH) / 500

FAJAS = ceil(Qx_FAJAS / 200)  [desde archivo externo]
```

### Stock final

```
STOCK_ROLLO  = max(STOCK_ROLLO_ANT, 0) + ENVIO_ROLLO  − ROLLOS
STOCK_RESMA  = max(STOCK_RESMA_ANT, 0) + ENVIO_RESMA  − RESMA
STOCK_SUBE   = max(STOCK_SUBE_ANT,  0) + ENVIO_SUBE   − ROLLO_SUBE
STOCK_PRISMA = max(STOCK_PRISMA_ANT,0) + ENVIO_PRISMA − ROLLO_PRISMA

AGENTE_NEGATIVO = (STOCK_ROLLO < 0) OR (STOCK_RESMA < 0)
```

---

## Lógica de reposición (`logica_reposicion.py`)

### Preparación

1. Lee los 3 archivos históricos (M-3, M-2, M-1) y les agrega sufijos `_m1`, `_m2`, `_m3`.
2. Hace outer join de los 3 históricos y luego left join con el maestro actual.
3. Convierte todas las columnas numéricas; rellena NaN con 0.

### Stock ajustado

```
STOCK_ROLLO  −= ROLLO_m3    (consumo M-1 como proxy del mes en curso)
STOCK_PRISMA −= ROLLO PRISMA_m3
STOCK_SUBE   −= ROLLO SUBE_m3

RESETEO_ROLLO  = max(STOCK_ROLLO,  0)
RESETEO_PRISMA = max(STOCK_PRISMA, 0)
RESETEO_SUBE   = max(STOCK_SUBE,   0)
```

### Regresión lineal (método "regresion")

Con los tres puntos históricos (x=1,2,3):

```
promedio  = (m1 + m2 + m3) / 3
pendiente = (m3 − m1) / 2
ordenada  = promedio − pendiente × 2
prediccion = pendiente × 4 + ordenada   ← proyección mes 4

repo = si pendiente ≤ 0 → (promedio × SUB × factor) − RESETEO
       si pendiente > 0 → (prediccion × SUB × factor) − RESETEO
```

### Otros métodos

- **promedio**: `(m1+m2+m3)/3 × SUBSEGMENTACION × factor`
- **promedio\_ajustado\_dep**: igual al promedio con ceil, pero fuerza 0 si DEP == 1

### Canal Propio

Los agentes en el archivo de agentes Canal Propio reciben el cantidad calculada multiplicada por `ajuste_canal_propio` (default 0.82) para los SKUs configurados en `REGLAS`.

### Redondeo

Fracción ≤ umbral → floor; fracción > umbral → ceil. Umbral por producto (0.3 para rollos, 0.2 para Prisma).

---

## Productos configurados (`config.py`)

| SKU | Descripción | Método | Factor |
|---|---|---|---|
| 9001222100 | ROLLO TERMICO PF-WU x5 (sin Mendoza) | regresion | factor\_ajuste\_rollos × 1.1 |
| 9001222101 | ROLLO TERMICO MZA PF-WU x5 | regresion | factor\_ajuste\_rollos × 1.1 |
| 9001219112 | BOLSA RECOLECCION x1 | promedio | — |
| 9001223489 | ROLLO TERMICO DEBITO PRISMA x5 | regresion | — |
| 9001214102 | ROLLO TERMICOS SUBE x5 | regresion | — |

---

## Archivos de entrada — formatos esperados

### TIV
Columnas requeridas: `ID_PF`, `BP + TU` (o `BP+TU`), `TXS S/FAC`, `TX IMT OB`, `TX IMT IB`, `TX DMT OB`, `TX DMT IB`, `PRISMA CI`, `PRISMA CO`. Opcional: `TX QCASH`.

### Maestro Consumo
Columnas requeridas: `ID P.F` (o `ID_PF`), `NOMBRE FANTASIA`, `STOCK ROLLO`, `STOCK SUBE`, `STOCK PRISMA`. Opcional: `STOCK RESMA`, `PROV`, `DEP`, `SEGMENTO`, `SUBSEGMENTACION`.

### Envíos (PRISMA, SUBE, ROLLO, RESMA)
Columnas: `AGENTE`, `CANTIDAD`. Se agrupa por `AGENTE` con suma.

### TRX SUBE
Columnas: `ID_PF`, `TRX_SUBE`. Se agrupa por `ID_PF` con suma.

### FAC TERMICAS / COM TX INT
Columna requerida: `ID_PF`.

### DSP / KYC
Columnas: `ID_PF`, `FLAG_DSP`, `FLAG_KYC`.

### FAJAS
Columnas: `ID_PF`, `Qx FAJAS`.

### Maestros históricos (Paso 3)
Deben tener el formato del MaestroStock exportado por Paso 2:
`ID P.F`, `NOMBRE FANTASIA`, `PROV`, `DEP`, `SEGMENTO`, `SUBSEGMENTACION`, `STOCK ROLLO`, `STOCK SUBE`, `STOCK PRISMA`, `STOCK RESMA`, `TIPO`, `FLAG_DSP_KYC`, `ROLLO`, `BOLSA RECOLECCION`, `ROLLO SUBE`, `ROLLO PRISMA`, `RESMA`, `FAJAS`.

---

## Formato de archivos CSV

La app soporta automáticamente dos formatos:

| Formato | Separador | Decimal | Miles |
|---|---|---|---|
| Internacional | `,` | `.` | — |
| Argentino/Europeo | `;` | `,` | `.` |

La detección es automática: si el CSV leído con coma tiene una sola columna, se reintenta con punto y coma. Si hay `ParserError`, también se reintenta con `;`. Las conversiones numéricas respetan el flag `decimal_coma` almacenado en `df.attrs`.

---

## Convención de nombres — Maestro\_Consumo/

```
MAESTRO_CONSUMO_ENVIO_{MES}_{AÑO}.xlsx
```

El archivo nombrado con el mes M se usa como **stock inicial del mes M**. Es generado automáticamente por el Paso 2 al final de cada cálculo.

Ejemplos:
- `MAESTRO_CONSUMO_ENVIO_MAYO_2026.xlsx` → stock de partida para el cálculo de Mayo
- Al correr Paso 2 en Junio, genera `MAESTRO_CONSUMO_ENVIO_JUNIO_2026.xlsx`

El auto-detector del Paso 1 busca primero el archivo del **mes actual**, luego el mes anterior como fallback.

---

## Dependencias

```
customtkinter
pandas
openpyxl
xlrd
numpy
```

Verificadas al inicio por `pre_app_check.py`. Si falta alguna, muestra instrucciones de instalación.

---

## Parámetros configurables (`config.py`)

| Parámetro | Default | Descripción |
|---|---|---|
| `factor_ajuste_rollos` | 1.1 | Multiplicador sobre consumo proyectado de rollos |
| `redondeo_rollos` | 0.3 | Umbral de fracción para redondear rollos |
| `redondeo_rollos_prisma` | 0.2 | Umbral de fracción para redondear Prisma |
| `redondeo_rollos_sube` | 0.3 | Umbral de fracción para redondear SUBE |
| `ajuste_canal_propio` | 0.82 | Factor de reducción para agentes Canal Propio |

Los parámetros son editables en la UI (Paso 3, pestaña Parámetros) sin necesidad de modificar el código.
