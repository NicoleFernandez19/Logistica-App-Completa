# Version 1.2 - App_Completa

Fecha: 2026-05-26

## Objetivo

La version 1.2 corrige el rumbo de la integracion: se elimina el concepto de archivero de la interfaz y se refuerza el Paso 3 para que tenga las piezas funcionales que estaban en `old/Logistica_Reposicion`, especialmente la lista editable de productos.

## Cambios retirados

Se quitaron los botones y acciones de archivar porque no aportaban al flujo operativo:

- Paso 1: se retiro `Archivar`.
- Paso 2: se retiro `Archivar MaestroStock`.
- Paso 3: se retiro `Archivar historicos`.
- Paso 4: se retiro `Archivar salidas`.

Tambien se elimino el modulo experimental:

- `App_Completa/app/logic/archivero.py`

Y se retiro la carpeta generada por ese flujo descartado:

- `App_Completa/Archivero`

## Cambios agregados

### Paso 3 - Archivos de reposicion

El Paso 3 ahora queda orientado al flujo real de reposicion:

- Maestro Stock Actual seleccionable desde archivo.
- Si no se selecciona Maestro Stock Actual, se usa el MaestroStock generado desde el Paso 2.
- Archivos historicos de consumo.
- Archivo de agentes de Canal Propio.
- Parametros de calculo.
- Definicion editable de productos.

La pantalla ya no queda como una lista larga. Se separo en tres paginas internas:

- `Archivos`: Maestro Stock Actual, tres historicos de consumo y agentes.
- `Productos`: lista editable de productos/SKUs/metodos.
- `Parametros`: factores, umbrales de redondeo y ajuste de Canal Propio.

El autodetector ahora reconoce tambien el Maestro Stock Actual y prioriza el archivo con mes identificado.

### Productos editables

Se agrego una seccion `Definicion de Productos` inspirada en `old/Logistica_Reposicion`.

Funciones disponibles:

- Buscar productos.
- Anadir producto.
- Editar producto seleccionado.
- Eliminar producto seleccionado.
- Restaurar productos por defecto.

Campos soportados:

- `nombre_base`
- `col_repo`
- `metodo`
- `factor_ajuste`
- `param_redondeo`
- `col_stock_reseteo`
- `sku_base`
- `desc_base`
- `col_consumo`
- `prov_filter`
- `prov_excluir`

La lista editada en Paso 3 se usa directamente en Paso 4 para calcular pedidos.

### Paso 4 conectado a productos editados

El calculo de reposicion ya no toma una lista fija importada desde `config.py` dentro del Paso 4. Ahora recibe los productos activos desde el Paso 3.

Esto permite ajustar productos/SKUs/reglas de producto antes de calcular, igual que en la app vieja de reposicion.

Paso 4 tambien recibe el Maestro Stock Actual desde Paso 3. Si el usuario no eligio un archivo manual, toma el generado en Paso 2.

### Instructivos breves en la app

Se agregaron ayudas cortas en los pasos principales:

- Paso 1: explica que TIV aporta consumo, Maestro aporta stock inicial y envios/flags ajustan el stock.
- Paso 2: muestra la formula `stock final = stock inicial + envios - consumo`.
- Paso 3: resume el uso de Maestro Actual, historicos, productos, parametros y ajuste Canal Propio.
- Paso 4: muestra la formula base `necesidad = consumo proyectado * factor - stock actual`.

### Mejora visual y legibilidad

Se ajusto la interfaz para que sea mas amable y facil de leer:

- Fuente base mas grande en titulos, botones, instrucciones y controles.
- Filas de tablas mas altas y texto de tabla mas legible.
- Stepper superior, botones de navegacion y paneles de metricas mas visibles.
- Mayor contraste en textos secundarios.
- Tablas con menor altura minima para que el footer no desaparezca en ventanas mas bajas.

### Lectura robusta de archivos

Se actualizo:

- `App_Completa/app/logic/cargador.py`

Mejoras:

- Detecta archivos Excel por firma interna (`PK...`) aunque tengan extension `.csv`.
- Para CSV intenta varios encodings: `utf-8-sig`, `utf-8`, `cp1252` y `latin1`.
- Reusa la misma lectura robusta en consumo historico y agentes.

### Normalizacion numerica en reposicion

Se actualizo:

- `App_Completa/app/logic/logica_reposicion.py`

La reposicion convierte a numerico las columnas calculables antes de aplicar regresion, promedios y redondeos.

Esto corrige un problema de integracion donde el MaestroStock generado por consumo podia llegar con valores como texto y romper la reposicion al multiplicar por factores decimales.

## Verificacion

Se valido:

- Compilacion de `App_Completa`.
- Pipeline de reposicion con Maestro Stock Actual manual + tres historicos + agentes.
- Resultado con datos de prueba: proceso completo exitoso y 59 lineas de pedidos.
- Revision visual de Paso 1, Paso 3 por paginas internas y Paso 4.
- Revision visual de legibilidad en ventana de 1366x820.

## Pendientes recomendados

- Validacion previa de columnas con mensajes claros por archivo.
- Persistencia opcional de productos editados en Excel o JSON.
- Test end-to-end sin interfaz grafica.
- Resumen final por SKU antes de exportar.
