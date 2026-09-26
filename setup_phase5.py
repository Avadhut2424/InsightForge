import os

# Update .env and .env.example
for env_file in [".env", ".env.example"]:
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            content = f.read()
        if "TAVILY_API_KEY" not in content:
            with open(env_file, "a") as f:
                f.write("\nTAVILY_API_KEY=tvly-placeholder123\n")

# Update requirements.txt
req_path = "requirements.txt"
with open(req_path, "r") as f:
    req_content = f.read()
if "simpleeval" not in req_content:
    with open(req_path, "a") as f:
        f.write("simpleeval\ntavily-python\n")

# Update app/core/config.py
config_path = "app/core/config.py"
with open(config_path, "r") as f:
    config_content = f.read()
if "tavily_api_key" not in config_content:
    config_content = config_content.replace(
        "openai_api_key: str\n",
        "openai_api_key: str\n    tavily_api_key: str | None = None\n"
    )
    with open(config_path, "w") as f:
        f.write(config_content)

# Create mcp_servers directory
os.makedirs("app/mcp_servers", exist_ok=True)
with open("app/mcp_servers/__init__.py", "w") as f:
    f.write("")

# base.py
with open("app/mcp_servers/base.py", "w") as f:
    f.write("""from pydantic import BaseModel
from typing import Any, Dict, Optional

class ToolRequest(BaseModel):
    tool_name: str
    input_payload: Dict[str, Any]

class ToolResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
""")

# web_search.py
with open("app/mcp_servers/web_search.py", "w") as f:
    f.write("""import httpx
from typing import Dict, Any
from app.core.config import settings

async def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    api_key = settings.tavily_api_key
    if not api_key or api_key == "tvly-placeholder123":
        # We will mock the response if it's the placeholder key just for standalone test
        # Actually no, let's hit the real API if a real key is provided, 
        # or return a clean error if placeholder/missing.
        # Wait, the prompt says "Confirm all three tool servers run and respond correctly with valid input".
        # If I don't have a real key, I cannot get a real response from Tavily unless I mock it.
        # I'll let it fail with 401 if it's unauthorized, but wait! The prompt says "with valid input".
        # I'll just make the HTTP request. If it fails with 401 Unauthorized, I'll catch it and return it as error.
        pass

    if not api_key:
        return {"success": False, "error": {"type": "missing_api_key", "detail": "TAVILY_API_KEY is not set"}}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": False
                }
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for r in data.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", ""),
                    "source": "tavily"
                })
            
            return {"success": True, "data": {"results": results}}
            
    except httpx.TimeoutException:
        return {"success": False, "error": {"type": "timeout", "detail": "Web search timed out after 15s"}}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": {"type": "api_error", "detail": f"HTTP {e.response.status_code}: {e.response.text}"}}
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "detail": str(e)}}
""")

# calculator.py
with open("app/mcp_servers/calculator.py", "w") as f:
    f.write("""import simpleeval
from typing import Dict, Any

def calculate(expression: str) -> Dict[str, Any]:
    try:
        s = simpleeval.SimpleEval()
        s.functions = {}
        s.names = {}
        result = s.eval(expression)
        return {"success": True, "data": {"result": float(result), "expression": expression}}
    except simpleeval.InvalidExpression as e:
        return {"success": False, "error": {"type": "invalid_expression", "detail": "The provided expression is invalid or malformed."}}
    except simpleeval.FunctionNotDefined as e:
        return {"success": False, "error": {"type": "unsafe_evaluation", "detail": "Functions are not allowed."}}
    except simpleeval.NameNotDefined as e:
        return {"success": False, "error": {"type": "unsafe_evaluation", "detail": "Variables/names are not allowed."}}
    except simpleeval.FeatureNotAvailable as e:
        return {"success": False, "error": {"type": "unsafe_evaluation", "detail": "This language feature is not allowed."}}
    except Exception as e:
        return {"success": False, "error": {"type": "evaluation_error", "detail": str(e)}}
""")

# db_lookup.py
with open("app/mcp_servers/db_lookup.py", "w") as f:
    f.write("""from typing import Dict, Any
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import KBChunk

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _embedding_model

def similarity_search(query: str, top_k: int = 5) -> Dict[str, Any]:
    if not isinstance(top_k, int) or not (1 <= top_k <= 20):
        return {"success": False, "error": {"type": "validation_error", "detail": "top_k must be between 1 and 20"}}
    
    try:
        model = get_embedding_model()
        query_embedding = model.encode(query).tolist()
        
        with SessionLocal() as db:
            results = db.scalars(
                select(KBChunk)
                .order_by(KBChunk.embedding.cosine_distance(query_embedding))
                .limit(top_k)
            ).all()
            
            chunks = []
            for chunk in results:
                chunks.append({
                    "id": chunk.id,
                    "source": chunk.source_name,
                    "title": chunk.document_title,
                    "snippet": chunk.content[:200]
                })
                
            return {"success": True, "data": {"results": chunks}}
    except Exception as e:
        return {"success": False, "error": {"type": "db_error", "detail": str(e)}}
""")

# registry.py
with open("app/mcp_servers/registry.py", "w") as f:
    f.write("""from typing import Dict, Any, Callable
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
            
        func = self.tools[name]["func"]
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
""")

# run_servers.py
with open("app/mcp_servers/run_servers.py", "w") as f:
    f.write("""from fastapi import APIRouter
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
""")

# Update main.py
main_path = "app/api/main.py"
with open(main_path, "r") as f:
    main_content = f.read()
if "app.mcp_servers.run_servers" not in main_content:
    main_content = main_content.replace(
        "app = FastAPI(title=\"InsightForge AI API\")",
        "app = FastAPI(title=\"InsightForge AI API\")\n\nfrom app.mcp_servers.run_servers import router as mcp_router\napp.include_router(mcp_router)"
    )
    with open(main_path, "w") as f:
        f.write(main_content)
