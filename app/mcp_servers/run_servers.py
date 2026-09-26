from fastapi import APIRouter
from typing import Any, Dict
from pydantic import BaseModel
from .registry import registry
from .base import ToolResponse

router = APIRouter(prefix="/mcp_tools", tags=["mcp_tools"])

class ToolCallRequest(BaseModel):
    tool_name: str
    input_payload: Dict[str, Any]

@router.get("/list")
def list_tools():
    return registry.list_tools()

@router.post("/call", response_model=ToolResponse)
async def call_tool(request: ToolCallRequest):
    result = await registry.call_tool(request.tool_name, request.input_payload)
    return result
