# Documentacion funcional y tecnica de App_Completa

Fecha de revision: 2026-05-26

## Alcance

Este documento describe la aplicacion `App_Completa` sin modificar su codigo. Cubre flujo de uso, archivos de entrada, funciones principales, calculos de consumo, calculos de reposicion, reglas de negocio, parametros, productos, salidas generadas y observaciones de control.

La app integra dos procesos:

- Calculo mensual de consumo y stock final.
- Calculo de pedidos de reposicion usando consumo historico, stock actual y reglas por producto.

## Estructura general

Carpetas y archivos principales:

- `main.pyw`: punto de entrada. Ajusta el path local, verifica dependencias y abre la ventana principal.
- `app/config.py`: parametros, reglas, columnas esperadas, productos y agentes a excluir.
- `app/logic/cargador.py`: lectura y normalizacion de archivos de consumo y reposicion.
- `app/logic/calculos_consumo.py`: formulas de consumo mensual y armado de MaestroStock exportable.
- `app/logic/logica_reposicion.py`: calculo de reposicion historica y armado del pedido final.
- `app/ui/ventana_principal.py`: ventana, estado compartido y navegacion entre pasos.
- `app/ui/paso1_carga.py`: carga de archivos de consumo.
- `app/ui/paso2_consumo.py`: ejecucion y visualizacion del consumo mensual.
- `app/ui/paso3_reposicion.py`: carga de historicos, parametros y productos.
- `app/ui/paso4_resultados.py`: ejecucion de reposicion, log, tabla final y exportacion.
- `app/ui/componentes.py`: widgets reutilizables de tabla, metricas e indicador de pasos.
- `app/ui/estilos.py`: colores, fuentes y tema visual.

## Flujo completo de la app

La interfaz trabaja como asistente de 4 pasos:

1. `Archivos Consumo`: selecciona los 9 archivos necesarios para calcular consumo.
2. `Consumo`: calcula consumo mensual, stock final y MaestroStock.
3. `Archivos Reposicion`: selecciona Maestro Stock Actual, 3 meses historicos y agentes Canal Propio; permite editar parametros y productos.
4. `Pedidos`: calcula reposicion, muestra el pedido final y permite exportar archivos.

El estado principal se guarda en memoria dentro de `VentanaPrincipal`:

- `_df_tiv`: detalle de consumo calculado por agente.
- `_df_maestro`: maestro enriquecido con stock final.
- `_df_maestro_repo`: MaestroStock preparado para el modulo de reposicion.

## Punto de entrada

`main.pyw` realiza estas tareas:

- Agrega la carpeta `App_Completa` al `sys.path`.
- Verifica dependencias: `customtkinter`, `pandas`, `openpyxl`, `numpy`.
- Si falta alguna dependencia, intenta instalarla con `pip`.
- Importa `VentanaPrincipal`.
- Ejecuta `app.mainloop()`.

Observacion: la auto-instalacion puede ser practica en entorno local, pero en ambientes corporativos puede bloquearse por permisos o politicas de red.

## Paso 1: carga de archivos de consumo

Archivo: `app/ui/paso1_carga.py`

La pantalla requiere 9 entradas:

- `tiv`: TIV, transacciones del mes por agente.
- `maestro`: Maestro Consumo, stock inicial o MaestroStock del mes anterior.
- `fac_termicas`: agentes con factura termica.
- `dsp_kyc`: flags DSP y KYC.
- `com_tx_int`: agentes con transacciones internacionales.
- `prisma`: envios de rollos Prisma.
- `sube`: envios de rollos SUBE.
- `rollo_env`: envios de rollos termicos.
- `trx_sube`: transacciones SUBE.

La autodeteccion busca archivos con extension:

- `.csv`
- `.xlsx`
- `.xls`

Reglas de autodeteccion:

- Para `maestro`, busca preferentemente en `Maestro_consumo/` el archivo del mes anterior cuyo nombre contenga `maestro`.
- Para el resto, busca primero en `Data/` y luego en la raiz de la app.
- Usa nombres esperados como `tiv`, `maestro_consumo`, `fac_termicas`, `dsp_kyc`, `com_tx_int`, `prisma`, `sube`, `rollo`, `trx_sube`.

El boton `Siguiente` queda habilitado solo cuando hay 9 de 9 archivos cargados.

