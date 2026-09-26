import httpx
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
