# Casos de Prueba — App Reposición

Pruebas funcionales para validar la app de extremo a extremo, organizadas por paso y escenario.  
Ejecutar en orden. Cada caso indica la acción, el resultado esperado y el criterio de aceptación.

---

## Preparación general

Antes de comenzar, tener disponibles archivos de prueba con las siguientes características:

| Archivo de prueba | Contenido |
|---|---|
| `TIV_valido.xlsx` | Columnas: `ID_PF`, `BP+TU`, `TX IMT OB`, `TX IMT IB`, `TX DMT OB`, `TX DMT IB`, `PRISMA CI`, `PRISMA CO`, `TX_QCASH`, `TXS S/FAC`. Al menos 5 agentes. |
| `TIV_sin_ID.xlsx` | Igual al anterior pero sin la columna `ID_PF`. |
| `TIV_vacio.xlsx` | Solo cabecera, sin filas de datos. |
| `Maestro_valido.xlsx` | Columnas: `ID P.F`, `NOMBRE FANTASIA`, `PROV`, `DEP`, `SEGMENTO`, `SUBSEGMENTACION`, `STOCK ROLLO`, `STOCK SUBE`, `STOCK PRISMA`. |
| `Maestro_vacio.xlsx` | Solo cabecera, sin filas. |
| `DSP_KYC_valido.xlsx` | Columnas: `ID_PF`, `FLAG_DSP`, `FLAG_KYC`. |
| `DSP_KYC_sin_flag.xlsx` | Sin columna `FLAG_DSP`. |
| `Envios_valido.xlsx` | Columnas: `AGENTE`, `CANTIDAD`. Usado para ROLLO, SUBE, PRISMA y RESMA. |
| `TRX_SUBE_valido.xlsx` | Columnas: `ID_PF`, `TRX_SUBE`. |
| `FAJAS_valido.xlsx` | Columnas: `ID_PF`, `Qx FAJAS`. |
| `Consumo_M1.xlsx`, `Consumo_M2.xlsx`, `Consumo_M3.xlsx` | Archivos MaestroStock de meses anteriores con columna `ID P.F` y columnas `ROLLO`, `ROLLO SUBE`, `ROLLO PRISMA`, `STOCK ROLLO`, etc. |
| `Agentes_CP.xlsx` | Columnas: `ID P.F`. Lista de agentes Canal Propio — **no afecta el cálculo** (ver CP-18); el ajuste se decide por `NOMBRE FANTASIA` conteniendo `"C.S."`. Sirve solo para probar que el slot de carga funciona. |

---

## PASO 1 — Carga de archivos

### CP-01: Autodetección de archivos

**Precondición:** Colocar archivos con nombres estándar en la carpeta `Data/` (ej: `tiv_final.xlsx`, `dsp_kyc.xlsx`, `prisma.xlsx`, etc.)  
**Acción:** Abrir la app y clickear **"Auto-detectar"** en el Paso 1.  
**Esperado:** Cada slot muestra el nombre del archivo correspondiente resaltado en verde. El contador muestra `11 / 11`.  
**Criterio:** Sin errores, todos los slots asignados correctamente.

---

### CP-02: Carga manual de un archivo

**Acción:** Clickear **"Examinar"** en el slot TIV. Seleccionar `TIV_valido.xlsx`.  
**Esperado:** El slot muestra el nombre del archivo en negro (carga manual). El contador incrementa en 1.  
**Criterio:** El archivo queda registrado y el contador refleja el total correcto.

---

### CP-03: Reemplazo de un archivo ya cargado

**Precondición:** CP-01 completado (11 archivos cargados).  
**Acción:** Clickear **"Examinar"** en el slot TIV y seleccionar un archivo diferente.  
**Esperado:** El slot se actualiza con el nuevo archivo. El contador permanece en `11 / 11`.  
**Criterio:** El slot muestra el nuevo nombre sin duplicar el conteo.

---

### CP-04: Botón "Calcular Consumo" habilitado solo con 11 archivos

**Acción:** Cargar 10 de los 11 archivos. Intentar avanzar al Paso 2.  
**Esperado:** El botón de avance permanece deshabilitado o muestra un mensaje de advertencia.  
**Criterio:** No es posible continuar con archivos faltantes.