## Carga y normalizacion de datos

Archivo: `app/logic/cargador.py`

### Funcion `_leer(path)`

Lee archivos segun firma real y extension:

- Si la extension es `xlsx`, lee con `openpyxl`.
- Si la firma es ZIP de Excel y la extension no es `csv`, lee como Excel.
- Si la extension es `xls` o la firma es OLE, intenta leer como Excel antiguo.
- Si no aplica Excel, intenta CSV con encodings:
  - `utf-8-sig`
  - `utf-8`
  - `cp1252`
  - `latin1`

Todos los datos se leen inicialmente como texto (`dtype=str`) y luego se convierten columnas numericas puntuales.

### Funcion `_strip_id(s)`

Normaliza identificadores:

- Convierte a texto.
- Quita espacios laterales.
- Elimina guiones.

Esta normalizacion se aplica a `ID_PF`, `ID P.F` o `AGENTE` segun el archivo.

### Funciones de carga de consumo

- `cargar_tiv(path)`: lee TIV, normaliza `ID_PF`, elimina duplicados, renombra columnas transaccionales y convierte numericas.
- `cargar_maestro(path)`: lee maestro, renombra `ID P.F` a `ID_PF`, normaliza ID, elimina duplicados, renombra stocks anteriores y convierte stocks a numero.
- `cargar_fac_termicas(path)`: lee agentes con factura termica y normaliza `ID_PF`.
- `cargar_dsp_kyc(path)`: lee flags DSP/KYC, normaliza ID, elimina duplicados y convierte flags a numero.
- `cargar_com_tx_int(path)`: lee agentes con TX internacionales y normaliza `ID_PF`.
- `cargar_rollo_env(path)`: lee envios de rollo, normaliza `AGENTE`, renombra `CANTIDAD` a `ROLLOS` y convierte a numero.
- `cargar_prisma(path)`: lee envios Prisma, normaliza `AGENTE` y convierte `CANTIDAD`.
- `cargar_sube(path)`: lee envios SUBE, normaliza `AGENTE` y convierte `CANTIDAD`.
- `cargar_trx_sube(path)`: lee transacciones SUBE, normaliza `ID_PF`, convierte `TRX_SUBE` y agrupa sumando por agente.

### Funciones de carga para reposicion

- `cargar_consumo_mes(path)`: lee un MaestroStock historico, asegura columna `ID P.F` y normaliza IDs.
- `cargar_agentes(path)`: lee archivo de agentes para ajuste Canal Propio y acepta `ID_PF` o `ID P.F`.

## Paso 2: calculo de consumo mensual

Archivos:

- `app/ui/paso2_consumo.py`
- `app/logic/calculos_consumo.py`

La pantalla ejecuta el calculo en un hilo para no congelar la UI. Al finalizar:

- Muestra metricas principales.
- Llena tablas de consumo, stock, reconciliacion, agentes sin TIV y agentes sin maestro.
- Prepara el MaestroStock para reposicion.
- Guarda automaticamente un Excel en `Maestro_consumo/`.

### Funcion principal `calcular(...)`

Recibe estos DataFrames:

- `tiv`
- `maestro`
- `fac_termicas`
- `prisma_env`
- `sube_env`
- `trx_sube`
- `dsp_kyc`
- `com_tx_int`
- `rollo_env`

Devuelve:

- `df`: TIV enriquecido con consumos calculados.
- `m`: maestro enriquecido con envios, consumos y stock final.

## Clasificacion de tipo de agente

En `calcular(...)`, cada agente recibe `TIPO_AGENTE`:

- `5`: esta en COM TX INT, en FAC TERMICAS y en DSP/KYC.
- `4`: esta en COM TX INT.
- `3`: esta en FAC TERMICAS.
- `2`: tiene `CANAL_AGENTE_AGRUP` igual a `Centros y Asistidos`.
- `1`: tiene `FLAG_DSP = 1`.
- `0`: no cumple ninguna condicion anterior.

Tambien se crea:

- `FLAG_DSP_KYC`: 1 si el agente aparece en DSP/KYC, 0 si no.

## Formula base de rollos

Variables usadas desde TIV:

