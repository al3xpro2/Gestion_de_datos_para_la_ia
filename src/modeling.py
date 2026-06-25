import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # backend sin ventana, apto para scripts
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os

# Componentes que SUMAN monto_total (total_amount). Usarlos como predictores sería
# fuga de datos (data leakage), porque permiten reconstruir el objetivo casi exacto.
COLUMNAS_LEAKAGE = ['tarifa_base', 'propina', 'peajes', 'extra', 'mta_tax',
                    'improvement_surcharge', 'congestion_surcharge', 'Airport_fee']

# Features de costo creadas SOLO para EDA/visualización. Derivan de componentes del
# total (propina/peajes), así que también se excluyen del entrenamiento.
FEATURES_COSTO_EDA = ['tiene_peaje', 'tiene_propina', 'porcentaje_propina']

def crear_features(df):
    """Genera nuevas variables y aplica codificación categórica."""
    print("Iniciando Ingeniería de Características...")

    # 1. Variables temporales
    df['pickup_hour'] = df['fecha_inicio_viaje'].dt.hour
    df['pickup_dayofweek'] = df['fecha_inicio_viaje'].dt.dayofweek
    df['pickup_month'] = df['fecha_inicio_viaje'].dt.month
    df['is_weekend'] = df['pickup_dayofweek'].isin([5, 6]).astype(int)
    df['is_rush_hour'] = df['pickup_hour'].isin([7, 8, 9, 16, 17, 18, 19]).astype(int)

    # 2. Velocidad promedio (Millas por hora)
    df['velocidad_promedio_mph'] = df['distancia_viaje'] / ((df['duracion_minutos'] + 0.0001) / 60.0)

    # 3. Indicador de viaje de aeropuerto
    zonas_aeropuerto = [1, 132, 138]
    if 'zona_origen' in df.columns and 'zona_destino' in df.columns:
        df['es_aeropuerto'] = (df['zona_origen'].isin(zonas_aeropuerto) |
                               df['zona_destino'].isin(zonas_aeropuerto)).astype(int)

    # 4. Features de costo SOLO PARA EDA (no se usan como predictores; ver preparar_datos).
    #    Se crean para describir el negocio, pero derivan de componentes del total,
    #    por lo que incluirlas en el modelo sería fuga de datos.
    if 'peajes' in df.columns:
        df['tiene_peaje'] = (df['peajes'] > 0).astype(int)
    if 'propina' in df.columns:
        df['tiene_propina'] = (df['propina'] > 0).astype(int)
        df['porcentaje_propina'] = (df['propina'] / df['monto_total'].replace(0, np.nan) * 100).fillna(0)

    # 5. Codificación de variables categóricas (One-Hot Encoding)
    categoricas = ['VendorID', 'zona_origen', 'zona_destino', 'tipo_tarifa', 'tipo_pago']
    columnas_presentes = [col for col in categoricas if col in df.columns]
    df = pd.get_dummies(df, columns=columnas_presentes, drop_first=True)

    return df

def preparar_datos(df):
    """Aplica el filtro anti data-leakage, convierte textos y divide cronológicamente."""
    print("Filtrando variables con Data Leakage y dividiendo datos...")

    # 1. Ordenar cronológicamente antes de dividir
    df = df.sort_values('fecha_inicio_viaje')

    # 2. Variables a ELIMINAR: componentes del total (leakage), fechas y features de costo de EDA
    columnas_a_eliminar = (COLUMNAS_LEAKAGE +
                           ['fecha_inicio_viaje', 'fecha_termino_viaje'] +
                           FEATURES_COSTO_EDA)
    X = df.drop(columns=[col for col in columnas_a_eliminar if col in df.columns])

    # 3. Transformar la columna de texto (Y/N) a números (1/0)
    if 'store_and_fwd_flag' in X.columns:
        X['store_and_fwd_flag'] = X['store_and_fwd_flag'].map({'Y': 1, 'N': 0}).fillna(0)

    # 4. Blindaje: Seleccionar ÚNICAMENTE columnas numéricas para evitar errores
    X = X.select_dtypes(include=[np.number, bool])

    # Separar la variable objetivo (monto_total)
    y = X.pop('monto_total')

    # División 80% Train / 20% Test sin barajar (shuffle=False)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    return X_train, X_test, y_train, y_test

