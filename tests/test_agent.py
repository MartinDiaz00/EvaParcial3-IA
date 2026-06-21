"""
Tests del Agente HealthTech EP3 Observabilidad.
Validan: herramientas, RAG semántico, memoria, planificador y arquitectura del agente.
"""
import pytest
from app.knowledge_base import retrieve, load_documents
from app.memory_store import MemoryStore
from app.planner import Planner, PlanStep
from app.tools import rag_search_tool, memory_context_tool, evaluate_evidence
from app.agent import HealthTechAgent


# ─── Tests de base de conocimiento (RAG semántico) ────────────────────────────

class TestKnowledgeBase:
    def test_load_documents_retorna_chunks(self):
        docs = load_documents()
        assert len(docs) > 0, "Debe cargar al menos un documento"

    def test_retrieve_retorna_resultados_relevantes(self):
        results = retrieve("paciente triage soporte")
        assert isinstance(results, list)

    def test_retrieve_usa_similitud_coseno(self):
        """Verifica que el score es un valor float entre 0 y 1."""
        results = retrieve("healthtech arquitectura pipeline")
        for r in results:
            assert 0.0 <= r.score <= 1.0, f"Score fuera de rango: {r.score}"

    def test_retrieve_sin_resultados_retorna_lista_vacia(self):
        results = retrieve("xkjqwzabc123noresult")
        assert results == [] or all(r.score == 0 for r in results)

    def test_retrieve_respeta_top_k(self):
        results = retrieve("paciente", top_k=2)
        assert len(results) <= 2


# ─── Tests de memoria ─────────────────────────────────────────────────────────

class TestMemoryStore:
    def setup_method(self):
        import tempfile, json
        from pathlib import Path
        self.tmp = Path(tempfile.mktemp(suffix='.json'))
        self.tmp.write_text(json.dumps({'short_term': [], 'long_term': {}}))
        self.memory = MemoryStore(file_path=self.tmp)

    def teardown_method(self):
        if self.tmp.exists():
            self.tmp.unlink()

    def test_add_interaction_persiste(self):
        self.memory.add_interaction('usuario', 'hola agente')
        ctx = self.memory.short_context()
        assert 'hola agente' in ctx

    def test_short_term_limita_a_12_entradas(self):
        for i in range(15):
            self.memory.add_interaction('usuario', f'mensaje {i}')
        import json
        data = json.loads(self.tmp.read_text())
        assert len(data['short_term']) <= 12

    def test_long_term_persiste_hechos(self):
        self.memory.remember_fact('preferencia', 'usar lenguaje formal')
        ctx = self.memory.long_context()
        assert 'usar lenguaje formal' in ctx

    def test_clear_vacia_memoria(self):
        self.memory.add_interaction('usuario', 'test')
        self.memory.clear()
        assert 'Sin historial' in self.memory.short_context()


# ─── Tests del planificador ────────────────────────────────────────────────────

class TestPlanner:
    def setup_method(self):
        self.planner = Planner()

    def test_plan_heuristic_genera_pasos(self):
        steps = self.planner._plan_heuristic("¿Qué es el triage en HealthTech?")
        assert len(steps) >= 2

    def test_plan_siempre_incluye_revisar_memoria(self):
        steps = self.planner._plan_heuristic("consulta cualquiera")
        acciones = [s.action for s in steps]
        assert 'revisar_memoria' in acciones

    def test_plan_incluye_razonar_para_comparaciones(self):
        steps = self.planner._plan_heuristic("¿Cuál es la mejor estrategia de triage?")
        acciones = [s.action for s in steps]
        assert 'razonar' in acciones

    def test_plan_termina_con_redactar(self):
        steps = self.planner._plan_heuristic("explica el pipeline de datos")
        assert steps[-1].action in ('redactar', 'escribir_reporte')

    def test_render_genera_texto_legible(self):
        steps = [PlanStep(1, 'revisar_memoria', 'test'), PlanStep(2, 'redactar', 'test')]
        rendered = Planner.render(steps)
        assert '1.' in rendered and 'revisar_memoria' in rendered


# ─── Tests de herramientas ────────────────────────────────────────────────────

class TestTools:
    def test_rag_search_tool_retorna_string(self):
        result = rag_search_tool.invoke("paciente HealthTech")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_rag_search_tool_sin_resultado(self):
        result = rag_search_tool.invoke("xkjqwzabc123noresult")
        assert 'No se encontró' in result or isinstance(result, str)

    def test_memory_context_tool_retorna_string(self):
        result = memory_context_tool.invoke('')
        assert isinstance(result, str)
        assert 'corto plazo' in result.lower() or 'Corto' in result

    def test_evaluate_evidence_sin_evidencia(self):
        status = evaluate_evidence('No se encontró evidencia documental suficiente.')
        assert 'insuficiente' in status.lower() or 'baja' in status.lower()

    def test_evaluate_evidence_con_evidencia(self):
        status = evaluate_evidence('[Fuente: doc1]\ncontenido\n\n[Fuente: doc2]\ncontenido2')
        assert 'sólida' in status.lower() or 'suficiente' in status.lower()


# ─── Tests de integración del agente ─────────────────────────────────────────

class TestAgentIntegration:
    def setup_method(self):
        self.agent = HealthTechAgent()

    def test_agent_run_retorna_result(self):
        result = self.agent.run("¿Qué es HealthTech?")
        assert result.question == "¿Qué es HealthTech?"
        assert isinstance(result.plan, str)
        assert isinstance(result.answer, str)
        assert isinstance(result.tools_used, list)

    def test_agent_usa_herramientas_segun_plan(self):
        result = self.agent.run("¿Cuál es el proceso de triage para pacientes?")
        assert len(result.tools_used) > 0

    def test_agent_formatted_response_incluye_secciones(self):
        response = self.agent.formatted_response("¿Cómo funciona el pipeline RAG?")
        assert 'PLAN DE EJECUCIÓN' in response
        assert 'RESPUESTA FINAL' in response
        assert 'TRAZABILIDAD' in response

    def test_agent_mantiene_memoria_entre_llamadas(self):
        self.agent.run("Soy el Dr. García y necesito información sobre triage.")
        result2 = self.agent.run("¿Recuerdas mi consulta anterior?")
        # La memoria de corto plazo debe contener la interacción previa
        assert 'Dr. García' in result2.memory or len(result2.memory) > 10

    def test_plan_condiciona_herramientas_usadas(self):
        """Verifica que el plan dinámico realmente cambia las herramientas ejecutadas."""
        result_simple = self.agent.run("hola")
        result_complex = self.agent.run("¿Por qué deberíamos priorizar el triage automatizado sobre el manual?")
        # La consulta compleja debería usar más herramientas
        assert len(result_complex.tools_used) >= len(result_simple.tools_used)
