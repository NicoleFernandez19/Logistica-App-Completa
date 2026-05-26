# Analisis de los tres proyectos de reposicion

Fecha de revision: 2026-05-26

## Alcance revisado

Se revisaron estos tres proyectos dentro del workspace:

- `App_Completa`
- `old/Logistica`
- `old/Logistica_Reposicion`

La revision cubrio estructura, flujo visual inicial, logica de negocio, ejecucion con datos de prueba y faltantes principales. No se modifico codigo fuente de las aplicaciones.

## Resumen ejecutivo

`App_Completa` es la version mas prometedora como producto final: integra el calculo mensual de consumo con el calculo posterior de reposicion en un asistente por pasos, usa `customtkinter` y tiene una experiencia visual mas clara y moderna.

`old/Logistica` funciona como modulo base de calculo de consumo mensual. Es mas simple, estable para probar la logica de consumo, pero queda corto como solucion final porque no genera directamente pedidos de reposicion historica.

`old/Logistica_Reposicion` es el modulo mas completo para la reposicion historica pura. Ejecuta el proceso completo con los datos de prueba, valida entradas y genera archivos finales, pero su estructura es monolitica y mas dificil de mantener.

La recomendacion es continuar sobre `App_Completa`, tomando como referencia la validacion robusta de `old/Logistica_Reposicion` y manteniendo `old/Logistica` solo como base historica o comparativa.

## Verificaciones ejecutadas

### Entorno

La terminal no tenia `python` disponible en PATH; `python`, `python3` y `py` resolvian a aliases de Microsoft Store. Se pudo ejecutar con `uv run --no-project python`, que proveyo Python 3.14.5.

### `old/Logistica`

Ejecucion logica con datos de prueba:

- Entrada usada para TIV: `Data_Test/TIV.csv`
- Resultado: ejecucion correcta.
- Registros procesados en consumo: 10.
- Registros procesados en maestro: 10.
- Suma de `ROLLOS`: 22.46.

Nota: si se usa `Data_Test/01_DATOS_v5.csv`, falla porque el archivo tiene extension `.csv` pero su contenido inicia como archivo Excel comprimido (`PK...`). El cargador lo intenta leer como CSV UTF-8 y produce error de decodificacion.

### `old/Logistica_Reposicion`

Ejecucion logica con datos de prueba:

- Validacion previa: correcta.
- Proceso de reposicion: correcto.
- Se generaron los reportes:
  - `output/REPOSICION_DETALLADO.xlsx`
  - `output/REPOSICION_CRUDO_FINAL_.xlsx`

El flujo completo de lectura, union de consumos, ajuste de stock, calculo por producto, aplicacion de reglas y generacion final termina exitosamente.

### `App_Completa`

Ejecucion logica con datos de prueba:

- Entrada usada para TIV: `Data_Test/TIV.csv`
- Resultado: ejecucion correcta para el calculo de consumo.
- Registros procesados en consumo: 10.
- Registros procesados en maestro: 10.
- Maestro exportable para reposicion: 10.
- Suma de `ROLLOS`: 22.46.

Igual que en `old/Logistica`, `Data_Test/01_DATOS_v5.csv` no debe tratarse como CSV aunque tenga esa extension.

## Revision visual

### `old/Logistica`

La app abre correctamente en una ventana de 1440x860 con marca Western Union, indicador de 3 pasos y deteccion automatica de los 9 archivos de entrada. Visualmente es clara y funcional, con botones amarillos y una estructura de formulario en dos columnas.

Puntos fuertes:

- Flujo simple: archivos, calculo, resultados.
- Auto-detecta los archivos de prueba.
- La pantalla inicial queda limpia y entendible.
- El footer con anterior/siguiente da buena guia de avance.

Puntos flojos:

- Estetica mas antigua que `App_Completa`.
- No integra el calculo final de pedidos de reposicion.
- Algunos textos no tienen acentos por decision o por compatibilidad.
- El usuario depende de avanzar y calcular para descubrir errores de formato.

### `old/Logistica_Reposicion`

La app abre correctamente maximizada como un formulario largo con scroll. Muestra archivos de entrada, parametros, definicion editable de productos y botones de ejecucion/log. Visualmente es mas administrativa: muy completa, pero densa.

Puntos fuertes:

- Carga automaticamente los archivos definidos en `config.py`.
- Permite editar productos desde la UI.
- Muestra parametros y guia de calculo.
- Tiene ventana de log, validacion previa y ejecucion en hilo.

Puntos flojos:

- El archivo `gui.pyw` concentra demasiada responsabilidad: UI, logging, validacion visual, edicion de productos, threading y coordinacion.
- La primera pantalla es larga y cargada; requiere scroll aun antes de ejecutar.
- Usa rutas relativas y globals desde `config.py`, lo que complica pruebas y empaquetado.
- Al importar o abrir, escribe `startup_log.txt`; esto es util para soporte, pero es un efecto lateral fuerte.

### `App_Completa`

La app abre correctamente maximizada con una interfaz moderna en 4 pasos: archivos de consumo, consumo, archivos de reposicion y pedidos. Visualmente es la mas pulida: buen contraste, stepper superior, cards limpias y botones consistentes.

Puntos fuertes:

