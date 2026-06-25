import streamlit as st
import sys
import os

# Solución antibalas: apuntar directamente a la carpeta utils
ruta_utils = os.path.abspath(os.path.join(os.path.dirname(__file__), '../utils'))
if ruta_utils not in sys.path:
    sys.path.append(ruta_utils)

# Ahora importamos directamente desde el archivo load_data.py
from load_data import cargar_datos_procesados

st.title("🧮 Consulta de Viajes")
st.markdown("Utiliza los filtros en el menú lateral para explorar viajes específicos.")

df = cargar_datos_procesados()

# --- Filtros Interactivos en el Sidebar ---
st.sidebar.header("Filtros de Búsqueda")

# Filtro 1: Cantidad de pasajeros
pasajeros = st.sidebar.slider(
    "Cantidad de Pasajeros", 
    int(df['cantidad_pasajeros'].min()), 
    int(df['cantidad_pasajeros'].max()), 
    (1, 4)
)

# Filtro 2: Rango de distancia (usamos el cuantil 0.99 para evitar valores extremos extraños en el slider)
dist_min = float(df['distancia_viaje'].min())
dist_max = float(df['distancia_viaje'].quantile(0.99))
distancia = st.sidebar.slider(
    "Distancia del Viaje (millas)", 
    dist_min, 
    dist_max, 
    (dist_min, dist_max)
)

# Aplicar los filtros al dataframe
df_filtrado = df[
    (df['cantidad_pasajeros'].between(pasajeros[0], pasajeros[1])) &
    (df['distancia_viaje'].between(distancia[0], distancia[1]))
]

# --- Resultados ---
st.write(f"Registros encontrados: **{len(df_filtrado):,}**")

# Mostrar solo los primeros 1000 para no colapsar el navegador del usuario
st.dataframe(df_filtrado.head(1000), use_container_width=True)

# Botón para descargar el CSV
csv = df_filtrado.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Descargar datos filtrados (CSV)",
    data=csv,
    file_name='viajes_filtrados.csv',
    mime='text/csv',
)