- `IB = TX_IMT_IB`
- `OB = TX_IMT_OB`
- `DIB = TX_DMT_IB`
- `DOB = TX_DMT_OB`
- `BP = BP_TU`
- `SFA = TXS_SIN_FAC`
- `PCI = PRISMA_CI`
- `PCO = PRISMA_CO`
- `SUB = TRX_SUBE`
- `DSP = FLAG_DSP`

La base de consumo de rollos es:

```text
BASE =
  DIB * 49.3
  + DOB * 100.90
  + (BP - SFA) * 0.1 * 11
  + (BP - SFA) * 0.9 * 6
  + SFA * 12
  + PCO * 9.5
```

Luego se divide por `6900` y por `5`, porque la unidad final se expresa en paquetes de 5 rollos.

## Calculo de rollos por tipo de agente

La columna calculada es `ROLLOS`.

Para tipos `0`, `1`, `2`:

```text
ROLLOS = BASE / 6900 / 5
```

Para tipo `3`:

```text
ROLLOS = (BASE + OB * 20) / 6900 / 5
```

Para tipo `4` sin DSP:

```text
ROLLOS = (BASE + IB * 108 + OB * 116) / 6900 / 5
```

Para tipo `4` con DSP:

```text
ROLLOS = (BASE + IB * 54 + OB * 58) / 6900 / 5
```

Para tipo `5` sin DSP:

```text
ROLLOS = (BASE + IB * 108 + OB * 136) / 6900 / 5
```

Para tipo `5` con DSP:

```text
ROLLOS = (BASE + IB * 54 + OB * 78) / 6900 / 5
```

## Calculo de bolsas

### Bolsas verdes

Para agentes sin DSP:

```text
BOLSAS_VERDES = (IB * 2 + OB * 4 + DIB + DOB) / 100
```

Para agentes con DSP:

```text
BOLSAS_VERDES = (DIB + DOB) / 100
```

### Bolsas magenta

Solo aplica cuando:

```text
FLAG_DSP = 1 y FLAG_KYC = 0
```

Formula:

```text
BOLSAS_MAGENTA = (IB + OB) / 50
```

### Bolsas de recoleccion

```text
BOLSAS_RECOLECCION = BOLSAS_VERDES + BOLSAS_MAGENTA
```

## Calculo de rollos SUBE y Prisma

### Rollos SUBE

```text
ROLLO_SUBE = (TRX_SUBE * 10 / 2000) / 5
```

### Rollos Prisma

```text
ROLLO_PRISMA = ((PRISMA_CI * 4.4 * 2) / 2000) / 5
```

## Calculo de stock final

El maestro se enriquece con envios:

- `ENVIO_PRISMA`: desde `prisma_env.CANTIDAD`
- `ENVIO_SUBE`: desde `sube_env.CANTIDAD`
- `ENVIO_ROLLO`: desde `rollo_env.ROLLOS`

Luego se agregan los consumos calculados:

- `ROLLOS`
- `ROLLO_PRISMA`
- `ROLLO_SUBE`
- `BOLSAS_RECOLECCION`

Si no existen stocks anteriores, se crean en cero:

- `STOCK_ROLLO_ANT`
- `STOCK_SUBE_ANT`
- `STOCK_PRISMA_ANT`

Formulas de stock:

```text
STOCK_ROLLO  = max(STOCK_ROLLO_ANT, 0)  + ENVIO_ROLLO  - ROLLOS
STOCK_SUBE   = max(STOCK_SUBE_ANT, 0)   + ENVIO_SUBE   - ROLLO_SUBE
STOCK_PRISMA = max(STOCK_PRISMA_ANT, 0) + ENVIO_PRISMA - ROLLO_PRISMA
```

Marca de negativo:

```text
AGENTE_NEGATIVO = 1 si STOCK_ROLLO < 0, si no 0
```

Nota: la marca de negativo solo mira `STOCK_ROLLO`, no SUBE ni PRISMA.

## MaestroStock exportable

Funcion: `preparar_maestro_exportable(df_tiv, df_maestro)`

Objetivo: armar un DataFrame compatible con reposicion historica.

Columnas base desde maestro:

- `ID_PF`
- `NOMBRE_FANTASIA`
- `PROV`
- `DEP`
- `SEGMENTO`
- `SUBSEGMENTACION`
- `STOCK_ROLLO`
- `STOCK_SUBE`
- `STOCK_PRISMA`