- Es la mejor experiencia visual de las tres.
- Integra el flujo completo esperado: consumo mensual -> maestro stock -> reposicion -> pedidos.
- Auto-detecta los 9 archivos de consumo y habilita el avance.
- En version 1.2, el Paso 3 tambien auto-detecta Maestro Stock Actual, 3 historicos y agentes.
- La separacion en pasos reduce carga cognitiva.
- La estructura de carpetas `app/ui` y `app/logic` es mas sana que la version monolitica.

Puntos flojos:

- Falta persistir la lista de productos editada si el usuario cierra la app.
- La validacion previa de archivos historicos existe en la logica, pero el paso final llama directo al proceso; convendria mostrar errores antes de empezar el calculo.
- Hay dependencia fuerte de nombres de columnas exactos.
- La integracion todavia necesita pruebas end-to-end que cubran los 4 pasos.

## Revision de logica

### Calculo de consumo mensual

Presente en `old/Logistica` y `App_Completa`.

La logica:

- Lee TIV, maestro, factura termica, DSP/KYC, COM TX INT, envios Prisma, envios SUBE, envios Rollo y TRX SUBE.
- Normaliza IDs.
- Clasifica tipo de agente.
- Calcula rollos, bolsas verdes, bolsas magenta, bolsas de recoleccion, rollos SUBE y rollos Prisma.
- Calcula stock final por producto restando consumos y sumando envios.
- Marca agentes con stock negativo.

Riesgos:

- La lectura depende de extension; si un Excel esta nombrado como `.csv`, falla.
- Faltan validaciones de columnas antes de procesar en consumo.
- La formula de negocio esta hardcodeada; es correcto si es estable, pero deberia estar documentada con casos esperados.
- No hay tests unitarios para formulas criticas.

### Calculo de reposicion historica

Presente en `old/Logistica_Reposicion` y adaptado en `App_Completa`.

La logica:

- Lee tres meses historicos de consumo.
- Une consumos por `ID P.F`.
- Une maestro de stock.
- Ajusta stock con consumo del mes mas reciente.
- Calcula reposicion por producto usando regresion, promedio o promedio ajustado por `DEP`.
- Aplica reglas como no enviar resmas a ciertos tipos de agente.
- Genera pedidos finales por SKU.
- Aplica ajuste de canal propio.

Riesgos:

- La regresion y los umbrales de redondeo no tienen tests visibles.
- Si faltan columnas, algunos productos quedan en cero con advertencia; esto puede ocultar errores de negocio si el usuario no lee el log.
- La regla `TIPO_m3` asume que el tercer mes trae la columna `TIPO`.
- El ajuste de canal propio depende de tipos y normalizacion de ID consistentes.

## Estructura comparada

### Mejor estructura

`App_Completa` tiene la mejor estructura:

- `app/logic`: calculos y carga de datos.
- `app/ui`: pantallas por paso.
- `app/config.py`: parametros y productos.
- `Data_Test`: datos de prueba.
- `main.pyw`: entrada simple.

### Estructura mas riesgosa

`old/Logistica_Reposicion` tiene demasiada logica en `gui.pyw`. Aunque funciona, es mas dificil de probar y mantener. La logica de negocio esta separada en `app/logica_reposicion.py`, pero la UI todavia concentra mucho comportamiento operativo.

### Proyecto base historico

`old/Logistica` esta bien como referencia para el calculo mensual, pero no deberia ser el proyecto principal si el objetivo es una app integrada.

## Que le falta

Prioridad alta:

- Agregar validacion previa de columnas en `App_Completa` para consumo y reposicion.
- Agregar pruebas unitarias para formulas de consumo, regresion, redondeo y reglas de negocio.
- Agregar una prueba end-to-end con los datos de `Data_Test`.
- Evitar que errores de columnas se transformen silenciosamente en pedidos en cero.

Prioridad media:

- Persistir productos editados y parametros en JSON o Excel de configuracion.
- Unificar mensajes, acentos y nomenclatura entre pantallas.
- Externalizar formulas y reglas en documentacion funcional.
- Agregar pantalla/resumen final con totales por SKU antes de exportar.
- Registrar un log de ejecucion visible en `App_Completa`, similar al de reposicion historica.

Prioridad baja:

- Empaquetar con instrucciones claras de instalacion.
- Evitar auto-instalacion de dependencias desde `main.pyw` en ambientes corporativos; suele ser mejor detectar y mostrar instrucciones.
- Agregar versionado de salida o carpeta de reportes por fecha.
- Mejorar README con flujo, archivos requeridos y ejemplos.

## Recomendacion final

Usaria `App_Completa` como base principal. Es la que mejor combina estructura mantenible, experiencia visual y flujo completo de negocio.

El siguiente paso tecnico seria endurecerla: validaciones antes de calcular, deteccion robusta de formatos, tests de formulas y una ejecucion end-to-end automatizada con los datos de prueba. Con eso, la app pasaria de "demo integrada funcional" a herramienta operativa confiable.

Nota posterior: se descarto agregar un archivero dentro de la app. El flujo debe mantenerse simple: seleccionar archivos, calcular, revisar y exportar salidas.

Actualizacion version 1.2: se corrigio la lectura por firma real del archivo, se agrego Maestro Stock Actual seleccionable en Paso 3, se separo Paso 3 en paginas internas y se sumaron instructivos breves con formulas en el flujo principal.
