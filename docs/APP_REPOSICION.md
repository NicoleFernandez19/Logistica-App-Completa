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

**Auto-detección:** busca en `Data/` por substring en el nombre del archivo. El orden de detección garantiza que `trx_sube` tiene prioridad sobre `sube` para evitar asignaciones incorrectas. Cada archivo solo puede asignarse a un slot (pool sin reemplazo).

### Paso 2 — Cálculo de Consumo

Ejecuta las fórmulas de consumo sobre los archivos del Paso 1 y muestra métricas y tablas de resultado. Al terminar, guarda automáticamente el MaestroStock en `Maestro_Consumo/MAESTRO_CONSUMO_ENVIO_{MES}_{AÑO}.xlsx`. Si ya existe un archivo con ese nombre, se crea un backup con sufijo `_anterior` antes de sobreescribir.

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
4. Si `SUBSEGMENTACION` quedó en 0 (celda vacía), se reemplaza por 1 para no anular la reposición.

### Stock ajustado (proyección al momento de entrega)

```
STOCK_ROLLO  −= ROLLO_m3    (consumo M-1 como proxy del mes en curso)
STOCK_PRISMA −= ROLLO PRISMA_m3
STOCK_SUBE   −= ROLLO SUBE_m3

RESETEO_ROLLO  = max(STOCK_ROLLO,  0)
RESETEO_PRISMA = max(STOCK_PRISMA, 0)
RESETEO_SUBE   = max(STOCK_SUBE,   0)
```

> El RESETEO representa el stock que el agente va a tener disponible cuando llegue el próximo pedido. Se descuenta del cálculo de reposición para no sobre-stockear.

### Regresión lineal (método "regresion")

Con los tres puntos históricos (x=1,2,3):

```
promedio   = (m1 + m2 + m3) / 3
pendiente  = (m3 − m1) / 2
ordenada   = promedio − pendiente × 2
prediccion = pendiente × 4 + ordenada   ← proyección mes 4

repo = si pendiente ≤ 0 → (promedio × SUBSEGMENTACION × factor) − RESETEO
       si pendiente > 0 → (prediccion × SUBSEGMENTACION × factor) − RESETEO
```

Si la tendencia es descendente o plana se usa el promedio (conservador). Si es ascendente se usa la proyección (anticipa mayor demanda).

### Otros métodos

- **promedio**: `(m1+m2+m3)/3 × SUBSEGMENTACION × factor`
- **promedio\_ajustado\_dep**: igual al promedio con ceil, pero fuerza 0 si `DEP == 1` (agentes dependientes no reciben ese producto)

### Redondeo

```
fracción = valor − floor(valor)
resultado = floor(valor) si fracción ≤ umbral
            ceil(valor)  si fracción > umbral
```

Umbral por producto: 0.3 para rollos térmicos, 0.2 para Prisma, 0.3 para SUBE.

### Canal Propio

Los agentes listados en el archivo de agentes Canal Propio reciben la cantidad calculada multiplicada por `ajuste_canal_propio` (default 0.82) **solo para los SKUs configurados** en `REGLAS.skus_ajuste_canal_propio` (actualmente 9001222100 y 9001222101).

### Normalización de IDs

Todos los `ID P.F` / `ID_PF` se normalizan con `strip()` + eliminación de guiones (`-`) antes de cualquier join o comparación. Esto incluye los IDs del maestro actual, los históricos y el archivo de agentes Canal Propio.

---

## Reglas de negocio

### Separación por provincia (MENDOZA)

El producto **ROLLO TERMICO** (SKU 9001222100) excluye agentes con `PROV = "MENDOZA"` (`prov_excluir`). El producto **ROLLO TERMICO MZA** (SKU 9001222101) incluye solo agentes de Mendoza (`prov_filter`). Esto garantiza que cada agente recibe el SKU logístico correcto según su ubicación.

### SUBSEGMENTACION como multiplicador