Columnas agregadas desde consumo:

- `TIPO_AGENTE`
- `FLAG_DSP_KYC`
- `ROLLOS`
- `BOLSAS_RECOLECCION`
- `ROLLO_SUBE`
- `ROLLO_PRISMA`

Renombres finales:

- `ID_PF` -> `ID P.F`
- `NOMBRE_FANTASIA` -> `NOMBRE FANTASIA`
- `STOCK_ROLLO` -> `STOCK ROLLO`
- `STOCK_SUBE` -> `STOCK SUBE`
- `STOCK_PRISMA` -> `STOCK PRISMA`
- `ROLLOS` -> `ROLLO`
- `BOLSAS_RECOLECCION` -> `BOLSA RECOLECCION`
- `ROLLO_SUBE` -> `ROLLO SUBE`
- `ROLLO_PRISMA` -> `ROLLO PRISMA`
- `TIPO_AGENTE` -> `TIPO`

Las columnas numericas nulas se completan con cero.

## Salida automatica del Paso 2

Al terminar el consumo se genera automaticamente:

```text
Maestro_consumo/MAESTRO_CONSUMO_ENVIO_<MES>_<ANIO>.xlsx
```

Hojas incluidas:

- `MaestroStock`: formato usado por reposicion.
- `Consumo Mensual`: consumo calculado por agente.
- `Maestro Stock`: stock final por agente.
- `Reconciliacion`: consumo, envios, stock anterior y stock final.
- `Sin TIV`: agentes del maestro sin transacciones del mes.
- `Sin Maestro`: agentes con transacciones sin registro en maestro.

El boton `Exportar MaestroStock` vuelve a escribir el mismo archivo destino.

## Paso 3: archivos, parametros y productos de reposicion

Archivo: `app/ui/paso3_reposicion.py`

Entradas requeridas:

- `maestro_actual`: stock de partida. Si no se selecciona archivo, usa el MaestroStock generado en Paso 2.
- `consumo_mes_1`: consumo M-3.
- `consumo_mes_2`: consumo M-2.
- `consumo_mes_3`: consumo M-1.
- `agentes`: listado de agentes Canal Propio.

El boton hacia Paso 4 queda habilitado cuando hay 5 de 5 entradas listas. El maestro generado por Paso 2 cuenta como entrada valida.

### Autodeteccion de reposicion

Busca en `Maestro_consumo/` archivos con fecha parseable por nombre:

- Para `maestro_actual`, prioriza el mes actual y archivos cuyo nombre contenga `maestro`.
- Para historicos:
  - `consumo_mes_3`: mes actual menos 1.
  - `consumo_mes_2`: mes actual menos 2.
  - `consumo_mes_1`: mes actual menos 3.

Tambien busca en `Data/` y raiz:

- Archivos con `consumo` en el nombre para historicos.
- Archivos con `maestro` y `stock` o `consumo` para maestro.
- Archivos con `agente` para agentes Canal Propio.

## Parametros configurables

Definidos por defecto en `app/config.py`:

```text
factor_ajuste_rollos = 1.1
redondeo_rollos = 0.3
redondeo_rollos_prisma = 0.2
redondeo_rollos_sube = 0.3
ajuste_canal_propio = 0.82
```

Significado:

- `factor_ajuste_rollos`: multiplica la necesidad calculada de rollos termicos.
- `redondeo_rollos`: umbral de redondeo para rollos termicos.
- `redondeo_rollos_prisma`: umbral de redondeo para rollos Prisma.
- `redondeo_rollos_sube`: umbral de redondeo para rollos SUBE.
- `ajuste_canal_propio`: factor aplicado a ciertos SKUs para agentes Canal Propio.

Regla de redondeo:

```text
si decimal <= umbral: redondea hacia abajo
si decimal > umbral: redondea hacia arriba
```

Ejemplo con umbral `0.3`:

- `4.30` -> `4`
- `4.31` -> `5`

## Productos configurados

Definidos en `app/config.py`.

### ROLLO

- Columna de reposicion: `ROLLOS REPO`
- Stock/reseteo: `RESETEO ROLLO`
- Metodo: `regresion`
- Factor: `factor_ajuste_rollos`
- Redondeo: `redondeo_rollos`
- SKU: `9001222100`
- Descripcion: `ROLLO TERMICO PF-WU x 5 R. PAPER`
- Excluye provincia: `MENDOZA`