def generar_graficos(y_train, y_test, pred_rf, importancias):
    """Genera los gráficos exigidos en la Parte 6 (no basta con mostrar números)."""
    os.makedirs("reports/graficos", exist_ok=True)

    # 1. Distribución del target
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(y_train, bins=60, color='#F6C90E', edgecolor='white')
    ax.set_title("Distribución del objetivo: monto_total ($)")
    ax.set_xlabel("Monto total ($)")
    ax.set_ylabel("Frecuencia")
    fig.tight_layout()
    fig.savefig("reports/graficos/distribucion_target.png", dpi=120)
    plt.close(fig)

    # 2. Análisis de errores del mejor modelo (Random Forest): predicho vs real y residuos
    residuos = y_test - pred_rf
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].scatter(y_test, pred_rf, alpha=0.3, color='#30475E', s=10)
    lim = [min(y_test.min(), pred_rf.min()), max(y_test.max(), pred_rf.max())]
    axes[0].plot(lim, lim, 'r--', linewidth=1)
    axes[0].set_title("Random Forest: Predicho vs. Real")
    axes[0].set_xlabel("Real ($)")
    axes[0].set_ylabel("Predicho ($)")
    axes[1].scatter(pred_rf, residuos, alpha=0.3, color='#E63946', s=10)
    axes[1].axhline(0, color='black', linewidth=1)
    axes[1].set_title("Distribución de residuos")
    axes[1].set_xlabel("Predicho ($)")
    axes[1].set_ylabel("Residuo (real - predicho)")
    fig.tight_layout()
    fig.savefig("reports/graficos/errores_modelo.png", dpi=120)
    plt.close(fig)

    # 3. Importancia de variables (top 15)
    top = importancias.head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top['variable'], top['importancia'], color='#30475E')
    ax.set_title("Top 15 variables más importantes (Random Forest)")
    ax.set_xlabel("Importancia")
    fig.tight_layout()
    fig.savefig("reports/graficos/importancia_variables.png", dpi=120)
    plt.close(fig)

    print("Gráficos guardados en 'reports/graficos/'")

def _df_a_markdown(df, decimales=3):
    """Convierte un DataFrame a tabla Markdown sin depender de 'tabulate'."""
    df = df.copy()
    for col in df.select_dtypes(include=[np.floating]).columns:
        df[col] = df[col].map(lambda v: f"{v:.{decimales}f}")
    encabezado = "| " + " | ".join(str(c) for c in df.columns) + " |"
    separador = "| " + " | ".join("---" for _ in df.columns) + " |"
    filas = ["| " + " | ".join(str(v) for v in fila) + " |" for fila in df.itertuples(index=False)]
    return "\n".join([encabezado, separador] + filas)

def escribir_informe(df_metricas, importancias, n_train, n_test):
    """Escribe el informe de resultados en Markdown con las métricas reales."""
    os.makedirs("reports", exist_ok=True)
    mejor = df_metricas.sort_values("RMSE").iloc[0]
    top5 = importancias.head(5)

    lineas = []
    lineas.append("# Informe de Resultados — Predicción de `monto_total` (Yellow Taxi NYC)\n")
    lineas.append("## 1. Datos y división")
    lineas.append(f"- Registros de entrenamiento: **{n_train:,}**")
    lineas.append(f"- Registros de prueba: **{n_test:,}**")
    lineas.append("- División **cronológica** 80/20 (`shuffle=False` tras ordenar por `fecha_inicio_viaje`).\n")
    lineas.append("## 2. Prevención de fuga de datos (data leakage)")
    lineas.append("Se excluyeron del entrenamiento todos los componentes que suman `total_amount` "
                  "(`tarifa_base`, `propina`, `peajes`, `extra`, `mta_tax`, `improvement_surcharge`, "
                  "`congestion_surcharge`, `Airport_fee`) y las features de costo derivadas "
                  "(`tiene_peaje`, `tiene_propina`, `porcentaje_propina`), creadas solo para EDA.\n")
    lineas.append("## 3. Métricas de los modelos\n")
    lineas.append(_df_a_markdown(df_metricas))
    lineas.append("")
    lineas.append(f"**Mejor modelo (por RMSE): {mejor['modelo']}** — "
                  f"MAE={mejor['MAE']:.2f}, RMSE={mejor['RMSE']:.2f}, R²={mejor['R2']:.3f}.\n")
    lineas.append("## 4. Variables más influyentes (Random Forest)\n")
    lineas.append(_df_a_markdown(top5))
    lineas.append("")
    lineas.append("## 5. Limitaciones y mejoras futuras")
    lineas.append("- El muestreo a 100.000 registros es aleatorio (`random_state=42`); puede sesgar "
                  "la representatividad temporal.")
    lineas.append("- One-Hot sobre `zona_origen`/`zona_destino` genera alta dimensionalidad; "
                  "una alternativa sería frequency/target encoding.")
    lineas.append("- Solo se serializa el Random Forest por ser el de mejor desempeño.")
    lineas.append("\n*Gráficos de soporte en `reports/graficos/`.*")

    with open("reports/informe_resultados.md", "w") as f:
        f.write("\n".join(lineas))
    print("Informe escrito en 'reports/informe_resultados.md'")

