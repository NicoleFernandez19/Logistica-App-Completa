"""
Copia de "App paso 4 anterior/repo_con_segmento_para_eliminar_agentes_v9.2.py"
para correrla directamente en el IDE contra los datos de prueba, sin depender
del harness de test (test_comparacion_version_anterior.py).

El script original queda INTACTO -- esto es solo una copia con las rutas de
entrada/salida apuntando a tests/datos_prueba_comparacion/, para poder abrir
este archivo y darle "Run" sin nada mas.

La logica de calculo (formulas, redondeos, reglas de negocio) es identica
linea por linea al script original; lo unico que cambia son las 4 lineas de
lectura de archivos y la ruta de salida.
"""
import numpy as np
import pandas as pd
from pathlib import Path

DIR_DATOS = Path(__file__).resolve().parent / "paso2_export"
DIR_SALIDA = Path(__file__).resolve().parent / "resultado_legacy"
DIR_SALIDA.mkdir(exist_ok=True)

#Los meses se deben ordenar de esa manera, el 3 es el mas reciente el 2 es el mes pasado y el 1 el mas viejo
df_CONSUMO1=pd.read_excel(DIR_DATOS / 'CONSUMO_ABRIL_2026.xlsx')
df_CONSUMO2=pd.read_excel(DIR_DATOS / 'CONSUMO_MAYO_2026.xlsx')
df_CONSUMO3=pd.read_excel(DIR_DATOS / 'CONSUMO_JUNIO_2026.xlsx')

df_STOCK=pd.read_excel(DIR_DATOS / 'MAESTRO_CONSUMO_ENVIO_AGOSTO_2026.xlsx')

#unimos los 3 archivos consumos con el siguiente codigo.

df_union=pd.merge(df_CONSUMO2,df_CONSUMO3, how="right", on="ID P.F").set_index("ID P.F")
df_union2=pd.merge(df_CONSUMO1,df_union, how="right", on="ID P.F").set_index("ID P.F")

#ES IMPORTANTE QUE EL ARCHIVO DE MAESTRO_CONSUMO_ENVIO EL LA ULTIMAS COLUMNAS DE STOCK DE ROLLOS Y RESMAS SE LLAMEN "stock rollo" Y "stock resma"

#Sacamos del archivo MAESTRO las columnas informadas y la guardamos en df_STOCK
df_STOCK= df_STOCK[['ID P.F','PROV','DEP','SEGMENTO','SUBSEGMENTACION','STOCK ROLLO','STOCK RESMA','STOCK SUBE','STOCK PRISMA']]

#UNIMOS nuestros archivos tanto de consumos y stock
df_union4 = pd.merge(df_union2,df_STOCK, how="left", on="ID P.F").set_index("ID P.F")

## Esta seccion conviene los valores null en 0 (cero)
## Esto se debe por que cuando hace los calculos, y una celda esta null() no lo realiza.

## Las columna que no queremos que se formateen, es decir que no se convierta los null en cero
excepciones = ['FLAG_DSP_KYC','TIPO','NOMBRE FANTASIA','FLAG_DSP_KYC_x','TIPO_x',' NOMBRE FANTASIA_x','FLAG_DSP_KYC_y','TIPO_y',' NOMBRE FANTASIA_y']

## Generamos un vector con los campos a modificar
columnas_completar = [col for col in df_union4.columns if col not in excepciones]

## Reemplazamos los valores null() por 0 (CERO).
df_union4[columnas_completar] = df_union4[columnas_completar].fillna(0)

#CUANDO CALCULAMOS EL ENVIO SE HACE PARA EL CONSUMOS DEL MES SIGUIENTE CON LO CUAL AL STOCK DE AHORA SE LE DEBE RESTAR EL CONSUMO
#QUE EL AGENTE VA A HACER DURANTE EL MES EN CURSO.

df_union4["STOCK ROLLO"]=df_union4["STOCK ROLLO"]-df_union4["ROLLO_y"]
df_union4["STOCK RESMA"]=df_union4["STOCK RESMA"]-df_union4["RESMA_y"]

## df_union4.to_excel('AGENTESSINSTOCK.xlsx', sheet_name='TODO')

