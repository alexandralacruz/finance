import pandas as pd
from app.core.utils import get_exchange_rate, convert_currency

def convert_column_currency(
    df: pd.DataFrame,
    column: str,
    target_currency: str,
    usd_to_cop: float
) -> pd.Series:
    """
    Convierte una columna monetaria a la moneda destino (COP o USD).
    """
    if target_currency == "COP":
        return df[column].where(
            df["MONEDA"] == "COP",
            df[column] * usd_to_cop
        )
    else:  # USD
        return df[column].where(
            df["MONEDA"] == "USD",
            df[column] / usd_to_cop
        )


def month_summary(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["FECHA"] = pd.to_datetime(df["FECHA"])
    df["MES"] = df["FECHA"].dt.to_period("M")

    df["INGRESO"] = df["CREDIT/DEBIT"].clip(lower=0)
    df["EGRESO"] = (-df["CREDIT/DEBIT"]).clip(lower=0)

    return (
        df
        .groupby("MES", as_index=False)
        .agg(
            saldo_inicio=("SALDO", "first"),
            saldo_final=("SALDO", "last"),
            ingreso_mes=("INGRESO", "sum"),
            gasto_mes=("EGRESO", "sum"),
        )
    )


def monthSummary(df_sorted: pd.DataFrame) -> pd.DataFrame:
    """ 
    Calcula el saldo inicial, saldo final, gasto e ingreso por mes.

    Parameters:
    df_sorted (pd.DataFrame): DataFrame ordenado por la columna 'FECHA'.

    Returns:
    pd.DataFrame: Un DataFrame con las columnas 'MES', 'saldo_inicio', 'saldo_final', 'gasto_mes' e 'ingreso_mes'.
    """
    # Paso 1: Asegurarse de que la columna FECHA sea de tipo datetime
    df_sorted['FECHA'] = pd.to_datetime(df_sorted['FECHA'])

    # Paso 2: Crear una columna 'MES' que contenga año y mes
    df_sorted['MES'] = df_sorted['FECHA'].dt.to_period('M')  # Agrupa por mes y año

    # Paso 3: Agrupar por 'MES' y calcular los valores solicitados
    result = df_sorted.groupby('MES').agg(
        saldo_inicio=('SALDO', 'first'),          # Saldo del inicio del mes
        saldo_final=('SALDO', 'last'),            # Saldo del final del mes
        gasto_mes=('CREDIT/DEBIT', lambda x: x[x < 0].sum()),   # Gasto por mes (sumar valores negativos)
        ingreso_mes=('CREDIT/DEBIT', lambda x: x[x > 0].sum())  # Ingreso por mes (sumar valores positivos)
    ).reset_index()

    # Mostrar el resultado
    return result

def clasificar_transaccion(descripcion:str, categorias:dict)->str:
    """
    Clasifica una transacción basada en su descripción usando categorías predefinidas.

    Parameters:
    descripcion (str): La descripción de la transacción.
    categorias (dict): Un diccionario que contiene categorías y una lista de palabras clave asociadas.

    Returns:
    str: La categoría correspondiente si se encuentra una coincidencia, de lo contrario 'otros'.
    """
    for categoria, detalles in categorias.items():
        for keyword in detalles["lista"]:
            if keyword in descripcion:
                return categoria
    return 'otros'  # Si no coincide con ninguna categoría

def summarize_dataframe(df: pd.DataFrame, usd_to_cop: float, currency: str = "COP"):
    df = df.copy()

    df["CREDIT/DEBIT_CONV"] = convert_column_currency(
        df,
        column="CREDIT/DEBIT",
        target_currency=currency,
        usd_to_cop=usd_to_cop
    )

    income = df.loc[df["CREDIT/DEBIT_CONV"] > 0, "CREDIT/DEBIT_CONV"].sum()
    expenses = -df.loc[df["CREDIT/DEBIT_CONV"] < 0, "CREDIT/DEBIT_CONV"].sum()

    return {
        "totalBalance": round(income - expenses, 2),
        "entities": df["ENTIDAD"].nunique(),
        "income": round(income, 2),
        "expenses": round(expenses, 2),
        "currency": currency
    }


# def summarize_dataframe(df, usd_to_cop, currency='COP'):
#     """
#     Resume el DataFrame en total balance, número de entidades, ingresos y gastos
#     en la moneda deseada (COP o USD).
    
#     df: DataFrame con columnas ['FECHA','DESCRIPCION','CREDIT/DEBIT','SALDO','MONEDA','ENTIDAD']
#     usd_to_cop: tasa de conversión USD -> COP
#     currency: 'COP' o 'USD'
#     """
#     # Función para convertir cualquier monto a la moneda deseada
#     def convert_amount(row, col):
#         val = row[col]
#         if row['MONEDA'] == 'USD':
#             val_cop = val * usd_to_cop
#             return val_cop if currency == 'COP' else val
#         else:  # MONEDA == 'COP'
#             return val if currency == 'COP' else val / usd_to_cop

#     df['CREDIT/DEBIT_CONV'] = df.apply(lambda row: convert_amount(row, 'CREDIT/DEBIT'), axis=1)
    
    

#     entities = df['ENTIDAD'].nunique()
#     income = df[df['CREDIT/DEBIT_CONV'] > 0]['CREDIT/DEBIT_CONV'].sum()
#     expenses = -df[df['CREDIT/DEBIT_CONV'] < 0]['CREDIT/DEBIT_CONV'].sum()  # positivo
#     # Total balance: Ingresos -gastos
#     total_balance = income - expenses
#     resumen = {
#         "totalBalance": round(total_balance, 2),
#         "entities": entities,
#         "income": round(income, 2),
#         "expenses": round(expenses, 2),
#         "currency": currency
#     }

#     return resumen



def summary_report(df, currency='USD'):
    df = df.copy()

    df['FECHA'] = pd.to_datetime(df['FECHA'])

    df['INGRESO'] = df['CREDIT/DEBIT'].clip(lower=0)
    df['EGRESO']  = (-df['CREDIT/DEBIT']).clip(lower=0)

    resumen = (
        df
        .groupby(['MONEDA', 'ENTIDAD'], as_index=False)
        .agg(
            INGRESO=('INGRESO', 'sum'),
            EGRESO=('EGRESO', 'sum')
        )
    )

    saldo = (
        df.loc[
            df.groupby(['MONEDA', 'ENTIDAD'])['FECHA'].idxmax(),
            ['MONEDA', 'ENTIDAD', 'SALDO']
        ]
    )

    resumen = resumen.merge(saldo, on=['MONEDA', 'ENTIDAD'], how='left')
    rates = {
        m: get_exchange_rate(m)
        for m in resumen['MONEDA'].unique()
        if m != currency
    }
    mask = resumen['MONEDA'] != currency
    for col in ['INGRESO', 'EGRESO', 'SALDO']:
        resumen.loc[mask, col] = resumen.loc[mask].apply(
            lambda r: r[col] * rates[r['MONEDA']],
            axis=1
        )

    resumen.loc[:, 'MONEDA'] = currency
    resumen['BALANCE'] = resumen['INGRESO'] - resumen['EGRESO']

    # --- Resumen global ---
    total = {
        "currency": currency,
        "income": round(resumen['INGRESO'].sum(), 2),
        "expenses": round(resumen['EGRESO'].sum(), 2),
        "totalBalance": round(resumen['SALDO'].sum(), 2),
        "entities": resumen['ENTIDAD'].nunique()
    }
    return total

