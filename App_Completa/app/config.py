MESES_NOMBRE = {
    1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO",
    7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE",
}
MESES_A_NUMERO = {nombre.lower(): numero for numero, nombre in MESES_NOMBRE.items()}
MESES_A_NUMERO["setiembre"] = 9  # variante ortografica usada en algunos nombres de archivo

PARAMETROS = {
    "factor_ajuste_rollos": 1.1,
    "factor_ajuste_fajas": 1.1,
    "redondeo_rollos": 0.3,
    "redondeo_rollos_prisma": 0.2,
    "redondeo_rollos_sube": 0.3,
    "redondeo_resma": 0.3,
    "ajuste_canal_propio": 0.82,
}

REGLAS = {
    "skus_ajuste_canal_propio": [9001222100, 9001222101],
}

PRODUCTOS = [
    {
        "nombre_base": "ROLLO",
        "col_repo": "ROLLOS REPO",
        "col_stock_reseteo": "RESETEO ROLLO",
        "metodo": "regresion",
        "factor_ajuste": "factor_ajuste_rollos",
        "param_redondeo": "redondeo_rollos",
        "sku_base": 9001222100,
        "desc_base": "ROLLO TERMICO PF-WU x 5 R. PAPER",
        "prov_excluir": "MENDOZA",
    },
    {
        "nombre_base": "ROLLO MENDOZA",
        "col_consumo": "ROLLO",
        "col_repo": "ROLLOS REPO MENDOZA",
        "col_stock_reseteo": "RESETEO ROLLO",
        "metodo": "regresion",
        "factor_ajuste": "factor_ajuste_rollos",
        "param_redondeo": "redondeo_rollos",
        "sku_base": 9001222101,
        "desc_base": "ROLLO TERMICO MZA PF-WU x 5 R. PAPER",
        "prov_filter": "MENDOZA",
    },
    {
        "nombre_base": "BOLSA RECOLECCION",
        "col_repo": "BOLSAS RECOLECCION REPO",
        "col_stock_reseteo": None,
        "metodo": "promedio",
        "factor_ajuste": None,
        "param_redondeo": None,
        "sku_base": 9001219112,
        "desc_base": "BOLSA RECOLECCION x 1 unid",
    },
    {
        "nombre_base": "ROLLO PRISMA",
        "col_repo": "ROLLO TERMICO PRISMA",
        "col_stock_reseteo": "RESETEO PRISMA",
        "metodo": "regresion",
        "factor_ajuste": None,
        "param_redondeo": "redondeo_rollos_prisma",
        "sku_base": 9001223489,
        "desc_base": "ROLLO TERMICO DEBITO PRISMA x 5 unid",
    },
    {
        "nombre_base": "ROLLO SUBE",
        "col_repo": "ROLLOS SUBE",
        "col_stock_reseteo": "RESETEO SUBE",
        "metodo": "regresion",
        "factor_ajuste": None,
        "param_redondeo": "redondeo_rollos_sube",
        "sku_base": 9001214102,
        "desc_base": "ROLLO TERMICOS SUBE x 5 unid",
    },
    {
        "nombre_base": "RESMA",
        "col_repo": "RESMA REPO",
        "col_stock_reseteo": "RESETEO RESMA",
        "metodo": "regresion",
        "factor_ajuste": None,
        "param_redondeo": "redondeo_resma",
        "sku_base": 9001218106,
        "desc_base": "RESMA DE PAPEL BLANCO TAMAÑO CARTA",
    },
    {
        "nombre_base": "FAJAS",
        "col_repo": "FAJAS REPO",
        "col_stock_reseteo": None,
        "metodo": "promedio_ajustado_dep",
        "factor_ajuste": "factor_ajuste_fajas",
        "param_redondeo": None,
        "sku_base": 9001214107,
        "desc_base": "FAJAS DE BILLETES x 200 unid",
    },
]

AGENTES_A_EXCLUIR = []
