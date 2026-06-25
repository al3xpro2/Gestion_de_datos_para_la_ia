# Informe de Resultados — Predicción de `monto_total` (Yellow Taxi NYC)

## 1. Datos y división
- Registros de entrenamiento: **160,000**
- Registros de prueba: **40,000**
- División **cronológica** 80/20 (`shuffle=False` tras ordenar por `fecha_inicio_viaje`).

## 2. Prevención de fuga de datos (data leakage)
Se excluyeron del entrenamiento todos los componentes que suman `total_amount` (`tarifa_base`, `propina`, `peajes`, `extra`, `mta_tax`, `improvement_surcharge`, `congestion_surcharge`, `Airport_fee`) y las features de costo derivadas (`tiene_peaje`, `tiene_propina`, `porcentaje_propina`), creadas solo para EDA.

## 3. Métricas de los modelos

| modelo | MAE | RMSE | R2 |
| --- | --- | --- | --- |
| Regresión Lineal | 3.718 | 7.342 | 0.895 |
| Random Forest | 2.051 | 4.280 | 0.964 |

**Mejor modelo (por RMSE): Random Forest** — MAE=2.05, RMSE=4.28, R²=0.964.

## 4. Variables más influyentes (Random Forest)

| variable | importancia |
| --- | --- |
| distancia_viaje | 0.824 |
| duracion_minutos | 0.104 |
| tipo_tarifa_5.0 | 0.013 |
| tipo_tarifa_2.0 | 0.011 |
| tipo_pago_2 | 0.008 |

## 5. Limitaciones y mejoras futuras
- El muestreo a 100.000 registros es aleatorio (`random_state=42`); puede sesgar la representatividad temporal.
- One-Hot sobre `zona_origen`/`zona_destino` genera alta dimensionalidad; una alternativa sería frequency/target encoding.
- Solo se serializa el Random Forest por ser el de mejor desempeño.

*Gráficos de soporte en `reports/graficos/`.*