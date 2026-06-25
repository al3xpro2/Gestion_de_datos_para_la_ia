import streamlit as st
import sys
import os

ruta_utils = os.path.abspath(os.path.join(os.path.dirname(__file__), '../utils'))
if ruta_utils not in sys.path:
    sys.path.append(ruta_utils)

# Se debe importar la función para cargar las métricas [cite: 51]
from load_data import cargar_metricas

st.title("🎯 Evaluación del Modelo")

# Mostrar métricas de evaluación [cite: 16]
st.markdown("A continuación se presentan los resultados de los algoritmos entrenados.")
metricas = cargar_metricas()
st.dataframe(metricas, use_container_width=True)

mejor_modelo = metricas.sort_values("RMSE").iloc[0]
st.subheader("Rendimiento del Mejor Modelo")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Modelo", mejor_modelo["modelo"])
col2.metric("MAE", f"{mejor_modelo['MAE']:.2f}")
col3.metric("RMSE", f"{mejor_modelo['RMSE']:.2f}")
col4.metric("R2", f"{mejor_modelo['R2']:.3f}")

st.info("El R² indica el porcentaje de varianza que nuestro modelo es capaz de explicar. Un valor cercano a 1.0 es excelente.")