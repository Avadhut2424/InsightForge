from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(title="InsightForge AI API")

@app.get("/health", summary="Health Check")
async def health_check():
    return {"status": "ok", "env": settings.app_env}