---

## PASO 2 — Cálculo de consumo

### CP-05: Cálculo exitoso con archivos válidos

**Precondición:** 11 archivos cargados correctamente.  
**Acción:** Clickear **"Calcular Consumo"**.  
**Esperado:**
- La barra de progreso se muestra durante el cálculo.
- El log muestra los pasos en orden: TIV, Maestro, envíos, consumo calculado.
- Las métricas (ROLLOS, SUBE, PRISMA, BOLSAS, RESMA, FAJAS) muestran valores mayores a 0.
- El maestro stock generado es exportable.  
**Criterio:** Proceso completa sin errores. Métricas visibles y coherentes.

---

### CP-06: TIV sin columna ID_PF

**Precondición:** Cargar `TIV_sin_ID.xlsx` en el slot TIV. Los demás archivos válidos.  
**Acción:** Clickear **"Calcular Consumo"**.  
**Esperado:** Aparece un mensaje de error descriptivo: `"columna(s) requeridas no encontradas: ['ID_PF']"` con las columnas disponibles listadas.  
**Criterio:** El error es legible e identifica el archivo y la columna faltante.

---

### CP-07: TIV vacío (sin filas)

**Precondición:** Cargar `TIV_vacio.xlsx` en slot TIV.  
**Acción:** Calcular consumo.  
**Esperado:** Error: `"sin datos (0 filas)"`.  
**Criterio:** El error menciona el nombre del archivo.

---

### CP-08: DSP/KYC sin columna FLAG_DSP

**Precondición:** Cargar `DSP_KYC_sin_flag.xlsx` en slot DSP/KYC.  
**Acción:** Calcular consumo.  
**Esperado:** Error: `"columna(s) requeridas no encontradas: ['FLAG_DSP']"`.  
**Criterio:** Error descriptivo que identifica el archivo y la columna faltante.

---

### CP-09: Archivo en slot incorrecto (ej: envíos donde va TIV)

**Precondición:** Cargar `Envios_valido.xlsx` (columnas AGENTE, CANTIDAD) en el slot TIV.  
**Acción:** Calcular consumo.  
**Esperado:** Error indicando que `ID_PF` no se encontró en el archivo.  
**Criterio:** El error identifica el problema sin crashear la app.

---

### CP-10: Agentes con ID_PF duplicados en TIV

**Precondición:** Cargar un TIV con 2 filas para el mismo `ID_PF`.  
**Acción:** Calcular consumo.  
**Esperado:** El log muestra `"ADVERTENCIA: N ID_PF duplicados eliminados"`. El cálculo continúa normalmente.  
**Criterio:** La app no falla; los duplicados se eliminan con advertencia visible.

---

### CP-11: Exportar MaestroStock generado

**Precondición:** CP-05 completado exitosamente.  
**Acción:** Clickear **"Exportar MaestroStock"** o verificar que el archivo se guardó automáticamente en `Maestro_Consumo/`.  
**Esperado:** El archivo Excel se guarda en `Maestro_Consumo/` con nombre que incluye el mes/año. Si ya existía uno anterior, se crea un backup con sufijo `_anterior`.  
**Criterio:** Archivo generado, sin sobreescritura silenciosa del anterior.

---

## PASO 3 — Maestro Stock y Parámetros

### CP-12: Carga automática del MaestroStock generado en Paso 2

**Precondición:** CP-05 y CP-11 completados.  
**Acción:** Navegar al Paso 3.  
**Esperado:** El Maestro Stock muestra los datos del archivo generado (columnas ID P.F, STOCK ROLLO, etc.). El número de agentes cargados se muestra.  
**Criterio:** El maestro está disponible sin necesidad de cargarlo manualmente.

---

### CP-13: Carga manual de MaestroStock alternativo

**Acción:** En el Paso 3, clickear **"Cargar Maestro Stock"** y seleccionar `Maestro_valido.xlsx`.  
**Esperado:** El maestro se actualiza con los datos del archivo seleccionado. El número de agentes cambia.  
**Criterio:** El maestro alternativo reemplaza al generado en Paso 2.

---