df_union4.loc[df_union4["STOCK ROLLO"]<0,"RESETEO ROLLO"]= 0
df_union4.loc[df_union4["STOCK ROLLO"]>=0,"RESETEO ROLLO"]= df_union4["STOCK ROLLO"]

df_union4.loc[df_union4["STOCK RESMA"]<0,"RESETEO RESMA"]= 0
df_union4.loc[df_union4["STOCK RESMA"]>=0,"RESETEO RESMA"]= df_union4["STOCK RESMA"]

## RESETEO SUBE, PRISMA

df_union4["STOCK PRISMA"]=df_union4["STOCK PRISMA"]-df_union4["ROLLO PRISMA_y"]
df_union4["STOCK SUBE"]=df_union4["STOCK SUBE"]-df_union4["ROLLO SUBE_y"]


## STOCK PRISMA
df_union4.loc[df_union4["STOCK PRISMA"]<0,"RESETEO PRISMA"]= 0
df_union4.loc[df_union4["STOCK PRISMA"]>=0,"RESETEO PRISMA"]= df_union4["STOCK PRISMA"]

## STOCK SUBE
df_union4.loc[df_union4["STOCK SUBE"]<0,"RESETEO SUBE"]= 0
df_union4.loc[df_union4["STOCK SUBE"]>=0,"RESETEO SUBE"]= df_union4["STOCK SUBE"]

## ROLLO, RESMAS, BOLSAS, FAJAS

#el calculo de  los rollos se hace en funcion de una regresion lineal de minimos cuadrados y lo multiplica por la segmentacion
df_union4["PENDIENTE"]=((df_union4["ROLLO"]*1+df_union4["ROLLO_x"]*2+df_union4["ROLLO_y"]*3)-2*(df_union4["ROLLO"]+df_union4["ROLLO_x"]+df_union4["ROLLO_y"]))/2
df_union4["ORDENADAORIGEN"]=((df_union4["ROLLO"]+df_union4["ROLLO_x"]+df_union4["ROLLO_y"])/3)-(df_union4["PENDIENTE"]*2)

#df_union4.to_excel('CALCULO_REGRESION_TEST.xlsx', sheet_name='DETALLE') - Export para validar la pendiente/ordenada al origen
#La regresion NO toma ningun criterio, hace el calculo de una regresion lineal normal.
#En funcion de la pendiente, hace el siguiente paso.
#Como la pendiente en negativa, no predice para el proximo mes, sino hace un promedio de los ultimos 3 meses.
#Como la pendiente es positiva, predice para el proximo mes, es decir para el 4to mes.


df_union4.loc[df_union4["PENDIENTE"]<=0,"ROLLOS REPO"]= ((((df_union4["ROLLO"]+df_union4["ROLLO_x"]+df_union4["ROLLO_y"])/3)*(df_union4["SUBSEGMENTACION"])*1.1)-df_union4["RESETEO ROLLO"])
df_union4.loc[df_union4["PENDIENTE"]>0,"ROLLOS REPO"]=((((df_union4["PENDIENTE"]*4 + df_union4["ORDENADAORIGEN"])*df_union4["SUBSEGMENTACION"])*1.1)-df_union4["RESETEO ROLLO"])
#SI EL ENVIO DA NEGATIVO SIGNIFICA QUE EL AGENTE CONTEMPLABA UN STOCK MAYOR AL ESTIMADO DE ENVIO

#el calculo de  lAS RESMAS se hace en fuincion de una regresion lineal de minimos cuadrados y lo multiplica por la segmentacion
df_union4["PENDIENTE1"]=((df_union4["RESMA"]*1+df_union4["RESMA_x"]*2+df_union4["RESMA_y"]*3)-2*(df_union4["RESMA"]+df_union4["RESMA_x"]+df_union4["RESMA_y"]))/2
df_union4["ORDENADAORIGEN1"]=((df_union4["RESMA"]+df_union4["RESMA_x"]+df_union4["RESMA_y"])/3)-(df_union4["PENDIENTE1"]*2)


df_union4.loc[df_union4["PENDIENTE1"]<=0,"RESMAS REPO"]= ((((df_union4["RESMA"]+df_union4["RESMA_x"]+df_union4["RESMA_y"])/3)*df_union4["SUBSEGMENTACION"])-df_union4["RESETEO RESMA"])
df_union4.loc[df_union4["PENDIENTE1"]>0,"RESMAS REPO"]=(((df_union4["PENDIENTE1"]*4 + df_union4["ORDENADAORIGEN1"])*df_union4["SUBSEGMENTACION"])-df_union4["RESETEO RESMA"])

