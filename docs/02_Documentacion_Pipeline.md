# Documentación Técnica — Pipeline DataOps: Detección de Fraude

---

## 1. Descripción General del Proyecto

El proyecto implementa un **pipeline de datos** orientado a DataOps para procesar transacciones bancarias y prepararlas para un modelo de inteligencia artificial de detección de fraude.

El flujo toma un archivo CSV crudo con 22 columnas de transacciones bancarias, aplica transformaciones, validaciones estructurales y semánticas, y genera dos salidas:

- `datos_listos_modelo.csv` — registros válidos listos para entrenar/inferir con IA.
- `datos_corruptos_log.csv` — registros inválidos en cuarentena con banderas de diagnóstico.

---

## 2. Arquitectura del Pipeline

```
[CSV Crudo]
    │
    ▼
renombrar_columnas()         ← Estandarización de cabeceras (inglés → español)
    │
    ▼
aplicar_transformaciones()   ← Ingeniería de características (edad, distancia, hora)
    │
    ▼
validaciones_estructurales() ← Verificación de tipos y valores permitidos
    │
    ▼
validaciones_semanticas()    ← Coherencia lógica entre campos relacionados
    │
    ▼
    ├──[Válidos]──► formatear_fechas() ──► datos_listos_modelo.csv
    │
    └──[Inválidos]──► formatear_fechas() ──► datos_corruptos_log.csv
```

El pipeline es **modular**: cada función tiene una única responsabilidad, lo que facilita el mantenimiento, el testing y la sustitución de etapas de forma independiente.

---

## 3. Etapas del Ciclo de Vida DataOps

### 3.1 Ingesta de Datos

**¿Qué hace?**
Lee el archivo CSV crudo desde `datos/crudos/02_fraudTest.csv` usando `pandas.read_csv()`.

**Decisión técnica:** Se eligió CSV como fuente de entrada por ser el formato estándar del dataset. En producción, esta etapa podría reemplazarse por una conexión a base de datos o un stream de eventos sin modificar el resto del pipeline.

**Estabilidad de paths:** Los paths se construyen con `os.path.abspath(__file__)` para que el script funcione independientemente del directorio desde donde se ejecute.

---

### 3.2 Estandarización de Cabeceras (`renombrar_columnas`)

**¿Qué hace?**
Aplica el diccionario `COLUMNAS_ES` para traducir los 22 nombres de columnas del inglés al español.

| Original | Español |
|---|---|
| `trans_date_trans_time` | `fecha_hora_transaccion` |
| `cc_num` | `numero_tarjeta` |
| `amt` | `monto` |
| `gender` | `genero` |
| `dob` | `fecha_nacimiento` |
| `is_fraud` | `es_fraude` |
| ... | ... |

**Justificación:** Centralizar el mapeo en un diccionario (`COLUMNAS_ES`) permite actualizar nombres en un solo lugar. Si el proveedor del dataset cambia un nombre de columna, solo se edita el diccionario sin tocar la lógica de negocio.

---

### 3.3 Transformaciones (`aplicar_transformaciones`)

**¿Qué hace?** Genera tres nuevas columnas derivadas con valor para el modelo de IA:

| Nueva columna | Cálculo | Justificación |
|---|---|---|
| `edad_titular` | Diferencia en días entre `fecha_hora_transaccion` y `fecha_nacimiento`, dividido entre 365 | La edad es un factor de riesgo relevante en modelos de fraude |
| `distancia_km` | Fórmula de Haversine entre coordenadas del titular y del comercio | Una transacción muy lejos de la residencia es un indicador de fraude |
| `hora_transaccion` | Hora extraída de `fecha_hora_transaccion` | Las transacciones nocturnas presentan mayor riesgo estadístico |

**Fórmula de Haversine:**
Calcula la distancia real sobre la superficie terrestre entre dos puntos geográficos usando sus coordenadas de latitud y longitud. Es más precisa que la distancia euclidiana para coordenadas geográficas.

```python
a = sin²(Δlat/2) + cos(lat1) · cos(lat2) · sin²(Δlon/2)
distancia = 2 · R · arctan2(√a, √(1−a))   # R = 6371 km
```

**Manejo de errores:** `pd.to_datetime(..., errors='coerce')` convierte fechas malformadas en `NaT` en lugar de lanzar una excepción. Esto permite que el pipeline continúe y que los registros con fechas inválidas sean capturados en la etapa de validación posterior.

---

### 3.4 Validaciones Estructurales (`validaciones_estructurales`)

**¿Qué hace?** Verifica que los datos tengan el tipo y formato correcto:

