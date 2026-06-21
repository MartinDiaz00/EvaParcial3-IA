# Matriz de cumplimiento EP3

| Indicador | Evidencia en el proyecto | Archivo / sección |
|---|---|---|
| IE1 - Precisión, consistencia y errores | Métricas de relevancia, consistencia y tasa de error | `app/metrics.py`, `scripts/evaluate_observability.py`, `outputs/metrics/` |
| IE2 - Latencia y recursos | Duración total, duración por span, CPU y memoria | `app/observability.py`, `dashboard.py`, `outputs/logs/agent_events.jsonl` |
| IE3 - Logs y eventos | Logs JSONL con `trace_id`, `span_id`, `span`, `event`, estado y duración | `outputs/logs/agent_events.jsonl` |
| IE4 - Patrones/anomalías | Detección de trazas lentas y anomalías por umbral | `app/metrics.py`, sección Anomalías del dashboard |
| IE5 - Dashboard visual | Dashboard Streamlit con métricas, logs y gráficos | `dashboard.py` |
| IE6 - Seguridad y uso responsable | Sanitización, bloqueo de prompt injection, audit trail y revisión humana | `app/security.py`, `outputs/logs/audit_trail.jsonl` |
| IE7 - Mejoras de desempeño | Recomendaciones basadas en latencia, errores, herramientas y trazas | `outputs/metrics/analisis_logs.md`, informe técnico |
| IE8 - Informe y visualizaciones | Informe EP3 en DOCX y PDF | `docs/INFORME_EP3_Observabilidad_HealthTech.*` |
| IE9 - Lenguaje técnico y evidencias | README, matriz e informe técnico | `README.md`, `docs/` |