# Se elimina Bolsas Verdes y Magentas, se consolidan y formar "BOLSAS RECOLECCION"

#df_union4["BOLSAS VERDES REPO"]=((df_union4["BOLSA VERDE"]+df_union4["BOLSA VERDE_x"]+df_union4["BOLSA VERDE_y"])/3)*df_union4["SUBSEGMENTACION"]

#df_union4["BOLSAS MAGENTAS REPO"]=((df_union4["BOLSA MAGENTA"]+df_union4["BOLSA MAGENTA_x"]+df_union4["BOLSA MAGENTA_y"])/3)*df_union4["SUBSEGMENTACION"]

df_union4["BOLSAS RECOLECCION REPO"] =  ((df_union4["BOLSA RECOLECCION"]+df_union4["BOLSA RECOLECCION_x"]+df_union4["BOLSA RECOLECCION_y"])/3)*df_union4["SUBSEGMENTACION"]

# si el agente figura como DEP=1 ENTONCES SE LE MANDA FAJAS Y SINO SE MANDA 0

df_union4.loc[df_union4["DEP"]==1,"FAJAS REPO"]=0
df_union4.loc[df_union4["DEP"]==0,"FAJAS REPO"]=(((df_union4["FAJAS"]+df_union4["FAJAS_x"]+df_union4["FAJAS_y"])/3)*df_union4["SUBSEGMENTACION"]*1.1).apply(np.ceil)

#LOS CONSUMOS NEGATIVOS LOS REDONDEO A 0 TANTO PARA ROLLOS COMO PARA RESMA

df_union4.loc[df_union4["ROLLOS REPO"]<=0,"ROLLOS REPO"]=0
df_union4.loc[df_union4["ROLLOS REPO"]>0,"ROLLOS REPO"]= df_union4["ROLLOS REPO"]

df_union4.loc[df_union4["RESMAS REPO"]<=0,"RESMAS REPO"]=0
df_union4.loc[df_union4["RESMAS REPO"]>0,"RESMAS REPO"]= df_union4["RESMAS REPO"]

##  REALIZA EL REDONDEO SOLO PARA ROLLOS Y RESMAS

#REDONDEO CON EL PARAMETRO 0.3 EL ENVIO DE CANTIDAD DE ROLLOS
df_union4["PARAMETRO"]=df_union4["ROLLOS REPO"]-df_union4["ROLLOS REPO"].apply(np.floor)
df_union4.loc[df_union4["PARAMETRO"]<=0.3 ,"ROLLOS REPO"]= df_union4["ROLLOS REPO"].apply(np.floor)
df_union4.loc[df_union4["PARAMETRO"]>0.3,"ROLLOS REPO"]= df_union4["ROLLOS REPO"].apply(np.ceil)

#REDONDEO CON EL PARAMETRO 0.3 EL ENVIO DE CANTIDAD DE RESMAS
df_union4["PARAMETRO2"]=df_union4["RESMAS REPO"]-df_union4["RESMAS REPO"].apply(np.floor)
df_union4.loc[df_union4["PARAMETRO2"]<=0.3 ,"RESMAS REPO"]= df_union4["RESMAS REPO"].apply(np.floor)
df_union4.loc[df_union4["PARAMETRO2"]>0.3,"RESMAS REPO"]= df_union4["RESMAS REPO"].apply(np.ceil)


# df_union4.to_excel('AGENTESSINSTOCK.xlsx', sheet_name='TODO')
# El archivo 'CONSUMO_U3M' es lo mismo que el archivo 'AGENTESSINSTOCK' pero se agrega las 2 columnas AVG_ROLLO y AVG_RESMA

#df_union4.to_excel('CONSUMO_U3M_REGRESION.xlsx', sheet_name='DETALLE')

#REGRESION LINEAL ROLLOS PRISMA y SUBE
#ROLLO TERMICO DEBITO POR "REGRESION LINEAL"