### ROLLO MENDOZA

- Columna historica usada: `ROLLO`
- Columna de reposicion: `ROLLOS REPO MENDOZA`
- Stock/reseteo: `RESETEO ROLLO`
- Metodo: `regresion`
- Factor: `factor_ajuste_rollos`
- Redondeo: `redondeo_rollos`
- SKU: `9001222101`
- Descripcion: `ROLLO TERMICO MZA PF-WU x 5 R. PAPER`
- Solo provincia: `MENDOZA`

### BOLSA RECOLECCION

- Columna de reposicion: `BOLSAS RECOLECCION REPO`
- Metodo: `promedio`
- SKU: `9001219112`
- Descripcion: `BOLSA RECOLECCION x 1 unid`

### ROLLO PRISMA

- Columna de reposicion: `ROLLO TERMICO PRISMA`
- Stock/reseteo: `RESETEO PRISMA`
- Metodo: `regresion`
- Redondeo: `redondeo_rollos_prisma`
- SKU: `9001223489`
- Descripcion: `ROLLO TERMICO DEBITO PRISMA x 5 unid`

### ROLLO SUBE

- Columna de reposicion: `ROLLOS SUBE`
- Stock/reseteo: `RESETEO SUBE`
- Metodo: `regresion`
- Redondeo: `redondeo_rollos_sube`
- SKU: `9001214102`
- Descripcion: `ROLLO TERMICOS SUBE x 5 unid`

Desde la UI se pueden agregar, editar, eliminar o restaurar productos durante la sesion. Esos cambios no se persisten al cerrar la app.

## Paso 4: calculo de reposicion y pedidos

Archivos:

- `app/ui/paso4_resultados.py`
- `app/logic/logica_reposicion.py`

La pantalla:

- Ejecuta el calculo en un hilo.
- Redirige los `print` de la logica hacia el panel de log.
- Muestra una tabla final de pedidos.
- Permite filtrar por producto.
- Permite exportar pedido final y detallado.
- Al terminar correctamente, mueve archivos de entrada ubicados en `Data/` hacia `Data_OLD/` con fecha de proceso.

## Funcion `validar_entradas(...)`

Verifica que existan:

- Los tres historicos de consumo.
- El archivo de agentes.

Devuelve:

- `(True, "OK")` si todo existe.
- `(False, mensaje)` con detalle de archivos faltantes.

Nota: esta funcion existe, pero el Paso 4 llama directamente al proceso de reposicion.

## Funcion `ejecutar_proceso_reposicion(...)`

Entradas:

- `df_maestro_actual`: DataFrame preparado como MaestroStock.
- `rutas_consumos`: diccionario con `consumo_mes_1`, `consumo_mes_2`, `consumo_mes_3`.
- `ruta_agentes`: archivo de agentes Canal Propio.
- `parametros_calculo`: parametros configurables.
- `productos`: lista de productos.
- `reglas`: reglas generales.
- `agentes_excluir`: lista opcional de agentes a excluir.

Devuelve:

- `success`: booleano.
- `mensaje`: texto de resultado o error.
- `df_detallado`: union completa con calculos intermedios.
- `df_final`: pedido final consolidado.

## Etapas internas de reposicion

El proceso informa 8 pasos:

1. Lee los tres archivos historicos de consumo.
2. Lee el archivo de agentes Canal Propio.
3. Unifica datos historicos y maestro actual.
4. Limpia datos numericos y de texto.
5. Calcula stock ajustado.
6. Calcula reposicion por producto.
7. Aplica reglas de negocio.
8. Genera archivo final.

## Union de historicos

Cada historico se normaliza:

- Si existe `ID_PF` y no existe `ID P.F`, renombra a `ID P.F`.
- El ID se convierte a texto, se limpia y se eliminan guiones.

Luego se renombran columnas:

- Historico 1: sufijo `_m1`
- Historico 2: sufijo `_m2`
- Historico 3: sufijo `_m3`

Ejemplo:

- `ROLLO` -> `ROLLO_m1`, `ROLLO_m2`, `ROLLO_m3`
- `ROLLO SUBE` -> `ROLLO SUBE_m1`, etc.

