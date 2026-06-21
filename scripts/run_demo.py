"""
Demo interactivo del Agente HealthTech EP3 Observabilidad.
Demuestra planificación dinámica, RAG semántico y toma de decisiones adaptativas.
"""
import sys
import os
from pathlib import Path

# Asegurar que el módulo app esté en el path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

from app.agent import HealthTechAgent

DEMO_QUERIES = [
    # IE6: Ejemplos que demuestran adaptación a distintas condiciones
    ("Consulta simple",
     "¿Qué es HealthTech y qué servicios ofrece?"),

    ("Consulta con razonamiento",
     "¿Por qué debería priorizar el triage automatizado sobre el proceso manual?"),

    ("Consulta de memoria",
     "¿Recuerdas las consultas que hice anteriormente en esta sesión?"),

    ("Consulta con escritura formal",
     "Genera un reporte ejecutivo sobre el proceso de soporte a pacientes en HealthTech."),

    ("Consulta sin evidencia (adaptación ante falta de datos)",
     "¿Cuál es el protocolo de emergencia para eventos sísmicos en las instalaciones?"),
]


def main():
    print("=" * 70)
    print("  DEMO - AGENTE HEALTHTECH EP3 OBSERVABILIDAD")
    print("  Arquitectura: Plan-and-Execute + RAG Semántico + LLM")
    print("=" * 70)

    agent = HealthTechAgent()

    for scenario_name, query in DEMO_QUERIES:
        print(f"\n{'─'*70}")
        print(f"📌 ESCENARIO: {scenario_name}")
        print(f"{'─'*70}")
        print(agent.formatted_response(query))
        input("\n[Presiona Enter para continuar al siguiente escenario...]\n")

    print("\n" + "=" * 70)
    print("✅ Demo completado. El agente demostró:")
    print("   • Planificación dinámica: el plan cambia según la consulta")
    print("   • RAG semántico: recuperación con TF-IDF + similitud coseno")
    print("   • Memoria dual: corto plazo (sesión) y largo plazo (persistente)")
    print("   • Razonamiento: análisis multi-paso con LLM")
    print("   • Adaptación: comportamiento distinto ante evidencia suficiente/insuficiente")
    print("=" * 70)


if __name__ == '__main__':
    main()
