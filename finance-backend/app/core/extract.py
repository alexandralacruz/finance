import pandas as pd
import os
from app.core import config
from pathlib import Path
import json

def read_json(file: str) -> dict:
    '''
    Lee un archivo JSON y lo convierte en un diccionario de Python.
    '''
    with open(file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    return json_data


def read_categories_class() -> dict:
    '''
    Lee el archivo JSON que contiene las categorías de clasificación de transacciones.
    '''
    file = str(Path(config.DATASET_ROOT_PATH) / "json/descripcion_BC.json")
    return read_json(file)

def extract_from_period(file: str) -> pd.DataFrame: 
    '''
    Lee un archivo de texto con formato de tab y lo convierte en un DataFrame de Pandas.
    '''
    df =  pd.read_csv(file, sep='\t', encoding='ISO-8859-1') 
    return df

def extract_from_period_xls(file: str) -> pd.DataFrame: 
    '''
    Lee un archivo de texto con formato de tab y lo convierte en un DataFrame de Pandas.
    '''
    #print(f"Processing file (extract_from_period_xls): {file}")
    df =  pd.read_excel(file) 
    #print(f"Columns found: {df.columns}")
    df.rename(columns={'Fecha':'FECHA','Valor':'CREDIT/DEBIT','Descripción':'DESCRIPCION'}, inplace=True)
    df.drop(columns=['Referencia'], inplace=True)
    df['FECHA'] = pd.to_datetime(df['FECHA'], format='%d/%m/%Y')
    df.sort_index(ascending=False, inplace=True)
    
    #print(f"Columns found: {df.columns}")
    #print (df.head())
    return df

def extract_from_extrato_file(file: str) -> pd.DataFrame:
    '''
    Lee un archivo de extracto bancario en formato Excel y lo convierte en un DataFrame de Pandas.

    '''
    try:
        df_xls = pd.read_excel(file)  # If it's tab-separated, specify sep="\t"
        #print(df_xls.head())  # Display first few rows to confirm the data
    except FileNotFoundError:
        #print(f"File not found at {file}. Please check the file path.")
        raise f"File not found at {file}. Please check the file path."
    except ValueError as e:
        #print(f"Error reading the file: {e}")
        raise f"Error reading the file: {e}"
    
    # Find all the indices where 'FECHA' and 'FIN ESTADO DE CUENTA' occur
    start_indices = df_xls[df_xls['Unnamed: 0'].str.contains("FECHA", na=False)].index
    end_indices = df_xls[df_xls['Unnamed: 0'].str.contains("Información Cliente:", na=False)].index

    # Lista para almacenar los DataFrames extraídos
    extracted_data = []
    cont = 0
    # Recorrer las listas de índices Start y End
    for start, end in zip(start_indices, end_indices[1:]):
        # Asegúrate de que el índice 'start' sea mayor que el 'end' para seleccionar el rango correcto
        if end > start:
            df_slot = df_xls.iloc[start+1:end]  # Incluyendo el índice 'end'
            cont = cont + len(df_slot)
            extracted_data.append(df_slot)

    start = start_indices[-1]
    df_slot = df_xls.iloc[start+1:]  # Incluyendo el índice 'end'
    cont = cont + len(df_slot)
    extracted_data.append(df_slot)

    # Now extracted_data is a list of DataFrames. Check if we have any data to concatenate
    if extracted_data:
        df_all_slots = pd.concat(extracted_data, ignore_index=True)
        df_cleaned = df_all_slots.dropna(axis=1, how='all')
        df_cleaned = df_cleaned.rename(columns={'Unnamed: 0': 'FECHA', 'Unnamed: 1': 'DESCRIPCION', 'Unnamed: 4': 'CREDIT/DEBIT', 'Unnamed: 5': 'SALDO'})
        df_cleaned = df_cleaned.drop(columns=['Unnamed: 2']) if 'Unnamed: 2' in df_cleaned.columns else df_cleaned
        df_cleaned = df_cleaned[~df_cleaned['DESCRIPCION'].str.contains("FIN ESTADO DE CUENTA", na=False)]
        return df_cleaned
    else:
        raise "No data was extracted between the FECHA and FIN ESTADO DE CUENTA pairs."



def extractFromFolderYear(baseFolder:str, year:int) -> pd.DataFrame:
    '''
    Extrae los datos de los archivos de extracto bancario de un año específico en una carpeta.
    '''
    # folder base
    folder = baseFolder + "/BC/" + str(year)
    #print(f"Extracting data from folder: {folder}")
    # Lista para almacenar los DataFrames extraídos
    df_list = []

    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.xlsx') or file.endswith('.xls'):  # Filtra solo los archivos Excel
                file_path = os.path.join(root, file)  # Construye la ruta completa del archivo
                # Leer el archivo Excel en un DataFrame
                df = extract_from_extrato_file(file_path)
                # Añadir el DataFrame a la lista
                df_list.append(df)

    # Concatenar todos los DataFrames en uno solo
    df_combined = pd.concat(df_list, ignore_index=True)
    df_combined[['CREDIT/DEBIT', 'SALDO']] = df_combined[['CREDIT/DEBIT', 'SALDO']].apply(lambda x: x.str.replace(',', '').astype(float))
    return df_combined

def extractExtractosFromFolderYearBC(baseFolder:str, year:int) -> pd.DataFrame:
    '''
    Extrae los datos de los archivos de extracto bancario de un año específico en una carpeta.
    '''
    # folder base
    folder = baseFolder + "/" + str(year) + "/BC/Extractos"
    #print(f"Extracting data from folder: {folder}")
    # Lista para almacenar los DataFrames extraídos
    df_list = []

    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.xlsx') or file.endswith('.xls'):  # Filtra solo los archivos Excel
                #print(f"Processing file (extractExtractosFromFolderYearBC): {file}")
                file_path = os.path.join(root, file)  # Construye la ruta completa del archivo
                # Leer el archivo Excel en un DataFrame
                df = extract_from_extrato_file(file_path)
                #print(f"Extracted {df.columns} columns.")
                # Añadir el DataFrame a la lista
                df_list.append(df)

    #print(f"Extracting data from folder: {folder} with df_list length: {len(df_list)}")
    folder = baseFolder + "/" + str(year) + "/BC/Periodos"
    for root, dirs, files in os.walk(folder):
        for file in files:
             if file.endswith('.xlsx') or file.endswith('.xls'):  # Filtra solo los archivos Excel
                #print(f"Processing file (extractExtractosFromFolderYearBC): {file}")
                file_path = os.path.join(root, file)  # Construye la ruta completa del archivo
                # Leer el archivo Excel en un DataFrame
                df = extract_from_period_xls(file_path)
                # Añadir el DataFrame a la lista
                df_list.append(df)
    #print(f"Extracting data from folder: {folder}")
    # Lista para almacenar los DataFrames extraídos

    
    
    # Concatenar todos los DataFrames en uno solo
    if df_list:
        df_combined = pd.concat(df_list, ignore_index=True)
        df_combined['FECHA'] = pd.to_datetime(df_combined['FECHA'] + '/'+ str(year), format='%d/%m/%Y')
        df_combined[['CREDIT/DEBIT', 'SALDO']] = df_combined[['CREDIT/DEBIT', 'SALDO']].apply(lambda x: x.str.replace(',', '').astype(float))
        df_combined['MONEDA'] = 'COP'   
        df_combined['ENTIDAD'] = 'BC' 
        return df_combined 
    else:
        return pd.DataFrame()


def summary_by_year(df: pd.DataFrame) -> dict:
    '''
    Genera un resumen financiero anual a partir de un DataFrame de transacciones.
    '''
    total_balance = df['SALDO'].iloc[-1]
    income = df[df['CREDIT/DEBIT'] > 0]['CREDIT/DEBIT'].sum()
    expenses = df[df['CREDIT/DEBIT'] < 0]['CREDIT/DEBIT'].sum() * -1
    entities = df['DESCRIPCION'].nunique()

    summary = {
        "totalBalance": round(total_balance, 2),
        "income": round(income, 2),
        "expenses": round(expenses, 2),
        "entities": entities
    }
    return summary  

def extract_dataset(baseFolder, year):
    '''
    Extrae los años disponibles en la carpeta del conjunto de datos.
    '''
    folder = Path(baseFolder) / str(year)  # Keep as Path object
    subfolders = [f.name for f in folder.iterdir() if f.is_dir()]

    dfs = []
    
    
    #print(f"Subfolders found in {folder}: {subfolders}")
    if 'BC' in subfolders:
        #print("Extracting BC data...")
        try:
            dfs.append(extractExtractosFromFolderYearBC(baseFolder, year))
            #print(f"BC data extracted for year {baseFolder} {year}")
        except Exception as e:
            print(f"Error extracting BC data for year {year}: {e}")

    if 'Amerant' in subfolders:
        #print("Extracting Amerant data...")
        try:
            dfs.append(extract_amerant(baseFolder, year))
            #print(f"Amerant data extracted for year {baseFolder} {year}")
        except Exception as e:
            print(f"Error extracting Amerant data for year {year}: {e}")

    if 'Payoneer' in subfolders:
        #print("Extracting Payoneer data...")
        try:
            dfs.append(extract_payoneer(baseFolder, year))
            #print(f"payoneer data extracted for year {baseFolder} {year}")
        except Exception as e:
            print(f"Error extracting Payoneer data for year {year}: {e}")

    # sort by date for each entity before concatenation
    for i in range(len(dfs)):
        #dfs[i]['FECHA'] = pd.to_datetime(dfs[i]['FECHA'])
        dfs[i] = dfs[i].sort_values(by='FECHA').reset_index(drop=True)

    if dfs:
        df = pd.concat(dfs, ignore_index=True)
    else:
        df = pd.DataFrame()  
    return df


def get_subfolders(root_folder: str) -> list[str]:
    """
    Retorna todos los subdirectorios a partir de un folder raíz.
    """
    root = Path(root_folder)

    if not root.exists() or not root.is_dir():
        raise ValueError(f"Ruta inválida: {root_folder}")

    return [str(p) for p in root.rglob('*') if p.is_dir()]


def extract_amerant(folder, year):
    file = str(Path(folder) / f"{year}/Amerant/INTLSAVINGS-7520 {year}.xls")
    #print(file)
    if not Path(file).exists():
        raise f"File not found at {file}. Please check the file path."
    
    df = pd.read_excel(file, skiprows=1)
    df = df.drop(df.index[-1])
    df = df.sort_values(by='Date').reset_index(drop=True)
    df['CREDIT/DEBIT'] = df.apply(
        lambda row: -row['Debit Amount'] if pd.notnull(row['Debit Amount']) else row['Credit Amount'], axis=1
    )
    df = df.drop(columns=['Debit Amount', 'Credit Amount'])
    df = df.rename(columns={'Description': 'DESCRIPCION', 'Date': 'FECHA', 'Running Balance': 'SALDO'})
    df = df.drop(columns=['Check Number'])
    df['MONEDA'] = 'USD'   
    df['ENTIDAD'] = 'AMERANT' 
    
    return df

def extract_payoneer(folder, year):
    #print(folder, year)
    file = str(Path(folder) / f"{year}/Payoneer/USD transactions {year}.csv")
    #print(f"file from extract payoneer {file}")
    if not Path(file).exists():
        raise f"File not found at {file}. Please check the file path."
    
    df = pd.read_csv(file)
    df['FECHA'] = pd.to_datetime(
        df['Transaction date'] + ' ' + df['Transaction time']
        )
    df['CREDIT/DEBIT'] = (
        df['Credit amount'].fillna(0) +
        df['Debit amount'].fillna(0)
        )
    df = df.rename(columns={
            'Description': 'DESCRIPCION',
            'Running balance': 'SALDO',
            'Currency': 'MONEDA'
        })
    
    #df = df.drop(df.index[-1])
    #df = df.sort_values(by='Date').reset_index(drop=True)
    #df['CREDIT/DEBIT'] = df.apply(
    #    lambda row: -row['Debit Amount'] if pd.notnull(row['Debit Amount']) else row['Credit Amount'], axis=1
    #)
    #df = df.drop(columns=['Debit Amount', 'Credit Amount'])
    #df = df.rename(columns={'Description': 'DESCRIPCION', 'Date': 'FECHA', 'Running Balance': 'SALDO'})
    #df = df.drop(columns=['Check Number'])
    df = df[['FECHA', 'DESCRIPCION', 'CREDIT/DEBIT', 'SALDO', 'MONEDA']]
    df['ENTIDAD'] = 'PAYONEER' 
    return df

def getBalanceByEntity(df, usd_to_cop, currency='COP'):
    """
    Resume el balance por entidad en la moneda deseada (COP o USD).
    
    Parámetros:
    - df: DataFrame con columnas ['FECHA', 'DESCRIPCION', 'CREDIT/DEBIT', 'SALDO', 'MONEDA', 'ENTIDAD']
    - usd_to_cop: tasa de conversión USD -> COP (ej: 4200)
    - currency: 'COP' o 'USD' (moneda de salida)
    
    Retorna:
    DataFrame con columnas:
    - ENTIDAD
    - total_balance: saldo neto final convertido
    - income: suma de créditos (ingresos)
    - expenses: suma de débitos en positivo (gastos)
    """
    
    # Aseguramos que el DataFrame esté ordenado por entidad y fecha (más reciente al final)
    df = df.sort_values(['ENTIDAD', 'FECHA']).reset_index(drop=True)
    
    # Tomar el último registro de cada entidad (contiene el SALDO final)
    last_rows = df.groupby('ENTIDAD').tail(1)[['ENTIDAD', 'SALDO', 'MONEDA']]
    
    # Función para convertir el saldo a la moneda deseada
    def convert_balance(row):
        saldo = row['SALDO']
        moneda_orig = row['MONEDA']
        
        if pd.isna(saldo):
            return 0.0
        
        if moneda_orig == 'USD':
            return round(saldo * usd_to_cop if currency == 'COP' else saldo,2)
        else:  # 'COP'
            return round(saldo if currency == 'COP' else saldo / usd_to_cop,2)
    # Aplicar conversión
    last_rows['BALANCE_FINAL'] = last_rows.apply(convert_balance, axis=1)
    #print(last_rows)

    result = {
    "currency": currency,
    "entities": (
            last_rows[['ENTIDAD', 'BALANCE_FINAL']]
            .dropna()
            .to_dict(orient='records')
        )
    }
    #
    # print(result)
    
    return result

def getBalanceByMonth(df, usd_to_cop, currency='COP'):
    """
    Resume el balance mensual en la moneda deseada (COP o USD).
    
    Parámetros:
    - df: DataFrame con columnas ['FECHA', 'DESCRIPCION', 'CREDIT/DEBIT', 'SALDO', 'MONEDA', 'ENTIDAD']
    - usd_to_cop: tasa de conversión USD -> COP (ej: 4200)
    - currency: 'COP' o 'USD' (moneda de salida)
    
    Retorna:
    DataFrame con columnas:
    - MES
    - total_balance: saldo neto final convertido
    - income: suma de créditos (ingresos)
    - expenses: suma de débitos en positivo (gastos)
    """
    df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
    # Crear columna de mes-año
    df['MES'] = df['FECHA'].dt.to_period('M').astype(str)
    
    # Función para convertir montos a la moneda deseada
    def convert_value(value, moneda_orig):
        if pd.isna(value):
            return 0.0

        if moneda_orig == 'USD':
            return value * usd_to_cop if currency == 'COP' else value
        else:  # COP
            return value if currency == 'COP' else value / usd_to_cop

    
    
    # Agrupar por MES y calcular totales convertidos
    # Aplicar conversión
    df['SALDO_CONV'] = df.apply(
        lambda r: round(convert_value(r['SALDO'], r['MONEDA']), 2),
        axis=1
    )
    
    df['MOV_CONV'] = df.apply(
        lambda r: round(convert_value(r['CREDIT/DEBIT'], r['MONEDA']), 2),
        axis=1
    )

    summary = (
        df.sort_values('FECHA')
          .groupby('MES')
          .agg(
              total_balance=('SALDO_CONV', 'last'),
              income=('MOV_CONV', lambda s: s[s > 0].sum()),
              expenses=('MOV_CONV', lambda s: -s[s < 0].sum())
          )
          .reset_index()
    )
    
    return summary.to_dict(orient='records')