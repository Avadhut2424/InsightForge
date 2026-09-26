from typing import Dict, Any, Callable
from .web_search import web_search
from .calculator import calculate
from .db_lookup import similarity_search

class ToolRegistry:
    def __init__(self):
        self.tools = {}
        
    def register(self, name: str, description: str, schema: Dict[str, Any], func: Callable):
        self.tools[name] = {
            "description": description,
            "schema": schema,
            "func": func
        }
        
    def list_tools(self) -> Dict[str, Any]:
        return {
            name: {
                "description": info["description"],
                "schema": info["schema"]
            } for name, info in self.tools.items()
        }
        
    async def call_tool(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if name not in self.tools:
            return {"success": False, "error": {"type": "unknown_tool", "detail": f"Tool '{name}' not found"}}
            
        tool_info = self.tools[name]
        schema = tool_info["schema"]
        
        # Explicit input validation
        if "required" in schema:
            for req_field in schema["required"]:
                if req_field not in payload:
                    return {"success": False, "error": {"type": "validation_error", "detail": f"Missing required field: '{req_field}'"}}
                    
        func = tool_info["func"]
        try:
            import inspect
            if inspect.iscoroutinefunction(func):
                return await func(**payload)
            else:
                return func(**payload)
        except TypeError as e:
             return {"success": False, "error": {"type": "invalid_arguments", "detail": str(e)}}
        except Exception as e:
             return {"success": False, "error": {"type": "execution_error", "detail": str(e)}}

registry = ToolRegistry()

registry.register(
    "web_search",
    "Search the web for current information",
    {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer", "default": 5}}, "required": ["query"]},
    web_search
)

registry.register(
    "calculator",
    "Evaluate a mathematical expression safely",
    {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]},
    calculate
)

registry.register(
    "db_lookup",
    "Perform semantic similarity search against the knowledge base",
    {"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer", "default": 5}}, "required": ["query"]},
    similarity_search
)
