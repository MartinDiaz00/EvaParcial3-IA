# Análisis de logs y métricas EP3

- Solicitudes registradas: 7
- Solicitudes completadas: 7
- Tasa de error: 0.0
- Latencia promedio: 20.73 ms
- Latencia p95: 40.93 ms
- Memoria máxima observada: 64.88 MB
- CPU máximo observado: 0.0 %
- Trazas lentas detectadas: 0

## Hallazgos

- La trazabilidad permite reconstruir cada solicitud por `trace_id`.
- Las métricas de latencia permiten detectar cuellos de botella por span.
- El uso de herramientas permite identificar qué componente concentra más trabajo.
- Las métricas de recursos entregan una referencia básica de CPU y memoria.

## Mejoras propuestas

1. Mantener trazabilidad por `trace_id` en cada consulta.
2. Agregar caché para consultas repetidas de RAG.
3. Definir umbrales de alerta para latencia, errores y consumo de recursos.
4. Revisar manualmente respuestas médicas sensibles.
5. Aumentar el set de preguntas evaluadas para medir calidad con mayor cobertura.