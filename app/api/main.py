from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.core.config import settings
from app.core.llm.client import call_llm
from app.core.llm.exceptions import LLMError

app = FastAPI(title="InsightForge AI API")

from app.mcp_servers.run_servers import router as mcp_router
app.include_router(mcp_router)

@app.get("/health", summary="Health Check")
async def health_check():
    return {"status": "ok", "env": settings.app_env}

class LLMTestRequest(BaseModel):
    prompt: str
    role: str = "default"

# TEMPORARY: remove once agents exist and call this via orchestration, not directly
@app.post("/internal/test-llm", summary="Test LLM Connectivity")
async def test_llm(request: LLMTestRequest):
    try:
        response = await call_llm(role=request.role, prompt=request.prompt)
        return {
            "text": response.text,
            "model_used": response.model_used,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "latency_ms": response.latency_ms
        }
    except LLMError as e:
        # We explicitly surface custom exceptions to prove failure modes
        raise HTTPException(status_code=500, detail=str(e))
