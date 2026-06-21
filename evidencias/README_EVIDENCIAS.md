# Evidencias esperadas para EP3

Después de configurar `.env`, ejecutar:

```bash
python -m scripts.evaluate_observability
python -m streamlit run dashboard.py
```

Capturas recomendadas para entregar:

1. Dashboard completo con métricas principales.
2. Tabla de logs estructurados con `trace_id` y `span_id`.
3. Gráficos de latencia, uso de herramientas, CPU y memoria.
4. Archivo `outputs/metrics/metrics_summary.json`.
5. Archivo `outputs/logs/audit_trail.jsonl`.
6. Salida de `python -m pytest -q`.
