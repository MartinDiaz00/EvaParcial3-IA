"""
Herramientas del agente HealthTech.
Cada herramienta es autónoma y puede ser invocada por el agente según el plan.
Integradas con LangChain Core para cumplir IL2.1 e IE1/IE2.
"""
from __future__ import annotations
from typing import List

from .knowledge_base import retrieve, DocumentChunk
from .memory_store import MemoryStore

try:
    from langchain_core.tools import tool
except ImportError:
    def tool(func=None, **kwargs):
        def decorator(f):
            f.name = f.__name__
            f.invoke = lambda value='': f(value)
            return f
        return decorator(func) if func else decorator


@tool
def rag_search_tool(query: str) -> str:
    """
    Busca evidencia relevante en los documentos internos de HealthTech
    usando recuperación semántica TF-IDF con similitud coseno.
    Retorna los fragmentos más relevantes con su fuente y puntuación.
    """
    results: List[DocumentChunk] = retrieve(query)
    if not results:
        return 'No se encontró evidencia documental suficiente para esta consulta.'
    lines = []
    for item in results:
        preview = item.content.replace('\n', ' ')[:500]
        lines.append(f'[Fuente: {item.source} | Sección: {item.title} | Relevancia: {item.score}]\n{preview}')
    return '\n\n'.join(lines)


@tool
def memory_context_tool(_: str = '') -> str:
    """
    Recupera el contexto conversacional del agente:
    - Memoria de corto plazo: últimas interacciones de la sesión.
    - Memoria de largo plazo: hechos y preferencias persistentes entre sesiones.
    """
    memory = MemoryStore()
    short = memory.short_context()
    long_ = memory.long_context()
    return f'[Memoria de corto plazo]\n{short}\n\n[Memoria de largo plazo]\n{long_}'


@tool
def writing_tool(content: str) -> str:
    """
    Genera un reporte ejecutivo estructurado a partir de contenido técnico.
    Usa el LLM para transformar información técnica en lenguaje organizacional claro.
    """
    try:
        from .llm_client import call_llm
        return call_llm(
            messages=[{"role": "user", "content": f"Redacta un reporte ejecutivo claro y profesional basado en:\n\n{content}"}],
            system_prompt="Eres un redactor técnico especializado en salud digital. Redacta reportes ejecutivos claros y concisos.",
            temperature=0.4,
            max_tokens=600,
        )
    except Exception as e:
        return f'Reporte generado (modo sin LLM):\n{content}\n[Nota: {e}]'


@tool
def reasoning_tool(inputs: str) -> str:
    """
    Herramienta de razonamiento: analiza coherencia entre consulta, contexto y memoria,
    y toma decisiones sobre cómo responder. Usa el LLM para razonamiento multi-paso.
    """
    try:
        from .llm_client import call_llm
        return call_llm(
            messages=[{"role": "user", "content": inputs}],
            system_prompt=(
                "Eres un agente analítico de HealthTech. Tu tarea es razonar sobre la coherencia "
                "entre la consulta del usuario, el contexto recuperado y la memoria conversacional. "
                "Identifica brechas, contradicciones o información faltante. "
                "Sé preciso y técnico."
            ),
            temperature=0.2,
            max_tokens=500,
        )
    except Exception as e:
        return f'Análisis de coherencia (modo sin LLM): Se requiere validación humana. [{e}]'


def evaluate_evidence(context: str) -> str:
    """Evalúa la calidad de la evidencia recuperada."""
    if 'No se encontró evidencia' in context:
        return 'Evidencia insuficiente: se recomienda ampliar la base documental.'
    chunk_count = context.count('[Fuente:')
    if chunk_count >= 2:
        return f'Evidencia sólida: {chunk_count} fragmentos documentales recuperados con alta relevancia.'
    return 'Evidencia parcial: se encontró contexto pero puede requerir validación adicional.'
