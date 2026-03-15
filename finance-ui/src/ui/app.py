import streamlit as st
import pandas as pd
from ..src import extract

# Título de la aplicación
st.title('Cargar múltiples archivos desde un folder')

# Subir múltiples archivos
uploaded_files = st.file_uploader("Cargar archivos CSV", type=["csv"], accept_multiple_files=True)

# Verificar si se cargaron archivos
if uploaded_files:
    st.write(f"Se han cargado {len(uploaded_files)} archivos.")
    
    # Iterar sobre los archivos cargados
    for uploaded_file in uploaded_files:
        # Leer cada archivo CSV en un DataFrame de pandas
        df = extract.extract_from_extrato_file(uploaded_file)
        
        # Mostrar el nombre del archivo y los primeros registros
        st.write(f"Archivo cargado: {uploaded_file.name}")
        st.dataframe(df.head())  # Mostrar primeras filas del dataframe
else:
    st.write("Por favor, cargue al menos un archivo CSV.")
