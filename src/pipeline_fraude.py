import pandas as pd
import numpy as np
import logging
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_LOGS        = os.path.join(BASE_DIR, 'logs')
DIR_CRUDOS      = os.path.join(BASE_DIR, 'datos', 'crudos')
DIR_PROCESADOS  = os.path.join(BASE_DIR, 'datos', 'procesados')

os.makedirs(DIR_LOGS, exist_ok=True)
os.makedirs(DIR_PROCESADOS, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(DIR_LOGS, 'pipeline_fraude.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_info(mensaje):
    print(mensaje)
    logging.info(mensaje)

def log_error(mensaje):
    print(f"ERROR: {mensaje}")
    logging.error(mensaje)


# Mapeo de columnas al español 
COLUMNAS_ES = {
    'trans_date_trans_time': 'fecha_hora_transaccion',
    'cc_num':                'numero_tarjeta',
    'merchant':              'comercio',
    'category':              'categoria',
    'amt':                   'monto',
    'first':                 'nombre',
    'last':                  'apellido',
    'gender':                'genero',
    'street':                'calle',
    'city':                  'ciudad',
    'state':                 'estado',
    'zip':                   'codigo_postal',
    'lat':                   'latitud',
    'long':                  'longitud',
    'city_pop':              'poblacion_ciudad',
    'job':                   'ocupacion',
    'dob':                   'fecha_nacimiento',
    'trans_num':             'numero_transaccion',
    'unix_time':             'tiempo_unix',
    'merch_lat':             'latitud_comercio',
    'merch_long':            'longitud_comercio',
    'is_fraud':              'es_fraude',
}

def renombrar_columnas(df):
    df = df.rename(columns=COLUMNAS_ES)
    log_info("Se renombran las columnas y se estandarizan los nombres.")
    return df

def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
    lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)
    dlat, dlon = lat2_rad - lat1_rad, lon2_rad - lon1_rad
    a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

def aplicar_transformaciones(df):
    df_trans = df.copy()
    try:
        df_trans['fecha_hora_transaccion'] = pd.to_datetime(df_trans['fecha_hora_transaccion'], errors='coerce')
        df_trans['fecha_nacimiento'] = pd.to_datetime(df_trans['fecha_nacimiento'], errors='coerce')
        df_trans['edad_titular'] = (df_trans['fecha_hora_transaccion'] - df_trans['fecha_nacimiento']).dt.days // 365
        df_trans['distancia_km'] = calcular_distancia_haversine(
            df_trans['latitud'], df_trans['longitud'],
            df_trans['latitud_comercio'], df_trans['longitud_comercio']
        )
        df_trans['hora_transaccion'] = df_trans['fecha_hora_transaccion'].dt.hour

        log_info("Transformaciones aplicadas con éxito.")
    except Exception as e:
        log_error(f"Error en transformaciones: {e}")
    return df_trans

def validaciones_estructurales(df):
    df['monto'] = pd.to_numeric(df['monto'], errors='coerce')
    df['genero_valido'] = df['genero'].isin(['M', 'F'])
    df['fraude_valido'] = df['es_fraude'].isin([0, 1])
    log_info("Validaciones estructurales completadas.")
    return df

def validaciones_semanticas(df):
    df['fechas_coherentes'] = df['fecha_hora_transaccion'] > df['fecha_nacimiento']
    df['monto_valido'] = df['monto'] > 0
    log_info("Validaciones semánticas completadas.")
    return df

def formatear_fechas(df):
    df = df.copy()
    if 'fecha_hora_transaccion' in df.columns:
        df['fecha_hora_transaccion'] = pd.to_datetime(df['fecha_hora_transaccion'], errors='coerce') \
            .dt.strftime('%d-%m-%Y %H:%M:%S')
    if 'fecha_nacimiento' in df.columns:
        df['fecha_nacimiento'] = pd.to_datetime(df['fecha_nacimiento'], errors='coerce') \
            .dt.strftime('%d-%m-%Y')
    return df

def procesar_datos_fraude(df_raw):
    log_info("--- INICIANDO PIPELINE DE DATOS: CASO FRAUDE ---")
    df = renombrar_columnas(df_raw)
    df = aplicar_transformaciones(df)
    df = validaciones_estructurales(df)
    df = validaciones_semanticas(df)

    es_valido = (
        df['monto'].notnull() &
        df['edad_titular'].notnull() &
        df['genero_valido'] &
        df['fraude_valido'] &
        df['fechas_coherentes'] &
        df['monto_valido']
    )

    columnas_bandera = ['genero_valido', 'fraude_valido', 'fechas_coherentes', 'monto_valido']
    df_validos = df[es_valido].drop(columns=columnas_bandera)
    df_invalidos = df[~es_valido]

    log_info(f"Total procesados: {len(df)}")
    log_info(f"Registros procesados exitosamente: {len(df_validos)}")
    log_info(f"Registros con errores o inconsistencias: {len(df_invalidos)}")
    log_info("--- FIN DEL PIPELINE ---")
    return df_validos, df_invalidos

# funcion main para ejecutar el pipeline
if __name__ == "__main__":
    archivo_csv = os.path.join(DIR_CRUDOS, '02_fraudTest.csv')

    if os.path.exists(archivo_csv):
        print(f"Cargando muestra de datos desde {archivo_csv}...")
        df_banco_crudo = pd.read_csv(archivo_csv)
        df_limpio, df_errores = procesar_datos_fraude(df_banco_crudo)

        df_limpio = formatear_fechas(df_limpio)
        df_errores = formatear_fechas(df_errores)

        df_limpio.to_csv(os.path.join(DIR_PROCESADOS, 'datos_listos_modelo.csv'), index=False)
        df_errores.to_csv(os.path.join(DIR_PROCESADOS, 'datos_corruptos_log.csv'), index=False)
        print("Archivos de salida generados con éxito.")
    else:
        print(f"No se encontró el archivo: {archivo_csv}")
