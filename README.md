# Pipeline de Ingesta de Datos: Mercado Laboral Tecnológico 📊

**Institución:** Duoc UC  
**Asignatura:** Gestion de Dato para la IA (Sección 001V)  
**Integrantes:** Alejandro González , Cristóbal Godoy , Jean Gordóniz y Leonel Toro 
**Fecha de entrega:** Miércoles 29 de abril de 2026

## Descripción del Proyecto
Este repositorio contiene un flujo automatizado ETL (Extract, Transform, Load) desarrollado en Python. El objetivo es recolectar, limpiar y estructurar diariamente ofertas de empleo desde portales laborales, sirviendo como la primera etapa (Data Ingestion) para el entrenamiento de un futuro modelo de Inteligencia Artificial enfocado en el análisis del mercado.

## Arquitectura del Repositorio
```text
data-ingestion-project/
│
├── data/
│   ├── raw/             # Reservado para volcados crudos
│   └── processed/       # Archivos procesados en formato CSV y JSON
│
├── scripts/
│   └── ingestion.py     # Script principal del pipeline ETL
│
├── logs/
│   └── ingestion.log    # Trazabilidad de eventos y errores del sistema
│
├── docs/
│   └── proceso.md       # Explicación técnica detallada y automatización
│
├── README.md            # Portada y manual de uso
└── requirements.txt     # Dependencias de librerías