| Columna | Validación | Bandera generada |
|---|---|---|
| `monto` | Convertible a número | `NaN` si falla |
| `genero` | Solo acepta `'M'` o `'F'` | `genero_valido` |
| `es_fraude` | Solo acepta `0` o `1` | `fraude_valido` |

**Decisión técnica:** Se usan columnas booleanas ("banderas") en lugar de eliminar registros inmediatamente. Esto permite que los registros inválidos pasen al final del pipeline con su diagnóstico completo, facilitando el análisis de calidad de datos.

---

### 3.5 Validaciones Semánticas (`validaciones_semanticas`)

**¿Qué hace?** Verifica la coherencia lógica entre campos relacionados:

| Validación | Regla | Bandera |
|---|---|---|
| Coherencia de fechas | La transacción debe ser posterior al nacimiento del titular | `fechas_coherentes` |
| Monto positivo | El monto debe ser mayor a 0 | `monto_valido` |

**Diferencia clave con validación estructural:** La validación estructural verifica el *tipo* del dato (¿es un número?). La semántica verifica el *significado* (¿tiene sentido que este número sea negativo?). Ambas capas son necesarias.

---

### 3.6 Separación Válidos / Inválidos

```python
es_valido = (
    df['monto'].notnull() &
    df['edad_titular'].notnull() &
    df['genero_valido'] &
    df['fraude_valido'] &
    df['fechas_coherentes'] &
    df['monto_valido']
)
```

Un registro es válido **solo si pasa todas las condiciones**. Los inválidos se envían a cuarentena conservando las columnas bandera para poder diagnosticar exactamente qué falló en cada registro.

---

### 3.7 Formateo de Fechas (`formatear_fechas`)

**¿Qué hace?** Convierte las columnas de fecha a string con formato legible en español:

| Columna | Formato de salida |
|---|---|
| `fecha_hora_transaccion` | `dd-MM-YYYY HH:mm:ss` |
| `fecha_nacimiento` | `dd-MM-YYYY` |

**¿Por qué al final?** Durante el procesamiento las fechas se mantienen como objetos `datetime` de pandas para poder hacer operaciones aritméticas (diferencias, comparaciones). Solo se convierten a string en el momento de exportar, evitando errores de tipo.

---

## 4. Observabilidad: Sistema de Logs

El pipeline registra cada etapa en `logs/pipeline_fraude.log`:

```
2026-05-25 10:00:01 - INFO - --- INICIANDO PIPELINE DE DATOS: CASO FRAUDE ---
2026-05-25 10:00:01 - INFO - Se renombran las columnas y se estandarizan los nombres.
2026-05-25 10:00:02 - INFO - Transformaciones aplicadas con éxito.
2026-05-25 10:00:02 - INFO - Validaciones estructurales completadas.
2026-05-25 10:00:02 - INFO - Validaciones semánticas completadas.
2026-05-25 10:00:03 - INFO - Total procesados: 555719
2026-05-25 10:00:03 - INFO - Registros procesados exitosamente: 553574
2026-05-25 10:00:03 - INFO - Registros con errores o inconsistencias: 2145
2026-05-25 10:00:03 - INFO - --- FIN DEL PIPELINE ---
```

**Justificación:** Los logs son el pilar de observabilidad en DataOps. Permiten auditar cada ejecución, detectar cuándo empeoró la calidad de datos y reproducir el estado del pipeline en cualquier punto del tiempo.

---

## 5. Estructura del Proyecto

```
Proyecto_DataOps_Fraude/
│
├── datos/
│   ├── crudos/
│   │   └── 02_fraudTest.csv        ← Datos de entrada (sin modificar)
│   └── procesados/                 ← Generada automáticamente por el pipeline
│       ├── datos_listos_modelo.csv
│       └── datos_corruptos_log.csv
│
├── docs/
│   ├── 01_Metadata.txt             ← Diccionario de datos original
│   └── 02_Documentacion_Pipeline.md ← Este archivo
│
├── logs/                           ← Generada automáticamente
│   └── pipeline_fraude.log
│
├── src/
│   └── pipeline_fraude.py          ← Código fuente principal
│
└── requirements.txt
```

---

## 6. Herramientas Seleccionadas y Justificación

