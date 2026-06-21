"""Dashboard de observabilidad para la EP3.
Ejecutar desde la raiz del proyecto:
    python -m streamlit run dashboard.py
"""
from __future__ import annotations
import json
from pathlib import Path

import pandas as pd
import streamlit as st

LOG_FILE = Path("outputs/logs/agent_events.jsonl")
METRICS_FILE = Path("outputs/metrics/metrics_summary.json")
EVAL_FILE = Path("outputs/metrics/evaluation_results.json")

st.set_page_config(page_title="HealthTech EP3 Observabilidad", layout="wide")
st.title("Dashboard de Observabilidad - HealthTech")
st.caption("Métricas, logs y trazas generadas durante la ejecución del agente.")


def read_jsonl(path: Path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows

logs = read_jsonl(LOG_FILE)
summary = json.loads(METRICS_FILE.read_text(encoding="utf-8")) if METRICS_FILE.exists() else {}
eval_rows = json.loads(EVAL_FILE.read_text(encoding="utf-8")) if EVAL_FILE.exists() else []

if not logs:
    st.warning("No hay datos todavía. Ejecuta primero: python -m scripts.evaluate_observability")
    st.stop()

df = pd.DataFrame(logs)
if "duration_ms" in df.columns:
    df["duration_ms"] = pd.to_numeric(df["duration_ms"], errors="coerce")
if "cpu_percent" in df.columns:
    df["cpu_percent"] = pd.to_numeric(df["cpu_percent"], errors="coerce")
if "memory_mb" in df.columns:
    df["memory_mb"] = pd.to_numeric(df["memory_mb"], errors="coerce")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Solicitudes", summary.get("total_requests", 0))
col2.metric("Tasa de error", summary.get("error_rate", 0))
col3.metric("Latencia promedio ms", summary.get("latency_ms", {}).get("mean", 0))
col4.metric("Latencia p95 ms", summary.get("latency_ms", {}).get("p95", 0))

if "quality_metrics" in summary:
    q = summary["quality_metrics"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Precisión/Relevancia promedio", q.get("mean_relevance_score", 0))
    c2.metric("Consistencia", q.get("consistency_score", 0))
    c3.metric("Preguntas evaluadas", q.get("evaluated_questions", 0))

st.subheader("Logs estructurados")
st.dataframe(df, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Latencia por span")
    span_latency = summary.get("span_latency_mean_ms", {})
    if span_latency:
        st.bar_chart(pd.DataFrame({"span": list(span_latency.keys()), "latencia_ms": list(span_latency.values())}).set_index("span"))
with right:
    st.subheader("Uso de herramientas")
    usage = summary.get("tool_usage", {})
    if usage:
        st.bar_chart(pd.DataFrame({"tool": list(usage.keys()), "uso": list(usage.values())}).set_index("tool"))

st.subheader("Uso de recursos")
r1, r2 = st.columns(2)
with r1:
    cpu_rows = df.dropna(subset=["cpu_percent"]) if "cpu_percent" in df.columns else pd.DataFrame()
    if not cpu_rows.empty:
        st.line_chart(cpu_rows[["cpu_percent"]].reset_index(drop=True))
    else:
        st.info("No hay datos de CPU aún.")
with r2:
    mem_rows = df.dropna(subset=["memory_mb"]) if "memory_mb" in df.columns else pd.DataFrame()
    if not mem_rows.empty:
        st.line_chart(mem_rows[["memory_mb"]].reset_index(drop=True))
    else:
        st.info("No hay datos de memoria aún.")

st.subheader("Errores y estados")
if "status" in df.columns:
    status_counts = df["status"].fillna("sin_estado").value_counts()
    st.bar_chart(status_counts)

st.subheader("Anomalías detectadas")
completed = df[(df.get("event") == "end") & (df.get("duration_ms").notna())] if "duration_ms" in df.columns else pd.DataFrame()
if not completed.empty:
    mean_latency = completed["duration_ms"].mean()
    threshold = max(mean_latency * 2, 3000)
    anomalies = completed[completed["duration_ms"] > threshold]
    if anomalies.empty:
        st.success(f"No se detectaron anomalías de latencia. Umbral aplicado: {threshold:.2f} ms.")
    else:
        st.warning(f"Se detectaron {len(anomalies)} spans sobre el umbral de {threshold:.2f} ms.")
        st.dataframe(anomalies, use_container_width=True)
else:
    st.info("No hay spans finalizados con duración para analizar anomalías.")

st.subheader("Evaluación de calidad")
if eval_rows:
    st.dataframe(pd.DataFrame(eval_rows), use_container_width=True)
else:
    st.info("Ejecuta la evaluación para generar resultados de calidad.")

st.subheader("Hallazgos y recomendaciones")
st.markdown("""
- Revisar trazas lentas usando el `trace_id` para reconstruir cada solicitud.
- Optimizar RAG o cachear consultas si la latencia p95 supera el umbral definido.
- Mantener revisión humana en consultas clínicas sensibles.
- Evitar guardar datos personales; los logs usan hash y sanitización básica.
- Separar métricas de rendimiento, calidad y seguridad para facilitar la mejora continua.
""")
