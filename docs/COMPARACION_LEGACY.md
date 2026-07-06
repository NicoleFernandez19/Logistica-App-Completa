# Comparación con el script legacy (`backup/repo_con_segmento_para_eliminar_agentes_v9.2.py`)

Investigación y hallazgos sobre por qué la app nueva y el script legacy pueden dar resultados muy distintos aunque parezcan estar usando los mismos archivos, qué se corrigió, y por qué la app nueva es la referencia confiable. Complementa a [`APP_REPOSICION.md`](APP_REPOSICION.md).

---

## Por qué los totales pueden dar muy distintos aunque "sean los mismos archivos"

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

La app nueva no sufre esto porque normaliza `ID P.F` a texto (`strip()` + eliminación de guiones) **antes** de cualquier merge, en los históricos, el maestro y el archivo de agentes (ver "Normalización de IDs" en `APP_REPOSICION.md`).

## En qué casos puede volver a pasar

- Cualquier archivo de consumo/maestro donde `ID P.F` se haya tipeado o pegado como número en Excel (en vez de como texto) mientras otro archivo del mismo cálculo lo tiene como texto. Es común que esto pase solo, por ejemplo al pegar valores con "Pegado especial → Valores" desde otro reporte, o al generar el Excel con una herramienta distinta (Power BI, un export de SQL) que tipa la columna distinto que el resto.
- Cuantos más agentes tengan el ID en un tipo de celda distinto al de los demás archivos del mismo cálculo, mayor la porción del historial que se pierde en silencio — y el error no lanza ninguna advertencia ni excepción, simplemente rellena con 0.
- Esto **solo afecta al script legacy** (o a cualquier código nuevo que vuelva a hacer merges sobre `ID P.F` sin normalizar el tipo primero). No es un riesgo para la app actual mientras la normalización de IDs en `logica_reposicion.py` / `cargador.py` siga aplicándose a todos los archivos de entrada.

## Por qué la app nueva es la referencia válida, y no conviene "bajar" al formato viejo

Podría pensarse que la solución es re-tipear los Excel de Abril/Mayo como texto para que calcen con el formato que el script legacy sí procesa bien. **No es la dirección correcta:**

1. El script legacy solo "funciona" con esos archivos por casualidad de que Abril y Mayo comparten el mismo tipo de celda entre sí — no porque valide o normalice nada. Cualquier archivo futuro con el tipo de celda "equivocado" (numérico en vez de texto, o viceversa) rompe el cálculo otra vez, en silencio, sin aviso.
2. La app nueva no depende de que los archivos de entrada vengan con un tipo de celda particular: normaliza el ID sin importar si Excel lo guardó como número o como texto. Es la versión robusta ante inconsistencias de formato entre archivos generados en momentos o herramientas distintas — que es exactamente lo que pasó acá.
3. Adaptar los archivos de entrada al formato que el script viejo tolera es resolver el síntoma para una corrida puntual, no la causa: el próximo mes, con un archivo nuevo, puede volver a romperse de la misma manera si nadie se acuerda de revisar el tipo de celda a mano.
4. La app nueva ya fue verificada: corriendo su propia lógica (`ejecutar_proceso_reposicion`) sobre los mismos 4 archivos, sus resultados coinciden con los valores reales de consumo de los archivos fuente (verificado fila por fila para agentes puntuales) — el script legacy, en cambio, coincide con datos que en un 99.98% de los casos son 0 donde no deberían serlo.

**Conclusión:** ante una discrepancia entre la app nueva y el script legacy, la app nueva es la fuente confiable por diseño (normaliza IDs), y el script legacy debe tratarse como referencia poco confiable salvo que se verifique explícitamente que todos sus archivos de entrada comparten el mismo tipo de celda en `ID P.F`.

## Copia corregida del script legacy

`backup/repo_con_segmento_para_eliminar_agentes_v9.2_CORREGIDO.py` es una copia del script original con un único cambio: normaliza `ID P.F` a texto (`.astype(str).str.strip()`) en los 4 archivos de entrada, antes de cualquier merge — el mismo fix que ya tiene la app nueva. No se tocó ninguna fórmula. Además:

