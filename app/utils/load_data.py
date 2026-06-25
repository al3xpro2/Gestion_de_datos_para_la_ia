import pandas as pd
import streamlit as st
import joblib

@st.cache_data
def cargar_datos_procesados(path="data/processed/yellow_taxi_limpio.parquet"):
    """Carga el dataset limpio en la memoria caché y calcula variables faltantes."""
    df = pd.read_parquet(path)
    
    # Solución al KeyError: Si no existe la duración, la calculamos aquí mismo
    if 'duracion_minutos' not in df.columns:
        df['fecha_inicio_viaje'] = pd.to_datetime(df['fecha_inicio_viaje'])
        df['fecha_termino_viaje'] = pd.to_datetime(df['fecha_termino_viaje'])
        df['duracion_minutos'] = (df['fecha_termino_viaje'] - df['fecha_inicio_viaje']).dt.total_seconds() / 60.0
        
    return df

@st.cache_data
def cargar_metricas(path="data/outputs/metricas_modelos.csv"):
    """Carga los resultados de los algoritmos."""
    return pd.read_csv(path)

@st.cache_resource
def cargar_modelo(path="models/modelo_final.pkl"):
    """Carga el modelo predictivo de Random Forest."""
    return joblib.load(path)