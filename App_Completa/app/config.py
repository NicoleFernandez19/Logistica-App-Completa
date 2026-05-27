PARAMETROS = {
    "factor_ajuste_rollos": 1.1,
    "redondeo_rollos": 0.3,
    "redondeo_rollos_prisma": 0.2,
    "redondeo_rollos_sube": 0.3,
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
]

AGENTES_A_EXCLUIR = []