`SUBSEGMENTACION` funciona como un multiplicador de la reposición base. Permite ajustar la cantidad a reponer según el volumen relativo del punto de venta dentro del segmento. Si el campo viene vacío o en 0, se trata como 1 (valor neutro) para no anular la reposición del agente.

### DEP (Agentes Dependientes)

Los agentes con `DEP = 1` son dependientes de otro punto de venta. En productos con método `promedio_ajustado_dep`, reciben reposición 0 porque el insumo se gestiona desde el punto principal.

### Agentes sin TIV

Un agente que no aparece en el TIV del mes (sin transacciones) no recibe insumos en el cálculo de consumo, pero sí puede recibir reposición si tiene consumo histórico en los 3 meses anteriores.

### Stock negativo

Si el stock calculado resulta negativo (el agente recibió menos insumos de los que consumió), `RESETEO` se fija en 0. El agente recibe la reposición completa sin descuento de stock.

### Archivado automático

Al finalizar el Paso 4 exitosamente, todos los archivos de `Data/` que fueron usados como entrada se mueven a `Data_OLD/` con el formato `<nombre>_YYYYMMDD.<ext>`. Esto evita reutilizar archivos del mes anterior en el siguiente ciclo.

### Backup del MaestroStock

Al guardar el MaestroStock al final del Paso 2, si ya existe un archivo con el mismo nombre en `Maestro_Consumo/`, se crea un backup con sufijo `_anterior` antes de sobreescribirlo.

---

## Productos configurados (`config.py`)

| SKU | Descripción | Método | Factor | Redondeo |
|---|---|---|---|---|
| 9001222100 | ROLLO TERMICO PF-WU x5 (excluye Mendoza) | regresion | 1.1 | 0.3 |
| 9001222101 | ROLLO TERMICO MZA PF-WU x5 (solo Mendoza) | regresion | 1.1 | 0.3 |
| 9001219112 | BOLSA RECOLECCION x1 | promedio | — | — |
| 9001223489 | ROLLO TERMICO DEBITO PRISMA x5 | regresion | — | 0.2 |
| 9001214102 | ROLLO TERMICOS SUBE x5 | regresion | — | 0.3 |
| 9001000000 | RESMA A4 (SKU/descripción placeholder, pendiente de reemplazar por el real) | regresion | — | 0.3 |

---

## Archivos de entrada — formatos esperados

### TIV
Columnas requeridas: `ID_PF`, al menos una de `BP + TU` / `BP+TU`, `TX IMT OB`, `TX IMT IB`, `TX DMT OB`, `TX DMT IB`, `PRISMA CI`, `PRISMA CO`. Opcionales: `TX_QCASH`, `TXS S/FAC`. Si alguna columna de transacciones está ausente, se asigna 0 automáticamente.

### Maestro Consumo
Columnas requeridas: `ID P.F` (o `ID_PF`). Opcionales: `NOMBRE FANTASIA`, `STOCK ROLLO`, `STOCK SUBE`, `STOCK PRISMA`, `STOCK RESMA`, `PROV`, `DEP`, `SEGMENTO`, `SUBSEGMENTACION`. Acepta variantes con guion bajo (`STOCK_ROLLO`) y con sufijo (`STOCK_ROLLO_MES ANTERIOR`).

### Envíos (PRISMA, SUBE, ROLLO, RESMA)
Columnas: `AGENTE`, `CANTIDAD`. Se agrupa por `AGENTE` con suma (permite múltiples filas por agente).

### TRX SUBE
Columnas: `ID_PF`, `TRX_SUBE`. Se agrupa por `ID_PF` con suma.

### FAC TERMICAS / COM TX INT
Columna requerida: `ID_PF`.

### DSP / KYC
Columnas requeridas: `ID_PF`, `FLAG_DSP`, `FLAG_KYC`.

### FAJAS
Columnas: `ID_PF`, `Qx FAJAS`. La columna `FAJAS` se calcula como `ceil(Qx FAJAS / 200)`.

