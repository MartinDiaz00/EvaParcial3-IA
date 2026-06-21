"""
Cliente LLM unificado compatible con la API de OpenAI.
Funciona con GitHub Models (gratuito), OpenAI, Groq u otros proveedores compatibles.
"""
from __future__ import annotations
import json
from typing import List, Dict, Optional
import urllib.request
import urllib.error

from .config import settings


def call_llm(
    messages: List[Dict[str, str]],
    system_prompt: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 800,
) -> str:
    """
    Llama al LLM configurado y retorna la respuesta como string.
    Si no hay API key configurada, lanza ValueError con instrucciones.
    """
    if not settings.api_key:
        raise ValueError(
            "No se encontró GITHUB_TOKEN ni OPENAI_API_KEY. "
            "Agrega tu token en el archivo .env para usar el LLM real."
        )

    all_messages = []
    if system_prompt:
        all_messages.append({"role": "system", "content": system_prompt})
    all_messages.extend(messages)

    payload = json.dumps({
        "model": settings.model_name,
        "messages": all_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    req = urllib.request.Request(
        url=f"{settings.api_base}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Error HTTP {e.code} del LLM: {body}") from e
