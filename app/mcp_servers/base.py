from pydantic import BaseModel
from typing import Any, Dict, Optional

class ToolRequest(BaseModel):
    tool_name: str
    input_payload: Dict[str, Any]

class ToolResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