### Maestros históricos (Paso 3)
Deben tener el formato del MaestroStock exportado por Paso 2 con columna `ID P.F` (o `ID_PF`):
`NOMBRE FANTASIA`, `PROV`, `DEP`, `SEGMENTO`, `SUBSEGMENTACION`, `STOCK ROLLO`, `STOCK SUBE`, `STOCK PRISMA`, `STOCK RESMA`, `TIPO`, `ROLLO`, `BOLSA RECOLECCION`, `ROLLO SUBE`, `ROLLO PRISMA`, `RESMA`, `FAJAS`.

### Agentes Canal Propio
Columna requerida: `ID P.F` (o `ID_PF`). **Este archivo actualmente no afecta el cálculo.** `ejecutar_proceso_reposicion` lo lee y arma una lista de IDs (`lista_agentes_ajuste`) que nunca se vuelve a usar — es código muerto. El ajuste Canal Propio del 18% se decide, igual que en el script legacy, buscando `"C.S."` dentro de `NOMBRE FANTASIA` (ver `logica_reposicion.py`, filtro `filtro_cp`). Cargar o no este archivo en el Paso 3 no cambia ninguna cantidad del resultado.

---

## Formato de archivos CSV

La app soporta automáticamente dos formatos:

| Formato | Separador | Decimal | Miles |
|---|---|---|---|
| Internacional | `,` | `.` | — |
| Argentino/Europeo | `;` | `,` | `.` |

La detección es automática: si el CSV leído con coma produce una sola columna, se reintenta con punto y coma. La distinción entre coma decimal y coma como miles se hace verificando que **todos** los valores con coma tengan exactamente 3 dígitos después (miles), no solo alguno. Esto evita que valores como `1,5` se interpreten incorrectamente como `15`.

---

## Normalización de columnas

- Los nombres de columna se limpian de espacios al inicio y fin (`strip`) en todos los archivos.
- Los IDs (`ID_PF` / `ID P.F`) se normalizan: `strip()` + eliminación de guiones. Esto aplica a TIV, maestro, históricos y agentes Canal Propio.
- Los ID duplicados en TIV, Maestro y DSP/KYC se eliminan conservando la primera ocurrencia; se muestra advertencia en el log.
- Si un archivo tiene columnas con nombres duplicados (ej: `STOCK SUBE` y `STOCK_SUBE` en el mismo archivo), se conserva la primera aparición después del rename.

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
| `factor_ajuste_rollos` | 1.1 | Multiplicador sobre consumo proyectado de rollos. **No editable desde la UI**: es parte fija del modelo de regresión, solo se cambia en `config.py`. |
| `redondeo_rollos` | 0.3 | Umbral de fracción para redondear rollos |
| `redondeo_rollos_prisma` | 0.2 | Umbral de fracción para redondear Prisma |
| `redondeo_rollos_sube` | 0.3 | Umbral de fracción para redondear SUBE |
| `redondeo_resma` | 0.3 | Umbral de fracción para redondear Resma |
| `ajuste_canal_propio` | 0.82 | Factor de reducción para agentes Canal Propio |

El resto de los parámetros son editables en la UI (Paso 3, pestaña Parámetros) sin necesidad de modificar el código.

---

## Comparación con el script legacy (`backup/repo_con_segmento_para_eliminar_agentes_v9.2.py`)

### Por qué los totales pueden dar muy distintos aunque "sean los mismos archivos"

Investigación (2026-07-06): se comparó `REPOSICION_FINAL_App_Actual.xlsx` (app nueva) contra `REPOSICION_FINAL_App_vieja.xlsx` (corrida manual del script legacy), ambos supuestamente generados con los mismos 4 archivos de `backup/` (`CONSUMO_ABRIL_2026.xlsx`, `CONSUMO_MAYO_2026.xlsx`, `CONSUMO_MENSUAL_202607.xlsx` como Junio, `MAESTRO_CONSUMO_ENVIO_SEPTIEMBRE_2026.xlsx`). Los totales por SKU diferían entre 30% y 80%. Se ejecutó el script legacy sin modificar (vía subprocess) con esos mismos archivos y su salida coincidió exactamente con `REPOSICION_FINAL_App_vieja.xlsx` — así que la diferencia no era un archivo mal comparado, era un problema real de cálculo del script legacy.