Los historicos se unen por `ID P.F` con merge externo (`outer`), para no perder agentes que aparezcan solo en algun mes.

Despues se une el maestro actual con columnas disponibles:

- `ID P.F`
- `PROV`
- `DEP`
- `SEGMENTO`
- `SUBSEGMENTACION`
- `STOCK ROLLO`
- `STOCK SUBE`
- `STOCK PRISMA`
- `NOMBRE FANTASIA`
- `TIPO`

## Limpieza de datos para reposicion

Columnas de texto:

- Las que contienen `NOMBRE FANTASIA`.
- `PROV`
- `SEGMENTO`

Estas se completan con texto vacio.

El resto de columnas se convierten a numero con `pd.to_numeric(errors="coerce")` y los nulos se completan con cero.

## Stock ajustado para reposicion

Antes de calcular necesidad, se descuenta el consumo del mes mas reciente (`m3`) al stock actual:

```text
STOCK ROLLO  = STOCK ROLLO  - ROLLO_m3
STOCK PRISMA = STOCK PRISMA - ROLLO PRISMA_m3
STOCK SUBE   = STOCK SUBE   - ROLLO SUBE_m3
```

Luego se crean stocks de reseteo:

```text
RESETEO ROLLO  = 0 si STOCK ROLLO < 0, si no STOCK ROLLO
RESETEO PRISMA = 0 si STOCK PRISMA < 0, si no STOCK PRISMA
RESETEO SUBE   = 0 si STOCK SUBE < 0, si no STOCK SUBE
```

El reseteo evita descontar stock negativo en la necesidad futura.

## Metodo de reposicion por regresion

Funcion: `_calcular_repo_regresion(df, nombre_base, col_reseteo_key, factor_ajuste)`

Usa tres meses historicos:

- `nombre_base_m1`
- `nombre_base_m2`
- `nombre_base_m3`

Si falta alguna columna, imprime advertencia y devuelve cero.

Promedio:

```text
promedio = (m1 + m2 + m3) / 3
```

Pendiente de regresion lineal para puntos 1, 2, 3:

```text
pendiente =
  (3 * (m1 * 1 + m2 * 2 + m3 * 3) - 6 * (m1 + m2 + m3))
  / (3 * 14 - 36)
```

Como `3 * 14 - 36 = 6`, equivale a:

```text
pendiente = (3 * (m1 + 2*m2 + 3*m3) - 6 * (m1 + m2 + m3)) / 6
```

Ordenada:

```text
ordenada = promedio - pendiente * 2
```

Prediccion del mes 4:

```text
prediccion = pendiente * 4 + ordenada
```

Seleccion de consumo base:

- Si `pendiente <= 0`, usa promedio.
- Si `pendiente > 0`, usa prediccion.

Necesidad:

```text
repo_promedio   = promedio   * SUBSEGMENTACION * factor_ajuste - stock_reseteado
repo_prediccion = prediccion * SUBSEGMENTACION * factor_ajuste - stock_reseteado
```

Resultado final:

```text
si pendiente <= 0: repo_promedio
si pendiente > 0: repo_prediccion
```

Si `SUBSEGMENTACION` no existe, usa `1`.
Si la columna de reseteo no existe, descuenta `0`.

## Metodo de reposicion por promedio

Aplica para productos como `BOLSA RECOLECCION`.

Formula:

```text
promedio = (m1 + m2 + m3) / 3
repo = promedio * SUBSEGMENTACION * factor
```

Si no hay factor configurado, usa `1.0`.

## Metodo `promedio_ajustado_dep`

Esta soportado por la logica y por el dialogo de productos, aunque no aparece en la lista default.

Formula:

```text
promedio = (m1 + m2 + m3) / 3
repo_tmp = ceil(promedio * SUBSEGMENTACION * factor)
```

Regla por `DEP`:

```text
si DEP == 1: repo = 0
si DEP != 1: repo = repo_tmp
```

## Reglas generales de cantidad

Despues de calcular la reposicion de cada producto:

```text
si repo <= 0: cantidad = 0
si repo > 0: cantidad = repo
```

Si el producto tiene parametro de redondeo y no usa `promedio_ajustado_dep`, se aplica `_redondear_con_parametro`.

