# 🚕 Sistema de Análisis y Predicción: Yellow Taxi NYC

Pipeline de datos de extremo a extremo + aplicación web interactiva (Streamlit) para explorar, consultar y **predecir el costo total** de los viajes de los taxis amarillos de Nueva York, evitando la fuga de datos (*data leakage*).

El flujo completo es:

```
data/raw/*.parquet  →  [ETL]  →  data/processed/yellow_taxi_limpio.parquet
                                          │
                                          ├─ [Modelado]  →  models/modelo_final.pkl
                                          │                  data/outputs/*.csv
                                          │                  reports/graficos/*.png + informe
                                          │
                                          └─ [App Streamlit]  →  exploración, KPIs, predicción
```

---

## 📋 Tabla de contenidos
1. [Requisitos](#1-requisitos)
2. [Estructura del proyecto](#2-estructura-del-proyecto)
3. [Instalación del entorno](#3-instalación-del-entorno)
4. [Paso 0 — Obtener los datos crudos](#4-paso-0--obtener-los-datos-crudos)
5. [Paso 1 — ETL (limpieza y preparación)](#5-paso-1--etl-limpieza-y-preparación)
6. [Paso 2 — Entrenamiento y evaluación](#6-paso-2--entrenamiento-y-evaluación)
7. [Paso 3 — Notebook (alternativa todo-en-uno)](#7-paso-3--notebook-alternativa-todo-en-uno)
8. [Paso 4 — Lanzar la aplicación web](#8-paso-4--lanzar-la-aplicación-web)
9. [Artefactos que genera el proyecto](#9-artefactos-que-genera-el-proyecto)
10. [Prevención de fuga de datos](#10-prevención-de-fuga-de-datos)
11. [Documentación adicional](#11-documentación-adicional)

---

## 1. Requisitos

- **Python 3.10+** (probado en 3.13).
- Las librerías del archivo `requirements.txt`

---

## 2. Estructura del proyecto

```
Gestion_de_datos_para_la_ia/
├── data/
│   ├── raw/            # Datos crudos TLC (.parquet)  ← debes colocarlos aquí
│   ├── processed/      # Dataset limpio (lo genera el ETL)
│   └── outputs/        # CSVs de métricas, predicciones, importancia, reporte de limpieza
├── src/
│   ├── pipeline.py     # ETL: carga + validación + limpieza + muestreo
│   └── modeling.py     # Features + split cronológico + entrenamiento + evaluación + artefactos
├── notebooks/
│   └── 01_pipeline_yellow_taxi.ipynb   # Pipeline completo documentado paso a paso
├── app/
│   ├── app.py          # Página principal de Streamlit
│   ├── pages/          # 6 páginas: exploración, KPIs, consulta, visualización, evaluación, predicción
│   └── utils/load_data.py
├── models/
│   └── modelo_final.pkl  # Random Forest serializado (lo genera el modelado)
├── reports/
│   ├── graficos/       # PNGs de distribución, errores e importancia
│   └── informe_resultados.md
├── docs/
│   ├── diccionario_variables.md
│   └── ANALISIS_CUMPLIMIENTO.md
├── requirements.txt
└── README.md
```

> **Importante:** todos los comandos se ejecutan **desde la raíz del proyecto** (`Gestion_de_datos_para_la_ia/`), porque tanto los scripts como la app usan rutas relativas (`data/...`, `models/...`).

---

## 3. Instalación del entorno

```bash
# 1. Posiciónate en la raíz del proyecto
cd Gestion_de_datos_para_la_ia

# 2. Instala las dependencias
pip install -r requirements.txt
# o, según tu sistema:
pip3 install -r requirements.txt
```

---

## 4. Obtener los datos crudos

El proyecto usa el dataset oficial **NYC TLC Yellow Taxi Trip Records** (formato Parquet).

1. Descarga los archivos mensuales desde la página oficial:
   <https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page>
2. Coloca en `data/raw/` los **5 meses** que cubre el pipeline:

   ```
   data/raw/yellow_tripdata_2023-12.parquet
   data/raw/yellow_tripdata_2024-01.parquet
   data/raw/yellow_tripdata_2024-02.parquet
   data/raw/yellow_tripdata_2024-03.parquet
   data/raw/yellow_tripdata_2024-04.parquet
   ```

> Tanto el ETL como el notebook leen **toda** la carpeta `data/raw/`. El periodo válido (`2023-12` a `2024-04`) está definido en `src/pipeline.py`; si cambias los meses, ajusta también esa lista (y la del notebook).

---

## 5. Paso 1 — ETL (limpieza y preparación)

```bash
python3 src/pipeline.py
```

Qué hace ([src/pipeline.py](src/pipeline.py)):
1. **Carga** todos los parquet de `data/raw/`.
2. **Renombra** las columnas al español.
3. **Validación inicial:** `shape`, `head()`, `info()`, nulos, duplicados y rangos (`describe()`).
4. **Limpieza** con reporte de registros eliminados **por cada filtro** (duplicados, nulos, distancia/monto/tarifa/pasajeros positivos, duración 0–180 min, coherencia temporal, periodo válido).
5. **Muestreo** aleatorio reproducible a 100.000 registros (`random_state=42`).

**Salidas:**
- `data/processed/yellow_taxi_limpio.parquet` (dataset limpio).
- `data/outputs/reporte_limpieza.csv` (registros perdidos por filtro).

---

## 6. Paso 2 — Entrenamiento y evaluación

```bash
python3 src/modeling.py
```

Qué hace ([src/modeling.py](src/modeling.py)):
1. **Ingeniería de características:** variables temporales (`pickup_hour`, `is_weekend`, `is_rush_hour`…), `velocidad_promedio_mph`, `es_aeropuerto`, features de costo para EDA y One-Hot Encoding de categóricas.
2. **División cronológica 80/20** (`sort_values` por fecha + `train_test_split(shuffle=False)`).
3. **Entrena** dos modelos: `LinearRegression` (baseline) y `RandomForestRegressor`.
4. **Evalúa** con MAE, RMSE y R².
5. **Genera** todos los artefactos (modelo, CSVs, gráficos e informe).

**Salidas:**
- `models/modelo_final.pkl` (Random Forest, el de mejor desempeño).
- `data/outputs/metricas_modelos.csv`, `predicciones.csv`, `importancia_variables.csv`.
- `reports/graficos/distribucion_target.png`, `errores_modelo.png`, `importancia_variables.png`.
- `reports/informe_resultados.md`.

**Resultados de referencia (5 meses, sin fuga de datos):**

| Modelo | MAE | RMSE | R² |
|---|---|---|---|
| Regresión Lineal | 2.71 | 5.56 | 0.938 |
| **Random Forest** | **2.03** | **4.43** | **0.961** |

> ⚠️ El **Paso 1 es prerrequisito del Paso 2**: `modeling.py` lee `data/processed/yellow_taxi_limpio.parquet`. Ejecuta siempre el ETL primero.

---

## 7. Paso 3 — Notebook (mismo proceso, documentado paso a paso)

El notebook [notebooks/01_pipeline_yellow_taxi.ipynb](notebooks/01_pipeline_yellow_taxi.ipynb) reproduce **exactamente el mismo proceso** que los scripts `pipeline.py` + `modeling.py`: misma carga (5 meses), misma validación, mismos filtros con reporte por regla, mismas features (incluido `es_aeropuerto` y One-Hot), mismo split cronológico, mismos modelos y **los mismos artefactos de salida**. Con `random_state=42` las métricas son idénticas a las del Paso 2.

Sirve como **versión didáctica y autocontenida** del pipeline: ejecuta los pasos 1 y 2 por sí solo (carga desde `data/raw/`, regenera el parquet limpio, los CSV, el modelo, los gráficos y el informe). Internamente hace `os.chdir` a la raíz del proyecto, así que las rutas son las mismas que las de los scripts.

```bash
# Opción A: abrir en Jupyter / VS Code y ejecutar las celdas en orden
jupyter notebook notebooks/01_pipeline_yellow_taxi.ipynb

# Opción B: ejecutarlo de forma no interactiva
pip install nbconvert ipykernel
jupyter nbconvert --to notebook --execute --inplace notebooks/01_pipeline_yellow_taxi.ipynb
```

> No necesita haber corrido el ETL previamente: parte de los datos crudos de `data/raw/` y genera todo lo demás.

---

## 8. Paso 4 — Lanzar la aplicación web

Requiere que existan `data/processed/yellow_taxi_limpio.parquet` (Paso 1), `data/outputs/metricas_modelos.csv` y `models/modelo_final.pkl` (Paso 2).

```bash
streamlit run app/app.py
```

Se abrirá en el navegador (por defecto <http://localhost:8501>). Páginas disponibles:
- **📊 Exploración de Datos** — vista previa y estadísticas del dataset limpio.
- **📈 Indicadores** — KPIs (recaudación, distancia/duración promedio, % con propina).
- **🧮 Consulta de Viajes** — filtros interactivos + exportación a CSV.
- **📊 Visualizaciones** — distancia vs. monto, distribución de duración.
- **🎯 Evaluación del Modelo** — métricas comparadas de los modelos.
- **🤖 Predicción** — estima el costo de un viaje nuevo con el Random Forest.

---

## 9. Artefactos que genera el proyecto

| Archivo | Generado por | Contenido |
|---|---|---|
| `data/processed/yellow_taxi_limpio.parquet` | `pipeline.py` | Dataset limpio (100k filas). |
| `data/outputs/reporte_limpieza.csv` | `pipeline.py` | Registros eliminados por filtro. |
| `data/outputs/metricas_modelos.csv` | `modeling.py` | MAE/RMSE/R² por modelo. |
| `data/outputs/predicciones.csv` | `modeling.py` | Real vs. predicho (LR y RF) en el set de prueba. |
| `data/outputs/importancia_variables.csv` | `modeling.py` | `feature_importances_` del Random Forest. |
| `models/modelo_final.pkl` | `modeling.py` | Modelo serializado. |
| `reports/graficos/*.png` | `modeling.py` | Distribución del target, errores, importancia. |
| `reports/informe_resultados.md` | `modeling.py` | Informe con métricas reales y limitaciones. |

> Estos artefactos están en `.gitignore` (se regeneran ejecutando los pasos 1 y 2).

---

## 10. Prevención de fuga de datos

La variable objetivo es `monto_total` (`total_amount`), que es la **suma** de varios componentes del recibo. Para que el modelo no "haga trampa", se **excluyen del entrenamiento**:

- Componentes del total: `tarifa_base`, `propina`, `peajes`, `extra`, `mta_tax`, `improvement_surcharge`, `congestion_surcharge`, `Airport_fee`.
- Features de costo derivadas (`tiene_peaje`, `tiene_propina`, `porcentaje_propina`): se crean **solo para el EDA** y no se usan como predictores.

El modelo predice con variables conocidas **antes** de cerrar el viaje (distancia, duración, hora, zona, tipo de tarifa/pago). Aun así el Random Forest logra R²≈0.96, porque `distancia_viaje` y `duracion_minutos` son predictores legítimos y dominantes. Detalle en [docs/diccionario_variables.md](docs/diccionario_variables.md).

---

## 11. Documentación adicional

- [docs/diccionario_variables.md](docs/diccionario_variables.md) — descripción de cada columna (cruda, renombrada y derivada).
- [docs/ANALISIS_CUMPLIMIENTO.md](docs/ANALISIS_CUMPLIMIENTO.md) — cumplimiento del proyecto frente a la rúbrica del examen.
- [reports/informe_resultados.md](reports/informe_resultados.md) — informe de resultados con métricas reales.

---

