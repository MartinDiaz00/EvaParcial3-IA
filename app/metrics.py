"""Cálculo de métricas EP3: precisión, consistencia, errores, latencia, recursos y anomalías."""
from __future__ import annotations

import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .config import METRICS_DIR
from .observability import LOG_FILE, SUMMARY_FILE, read_jsonl


def _tokens(text: str) -> set[str]:
    import re
    return {t for t in re.sub(r"[^a-záéíóúñü0-9 ]", " ", text.lower()).split() if len(t) > 2}


def relevance_score(answer: str, expected_keywords: Iterable[str]) -> float:
    """Métrica simple de precisión/relevancia: porcentaje de keywords esperadas presentes."""
    expected = {k.lower() for k in expected_keywords if k.strip()}
    if not expected:
        return 0.0
    text_tokens = _tokens(answer)
    hits = sum(1 for k in expected if k in text_tokens or k in answer.lower())
    return round(hits / len(expected), 3)


def consistency_score(answers: List[str]) -> float:
    """Similitud promedio Jaccard entre respuestas repetidas a la misma pregunta."""
    if len(answers) < 2:
        return 1.0
    pairs = []
    token_sets = [_tokens(a) for a in answers]
    for i in range(len(token_sets)):
        for j in range(i + 1, len(token_sets)):
            union = token_sets[i] | token_sets[j]
            inter = token_sets[i] & token_sets[j]
            pairs.append(len(inter) / max(len(union), 1))
    return round(statistics.mean(pairs), 3)


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    index = min(int(math.ceil((p / 100) * len(values))) - 1, len(values) - 1)
    return round(values[index], 2)


def analyze_logs(log_path: Path = LOG_FILE) -> Dict[str, Any]:
    rows = read_jsonl(log_path)
    completed = [r for r in rows if r.get("event") == "end"]
    errors = [r for r in rows if r.get("event") == "error"]
    full_requests = [r for r in completed if r.get("span") == "full_request"]
    durations = [float(r.get("duration_ms", 0)) for r in full_requests]

    span_durations = defaultdict(list)
    tools = Counter()
    for r in completed:
        span = r.get("span", "unknown")
        span_durations[span].append(float(r.get("duration_ms", 0)))
        if span.startswith("tool_"):
            tools[span] += 1

    total_requests = len({r.get("trace_id") for r in rows if r.get("span") == "full_request" and r.get("event") == "start"})
    mean_latency = statistics.mean(durations) if durations else 0.0
    anomaly_threshold = max(mean_latency * 2, 3000.0)
    slow_requests = [r for r in full_requests if float(r.get("duration_ms", 0)) > anomaly_threshold]

    summary = {
        "total_events": len(rows),
        "total_requests": total_requests,
        "completed_requests": len(full_requests),
        "error_count": len(errors),
        "error_rate": round(len(errors) / max(total_requests, 1), 3),
        "latency_ms": {
            "mean": round(mean_latency, 2) if durations else 0.0,
            "median": round(statistics.median(durations), 2) if durations else 0.0,
            "p95": percentile(durations, 95),
            "max": round(max(durations), 2) if durations else 0.0,
        },
        "span_latency_mean_ms": {k: round(statistics.mean(v), 2) for k, v in span_durations.items() if v},
        "tool_usage": dict(tools),
        "error_types": dict(Counter(r.get("error_type", "unknown") for r in errors)),
        "anomalies": {
            "latency_threshold_ms": round(anomaly_threshold, 2),
            "slow_request_count": len(slow_requests),
            "slow_traces": [r.get("trace_id") for r in slow_requests],
        },
        "resource_usage": {
            "max_memory_mb": max([float(r.get("memory_mb", 0)) for r in completed] or [0.0]),
            "max_cpu_percent": max([float(r.get("cpu_percent", 0)) for r in completed] or [0.0]),
        },
    }
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def write_markdown_report(summary: Dict[str, Any], path: Path | None = None) -> Path:
    path = path or (METRICS_DIR / "analisis_logs.md")
    lines = [
        "# Análisis de logs y métricas EP3",
        "",
        f"- Solicitudes registradas: {summary['total_requests']}",
        f"- Solicitudes completadas: {summary['completed_requests']}",
        f"- Tasa de error: {summary['error_rate']}",
        f"- Latencia promedio: {summary['latency_ms']['mean']} ms",
        f"- Latencia p95: {summary['latency_ms']['p95']} ms",
        f"- Memoria máxima observada: {summary['resource_usage']['max_memory_mb']} MB",
        f"- CPU máximo observado: {summary['resource_usage']['max_cpu_percent']} %",
        f"- Trazas lentas detectadas: {summary.get('anomalies', {}).get('slow_request_count', 0)}",
        "",
        "## Hallazgos",
        "",
        "- La trazabilidad permite reconstruir cada solicitud por `trace_id`.",
        "- Las métricas de latencia permiten detectar cuellos de botella por span.",
        "- El uso de herramientas permite identificar qué componente concentra más trabajo.",
        "- Las métricas de recursos entregan una referencia básica de CPU y memoria.",
        "",
        "## Mejoras propuestas",
        "",
        "1. Mantener trazabilidad por `trace_id` en cada consulta.",
        "2. Agregar caché para consultas repetidas de RAG.",
        "3. Definir umbrales de alerta para latencia, errores y consumo de recursos.",
        "4. Revisar manualmente respuestas médicas sensibles.",
        "5. Aumentar el set de preguntas evaluadas para medir calidad con mayor cobertura.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
