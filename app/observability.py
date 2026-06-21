"""Observabilidad para el agente HealthTech: logs JSON, trazas y métricas.

Incluye trace_id/span_id por petición, medición de latencia, CPU/RAM,
frecuencia de errores, uso de herramientas y audit trail básico.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from .config import LOGS_DIR, METRICS_DIR

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None

LOG_FILE = LOGS_DIR / "agent_events.jsonl"
AUDIT_FILE = LOGS_DIR / "audit_trail.jsonl"
SUMMARY_FILE = METRICS_DIR / "metrics_summary.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _safe_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def get_resource_usage() -> Dict[str, float]:
    """Retorna CPU y RAM del proceso. Si psutil no está instalado usa valores seguros."""
    if psutil is None:
        return {"cpu_percent": 0.0, "memory_mb": 0.0}
    process = psutil.Process(os.getpid())
    return {
        "cpu_percent": float(process.cpu_percent(interval=None)),
        "memory_mb": round(process.memory_info().rss / (1024 * 1024), 2),
    }


@dataclass
class TraceContext:
    trace_id: str
    user_id: str = "demo_user"
    agent_version: str = "ep3-observability-v1"


def new_trace(user_id: str = "demo_user") -> TraceContext:
    return TraceContext(trace_id=str(uuid.uuid4()), user_id=user_id)


def log_event(
    context: TraceContext,
    span: str,
    event: str,
    level: str = "INFO",
    duration_ms: Optional[float] = None,
    **metadata: Any,
) -> None:
    payload: Dict[str, Any] = {
        "timestamp": utc_now(),
        "level": level,
        "trace_id": context.trace_id,
        "span_id": str(uuid.uuid4())[:8],
        "span": span,
        "event": event,
        "user_id": context.user_id,
        "agent_version": context.agent_version,
    }
    if duration_ms is not None:
        payload["duration_ms"] = round(duration_ms, 2)
    payload.update(metadata)
    _append_jsonl(LOG_FILE, payload)


@contextlib.contextmanager
def span(context: TraceContext, name: str, **metadata: Any) -> Iterator[None]:
    start = time.perf_counter()
    log_event(context, name, "start", **metadata)
    try:
        yield
        duration = (time.perf_counter() - start) * 1000
        resources = get_resource_usage()
        log_event(context, name, "end", duration_ms=duration, status="ok", **resources)
    except Exception as exc:
        duration = (time.perf_counter() - start) * 1000
        log_event(
            context,
            name,
            "error",
            level="ERROR",
            duration_ms=duration,
            status="failed",
            error_type=type(exc).__name__,
            error_message=str(exc)[:300],
        )
        raise


def audit_decision(
    context: TraceContext,
    user_input: str,
    decision: str,
    factors: list[str],
    confidence_score: float,
    human_review_required: bool,
) -> None:
    record = {
        "record_id": str(uuid.uuid4()),
        "trace_id": context.trace_id,
        "timestamp": utc_now(),
        "agent_version": context.agent_version,
        "user_id": context.user_id,
        "input_hash": _safe_hash(user_input),
        "decision": decision,
        "decision_factors": factors,
        "confidence_score": round(confidence_score, 3),
        "human_review_required": human_review_required,
        "regulation_context": "Ley 21.719 / GDPR / AI Act como referencia académica",
    }
    checksum = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()[:16]
    record["checksum"] = checksum
    _append_jsonl(AUDIT_FILE, record)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows
