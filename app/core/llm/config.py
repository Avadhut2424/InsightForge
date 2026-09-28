from app.core.config import settings
import os

# Sensible defaults for LLM interactions
DEFAULT_TIMEOUT_SECONDS = 120.0 # Increased timeout for local LLMs
DEFAULT_MAX_TOKENS = 500
MAX_RETRIES = 3

ROLE_MODEL_MAP = {
    "default": "gpt-4o-mini",
    "planner": "gpt-4o-mini",
    "writer": "gpt-4o-mini",
    "critic": "gpt-4o-mini",
}

def get_model_for_role(role: str) -> str:
    if settings.llm_provider.lower() == "ollama":
        return settings.ollama_model
    return ROLE_MODEL_MAP.get(role, ROLE_MODEL_MAP["default"])