- Las rutas de entrada y salida están como variables al principio del archivo (`CARPETA_ENTRADA`, `CARPETA_SALIDA`, `NOMBRE_CONSUMO_MES_1/2/3`, `NOMBRE_MAESTRO_STOCK`, `NOMBRE_SALIDA_DETALLADO`, `NOMBRE_SALIDA_FINAL`), para no tener que buscar y editar nombres de archivo dispersos por el código cada mes.
- Si se usa una ruta de Windows con backslash (`\`) en `CARPETA_ENTRADA`/`CARPETA_SALIDA`, hay que escribirla como raw string (`r'C:\ruta\...'`) o con barras normales (`'C:/ruta/...'`). Sin el prefijo `r`, Python interpreta secuencias como `\U` como un escape unicode y tira `SyntaxError: (unicode error) 'unicodeescape'...`.
- Genera `REPOSICION_DETALLADO_CORREGIDO.xlsx` y `REPOSICION_CRUDO_FINAL_CORREGIDO.xlsx` (nombres distintos a los del script original, para no pisar corridas viejas).

Verificado (2026-07-06): corriendo esta copia contra los mismos 4 archivos de `backup/`, el resultado pasó de estar 30-80% desviado por SKU (script original) a estar dentro de ~1% de la app nueva en todos los productos.

## Universo de agentes: join `outer` (app nueva) vs. join `right` (script legacy)

Ese ~1% residual que queda incluso con el fix de `ID P.F` no es un bug — es una diferencia de diseño en cómo cada versión arma el historial de 3 meses:

- **Script legacy:** encadena los 3 meses con `pd.merge(..., how="right")`, siempre fijado al mes 3 (el más reciente). Si un agente no aparece en el archivo del mes 3, **se cae del cálculo entero**, aunque tenga historial válido en los meses 1 y 2.
- **App nueva** (`logica_reposicion.py`): hace `pd.merge(..., how="outer")` entre los 3 meses. Un agente que falte en el archivo más reciente pero tenga historial en los otros dos **se mantiene** en el cálculo.

Con los archivos de `backup/`, esto afecta a 222 agentes (presentes en Abril/Mayo, ausentes en el archivo de Junio). Se investigó si convenía imitar el criterio del script legacy (descartarlos) y la respuesta es no, por dos motivos verificados con datos reales:

1. **Los 222 siguen en el maestro actual (Septiembre) — ninguno se dio de baja.** Si un agente hubiera cerrado, el propio cálculo ya lo neutraliza solo: al no estar en el maestro más reciente, su `SUBSEGMENTACION` llega vacía → se rellena en 0 (no en 1, ver "SUBSEGMENTACION como multiplicador" en `APP_REPOSICION.md`) → reposición 0 en todos los productos para ese agente. Esto es automático, no depende de qué tipo de join se use para el historial.
2. **El stock sobrante de un agente que no vendió ese mes ya se descuenta solo.** Si a un agente le falta el consumo del mes 3, ese valor se toma como 0 → no se le resta nada al `STOCK` → el `RESETEO` (stock disponible) sale alto → ese `RESETEO` se resta de la reposición calculada. En la práctica, de los 222 agentes "extra", la reposición de ROLLO promedio es 0,09 unidades (percentil 75 = 0) — el mecanismo de stock ya frena la sobre-reposición sin necesidad de excluir al agente.

En los datos de `backup/`, los 222 agentes extra aportan en total 135 unidades sobre 26.179 (~0,5%) — no una cantidad inflada, sino el reflejo correcto de que la mayoría de ellos no necesita nada.

**Conclusión:** mantener el join `outer` en la app nueva. Descartar agentes por faltar en un solo archivo mensual (como hace el script legacy) es el mismo tipo de pérdida silenciosa de datos que el bug de `ID P.F` — castiga a un agente activo por un hueco puntual en un export, no porque realmente no necesite reposición. Los controles de `SUBSEGMENTACION` (maestro actual) y `RESETEO` (stock) ya evitan que eso derive en sobre-stockear a alguien que se dio de baja o que no vendió.

## Verificación fila por fila (`ID P.F` + `SKU`)

Además de comparar totales por SKU, se verificó cantidad por cantidad: se cruzó la salida de la app nueva contra la del script legacy corregido por `(ID P.F, SKU)`, sobre 7.977 combinaciones.

| | Cantidad |
|---|---|
| Coinciden exacto (misma cantidad, ambos lados) | 7.852 |
| Presentes solo en la app nueva (los 222 agentes del punto anterior) | 125 filas, 135 unidades |
| Presentes solo en el script corregido | 0 |
| Presentes en ambos lados con cantidad **distinta** | 0 |

Cero filas con cantidad distinta entre agentes presentes en ambos cálculos: para cualquier agente que exista en los dos universos, el número da idéntico al dígito. Toda la diferencia que pueda verse entre la app nueva y el script legacy corregido se explica por qué agentes entran al cálculo, nunca por la fórmula en sí.