| Herramienta | Uso | Alternativas evaluadas | Razón de selección |
|---|---|---|---|
| **pandas** | Manipulación de datos tabulares | PySpark, Polars | Suficiente para el volumen del dataset; curva de aprendizaje baja; integración nativa con numpy |
| **numpy** | Operaciones matemáticas vectorizadas (Haversine) | math (módulo estándar) | `numpy` opera sobre columnas enteras en una sola instrucción; `math` requeriría un loop por fila |
| **logging** | Registro de eventos del pipeline | print(), loguru | Módulo estándar de Python; permite niveles (INFO/ERROR), rotación de archivos y formato configurable sin dependencias externas |
| **os** | Gestión de paths y directorios | pathlib | Ambos válidos; `os` es más universal en entornos de producción legacy |

---

## 7. Manejo de Anomalías

### 7.1 Tipos de anomalías contempladas

| Tipo | Ejemplo | Estrategia |
|---|---|---|
| Datos faltantes | Monto vacío, fecha en blanco | `errors='coerce'` → convierte a `NaN`/`NaT`; el registro cae en cuarentena |
| Tipo incorrecto | Texto en columna numérica | `pd.to_numeric(..., errors='coerce')` → convierte a `NaN` |
| Valor fuera de dominio | Género distinto de M/F | `.isin(['M','F'])` → bandera `genero_valido=False` |
| Inconsistencia lógica | Fecha de nacimiento posterior a la transacción | Comparación directa → bandera `fechas_coherentes=False` |
| Monto inválido | Monto negativo o cero | `df['monto'] > 0` → bandera `monto_valido=False` |

### 7.2 Proceso de diagnóstico ante un error

1. **Identificar:** Revisar `logs/pipeline_fraude.log` para localizar en qué etapa apareció el error y el mensaje exacto.
2. **Diagnosticar:** Abrir `datos_corruptos_log.csv` y filtrar por la columna bandera que está en `False` para el registro problemático.
3. **Corregir:** Dependiendo del origen:
   - Si es un error en la fuente → coordinar corrección con el proveedor del dato.
   - Si es un error de lógica en el pipeline → ajustar la validación correspondiente y re-ejecutar.
4. **Verificar:** Confirmar que el registro ahora pasa a `datos_listos_modelo.csv` y que el log refleja el resultado esperado.

---

## 8. Escalabilidad

El pipeline está diseñado para escalar de forma progresiva:

| Nivel | Cambio necesario | Sin cambiar |
|---|---|---|
| **Mayor volumen de datos** | Reemplazar `pandas` por `PySpark` o `Polars` en las funciones de transformación | La lógica de negocio, validaciones y estructura de carpetas |
| **Múltiples fuentes de datos** | Modificar solo la etapa de ingesta para leer de BD, API o stream (Kafka) | El resto del pipeline desde `renombrar_columnas()` en adelante |
| **Automatización** | Orquestar con Apache Airflow o cron; cada función ya es un task independiente | El código de las funciones |
| **Nube** | Mover `datos/` a S3 o GCS; usar rutas absolutas de cloud storage | La lógica de transformación |
| **Monitoreo avanzado** | Reemplazar `logging` por herramientas como Great Expectations o MLflow para validación de calidad de datos en producción | La estructura modular del pipeline |

**Principio de diseño clave:** cada función del pipeline tiene exactamente una responsabilidad. Esto garantiza que escalar o modificar una etapa no rompa las demás.

---

## 9. Preguntas Frecuentes de Evaluación

**¿Por qué separar en funciones en lugar de escribir todo en un bloque?**
La modularidad permite testear cada etapa de forma aislada, reemplazar una etapa sin tocar las demás y reutilizar funciones (por ejemplo, `calcular_distancia_haversine` podría usarse en otro pipeline).

**¿Por qué no eliminar los registros inválidos directamente?**
Porque los datos inválidos tienen valor: permiten medir la calidad de la fuente de datos a lo largo del tiempo. Si el porcentaje de inválidos aumenta de una ejecución a la siguiente, es una señal de alerta sobre la fuente.

**¿Qué pasa si el archivo CSV no existe?**
El bloque `if os.path.exists(archivo_csv)` detecta la ausencia del archivo. En la versión actual muestra un mensaje de error. En producción se lanzaría una excepción controlada con notificación al equipo.

**¿Por qué usar Haversine y no distancia euclidiana?**
La distancia euclidiana entre coordenadas geográficas es incorrecta porque la Tierra es esférica. Haversine calcula la distancia real sobre la superficie, lo que es crítico para detectar transacciones geográficamente anómalas.

**¿Cómo se garantiza la reproducibilidad del pipeline?**
Los datos de entrada no se modifican nunca (están en `datos/crudos/`). Cada ejecución genera outputs frescos y un log con timestamp. Esto permite comparar ejecuciones distintas y detectar deriva en los datos.
