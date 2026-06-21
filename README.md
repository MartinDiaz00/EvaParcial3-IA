# HealthTech EP3 - Observabilidad de Agente IA

Proyecto para la Evaluación Parcial 3 de Ingeniería de Soluciones con IA. Esta versión está enfocada solo en observabilidad: métricas, logs, trazabilidad, dashboard, seguridad y recomendaciones de mejora.

## Qué incluye

- Agente HealthTech con RAG local y conexión opcional a GitHub Models.
- Logs estructurados en JSONL con `trace_id`, `span_id`, eventos y duración.
- Métricas de latencia, tasa de error, relevancia, consistencia, CPU y memoria.
- Detección básica de anomalías por latencia.
- Dashboard en Streamlit para revisar el comportamiento del agente.
- Audit trail con hash de entrada y decisión tomada.
- Informe EP3 y matriz de cumplimiento.

## Instalación

```bash
pip install -r requirements.txt
```

## Configurar token

Copia el archivo `.env.example` como `.env` y pega tu token:

```env
GITHUB_TOKEN=PEGAR_TOKEN_AQUI
GITHUB_BASE_URL=https://models.inference.ai.azure.com
MODEL_NAME=gpt-4o-mini
USE_EXTERNAL_LLM=true
TOP_K=3
```

El archivo `.env` no se sube al repositorio.

## Generar métricas y evidencias

```bash
python -m scripts.evaluate_observability
```

Esto genera:

- `outputs/logs/agent_events.jsonl`
- `outputs/logs/audit_trail.jsonl`
- `outputs/metrics/metrics_summary.json`
- `outputs/metrics/evaluation_results.json`
- `outputs/metrics/analisis_logs.md`

## Abrir dashboard

```bash
python -m streamlit run dashboard.py
```

Luego abrir la URL local que indique la consola.

## Ejecutar pruebas

```bash
python -m pytest -q
```

## Estructura

```text
app/                 Código del agente, métricas, seguridad y observabilidad
data/                Documentos internos usados por el RAG
scripts/             Scripts de evaluación y demo
docs/                Informe EP3 y matriz de cumplimiento
diagrams/            Diagramas de arquitectura y flujo
dashboard.py         Dashboard Streamlit
outputs/             Evidencias generadas al ejecutar el sistema
```

## Nota de uso responsable

El agente no reemplaza criterio médico profesional. Las respuestas generadas deben considerarse apoyo informativo y las consultas clínicas sensibles requieren revisión humana.