df_union4["PENDIENTE2"]=((df_union4["ROLLO PRISMA"]*1+df_union4["ROLLO PRISMA_x"]*2+df_union4["ROLLO PRISMA_y"]*3)-2*(df_union4["ROLLO PRISMA"]+df_union4["ROLLO PRISMA_x"]+df_union4["ROLLO PRISMA_y"]))/2
df_union4["ORDENADAORIGEN2"]=((df_union4["ROLLO PRISMA"]+df_union4["ROLLO PRISMA_x"]+df_union4["ROLLO PRISMA_y"])/3)-(df_union4["PENDIENTE2"]*2)


df_union4.loc[df_union4["PENDIENTE2"]<=0,"ROLLO TERMICO PRISMA"]= ((((df_union4["ROLLO PRISMA"]+df_union4["ROLLO PRISMA_x"]+df_union4["ROLLO PRISMA_y"])/3)*df_union4["SUBSEGMENTACION"])-df_union4["RESETEO PRISMA"]) ## SE AGREGA 0(cero) ya que no hay reseteo Rollo Debito
df_union4.loc[df_union4["PENDIENTE2"]>0,"ROLLO TERMICO PRISMA"]=(((df_union4["PENDIENTE2"]*4 + df_union4["ORDENADAORIGEN2"])*df_union4["SUBSEGMENTACION"])-df_union4["RESETEO PRISMA"]) ## SE AGREGA 0(cero) ya que no hay reseteo Rollo Debito

#ROLLO SUBE POR "REGRESION LINEAL"

df_union4["PENDIENTE3"]=((df_union4["ROLLO SUBE"]*1+df_union4["ROLLO SUBE_x"]*2+df_union4["ROLLO SUBE_y"]*3)-2*(df_union4["ROLLO SUBE"]+df_union4["ROLLO SUBE_x"]+df_union4["ROLLO SUBE_y"]))/2
df_union4["ORDENADAORIGEN3"]=((df_union4["ROLLO SUBE"]+df_union4["ROLLO SUBE_x"]+df_union4["ROLLO SUBE_y"])/3)-(df_union4["PENDIENTE3"]*2)


df_union4.loc[df_union4["PENDIENTE3"]<=0,"ROLLOS SUBE"]= ((((df_union4["ROLLO SUBE"]+df_union4["ROLLO SUBE_x"]+df_union4["ROLLO SUBE_y"])/3)*df_union4["SUBSEGMENTACION"])-df_union4["RESETEO SUBE"]) ## SE AGREGA 0(cero) ya que no hay reseteo ROLLO SUBE
df_union4.loc[df_union4["PENDIENTE3"]>0,"ROLLOS SUBE"]=(((df_union4["PENDIENTE3"]*4 + df_union4["ORDENADAORIGEN3"])*df_union4["SUBSEGMENTACION"])-df_union4["RESETEO SUBE"]) ## SE AGREGA 0(cero) ya que no hay reseteo Rollo SUBE

#LOS CONSUMOS NEGATIVOS LOS REDONDEO A 0
df_union4.loc[df_union4["ROLLO TERMICO PRISMA"]<=0,"ROLLO TERMICO PRISMA"]=0
df_union4.loc[df_union4["ROLLO TERMICO PRISMA"]>0,"ROLLO TERMICO PRISMA"]= df_union4["ROLLO TERMICO PRISMA"]

#REDONDEO CON EL PARAMETRO 0.2 EL ENVIO DE CANTIDAD DE ROLLOS DEBITO
df_union4["PARAMETRO3"]=df_union4["ROLLO TERMICO PRISMA"]-df_union4["ROLLO TERMICO PRISMA"].apply(np.floor)
df_union4.loc[df_union4["PARAMETRO3"]<=0.2 ,"ROLLO TERMICO PRISMA"]= df_union4["ROLLO TERMICO PRISMA"].apply(np.floor)
df_union4.loc[df_union4["PARAMETRO3"]>0.2,"ROLLO TERMICO PRISMA"]= df_union4["ROLLO TERMICO PRISMA"].apply(np.ceil)

#LOS CONSUMOS NEGATIVOS LOS REDONDEO A 0
df_union4.loc[df_union4["ROLLOS SUBE"]<=0,"ROLLOS SUBE"]=0
df_union4.loc[df_union4["ROLLOS SUBE"]>0,"ROLLOS SUBE"]= df_union4["ROLLOS SUBE"]