def entrenar_y_evaluar():
    # Cargar los datos limpios que generó tu ETL anterior
    ruta_datos = "data/processed/yellow_taxi_limpio.parquet"
    df = pd.read_parquet(ruta_datos)

    # 1. Feature Engineering
    df_features = crear_features(df)

    # 2. Preparación y Split
    X_train, X_test, y_train, y_test = preparar_datos(df_features)

    print(f"Set de entrenamiento: {X_train.shape[0]} viajes.")
    print(f"Set de prueba: {X_test.shape[0]} viajes.")

    # 3. Entrenamiento: Modelo Baseline (Regresión Lineal)
    print("Entrenando Regresión Lineal (Baseline)...")
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    pred_lr = lr.predict(X_test)

    # 4. Entrenamiento: Modelo Avanzado (Random Forest)
    print("Entrenando Random Forest Regressor...")
    rf = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    pred_rf = rf.predict(X_test)

    # 5. Evaluación de Métricas
    metricas = []
    for nombre, predicciones in [("Regresión Lineal", pred_lr), ("Random Forest", pred_rf)]:
        mae = mean_absolute_error(y_test, predicciones)
        rmse = np.sqrt(mean_squared_error(y_test, predicciones))
        r2 = r2_score(y_test, predicciones)
        metricas.append({"modelo": nombre, "MAE": mae, "RMSE": rmse, "R2": r2})

    df_metricas = pd.DataFrame(metricas)
    print("\n--- Resultados de los Modelos ---")
    print(df_metricas)

    # 6. Guardar Artefactos
    os.makedirs("data/outputs", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    # 6.1 Métricas
    df_metricas.to_csv("data/outputs/metricas_modelos.csv", index=False)

    # 6.2 Predicciones sobre el set de prueba (real vs. cada modelo)
    df_pred = pd.DataFrame({
        "valor_real": y_test.values,
        "pred_regresion_lineal": pred_lr,
        "pred_random_forest": pred_rf
    }, index=y_test.index)
    df_pred.to_csv("data/outputs/predicciones.csv", index=False)

    # 6.3 Importancia de variables (Random Forest)
    importancias = (pd.DataFrame({"variable": X_train.columns, "importancia": rf.feature_importances_})
                    .sort_values("importancia", ascending=False)
                    .reset_index(drop=True))
    importancias.to_csv("data/outputs/importancia_variables.csv", index=False)

    # 6.4 Modelo serializado (Random Forest, el de mejor desempeño)
    joblib.dump(rf, "models/modelo_final.pkl")

    # 7. Gráficos e informe (Parte 6: análisis visual)
    generar_graficos(y_train, y_test, pred_rf, importancias)
    escribir_informe(df_metricas, importancias, X_train.shape[0], X_test.shape[0])

    print("\nArtefactos guardados:")
    print("  - data/outputs/metricas_modelos.csv")
    print("  - data/outputs/predicciones.csv")
    print("  - data/outputs/importancia_variables.csv")
    print("  - models/modelo_final.pkl")
    print("  - reports/graficos/*.png")
    print("  - reports/informe_resultados.md")

if __name__ == "__main__":
    entrenar_y_evaluar()