**Causa encontrada:** la columna `ID P.F` viene guardada con **tipo de celda distinto según el archivo**:

| Archivo | Tipo de celda `ID P.F` |
|---|---|
| `CONSUMO_ABRIL_2026.xlsx` | numérico (Excel "Número") |
| `CONSUMO_MAYO_2026.xlsx` | numérico (Excel "Número") |
| `CONSUMO_MENSUAL_202607.xlsx` (Junio) | texto (Excel "Texto") |
| `MAESTRO_CONSUMO_ENVIO_SEPTIEMBRE_2026.xlsx` | texto (Excel "Texto") |

El script legacy hace `pd.merge(..., on="ID P.F")` sin convertir nada a texto primero. Pandas lee cada columna con el tipo que trae la celda de Excel, así que compara `90001288` (int) contra `'90001288'` (str) — no matchean nunca. El resultado: en la corrida real, **4.941 de 4.942 agentes (99.98%) perdieron el consumo de Abril y Mayo**, quedando en 0 por el `fillna(0)` del script, y la "regresión de 3 meses" terminó calculando en la práctica con `(0, 0, junio)` en vez de los tres meses reales. Esto explica el patrón completo:
- Productos con método **regresión** (ROLLO, ROLLO PRISMA, ROLLO SUBE, RESMA) salían más altos en el legacy: extrapolar una "tendencia" desde `0 → 0 → junio` sobreestima el mes siguiente.
- **BOLSA RECOLECCION** (método promedio simple) salía más bajo: promediar un solo mes real entre tres lo diluye a un tercio.

La app nueva no sufre esto porque normaliza `ID P.F` a texto (`strip()` + eliminación de guiones) **antes** de cualquier merge, en los históricos, el maestro y el archivo de agentes (ver "Normalización de IDs" más arriba).

### En qué casos puede volver a pasar

- Cualquier archivo de consumo/maestro donde `ID P.F` se haya tipeado o pegado como número en Excel (en vez de como texto) mientras otro archivo del mismo cálculo lo tiene como texto. Es común que esto pase solo, por ejemplo al pegar valores con "Pegado especial → Valores" desde otro reporte, o al generar el Excel con una herramienta distinta (Power BI, un export de SQL) que tipa la columna distinto que el resto.
- Cuantos más agentes tengan el ID en un tipo de celda distinto al de los demás archivos del mismo cálculo, mayor la porción del historial que se pierde en silencio — y el error no lanza ninguna advertencia ni excepción, simplemente rellena con 0.
- Esto **solo afecta al script legacy** (o a cualquier código nuevo que vuelva a hacer merges sobre `ID P.F` sin normalizar el tipo primero). No es un riesgo para la app actual mientras la normalización de IDs en `logica_reposicion.py` / `cargador.py` siga aplicándose a todos los archivos de entrada.

### Por qué la app nueva es la referencia válida, y no conviene "bajar" al formato viejo

Podría pensarse que la solución es re-tipear los Excel de Abril/Mayo como texto para que calcen con el formato que el script legacy sí procesa bien. **No es la dirección correcta:**