#REDONDEO CON EL PARAMETRO 0.3 EL ENVIO DE CANTIDAD DE ROLLOS SUBE
df_union4["PARAMETRO4"]=df_union4["ROLLOS SUBE"]-df_union4["ROLLOS SUBE"].apply(np.floor)
df_union4.loc[df_union4["PARAMETRO4"]<=0.3 ,"ROLLOS SUBE"]= df_union4["ROLLOS SUBE"].apply(np.floor)
df_union4.loc[df_union4["PARAMETRO4"]>0.3,"ROLLOS SUBE"]= df_union4["ROLLOS SUBE"].apply(np.ceil)

df_union4.to_excel(DIR_SALIDA / 'REPOSICION_DETALLADO.xlsx', sheet_name='DETALLE')

#Buscamos los siguientes tipos de agentes y le asignamos un 0 (cero) al valor de resma

# TIPO = 2 -> Agente Centros y Servicios
# TIPO = 3 -> Agente con comprobante de Txs internacionales
# TIPO = 4 -> Agente con Factura Termica
# TIPO = 5 -> Agente con Fac Termica + Comp. Txs Internacionales + DSP

df_union4.loc[df_union4["TIPO_y"] == 2 ,"RESMAS REPO"]= 0
df_union4.loc[df_union4["TIPO_y"] == 3 ,"RESMAS REPO"]= 0
df_union4.loc[df_union4["TIPO_y"] == 4 ,"RESMAS REPO"]= 0
df_union4.loc[df_union4["TIPO_y"] == 5 ,"RESMAS REPO"]= 0

# Cuando el agente es 1 NO le asigna, cuando es 0 le asigna bolsas.

# FLAG_DSP_KYC :
#   -- CONDICIONES
#-- SI TIENE DSP Y NO TIENE KYC, = 0
#-- SI NO TIENE DSP Y NO TIENE KYC, = 1
#-- SI NO TIENE DSP Y TIENE KYC, = 1
#-- SI TIENE DSP Y TIENE KYC, = 1

#Se elimina este filtro, ya que este se aplica en PowerBI directamente

#df_union4.loc[df_union4["FLAG_DSP_KYC_y"] == 1 ,"BOLSAS MAGENTAS REPO"]= 0


#todo lo que viene abajo es para generar el archivo repo como un listadito

pedidos_rollos=df_union4[['NOMBRE FANTASIA_y','PROV','ROLLOS REPO','SEGMENTO']]
pedidos_rollos.rename(columns={'ROLLOS REPO':'CANTIDAD'},inplace=True)

pedidos_rollos.loc[pedidos_rollos["PROV"]=='MENDOZA',"SKU"] = 9001222101
# pedidos_rollos.loc[pedidos_rollos["PROV"]=='MENDOZA',"SKU"] = 9001220102

pedidos_rollos.loc[pedidos_rollos["PROV"]!='MENDOZA',"SKU"] = 9001222100
# pedidos_rollos.loc[pedidos_rollos["PROV"]!='MENDOZA',"SKU"] = 9001220106

pedidos_rollos.loc[pedidos_rollos["PROV"]=='MENDOZA',"DESCRIPCION"]="ROLLO TERMICO MZA PF-WU x 5 R. PAPER"
pedidos_rollos.loc[pedidos_rollos["PROV"]!='MENDOZA',"DESCRIPCION"]="ROLLO TERMICO PF-WU x 5 R. PAPER"

pedidos_rollos=pedidos_rollos[['NOMBRE FANTASIA_y','SKU','DESCRIPCION','CANTIDAD','SEGMENTO']]

pedidos_resmas=df_union4[['NOMBRE FANTASIA_y','RESMAS REPO','SEGMENTO']]
pedidos_resmas.rename(columns={'RESMAS REPO':'CANTIDAD'},inplace=True)
pedidos_resmas["SKU"]=9001218106
pedidos_resmas["DESCRIPCION"]="RESMA DE PAPEL BLANCO TAMAÑO CARTA"
pedidos_resmas=pedidos_resmas[['NOMBRE FANTASIA_y','SKU','DESCRIPCION','CANTIDAD','SEGMENTO']]

# Se eliminan las Bolsas Verdes, Magentas y se reemplaza por "Pedido Recoleccion" consolida ambas bolsas

