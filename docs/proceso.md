# Documentación del Proceso de Ingesta (ETL)
**Proyecto:** Ingesta de Datos del Mercado Laboral (Empleos Remotos)
**Integrantes:** Alejandro González , Cristobal Godoy , Jean Gordóniz y Leonel Toro
**Fecha:** Abril 2026

## 1. Definición y Fuente de Datos
Para este taller, definimos que nuestro modelo de Inteligencia Artificial requerirá datos actualizados del mercado laboral tecnológico. 
Se seleccionó la API pública de **Remotive** (`https://remotive.com/api/remote-jobs`), la cual provee información estructurada sobre ofertas de trabajo a nivel global sin requerir autenticación compleja, garantizando la fiabilidad de la extracción.

## 2. Fase de Extracción (Extract)
El proceso se realiza mediante un script en Python (`scripts/ingestion.py`). 
Se utiliza la librería `requests` para consumir el endpoint de la API filtrando por la categoría *Software Development*. Se implementó un control de excepciones mediante un bloque `try/catch` y el método `raise_for_status()` para asegurar que el script no colapse ante caídas de red o errores de servidor (ej. Errores 500 o 404), retornando `None` y registrando el fallo de manera segura.

## 3. Fase de Transformación (Transform)
La manipulación de los datos en memoria se realiza con la librería `pandas`. Las reglas de negocio aplicadas son:
* **Selección de Columnas:** Solo se conservan atributos útiles para el modelo: `id`, `title`, `company_name`, `category`, `job_type`, y `publication_date`.
* **Limpieza de Nulos (Drop & Fill):** Se eliminan los registros que no posean el Título del cargo o el Nombre de la empresa, ya que son críticos. Los tipos de contrato vacíos se rellenan con el string `"no_especificado"`.
* **Normalización:** Los textos categóricos (títulos y categorías) se transforman a minúsculas y se limpian de espacios en blanco residuales (`strip()`). Las fechas se formatean al estándar `YYYY-MM-DD`.

## 4. Fase de Carga (Load)
Para maximizar la compatibilidad con futuras herramientas de análisis y Machine Learning, se implementó un guardado dual estructurado. Los DataFrames procesados se exportan simultáneamente a:
1. **Formato CSV** (Análisis tabular tradicional).
2. **Formato JSON** (Ingesta óptima para modelos basados en diccionarios/documentos).
Los archivos se guardan en el directorio `data/processed/` etiquetados dinámicamente con la fecha de ejecución.

## 5. Control de Errores y Trazabilidad
Se integró la librería nativa `logging`. Cada ejecución del pipeline deja un rastro de auditoría en `logs/ingestion.log`. Esto clasifica los eventos en niveles `INFO` (ejecuciones exitosas), `WARNING` (datos vacíos) y `ERROR` (fallos de conexión o escritura), permitiendo un monitoreo sin supervisión visual de la consola.

## 6. Automatización del Sistema
Para cumplir con el requerimiento de periodicidad, el pipeline fue configurado para ejecutarse diariamente de forma desatendida.