1. El script legacy solo "funciona" con esos archivos por casualidad de que Abril y Mayo comparten el mismo tipo de celda entre sí — no porque valide o normalice nada. Cualquier archivo futuro con el tipo de celda "equivocado" (numérico en vez de texto, o viceversa) rompe el cálculo otra vez, en silencio, sin aviso.
2. La app nueva no depende de que los archivos de entrada vengan con un tipo de celda particular: normaliza el ID sin importar si Excel lo guardó como número o como texto. Es la versión robusta ante inconsistencias de formato entre archivos generados en momentos o herramientas distintas — que es exactamente lo que pasó acá.
3. Adaptar los archivos de entrada al formato que el script viejo tolera es resolver el síntoma para una corrida puntual, no la causa: el próximo mes, con un archivo nuevo, puede volver a romperse de la misma manera si nadie se acuerda de revisar el tipo de celda a mano.
4. La app nueva ya fue verificada: corriendo su propia lógica (`ejecutar_proceso_reposicion`) sobre los mismos 4 archivos, sus resultados coinciden con los valores reales de consumo de los archivos fuente (verificado fila por fila para agentes puntuales) — el script legacy, en cambio, coincide con datos que en un 99.98% de los casos son 0 donde no deberían serlo.

**Conclusión:** ante una discrepancia entre la app nueva y el script legacy, la app nueva es la fuente confiable por diseño (normaliza IDs), y el script legacy debe tratarse como referencia poco confiable salvo que se verifique explícitamente que todos sus archivos de entrada comparten el mismo tipo de celda en `ID P.F`.

---

## Historial de cambios relevantes

### Robustez y validaciones (mayo 2026)

**`cargador.py`**
- `_leer()`: columnas normalizadas con `str.strip()` en un único punto de retorno. Detección de formato por firma binaria (no solo extensión).
- `_num()`: corrección en detección de coma como miles — se exige que **todos** los valores con coma tengan exactamente 3 dígitos decimales (antes usaba `.any()`, lo que convertía valores decimales como `1,5` en `15`).
- `_validar()`: helper centralizado que lanza `ValueError` descriptivo con nombre de archivo y columnas disponibles cuando falta una columna requerida.
- Todos los `cargar_*`: validación de columnas requeridas mediante `_validar()`. Archivos vacíos (0 filas) lanzan `ValueError` descriptivo.
- `cargar_tiv`: verifica presencia de al menos una columna de transacciones. Columnas ausentes del TIV se inicializan en 0 (degradación graceful).
- `cargar_maestro`: eliminación de columnas duplicadas movida **antes** de `_num()` para evitar crash cuando el archivo tiene `STOCK SUBE` y `STOCK_SUBE` simultáneamente.
- `cargar_tiv`, `cargar_maestro`, `cargar_dsp_kyc`: advertencia en log cuando hay `ID_PF` duplicados.

**`calculos_consumo.py`**
- Todas las columnas de transacciones (`BP_TU`, `TX_QCASH`, `TXS_SIN_FAC`, `TX_IMT_OB`, `TX_IMT_IB`, `TX_DMT_OB`, `TX_DMT_IB`, `PRISMA_CI`, `PRISMA_CO`) se inicializan en 0 si no vienen en el TIV.

**`logica_reposicion.py`**
- Validación de columna `ID P.F` en cada archivo histórico con mensaje descriptivo.
- Normalización de IDs del archivo de agentes Canal Propio (strip + eliminación de guiones) para garantizar coincidencia correcta con los IDs del resultado.
- `SUBSEGMENTACION = 0` se reemplaza por 1 después de la conversión numérica.

**`paso1_carga.py`**
- Auto-detección reescrita con matching por substring y pool sin reemplazo. `trx_sube` tiene prioridad sobre `sube`. Keywords ordenados de más específico a más genérico.

**`paso2_consumo.py`**
- Validación de los 11 archivos requeridos antes de iniciar el cálculo.
- Backup automático del MaestroStock anterior antes de sobreescribir.
- Errores de `ValueError`/`KeyError` se muestran como mensaje limpio sin traceback.

**`paso4_resultados.py`**
- Validación de archivos de consumo histórico y maestro actual antes de iniciar el cálculo.
- Errores de `ValueError`/`KeyError` se muestran como mensaje limpio.

**Limpieza**
- Eliminado `loader.py` (duplicado de `cargador.py`, nunca importado).
- Eliminadas constantes y fuentes sin uso en `config.py`, `estilos.py` y `componentes.py`.