pedidos_recoleccion=df_union4[['NOMBRE FANTASIA_y','BOLSAS RECOLECCION REPO','SEGMENTO']]
pedidos_recoleccion.rename(columns={'BOLSAS RECOLECCION REPO':'CANTIDAD'},inplace=True)
pedidos_recoleccion["SKU"]= 9001219112
pedidos_recoleccion["DESCRIPCION"]="BOLSA RECOLECCION x 1 unid"
pedidos_recoleccion=pedidos_recoleccion[['NOMBRE FANTASIA_y','SKU','DESCRIPCION','CANTIDAD','SEGMENTO']]

pedidos_fajas=df_union4[['NOMBRE FANTASIA_y','FAJAS REPO','SEGMENTO']]
pedidos_fajas.rename(columns={'FAJAS REPO':'CANTIDAD'},inplace=True)
pedidos_fajas["SKU"]=9001214107
pedidos_fajas["DESCRIPCION"]="FAJAS DE BILLETES x 200 unid"
pedidos_fajas=pedidos_fajas[['NOMBRE FANTASIA_y','SKU','DESCRIPCION','CANTIDAD','SEGMENTO']]

pedido_rollo_debito = df_union4[['NOMBRE FANTASIA_y','ROLLO TERMICO PRISMA','SEGMENTO']]
pedido_rollo_debito.rename(columns={'ROLLO TERMICO PRISMA':'CANTIDAD'},inplace=True)
pedido_rollo_debito["SKU"]=9001223489
pedido_rollo_debito["DESCRIPCION"]="ROLLO TERMICO DEBITO PRISMA x 5 unid"
pedido_rollo_debito=pedido_rollo_debito[['NOMBRE FANTASIA_y','SKU','DESCRIPCION','CANTIDAD','SEGMENTO']]

pedido_rollo_sube = df_union4[['NOMBRE FANTASIA_y','ROLLOS SUBE','SEGMENTO']]
pedido_rollo_sube.rename(columns={'ROLLOS SUBE':'CANTIDAD'},inplace=True)
pedido_rollo_sube["SKU"]=9001214102
pedido_rollo_sube["DESCRIPCION"]="ROLLO TERMICOS SUBE x 5 unid "
pedido_rollo_sube=pedido_rollo_sube[['NOMBRE FANTASIA_y','SKU','DESCRIPCION','CANTIDAD','SEGMENTO']]

frames = [pedidos_rollos,pedidos_resmas,pedidos_recoleccion,pedidos_fajas,pedido_rollo_debito,pedido_rollo_sube]
REPOSICION= pd.concat(frames)

#REDONDEA TODOS LOS VALORES PARA ARRIBA DE BOLSAS MAGENTAS Y VERDES

REPOSICION['CANTIDAD']=REPOSICION['CANTIDAD'].apply(np.ceil)

#ELIMINA TODAS LAS FILAS QUE TENGAN EL VALOR NULL() EN CANTIDAD

REPOSICION=REPOSICION.dropna(subset=['CANTIDAD'])

REPOSICION=REPOSICION[REPOSICION['CANTIDAD']!=0]

# AJUSTES POR CAMBIO DE SOFTWARE DE LA IMPRESORA TERMINCA
# FASE 1: SOLO CANAL PROPIO
# FILTRO: SKU (9001223209,9001223210) AND NOMBRE FANTASIA_y CONTAINS 'C.S.'
# ACCION: CANTIDAD -18% ROUND UP 0d
# SECCION-DESARROLLO-1

# Crear un filtro para las condiciones especificadas (corregido con .str.contains)
filtro_cs = (REPOSICION['NOMBRE FANTASIA_y'].str.contains('C.S.', na=False)) & (REPOSICION['SKU'].isin([9001222100, 9001222101]))

# Aplicar el ajuste a la columna 'CANTIDAD' para las filas que cumplen con el filtro
# Se multiplica por 0.82 (que es 1 - 0.18) y se redondea al entero superior con np.ceil
REPOSICION.loc[filtro_cs, 'CANTIDAD'] = REPOSICION.loc[filtro_cs, 'CANTIDAD'].apply(lambda x: np.ceil(x * 0.82))

#ultimo paso genera el archivo reposición en la carpeta.
REPOSICION.to_excel(DIR_SALIDA / 'REPOSICION_CRUDO_FINAL_.xlsx', sheet_name='DETALLE')