Mas tarde, al armar `df_final`, se vuelve a aplicar:

```text
CANTIDAD = ceil(CANTIDAD)
```

Por eso las cantidades finales exportadas son enteras positivas.

## Reglas por provincia

Cada producto puede filtrar por provincia:

- `prov_filter`: deja solo registros de esa provincia.
- `prov_excluir`: excluye registros de esa provincia.

Uso actual:

- `ROLLO` excluye `MENDOZA`.
- `ROLLO MENDOZA` incluye solo `MENDOZA`.

Esto separa los SKUs de rollo termico comun y rollo termico Mendoza.

## Regla Canal Propio

En `config.py`:

```text
skus_ajuste_canal_propio = [9001222100, 9001222101]
ajuste_canal_propio = 0.82
```

La logica:

1. Lee el archivo de agentes Canal Propio.
2. Toma la columna `ID P.F`, `ID_PF`, `ID P.F ` o, si no existe ninguna, la primera columna.
3. Arma una lista de IDs.
4. En el pedido final, si:
   - `ID P.F` esta en esa lista, y
   - `SKU` esta en `skus_ajuste_canal_propio`,
   aplica:

```text
CANTIDAD = ceil(CANTIDAD * ajuste_canal_propio)
```

Con los parametros default, reduce los SKUs de rollos termicos al 82% y redondea hacia arriba.

## Exclusion de agentes

`AGENTES_A_EXCLUIR` esta definido como lista vacia:

```text
AGENTES_A_EXCLUIR = []
```

Si se cargaran IDs en esa lista, el pedido final excluiria esos agentes:

```text
df_final = df_final[~df_final["ID P.F"].isin(agentes_excluir)]
```

## Pedido final

Para cada producto se arma un DataFrame con:

- `ID P.F`
- `NOMBRE FANTASIA`
- `SKU`
- `DESCRIPCION`
- `CANTIDAD`
- `SEGMENTO`

Luego todos los productos se concatenan.

Se eliminan:

- Filas con `CANTIDAD` nula.
- Filas con `CANTIDAD <= 0`.

La salida final contiene solo pedidos efectivos.

## Salidas del Paso 4

### Exportar Pedidos

Genera un Excel seleccionado por el usuario, con nombre sugerido:

```text
REPOSICION_FINAL.xlsx
```

Hoja:

```text
REPOSICION
```

Columnas:

- `ID P.F`
- `NOMBRE FANTASIA`
- `SKU`
- `DESCRIPCION`
- `CANTIDAD`
- `SEGMENTO`

### Exportar Detallado

Genera un Excel seleccionado por el usuario, con nombre sugerido:

```text
REPOSICION_DETALLADO.xlsx
```

Hoja:

```text
DETALLE
```

Incluye la union completa con consumos historicos, maestro, stock ajustado, reseteos y columnas de reposicion calculadas.

## Archivado automatico de archivos de entrada

Despues de una reposicion exitosa, `Paso4Resultados._archivar_data_files()` mueve archivos desde:

```text
Data/
```

hacia:

```text
Data_OLD/
```

Solo mueve:

- Archivos de entrada del Paso 1 que esten fisicamente dentro de `Data/`.
- Archivo de agentes del Paso 3 si esta dentro de `Data/`.

No mueve:

- Maestro generado en Paso 2 (`__GENERADO_PASO_2__`).
- Historicos o maestros ubicados fuera de `Data/`.

El nombre destino agrega fecha:

```text
<nombre_original>_<AAAAMMDD>.<extension>
```

Si ya existe, agrega contador:

```text
<nombre_original>_<AAAAMMDD>_1.<extension>
```

## Validaciones actuales

Validaciones existentes:

- La UI no permite avanzar del Paso 1 hasta tener 9 archivos.
- La UI no permite avanzar del Paso 3 hasta tener 5 entradas listas.
- `validar_entradas` puede verificar existencia de historicos y agentes.
- Los errores de columna faltante en reposicion se capturan como `KeyError` y muestran mensaje.
- Si faltan columnas historicas para un producto, ese producto queda en cero y se imprime advertencia.

Validaciones debiles o pendientes:

