"""Protocolos básicos de seguridad y uso responsable para HealthTech."""
from __future__ import annotations
import re
from dataclasses import dataclass

SENSITIVE_PATTERNS = [
    r"\b\d{1,2}\.\d{3}\.\d{3}-[0-9kK]\b",  # RUT con puntos
    r"\b\d{7,8}-[0-9kK]\b",                  # RUT simple
    r"[\w\.-]+@[\w\.-]+\.\w+",              # email
    r"\+?56\s?9\s?\d{4}\s?\d{4}",         # teléfono Chile
]

INJECTION_TERMS = [
    "ignora instrucciones", "ignore previous", "system prompt", "revela tu prompt",
    "olvida las reglas", "actua como doctor", "diagnostica definitivamente",
]

@dataclass
class SafetyResult:
    allowed: bool
    sanitized_input: str
    warning: str
    human_review_required: bool = False


def sanitize_input(text: str) -> str:
    clean = text
    for pattern in SENSITIVE_PATTERNS:
        clean = re.sub(pattern, "[DATO_SENSIBLE]", clean, flags=re.IGNORECASE)
    return clean


def safety_check(text: str) -> SafetyResult:
    lower = text.lower()
    sanitized = sanitize_input(text)
    if any(term in lower for term in INJECTION_TERMS):
        return SafetyResult(
            allowed=False,
            sanitized_input=sanitized,
            warning="Se detectó posible prompt injection o solicitud insegura.",
            human_review_required=True,
        )
    medical_risk = any(w in lower for w in ["diagnóstico", "diagnostico", "medicamento", "dosis", "urgencia", "dolor pecho"])
    return SafetyResult(
        allowed=True,
        sanitized_input=sanitized,
        warning="Consulta permitida. No reemplaza criterio médico profesional.",
        human_review_required=medical_risk,
    )