### CP-14: Selección de archivos de consumo histórico (3 meses)

**Acción:** En el Paso 3, cargar `Consumo_M1.xlsx`, `Consumo_M2.xlsx` y `Consumo_M3.xlsx` en sus slots correspondientes (M-3, M-2, M-1).  
**Acción adicional:** Cargar `Agentes_CP.xlsx` en el slot **Agentes Canal Propio**.  
**Esperado:** Cada slot muestra el nombre del archivo cargado.  
**Criterio:** Los 4 archivos quedan registrados correctamente.

---

### CP-15: Verificación de parámetros de cálculo

**Acción:** Revisar los parámetros mostrados en la pantalla (factor ajuste rollos, parámetro de redondeo, ajuste Canal Propio).  
**Esperado:** Los valores por defecto son: factor=1.1, redondeo=0.3, ajuste CP=0.82.  
**Criterio:** Los parámetros son visibles y editables si la UI lo permite.

---

## PASO 4 — Cálculo de Reposición y Exportación

### CP-16: Cálculo de reposición exitoso

**Precondición:** Pasos 1–3 completados con todos los archivos válidos.  
**Acción:** Clickear **"CALCULAR REPOSICIÓN"**.  
**Esperado:**
- El log muestra los 8 pasos del proceso.
- La tabla se llena con las filas del pedido (columnas: ID P.F, NOMBRE FANTASIA, SKU, DESCRIPCION, CANTIDAD, SEGMENTO).
- Todas las cantidades son enteras y mayores a 0.
- El log finaliza con `"✓ Proceso completado exitosamente."`.  
**Criterio:** Sin errores. Tabla visible con al menos una fila por producto con consumo > 0.

---

### CP-17: Separación MENDOZA / estándar

**Precondición:** El MaestroStock tiene agentes con PROV = "MENDOZA".  
**Verificación:** En el resultado, los agentes MENDOZA aparecen bajo el SKU `9001222101` (ROLLO TERMICO MZA) y NO bajo el SKU `9001222100` (ROLLO TERMICO PF-WU).  
**Criterio:** La separación por provincia funciona correctamente.

---

### CP-18: Ajuste Canal Propio

**Precondición:** Al menos un agente con `NOMBRE FANTASIA` que contenga `"C.S."` (ej: `"C.S. CARREFOUR BERUTI"`) tiene reposición de rollos > 0.  
**Verificación:** Buscar en el resultado las filas de ese agente para SKU `9001222100` o `9001222101`. La CANTIDAD debe ser `ceil(valor_base * 0.82)`.  
**Criterio:** El ajuste del 18% aplica solo a agentes cuyo `NOMBRE FANTASIA` contiene `"C.S."` y solo a los SKUs configurados en `skus_ajuste_canal_propio`.

**Importante:** el archivo cargado en el slot "Agentes Canal Propio" (Paso 3) **no participa en esta decisión** — se lee pero no se usa (ver nota en "Agentes Canal Propio" en `APP_REPOSICION.md`). Cargar `Agentes_CP.xlsx` con o sin el agente de prueba no cambia el resultado; lo único que importa es el texto de `NOMBRE FANTASIA`.

---

### CP-19: Filtro por producto en la tabla

**Acción:** En el desplegable "Filtrar por producto", seleccionar "ROLLO TERMICO PF-WU x 5 R. PAPER".  
**Esperado:** La tabla muestra solo las filas de ese producto.  
**Acción:** Volver a "(Todos)".  
**Esperado:** La tabla vuelve a mostrar todos los productos.  
**Criterio:** El filtro funciona sin recargar el cálculo.

---

### CP-20: Exportar pedidos

**Acción:** Clickear **"↓ Exportar Pedidos"**. Guardar el archivo como `REPOSICION_FINAL.xlsx`.  
**Esperado:** El archivo se guarda correctamente. Contiene una hoja "REPOSICION" con columnas: ID P.F, NOMBRE FANTASIA, SKU, DESCRIPCION, CANTIDAD, SEGMENTO.  
**Criterio:** El Excel abre sin errores y contiene los mismos datos que la tabla en pantalla.

---

### CP-21: Exportar detallado

**Acción:** Clickear **"↓ Exportar Detallado"**. Guardar como `REPOSICION_DETALLADO.xlsx`.  
**Esperado:** El archivo se guarda con la hoja "DETALLE" que incluye columnas intermedias del cálculo (stocks, consumos por mes, valores de regresión).  
**Criterio:** El Excel abre sin errores y contiene más columnas que el archivo final.

---

### CP-22: Archivos de Data/ archivados tras el cálculo

**Precondición:** Los archivos de entrada estaban en la carpeta `Data/`.  
**Verificación post-cálculo:** Los archivos ya no están en `Data/`. Aparecen en `Data_OLD/` con el formato `<nombre>_YYYYMMDD.<ext>`.  
**Criterio:** El archivado automático funcionó. Los archivos no se perdieron.

---

### CP-23: Falta un archivo de consumo histórico

**Precondición:** Solo cargar 2 de los 3 archivos de consumo (dejar M-3 vacío).  
**Acción:** Calcular reposición.  
**Esperado:** Error: `"Archivos faltantes para calcular la reposición: • Consumo M-3"`.  
**Criterio:** El error identifica qué archivo falta sin crashear.

---

### CP-24: Histórico sin columna ID P.F

**Precondición:** Cargar un archivo de consumo que no tenga la columna `ID P.F` ni `ID_PF`.  
**Acción:** Calcular reposición.  
**Esperado:** Error: `"columna 'ID P.F' no encontrada"` con lista de columnas disponibles.  
**Criterio:** Error descriptivo y accionable.

---

### CP-25: SUBSEGMENTACION vacía en el maestro

**Precondición:** El MaestroStock tiene celdas vacías en la columna `SUBSEGMENTACION`.  
**Verificación:** Los agentes con `SUBSEGMENTACION` vacía o en 0 reciben reposición **0 en todos los productos** (el valor se mantiene en 0, no se reemplaza por 1 — es el mismo comportamiento del script legacy).  
**Criterio:** La reposición es 0 para esos agentes; si se esperaba que recibieran algo, el problema está en el dato de origen (`SUBSEGMENTACION` vacía en el maestro), no en la app.

---

## Casos de formato de archivo

### CP-26: CSV con separador `;` (formato Argentina/Excel)

**Acción:** Cargar un archivo CSV exportado desde Excel argentino (separador `;`, coma decimal como en `1.234,56`).  
**Esperado:** Los valores numéricos se interpretan correctamente (ej: `1.234,56` → 1234.56).  
**Criterio:** Sin errores de conversión numérica.

---

### CP-27: CSV con codificación latin1 o UTF-8

**Acción:** Cargar un CSV guardado con codificación latin1 (ej: exportado desde Excel en Windows).  
**Esperado:** El archivo se carga correctamente. Los nombres con tildes y eñes aparecen sin caracteres extraños.  
**Criterio:** Sin errores de lectura.

---

### CP-28: Columnas con espacios al inicio/fin

**Acción:** Cargar un archivo cuyas cabeceras tengan espacios invisibles (ej: `" ID_PF "` en lugar de `"ID_PF"`).  
**Esperado:** El archivo se carga correctamente; los espacios se eliminan automáticamente.  
**Criterio:** Sin error de columna no encontrada.

---

### CP-29: Archivo XLS (formato Excel 97-2003)

**Acción:** Cargar un archivo `.xls` en cualquier slot.  
**Esperado:** Se carga correctamente igual que un `.xlsx`.  
**Criterio:** Sin errores de formato.

---

## Resultado esperado global

| Escenario | Resultado |
|---|---|
| Archivos válidos, flujo completo | Proceso exitoso, pedido exportable |
| Columna faltante en cualquier archivo | Error descriptivo con nombre de archivo y columna |
| Archivo vacío | Error indicando 0 filas |
| Archivo en slot incorrecto | Error de columna requerida no encontrada |
| CSV con formato argentino | Valores numéricos correctos |
| Duplicados de ID | Advertencia en log, proceso continúa |
| SUBSEGMENTACION = 0 | Reposición no anulada (fallback a 1) |
| Agentes sin coincidencia en Canal Propio | Pipeline completa sin crash |