- No hay validacion previa completa de columnas requeridas para consumo.
- No hay validacion previa completa de columnas requeridas para reposicion antes de calcular.
- Algunas columnas faltantes en reposicion pueden producir pedidos en cero en vez de detener el proceso.
- La marca `AGENTE_NEGATIVO` solo evalua stock de rollo.
- Los cambios de productos hechos en la UI no se guardan entre sesiones.

## Columnas importantes esperadas

### TIV

Columnas usadas o renombradas:

- `ID_PF`
- `BP + TU` o `BP+TU`
- `TX QCASH`
- `TXS S/FAC`
- `TX IMT OB`
- `TX IMT IB`
- `TX DMT OB`
- `TX DMT IB`
- `PRISMA CI`
- `PRISMA CO`
- `CANAL_AGENTE_AGRUP`
- `PROVINCIA` o `PROV`

### Maestro consumo

Columnas usadas o renombradas:

- `ID P.F`
- `NOMBRE FANTASIA`
- `PROV`
- `DEP`
- `SEGMENTO`
- `SUBSEGMENTACION`
- `STOCK ROLLO`
- `STOCK SUBE`
- `STOCK PRISMA`

Tambien acepta variantes:

- `STOCK_SUBE`
- `STOCK_PRISMA`
- `STOCK_ROLLO_MES ANTERIOR`
- `STOCK_SUBE_MES ANTERIOR`
- `STOCK_PRISMA_MES ANTERIOR`

### Historicos de reposicion

Columnas esperadas principales:

- `ID P.F` o `ID_PF`
- `ROLLO`
- `BOLSA RECOLECCION`
- `ROLLO PRISMA`
- `ROLLO SUBE`
- `TIPO` si se requiere para analisis futuro
- `NOMBRE FANTASIA` si se quiere conservar nombre desde historico

### Agentes Canal Propio

Puede usar:

- `ID P.F`
- `ID_PF`
- `ID P.F `
- o la primera columna del archivo si no encuentra esas.

## Riesgos operativos detectados

- Dependencia fuerte de nombres de columnas exactos.
- No hay tests unitarios visibles para formulas criticas.
- El proceso de reposicion puede continuar con advertencias y dejar productos en cero si faltan columnas historicas.
- La auto-instalacion de dependencias desde `main.pyw` puede fallar en equipos sin permisos.
- La limpieza numerica convierte valores invalidos a cero; esto evita fallas pero puede ocultar errores de origen.
- La autodeteccion depende del nombre de archivo y de que el mes/anio aparezcan de forma parseable.
- `Data_OLD` mueve archivos despues de calcular reposicion; esto es correcto para proceso mensual, pero debe estar claro para el usuario.

## Resumen de reglas de negocio

- El consumo de rollos depende de tipo de agente, DSP, TX IMT, TX DMT, BP/TU, TX sin factura y Prisma CO.
- Las bolsas verdes dependen de IMT/DMT y cambian si el agente es DSP.
- Las bolsas magenta solo aplican para DSP sin KYC.
- SUBE y Prisma se calculan como rollos equivalentes por cantidad de transacciones.
- El stock final del mes es stock anterior positivo + envios - consumo.
- La reposicion usa tres meses historicos.
- Si el consumo historico crece, la regresion proyecta el mes 4.
- Si el consumo historico baja o se mantiene, se usa promedio.
- La necesidad descuenta stock disponible reseteado.
- Las cantidades no positivas se eliminan.
- Mendoza usa SKU propio para rollos termicos.
- Canal Propio reduce los SKUs de rollos configurados por el factor `0.82`.
- Los pedidos finales se exportan solo con cantidades enteras positivas.

## Recomendaciones tecnicas

- Agregar validacion previa de columnas obligatorias antes de calcular consumo.
- Agregar validacion previa de columnas historicas por producto antes de calcular reposicion.
- Convertir advertencias criticas de columnas faltantes en errores visibles si afectan productos principales.
- Agregar tests de formulas:
  - Clasificacion `TIPO_AGENTE`.
  - Calculo `ROLLOS`.
  - Bolsas verdes y magenta.
  - Stock final.
  - Regresion, promedio y redondeo.
  - Canal Propio.
  - Filtro Mendoza/no Mendoza.
- Persistir productos y parametros editados en JSON o Excel de configuracion.
- Documentar oficialmente el layout de cada archivo de entrada.
- Mostrar una pantalla de resumen por SKU antes de exportar.

