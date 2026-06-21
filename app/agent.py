"""
Agente principal HealthTech con planificación real y LLM.

Arquitectura Plan-and-Execute:
1. El Planner llama al LLM para generar un plan dinámico según la consulta.
2. El agente ejecuta SOLO las herramientas indicadas en el plan, en orden.
3. El LLM genera la respuesta final con todo el contexto acumulado.

Esto garantiza que el plan realmente condicione la ejecución (IE5, IE6).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List
import time

from .memory_store import MemoryStore
from .planner import Planner, PlanStep
from .tools import rag_search_tool, memory_context_tool, writing_tool, reasoning_tool, evaluate_evidence
from .prompts import SYSTEM_PROMPT, ANSWER_TEMPLATE
from .observability import new_trace, span, log_event, audit_decision
from .security import safety_check

# Mapa de acciones → herramientas
ACTION_MAP = {
    'revisar_memoria': memory_context_tool,
    'consultar_rag': rag_search_tool,
    'escribir_reporte': writing_tool,
    'razonar': reasoning_tool,
}


@dataclass
class AgentResult:
    question: str
    plan: str
    context: str
    memory: str
    reasoning: str
    answer: str
    trace: str
    tools_used: List[str] = field(default_factory=list)


class HealthTechAgent:
    """
    Agente funcional HealthTech con:
    - Planificación dinámica via LLM (Plan-and-Execute)
    - Herramientas autónomas: RAG semántico, memoria, razonamiento, escritura
    - Generación de respuesta final via LLM con contexto completo
    - Trazabilidad completa de decisiones
    """

    def __init__(self):
        self.memory = MemoryStore()
        self.planner = Planner()

    def run(self, question: str, user_id: str = "demo_user") -> AgentResult:
        trace_context = new_trace(user_id=user_id)
        safety = safety_check(question)
        safe_question = safety.sanitized_input
        request_start = time.perf_counter()
        log_event(trace_context, "full_request", "start", input_length=len(question), safety_warning=safety.warning)
        if not safety.allowed:
            answer = "Solicitud bloqueada por seguridad: posible prompt injection o instrucción insegura."
            audit_decision(trace_context, question, "blocked", [safety.warning], 0.95, True)
            log_event(trace_context, "full_request", "end", duration_ms=(time.perf_counter()-request_start)*1000, success=False, blocked=True)
            return AgentResult(question=question, plan="Bloqueado por protocolo de seguridad", context="", memory="", reasoning=safety.warning, answer=answer, trace=safety.warning, tools_used=["safety_check"])

        # 1. Registrar interacción en memoria de corto plazo
        self.memory.add_interaction('usuario', safe_question)

        # 2. Generar plan dinámico con el LLM
        with span(trace_context, "planner"):
            plan_steps = self.planner.create_plan(safe_question, use_llm=True)
        plan_text = self.planner.render(plan_steps)

        # 3. Ejecutar herramientas según el plan (plan condiciona ejecución)
        memory_text = ''
        context_text = ''
        reasoning_text = ''
        report_text = ''
        tools_used: List[str] = []

        for step in plan_steps:
            action = step.action

            if action == 'revisar_memoria':
                with span(trace_context, "tool_memory_context"):
                    memory_text = self._invoke(memory_context_tool, '')
                tools_used.append('memory_context_tool')

            elif action == 'consultar_rag':
                with span(trace_context, "tool_rag_search"):
                    context_text = self._invoke(rag_search_tool, safe_question)
                tools_used.append('rag_search_tool')

            elif action == 'razonar':
                reasoning_input = (
                    f"Consulta: {safe_question}\n\n"
                    f"Contexto documental:\n{context_text or 'No recuperado aún.'}\n\n"
                    f"Memoria conversacional:\n{memory_text or 'No recuperada aún.'}"
                )
                with span(trace_context, "tool_reasoning"):
                    reasoning_text = self._invoke(reasoning_tool, reasoning_input)
                tools_used.append('reasoning_tool')

            elif action == 'escribir_reporte':
                report_input = (
                    f"Consulta: {safe_question}\nContexto: {context_text}\n"
                    f"Análisis: {reasoning_text}"
                )
                with span(trace_context, "tool_writing"):
                    report_text = self._invoke(writing_tool, report_input)
                tools_used.append('writing_tool')

            elif action == 'solicitar_aclaracion':
                context_text = 'El agente detectó que la consulta requiere información adicional del usuario.'
                tools_used.append('solicitar_aclaracion')

        # 4. Evaluar calidad de evidencia recuperada
        evidence_status = evaluate_evidence(context_text)

        # 5. Generar respuesta final con LLM usando TODO el contexto acumulado
        answer = self._generate_final_answer(
            safe_question, context_text, memory_text, reasoning_text,
            report_text, evidence_status
        )

        # 6. Persistir respuesta y hechos relevantes en memoria
        self.memory.add_interaction('agente', answer)
        self._extract_and_remember(safe_question)

        # 7. Construir traza de decisiones
        confidence = 0.75 if "insuficiente" not in evidence_status.lower() else 0.45
        audit_decision(trace_context, safe_question, "answer_generated", [evidence_status, f"tools={tools_used}"], confidence, safety.human_review_required)
        log_event(trace_context, "full_request", "end", duration_ms=(time.perf_counter()-request_start)*1000, success=True, tools_used=tools_used, evidence_status=evidence_status)

        trace = (
            f"trace_id: {trace_context.trace_id}\n"
            f"Herramientas ejecutadas (según plan): {', '.join(tools_used)}\n"
            f"Estado de evidencia: {evidence_status}\n"
            f"Pasos del plan: {len(plan_steps)}\n"
            "Decisión: respuesta generada por LLM con contexto documental y memoria conversacional."
        )

        return AgentResult(
            question=question,
            plan=plan_text,
            context=context_text,
            memory=memory_text,
            reasoning=reasoning_text,
            answer=answer,
            trace=trace,
            tools_used=tools_used,
        )

    def _invoke(self, tool_fn, input_str: str) -> str:
        """Invoca una herramienta de forma segura."""
        try:
            if hasattr(tool_fn, 'invoke'):
                return tool_fn.invoke(input_str)
            return tool_fn(input_str)
        except Exception as e:
            return f'[Error en herramienta {getattr(tool_fn, "name", str(tool_fn))}: {e}]'

    def _generate_final_answer(
        self,
        question: str,
        context: str,
        memory: str,
        reasoning: str,
        report: str,
        evidence_status: str,
    ) -> str:
        """Genera la respuesta final usando el LLM con todo el contexto acumulado."""
        try:
            from .llm_client import call_llm
            user_content = (
                f"Consulta del usuario: {question}\n\n"
                f"Contexto documental recuperado:\n{context}\n\n"
                f"Memoria conversacional:\n{memory}\n\n"
                f"Análisis de razonamiento:\n{reasoning}\n\n"
                f"Estado de evidencia: {evidence_status}\n"
            )
            if report:
                user_content += f"\nReporte generado:\n{report}\n"
            user_content += (
                "\nGenera una respuesta final clara, técnica y útil para el equipo de HealthTech. "
                "Cita las fuentes documentales cuando uses información de ellas. "
                "Si la evidencia es insuficiente, indícalo explícitamente."
            )
            return call_llm(
                messages=[{"role": "user", "content": user_content}],
                system_prompt=SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=700,
            )
        except Exception as e:
            # Fallback si el LLM no está disponible
            if 'No se encontró evidencia' in context:
                return (
                    f'[Modo sin LLM — {e}]\n'
                    'No se encontró evidencia documental suficiente. '
                    'Se recomienda ampliar la base de conocimiento antes de usar esta respuesta.'
                )
            return (
                f'[Modo sin LLM — {e}]\n'
                f'Basado en los documentos internos de HealthTech: {evidence_status} '
                'La respuesta completa requiere conexión al LLM. '
                'Configura GITHUB_TOKEN en el archivo .env para habilitar respuestas generadas por IA.'
            )

    def _extract_and_remember(self, question: str) -> None:
        """Persiste hechos relevantes en memoria de largo plazo."""
        q = question.lower()
        if any(w in q for w in ['prefiero', 'recordar', 'siempre', 'mi nombre', 'soy']):
            self.memory.remember_fact('preferencia_usuario', question)
        if any(w in q for w in ['urgente', 'crítico', 'critico', 'prioridad alta']):
            self.memory.remember_fact('ultima_tarea_urgente', question)

    def formatted_response(self, question: str) -> str:
        result = self.run(question)
        return ANSWER_TEMPLATE.format(
            question=result.question,
            plan=result.plan,
            context=result.context,
            memory=result.memory,
            reasoning=result.reasoning if result.reasoning else '(No se ejecutó paso de razonamiento)',
            answer=result.answer,
            trace=result.trace,
        )
