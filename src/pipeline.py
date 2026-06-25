import pandas as pd
import os

def cargar_datos(ruta):
    print("Iniciando carga de datos...")
    return pd.read_parquet(ruta)

def renombrar_columnas(df):
    """Estandariza las cabeceras del dataset al español."""
    mapeo_columnas = {
        'tpep_pickup_datetime': 'fecha_inicio_viaje',
        'tpep_dropoff_datetime': 'fecha_termino_viaje',
        'passenger_count': 'cantidad_pasajeros',
        'trip_distance': 'distancia_viaje',
        'PULocationID': 'zona_origen',
        'DOLocationID': 'zona_destino',
        'RatecodeID': 'tipo_tarifa',
        'payment_type': 'tipo_pago',
        'fare_amount': 'tarifa_base',
        'tip_amount': 'propina',
        'tolls_amount': 'peajes',
        'total_amount': 'monto_total'
    }
    return df.rename(columns=mapeo_columnas)

def validacion_inicial(df):
    """Revisa tipos, nulos, duplicados y rangos antes de limpiar (exigido por la rúbrica)."""
    print("\n===== VALIDACIÓN INICIAL DEL DATASET =====")
    print(f"Dimensiones (shape): {df.shape[0]} filas x {df.shape[1]} columnas")

    print("\n--- Vista previa (head) ---")
    print(df.head())

    print("\n--- Tipos de datos e info ---")
    df.info()

    print("\n--- Nulos por columna ---")
    nulos = df.isna().sum()
    print(nulos[nulos > 0] if (nulos > 0).any() else "Sin nulos.")

    n_duplicados = df.duplicated().sum()
    print(f"\n--- Filas duplicadas: {n_duplicados} ---")

    print("\n--- Rangos de variables numéricas (describe) ---")
    print(df.describe())
    print("==========================================\n")

def limpiar_y_transformar(df):
    print("Iniciando limpieza y transformación de columnas...")

    # 1. Renombrado a cabeceras en español
    df = renombrar_columnas(df)

    columnas_requeridas = ['fecha_inicio_viaje', 'fecha_termino_viaje', 'cantidad_pasajeros',
                            'distancia_viaje', 'tarifa_base', 'monto_total']
    columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
    if columnas_faltantes:
        raise ValueError(f"Faltan columnas requeridas para la limpieza: {columnas_faltantes}")

    # 2. Validación inicial (tipos, nulos, duplicados, rangos)
    validacion_inicial(df)

    # 3. Formateo de fechas y cálculo de duración del viaje en minutos
    df['fecha_inicio_viaje'] = pd.to_datetime(df['fecha_inicio_viaje'], errors='coerce')
    df['fecha_termino_viaje'] = pd.to_datetime(df['fecha_termino_viaje'], errors='coerce')
    df['duracion_minutos'] = (df['fecha_termino_viaje'] - df['fecha_inicio_viaje']).dt.total_seconds() / 60.0

    n_inicial = len(df)
    periodos_validos = pd.PeriodIndex(['2023-12', '2024-01', '2024-02', '2024-03', '2024-04'], freq='M')

    # 4. Limpieza con reporte de registros perdidos POR CADA filtro
    print("Aplicando filtros de calidad (registros eliminados por regla):")
    reporte = []

    def aplicar(df, nombre, mascara):
        antes = len(df)
        df = df[mascara]
        perdidos = antes - len(df)
        print(f"  - {nombre}: -{perdidos:>8} (quedan {len(df)})")
        reporte.append({'filtro': nombre, 'registros_eliminados': perdidos, 'registros_restantes': len(df)})
        return df

    # 4.0 Duplicados exactos
    antes = len(df)
    df = df.drop_duplicates()
    perdidos = antes - len(df)
    print(f"  - {'Filas duplicadas':<30}: -{perdidos:>8} (quedan {len(df)})")
    reporte.append({'filtro': 'Filas duplicadas', 'registros_eliminados': perdidos, 'registros_restantes': len(df)})

    # 4.1 Completitud: descartamos registros con datos esenciales nulos
    df = aplicar(df, f"{'Nulos esenciales':<30}",
                 df[['fecha_inicio_viaje', 'fecha_termino_viaje', 'cantidad_pasajeros']].notna().all(axis=1))

    # 4.2 Reglas de negocio: montos, distancias y duraciones positivos y coherentes
    df = aplicar(df, f"{'Distancia > 0':<30}", df['distancia_viaje'] > 0)
    df = aplicar(df, f"{'Monto total > 0':<30}", df['monto_total'] > 0)
    df = aplicar(df, f"{'Tarifa base > 0':<30}", df['tarifa_base'] > 0)
    df = aplicar(df, f"{'Cantidad pasajeros > 0':<30}", df['cantidad_pasajeros'] > 0)
    df = aplicar(df, f"{'Duración > 0 min':<30}", df['duracion_minutos'] > 0)
    df = aplicar(df, f"{'Duración < 180 min':<30}", df['duracion_minutos'] < 180)
    df = aplicar(df, f"{'fecha_inicio < fecha_termino':<30}", df['fecha_inicio_viaje'] < df['fecha_termino_viaje'])
    df = aplicar(df, f"{'Periodo 2023-12..2024-04':<30}",
                 df['fecha_inicio_viaje'].dt.to_period('M').isin(periodos_validos))

    print(f"\nValidación completada: {n_inicial - len(df)} de {n_inicial} registros descartados en total.")

    # 5. Guardar el reporte de limpieza
    os.makedirs("data/outputs", exist_ok=True)
    pd.DataFrame(reporte).to_csv("data/outputs/reporte_limpieza.csv", index=False)
    print("Reporte de limpieza guardado en 'data/outputs/reporte_limpieza.csv'")

    # 6. Muestreo de datos
    n_muestra = 200000
    if len(df) > n_muestra:
        print(f"Reduciendo el dataset de {len(df)} a {n_muestra} registros (muestra aleatoria, random_state=42)...")
        df = df.sample(n=n_muestra, random_state=42)

    return df

def ejecutar_etl():
    ruta_entrada = "data/raw/"
    ruta_salida = "data/processed/yellow_taxi_limpio.parquet"

    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    try:
        df_bruto = cargar_datos(ruta_entrada)
        df_limpio = limpiar_y_transformar(df_bruto)

        df_limpio.to_parquet(ruta_salida, index=False)
        print(f"Pipeline finalizado. Dataset procesado guardado en {ruta_salida}")
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {ruta_entrada}.")

if __name__ == "__main__":
    ejecutar_etl()
