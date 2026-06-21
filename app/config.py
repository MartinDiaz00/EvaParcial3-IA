from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT_DIR / ".env"
load_dotenv(ENV_FILE)

DATA_DIR = ROOT_DIR / "data"
OUTPUTS_DIR = ROOT_DIR / "outputs"
MEMORY_FILE = OUTPUTS_DIR / "memory_store.json"
LOGS_DIR = OUTPUTS_DIR / "logs"
METRICS_DIR = OUTPUTS_DIR / "metrics"
REPORTS_DIR = OUTPUTS_DIR / "reports"

@dataclass
class Settings:
    app_name: str = "HealthTech EP3 Observabilidad"
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    api_key: str = os.getenv("GITHUB_TOKEN", os.getenv("OPENAI_API_KEY", ""))
    api_base: str = os.getenv("GITHUB_BASE_URL", os.getenv("API_BASE", "https://models.inference.ai.azure.com"))
    use_external_llm: bool = os.getenv("USE_EXTERNAL_LLM", "true").lower() == "true"
    top_k: int = int(os.getenv("TOP_K", "3"))

settings = Settings()
OUTPUTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
