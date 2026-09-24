import os

# Sensible defaults for LLM interactions
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_TOKENS = 500
MAX_RETRIES = 3

ROLE_MODEL_MAP = {
    "default": "gpt-4o-mini",
    "planner": "gpt-4o-mini",
    "writer": "gpt-4o-mini",
    "critic": "gpt-4o-mini",
}

def get_model_for_role(role: str) -> str:
    return ROLE_MODEL_MAP.get(role, ROLE_MODEL_MAP["default"])
