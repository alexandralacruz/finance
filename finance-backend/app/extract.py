import pandas as pd
import os
from app import config
from pathlib import Path
import json
from datetime import date, datetime

import logging

logger = logging.getLogger("finance.extract")

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
    #df['FECHA'] = pd.to_datetime(df['FECHA'], format='%d/%m/%Y')
    df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')

    
        
    df.sort_index(ascending=False, inplace=True)
    
    #print(f"Columns found: {df.columns}")
    #print (df.head())
    return df

def extract_from_extrato_file(file: str, year: int = None) -> pd.DataFrame:
    '''
    Lee un archivo de extracto bancario en formato Excel y lo convierte en un DataFrame de Pandas.
    '''
    import re

    try:
        df_xls = pd.read_excel(file, header=None)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found at {file}")
    except ValueError as e:
        raise ValueError(f"Error reading Excel format in {file}: {e}")

    # Try to extract year from the file metadata (DESDE/HASTA dates)
    if year is None:
        for i in range(min(30, len(df_xls))):
            row_text = ' '.join([str(c) for c in df_xls.iloc[i] if pd.notna(c)])
            m = re.search(r'(\d{4})/(\d{2})/(\d{2})', row_text)
            if m:
                year = int(m.group(1))
                break
        if year is None:
            year = datetime.now().year

    # Find all the indices where 'FECHA' header row appears and 'Información Cliente:' ends a block
    start_indices = df_xls[df_xls[0].astype(str).str.contains("FECHA", na=False)].index
    end_indices = df_xls[df_xls[0].astype(str).str.contains("Información Cliente:", na=False)].index

    if len(start_indices) == 0:
        raise ValueError(f"No 'FECHA' header found in {file}")

    extracted_data = []
    for start, end in zip(start_indices, list(end_indices[1:]) + [len(df_xls)]):
        if end > start:
            df_slot = df_xls.iloc[start+1:end]
            extracted_data.append(df_slot)

    if not extracted_data:
        raise ValueError("No data blocks extracted")

    df_all_slots = pd.concat(extracted_data, ignore_index=True)
    df_cleaned = df_all_slots.dropna(axis=1, how='all')
    df_cleaned = df_cleaned[[0, 1, 4, 5]]  # Columns: FECHA, DESCRIPCION, VALOR, SALDO
    df_cleaned.columns = ['FECHA', 'DESCRIPCION', 'CREDIT/DEBIT', 'SALDO']

    # Remove summary/header rows
    df_cleaned = df_cleaned[~df_cleaned['DESCRIPCION'].astype(str).str.contains(
        "FIN ESTADO DE CUENTA|SALDO ANTERIOR|TOTAL ABONOS|TOTAL CARGOS|SALDO ACTUAL|DESCRIPCIÓN", na=False)]
    df_cleaned = df_cleaned.dropna(subset=['CREDIT/DEBIT'])

    # Parse dates: DD/MM → YYYY-MM-DD
    def _parse_date(val):
        val = str(val).strip()
        try:
            parts = val.split('/')
            if len(parts) == 2:
                day, month = int(parts[0]), int(parts[1])
                return date(year, month, day)
            return pd.to_datetime(val, errors='coerce').date()
        except Exception:
            return None

    df_cleaned['FECHA'] = df_cleaned['FECHA'].apply(_parse_date)
    df_cleaned = df_cleaned.dropna(subset=['FECHA'])

    # Parse numeric values (handle comma thousands separator)
    for col in ['CREDIT/DEBIT', 'SALDO']:
        df_cleaned[col] = pd.to_numeric(
            df_cleaned[col].astype(str).str.replace(',', '').str.strip(),
            errors='coerce'
        )

    df_cleaned = df_cleaned.dropna(subset=['CREDIT/DEBIT'])
    return df_cleaned



def extractFromFolderYear(baseFolder:str, year:int) -> pd.DataFrame:
    '''
    Extrae los datos de los archivos de extracto bancario de un año específico en una carpeta.
    '''
    # folder base
    #folder = baseFolder + "/BC/" + str(year)
    folder = Path(baseFolder) / str(year) / "BC"
    #print(f"Extracting data from folder: {folder}")
    # Lista para almacenar los DataFrames extraídos
    df_list = []

    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.xlsx') or file.endswith('.xls'):  # Filtra solo los archivos Excel
                file_path = os.path.join(root, file)  # Construye la ruta completa del archivo
                # Leer el archivo Excel en un DataFrame
                df = extract_from_extrato_file(file_path, year)
                # Añadir el DataFrame a la lista
                df_list.append(df)

    # Concatenar todos los DataFrames en uno solo
    df_combined = pd.concat(df_list, ignore_index=True)
    #df_combined[['CREDIT/DEBIT', 'SALDO']] = df_combined[['CREDIT/DEBIT', 'SALDO']].apply(lambda x: x.str.replace(',', '').astype(float))
    df_combined['CREDIT/DEBIT'] = pd.to_numeric(
        df_combined['CREDIT/DEBIT'].astype(str).str.replace(',', ''),
        errors='coerce'
    )

    df_combined['SALDO'] = pd.to_numeric(
        df_combined['SALDO'].astype(str).str.replace(',', ''),
        errors='coerce'
    )
    return df_combined

