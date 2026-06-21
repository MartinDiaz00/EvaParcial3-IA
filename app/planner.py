"""
Planificador tipo Plan-and-Execute con LLM real.
El LLM clasifica la consulta y genera un plan dinámico.
La ejecución del agente respeta el plan generado.
"""
from __future__ import annotations
import json
import re
from dataclasses import dataclass
from typing import List

from .prompts import PLANNER_PROMPT

@dataclass
class PlanStep:
    order: int
    action: str
    reason: str


VALID_ACTIONS = {
    'revisar_memoria',
    'consultar_rag',
    'razonar',
    'redactar',
    'solicitar_aclaracion',
    'escribir_reporte',
}

# Plan por defecto si el LLM no está disponible
DEFAULT_PLAN = [
    PlanStep(1, 'revisar_memoria', 'Recuperar contexto conversacional previo.'),
    PlanStep(2, 'consultar_rag', 'Buscar información relevante en documentos internos.'),
    PlanStep(3, 'razonar', 'Analizar coherencia entre la consulta, memoria y documentos.'),
    PlanStep(4, 'redactar', 'Generar respuesta final trazable.'),
]


class Planner:
    """
    Planificador inteligente que usa el LLM para generar planes dinámicos.
    Si el LLM no está disponible, usa heurísticas como fallback.
    """

    def create_plan(self, question: str, use_llm: bool = True) -> List[PlanStep]:
        if use_llm:
            try:
                return self._plan_with_llm(question)
            except Exception:
                pass
        return self._plan_heuristic(question)

    def _plan_with_llm(self, question: str) -> List[PlanStep]:
        from .llm_client import call_llm
        prompt = (
            f"Consulta del usuario: {question}\n\n"
            "Genera un plan de ejecución en formato JSON. "
            "Usa SOLO estas acciones: revisar_memoria, consultar_rag, razonar, redactar, solicitar_aclaracion, escribir_reporte. "
            "Formato esperado (array JSON, sin markdown):\n"
            '[{"order":1,"action":"revisar_memoria","reason":"..."},...]\n'
            "Incluye solo los pasos necesarios, entre 2 y 5 pasos."
        )
        raw = call_llm(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=PLANNER_PROMPT,
            temperature=0.1,
            max_tokens=400,
        )
        # Limpiar posibles bloques markdown
        raw = re.sub(r'```(?:json)?', '', raw).strip().strip('`')
        steps_data = json.loads(raw)
        steps = []
        for i, s in enumerate(steps_data):
            action = s.get('action', 'razonar')
            if action not in VALID_ACTIONS:
                action = 'razonar'
            steps.append(PlanStep(
                order=s.get('order', i + 1),
                action=action,
                reason=s.get('reason', ''),
            ))
        return steps if steps else DEFAULT_PLAN

    def _plan_heuristic(self, question: str) -> List[PlanStep]:
        """Fallback heurístico cuando el LLM no está disponible."""
        q = question.lower()
        steps: List[PlanStep] = [
            PlanStep(1, 'revisar_memoria', 'Mantener continuidad del flujo conversacional.')
        ]
        if any(w in q for w in ['healthtech', 'documento', 'paciente', 'cita', 'triage',
                                  'soporte', 'arquitectura', 'pipeline', 'clínico', 'clinico']):
            steps.append(PlanStep(2, 'consultar_rag', 'La consulta requiere información documental interna.'))
        else:
            steps.append(PlanStep(2, 'consultar_rag', 'Validar si existe información interna relacionada.'))

        if any(w in q for w in ['compara', 'decide', 'recomienda', 'prioriza', 'riesgo', 'mejor', 'por qué']):
            steps.append(PlanStep(3, 'razonar', 'La consulta requiere evaluación de alternativas.'))

        if any(w in q for w in ['informe', 'reporte', 'resumen ejecutivo', 'documento']):
            steps.append(PlanStep(len(steps) + 1, 'escribir_reporte', 'Generar documento de salida estructurado.'))

        steps.append(PlanStep(len(steps) + 1, 'redactar', 'Construir respuesta final con trazabilidad.'))
        return steps

    @staticmethod
    def render(plan: List[PlanStep]) -> str:
        return '\n'.join([f'{s.order}. [{s.action}] {s.reason}' for s in plan])
