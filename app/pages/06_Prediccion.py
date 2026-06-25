import streamlit as st
import pandas as pd
import joblib
import os

st.title("🤖 Predicción de Viajes")
st.markdown("Ingrese las características del viaje para estimar el costo total utilizando nuestro modelo de Machine Learning.")

# Función para cargar el modelo utilizando caché [cite: 54]
@st.cache_resource
def cargar_modelo(path="models/modelo_final.pkl"):
    # Se utiliza joblib para cargar el archivo [cite: 54]
    return joblib.load(path)

try:
    modelo = cargar_modelo()
    
    st.subheader("Datos del Viaje")
    
    col1, col2 = st.columns(2)
    with col1:
        cantidad_pasajeros = st.number_input("Cantidad de pasajeros", min_value=1, max_value=6, value=1)
        distancia_viaje = st.number_input("Distancia estimada (millas)", min_value=0.1, max_value=50.0, value=2.5)
        duracion_minutos = st.number_input("Duración estimada (minutos)", min_value=1.0, value=15.0)
    
    with col2:
        pickup_hour = st.slider("Hora de inicio (0-23)", 0, 23, 12)
        pickup_dayofweek = st.selectbox("Día de la semana", options=[0, 1, 2, 3, 4, 5, 6], format_func=lambda x: ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][x])
        pickup_month = st.selectbox("Mes", options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

    if st.button("Calcular Estimación"):
        # 1. Recrear las features exactas que necesita el modelo
        is_weekend = 1 if pickup_dayofweek in [5, 6] else 0
        is_rush_hour = 1 if pickup_hour in [7, 8, 9, 16, 17, 18, 19] else 0
        velocidad_promedio_mph = distancia_viaje / (duracion_minutos / 60.0)
        
        # 2. Crear el DataFrame base
        input_data = pd.DataFrame([{
            "cantidad_pasajeros": cantidad_pasajeros,
            "distancia_viaje": distancia_viaje,
            "duracion_minutos": duracion_minutos,
            "pickup_hour": pickup_hour,
            "pickup_dayofweek": pickup_dayofweek,
            "pickup_month": pickup_month,
            "is_weekend": is_weekend,
            "is_rush_hour": is_rush_hour,
            "velocidad_promedio_mph": velocidad_promedio_mph,
        }])
        
        # 3. Alinear columnas con el modelo (Rellena con 0 las columnas One-Hot Encoding que falten)
        columnas_modelo = modelo.feature_names_in_
        for col in columnas_modelo:
            if col not in input_data.columns:
                input_data[col] = 0
                
        # Asegurar el mismo orden de columnas
        input_data = input_data[columnas_modelo]
        
        # 4. Realizar predicción [cite: 55]
        prediccion = modelo.predict(input_data)[0]
        
        st.success(f"Costo estimado del viaje: ${prediccion:.2f}")
        st.caption("Esta proyección utiliza el algoritmo Random Forest Regressor y asume condiciones normales de tráfico.")

except FileNotFoundError:
    st.error("No se encontró el archivo del modelo. Asegúrese de haber ejecutado el pipeline de entrenamiento primero.")