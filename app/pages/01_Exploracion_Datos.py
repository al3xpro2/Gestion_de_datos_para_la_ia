import streamlit as st
import sys
import os

# Solución antibalas: apuntar directamente a la carpeta utils
ruta_utils = os.path.abspath(os.path.join(os.path.dirname(__file__), '../utils'))
if ruta_utils not in sys.path:
    sys.path.append(ruta_utils)

# Ahora importamos directamente desde el archivo load_data.py
from load_data import cargar_datos_procesados

st.title("🔍 Exploración de Datos")

df = cargar_datos_procesados()

st.subheader("Vista previa del Dataset Limpio")
st.dataframe(df.head(50), use_container_width=True)

col1, col2 = st.columns(2)
col1.metric("Filas (Viajes Procesados)", f"{df.shape[0]:,}")
col2.metric("Columnas (Variables)", f"{df.shape[1]:,}")

st.subheader("Estadísticas Descriptivas")
st.dataframe(df.describe(), use_container_width=True)