# def extractExtractosFromFolderYearBC(baseFolder:str, year:int) -> pd.DataFrame:
#     '''
#     Extrae los datos de los archivos de extracto bancario de un año específico en una carpeta.
#     '''
#     # folder base
#     #folder = baseFolder + "/" + str(year) + "/BC/Extractos"
#     folder = Path(baseFolder) / str(year) / "BC" / "Extractos"
#     #print(f"Extracting data from folder: {folder}")
#     # Lista para almacenar los DataFrames extraídos
#     df_list = []
#     logging.info(f"*Extracting data from folder: {folder} for year {year} in BC Extractos")

#     for root, dirs, files in os.walk(folder):
#         logging.info(f"*Processing folder: {root} with {len(files)} files for year {year} in BC Extractos")
#         for file in files:
#             if file.endswith('.xlsx') or file.endswith('.xls'):  # Filtra solo los archivos Excel
#                 #print(f"Processing file (extractExtractosFromFolderYearBC): {file}")
#                 file_path = os.path.join(root, file)  # Construye la ruta completa del archivo
#                 # Leer el archivo Excel en un DataFrame
#                 df = extract_from_extrato_file(file_path)
#                 #print(f"Extracted {df.columns} columns.")
#                 # Añadir el DataFrame a la lista
#                 df_list.append(df)
#     logging.info(f"*Finished extracting data from folder: {folder} for year {year}. Total files processed: {len(df_list)}")
    
#     print(f"*Extracting data from folder: {folder} with df_list length: {len(df_list)}")
#     folder = Path(baseFolder) / str(year) / "BC" / "Periodos"
#     #folder = baseFolder + "/" + str(year) + "/BC/Periodos"
#     logging.info(f"Extracting data from folder: {folder} for year {year} in BC Periodos")
#     for root, dirs, files in os.walk(folder):
#         for file in files:
#              if file.endswith('.xlsx') or file.endswith('.xls'):  # Filtra solo los archivos Excel
#                 #print(f"Processing file (extractExtractosFromFolderYearBC): {file}")
#                 file_path = os.path.join(root, file)  # Construye la ruta completa del archivo
#                 # Leer el archivo Excel en un DataFrame
#                 df = extract_from_period_xls(file_path)
#                 # Añadir el DataFrame a la lista
#                 df_list.append(df)
#     #print(f"Extracting data from folder: {folder}")
#     # Lista para almacenar los DataFrames extraídos

    
    
#     # Concatenar todos los DataFrames en uno solo
#     if not df_list:
#         return pd.DataFrame()

#     df_combined = pd.concat(df_list, ignore_index=True)

#     # --- FIX FECHA ---
#     df_combined['FECHA'] = pd.to_datetime(df_combined['FECHA'], errors='coerce')

#     df_combined['FECHA'] = df_combined['FECHA'].apply(
#         lambda d: d.replace(year=year) if pd.notnull(d) else d
#     )

#     # --- VALIDAR COLUMNAS ---
#     required_cols = ['CREDIT/DEBIT', 'SALDO']
#     missing = [col for col in required_cols if col not in df_combined.columns]

#     if missing:
#         raise ValueError(f"Missing columns {missing} in dataset")

#     # --- FIX NUMERICOS ---
#     df_combined['CREDIT/DEBIT'] = pd.to_numeric(
#         df_combined['CREDIT/DEBIT'].astype(str).str.replace(',', ''),
#         errors='coerce'
#     )

#     df_combined['SALDO'] = pd.to_numeric(
#         df_combined['SALDO'].astype(str).str.replace(',', ''),
#         errors='coerce'
#     )

#     df_combined['MONEDA'] = 'COP'
#     df_combined['ENTIDAD'] = 'BC'

#     return df_combined

