import streamlit as st
import sys
import os

# Solución antibalas: apuntar directamente a la carpeta utils
ruta_utils = os.path.abspath(os.path.join(os.path.dirname(__file__), '../utils'))
if ruta_utils not in sys.path:
    sys.path.append(ruta_utils)

# Ahora importamos directamente desde el archivo load_data.py
from load_data import cargar_datos_procesados

st.title("📈 Indicadores Principales")

df = cargar_datos_procesados()

st.markdown("### Rendimiento General del Servicio")
col1, col2, col3 = st.columns(3)
col1.metric("Total de Viajes", f"{len(df):,}")
col2.metric("Recaudación Total", f"${df['monto_total'].sum():,.0f}")
col3.metric("Monto Promedio por Viaje", f"${df['monto_total'].mean():.2f}")

st.markdown("### Comportamiento del Viaje")
col4, col5, col6 = st.columns(3)
col4.metric("Distancia Promedio", f"{df['distancia_viaje'].mean():.2f} millas")
col5.metric("Duración Promedio", f"{df['duracion_minutos'].mean():.1f} min")

porcentaje_propina = (df[df['propina'] > 0].shape[0] / len(df)) * 100
col6.metric("Viajes con Propina", f"{porcentaje_propina:.1f}%")