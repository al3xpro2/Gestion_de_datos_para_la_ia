import os
import logging
import pandas as pd
import json
import requests
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN INICIAL Y RUTAS
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'ingestion.log')
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')

# Configurar el sistema de logs
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# API pública de Remotive para empleos en tecnología
API_URL = "https://remotive.com/api/remote-jobs?category=software-dev&limit=50"

# ==========================================
# 2. FUNCIONES DEL PIPELINE (ETL)
# ==========================================

def extraer_datos():
    """EXTRACCIÓN: Descarga los datos desde la API de Remotive."""
    print("Iniciando conexión con la API de empleos...")
    logging.info("Iniciando extracción de datos desde Remotive API.")
    try:
        response = requests.get(API_URL, timeout=15)
        response.raise_for_status() 
        
        datos = response.json().get('jobs', [])
        logging.info(f"Se extrajeron {len(datos)} ofertas de empleo con éxito.")
        return datos
    except requests.exceptions.RequestException as e:
        logging.error(f"Error de conexión al extraer los datos: {e}")
        return None

def guardar_datos_crudos(datos):
    """NUEVO PASO: Guarda una copia exacta del JSON descargado antes de manipularlo."""
    if not datos:
        return
        
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    archivo_raw = os.path.join(RAW_DIR, f"empleos_raw_{fecha_hoy}.json")
    
    try:
        # Aseguramos que la carpeta raw exista
        os.makedirs(RAW_DIR, exist_ok=True)
        
        print(f"Guardando respaldo de datos crudos en: {archivo_raw}")
        # Guardamos usando la librería json estándar
        with open(archivo_raw, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
            
        logging.info(f"Datos crudos guardados exitosamente en: {archivo_raw}")
    except Exception as e:
        logging.error(f"Error al guardar los datos crudos: {e}")

def transformar_datos(datos_json):
    """TRANSFORMACIÓN: Filtra campos, limpia nulos y normaliza textos."""
    print("Filtrando y limpiando los datos extraídos...")
    logging.info("Iniciando transformación de datos.")
    try:
        df = pd.DataFrame(datos_json)
        if df.empty:
            return None
            
        # 1. Selección de columnas clave
        columnas_deseadas = ['id', 'title', 'company_name', 'category', 'job_type', 'publication_date']
        columnas_existentes = [col for col in columnas_deseadas if col in df.columns]
        df = df[columnas_existentes]
        
        # 2. Limpieza de datos nulos (Reglas de negocio)
        df.dropna(subset=['title', 'company_name'], inplace=True)
        if 'job_type' in df.columns:
            df['job_type'] = df['job_type'].fillna('no_especificado')
        
        # 3. Normalización de texto y fechas
        df['title'] = df['title'].str.lower().str.strip()
        if 'category' in df.columns:
            df['category'] = df['category'].str.lower().str.strip()
            
        if 'publication_date' in df.columns:
            # Convierte la fecha a un formato estándar YYYY-MM-DD
            df['publication_date'] = pd.to_datetime(df['publication_date'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        mapeo_nombres = {
            'title': 'cargo',
            'company_name': 'nombre_compañia',
            'category': 'categoria',
            'job_type': 'tipo_trabajo',
            'publication_date': 'fecha_publicacion'
        }
        df.rename(columns=mapeo_nombres, inplace=True)
        
        logging.info(f"Transformación exitosa. Registros finales listos: {len(df)}")
        return df
    except Exception as e:
        logging.error(f"Error durante la transformación de datos: {e}")
        return None

def cargar_datos(df):
    """CARGA: Guarda los datos procesados en CSV organizados por fecha."""
    if df is None or df.empty:
        logging.warning("No hay datos para guardar.")
        return
        
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    archivo_salida = os.path.join(PROCESSED_DIR, f"empleos_mercado_{fecha_hoy}.csv")
    
    try:
        print(f"Guardando archivo final en: {archivo_salida}")
        df.to_csv(archivo_salida, index=False, encoding='utf-8')
        logging.info(f"Datos cargados exitosamente en: {archivo_salida}")
    except Exception as e:
        logging.error(f"Error al guardar el archivo: {e}")


def main():
    """Ejecuta el flujo completo automatizado."""
    print("--- INICIANDO PIPELINE DE DATOS ---")
    logging.info("--- INICIO DE PROCESO AUTOMATIZADO ---")
    
    datos_crudos = extraer_datos()
    
    if datos_crudos:
        guardar_datos_crudos(datos_crudos)
        datos_limpios = transformar_datos(datos_crudos)
        cargar_datos(datos_limpios)
        print("¡Pipeline ETL ejecutado con éxito! Revisa la carpeta data/processed.")
    else:
        print("Fallo en la extracción. Revisa el archivo logs/ingestion.log.")
        
    logging.info("--- FIN DE PROCESO ---")

if __name__ == "__main__":
    main()