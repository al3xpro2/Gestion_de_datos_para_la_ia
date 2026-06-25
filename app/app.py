import streamlit as st

# Configuración global de la página
st.set_page_config(
    page_title="NYC Taxi Analytics",
    page_icon="🚕",
    layout="wide"
)

st.title("🚕 Sistema de Análisis y Predicción: Yellow Taxi NYC")

st.markdown("""
### ¡Bienvenidos al portal interactivo!
Esta herramienta permite explorar los datos históricos de los viajes en taxi de Nueva York, 
analizar indicadores clave y proyectar el costo de nuevos viajes utilizando Inteligencia Artificial.

**Utilice el menú lateral para navegar entre las distintas secciones:**
* 📊 **Exploración e Indicadores:** Revise el estado de salud del dataset y los KPIs.
* 🔍 **Consulta y Visualización:** Filtre viajes históricos y analice gráficos.
* 🤖 **Evaluación y Predicción:** Ponga a prueba nuestro modelo Random Forest y cotice viajes.
""")

st.info("👈 Despliegue el menú de la izquierda para comenzar.")