def extractExtractosFromFolderYearBC(baseFolder: str, year: int) -> pd.DataFrame:

    df_extractos = []
    df_periodos = []

    # -------- EXTRACTOS --------
    folder_extractos = Path(baseFolder) / str(year) / "BC" / "Extractos"

    if folder_extractos.exists():
        for root, dirs, files in os.walk(folder_extractos):
            for file in files:
                if file.endswith(('.xlsx', '.xls')):
                    file_path = os.path.join(root, file)
                    try:
                        df = extract_from_extrato_file(file_path, year)
                        if not df.empty:
                            df_extractos.append(df)
                    except Exception as e:
                        logging.warning(f"Skipping extracto file {file_path}: {e}")

    # -------- PERIODOS --------
    folder_periodos = Path(baseFolder) / str(year) / "BC" / "Periodos"

    if folder_periodos.exists():
        for root, dirs, files in os.walk(folder_periodos):
            for file in files:
                if file.endswith(('.xlsx', '.xls')):
                    file_path = os.path.join(root, file)
                    try:
                        df = extract_from_period_xls(file_path)
                        if not df.empty:
                            df_periodos.append(df)
                    except Exception as e:
                        logging.warning(f"Skipping periodo file {file_path}: {e}")

    # -------- PRIORIDAD --------
    dfs = []

    if df_extractos:
        df_ext = pd.concat(df_extractos, ignore_index=True)
        dfs.append(df_ext)

    if df_periodos:
        df_per = pd.concat(df_periodos, ignore_index=True)

        # Periodos no tiene SALDO → lo generamos
        if 'SALDO' not in df_per.columns:
            df_per = df_per.sort_values('FECHA')
            df_per['SALDO'] = df_per['CREDIT/DEBIT'].cumsum()

        dfs.append(df_per)

    
    if not dfs:
        return pd.DataFrame()
    
    df_combined = pd.concat(dfs, ignore_index=True)

    # -------- NORMALIZACIÓN --------

    df_combined['FECHA'] = pd.to_datetime(df_combined['FECHA'], errors='coerce')

    df_combined['CREDIT/DEBIT'] = pd.to_numeric(
        df_combined['CREDIT/DEBIT'].astype(str).str.replace(',', ''),
        errors='coerce'
    )

    df_combined['SALDO'] = pd.to_numeric(
        df_combined['SALDO'],
        errors='coerce'
    )

    df_combined['MONEDA'] = 'COP'
    df_combined['ENTIDAD'] = 'BC'

    return df_combined

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
    
    logging.info(f"Extracting dataset for year {year} from folder: {folder}")
    
    #print(f"Subfolders found in {folder}: {subfolders}")
    if 'BC' in subfolders:
        #print("Extracting BC data...")
        try:

            dfs.append(extractExtractosFromFolderYearBC(baseFolder, year))
            logging.info(f"BC data extracted for year {baseFolder} {year}")
            #print(f"BC data extracted for year {baseFolder} {year}")
        except Exception as e:
            logging.exception(f"Error extracting BC data for year {year}: {e}")
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
        raise FileNotFoundError(f"File not found at {file}. Please check the file path.")
    
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
    #logger.info(f"Extracting Payoneer data for year {year} from folder: {folder}")
    folder = Path(folder) / f"{year}/Payoneer"
    dfs = []
    if folder.exists():
        files = [f for f in folder.iterdir() if f.is_file() and f.suffix in ['.csv']]
        #logger.info(f"Found {len(files)} Payoneer files for year {year} in folder: {folder}")
        if not files:
            raise FileNotFoundError(f"No CSV files found in {folder}")
        for file in files:
            #logger.info(f"Processing Payoneer file: {file}")
            df = pd.read_csv(file)
            #logger.info(f"Columns in {file}: {df.columns.tolist()}")
            df['FECHA'] = pd.to_datetime(
                df['Transaction Date'] + ' ' + df['Transaction Time']
                )
            df['CREDIT/DEBIT'] = (
                df['Credit Amount'].fillna(0) -
                df['Debit Amount'].fillna(0)
                )
            df = df.rename(columns={
                    'Description': 'DESCRIPCION',
                    'Running Balance': 'SALDO',
                    'Currency': 'MONEDA'
                })
            
    
            df = df[['FECHA', 'DESCRIPCION', 'CREDIT/DEBIT', 'SALDO', 'MONEDA']]
            df['ENTIDAD'] = 'PAYONEER' 
            #logger.info(f"Finished processing Payoneer file: {file} with {len(df)} records and the columns are {df.columns.tolist()}")	
            dfs.append(df)

    df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
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