import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import sys
import os

# Solución antibalas: apuntar directamente a la carpeta utils
ruta_utils = os.path.abspath(os.path.join(os.path.dirname(__file__), '../utils'))
if ruta_utils not in sys.path:
    sys.path.append(ruta_utils)

# Ahora importamos directamente desde el archivo load_data.py
from load_data import cargar_datos_procesados

st.title("📊 Visualizaciones")

df = cargar_datos_procesados()

# Tomamos una muestra aleatoria para que los gráficos carguen rápido
df_sample = df.sample(n=min(10000, len(df)), random_state=42)

st.subheader("Relación entre Distancia y Monto Total")
fig1, ax1 = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=df_sample, x='distancia_viaje', y='monto_total', alpha=0.4, color='#F6C90E', ax=ax1)
ax1.set_xlabel("Distancia (millas)")
ax1.set_ylabel("Monto Total ($)")
ax1.grid(True, linestyle='--', alpha=0.5)
st.pyplot(fig1)

st.subheader("Distribución de la Duración de los Viajes")
fig2, ax2 = plt.subplots(figsize=(10, 6))
# Filtramos viajes de menos de 100 minutos solo para que el gráfico se vea más claro
sns.histplot(data=df_sample[df_sample['duracion_minutos'] < 100], x='duracion_minutos', bins=40, kde=True, color='#30475E', ax=ax2)
ax2.set_xlabel("Duración (minutos)")
ax2.set_ylabel("Frecuencia")
st.pyplot(fig2)