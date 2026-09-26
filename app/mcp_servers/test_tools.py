import asyncio
import os
import sys

# Ensure the app can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.mcp_servers.registry import registry
import json

async def test_tools():
    print("--- Listing Tools ---")
    tools = registry.list_tools()
    print(json.dumps(tools, indent=2))
    print()

    print("--- Testing Web Search ---")
    # Valid
    print("[Web Search] Valid query:")
    res = await registry.call_tool("web_search", {"query": "AI economic and environmental impact latest research", "max_results": 2})
    print(json.dumps(res, indent=2))
    # Invalid (empty)
    print("\n[Web Search] Invalid query (missing arg):")
    res = await registry.call_tool("web_search", {})
    print(json.dumps(res, indent=2))
    print()

    print("--- Testing Calculator ---")
    # Valid
    print("[Calculator] Valid expression:")
    res = await registry.call_tool("calculator", {"expression": "12 * (4 + 3) / 2"})
    print(json.dumps(res, indent=2))
    # Invalid (malicious)
    print("\n[Calculator] Invalid/malicious expression (__import__('os')):")
    res = await registry.call_tool("calculator", {"expression": "__import__('os').system('ls')"})
    print(json.dumps(res, indent=2))
    print()

    print("--- Testing DB Lookup ---")
    # Valid
    print("[DB Lookup] Valid similarity search:")
    res = await registry.call_tool("db_lookup", {"query": "AI research", "top_k": 2})
    print(json.dumps(res, indent=2))
    # Invalid
    print("\n[DB Lookup] Invalid top_k (500):")
    res = await registry.call_tool("db_lookup", {"query": "AI research", "top_k": 500})
    print(json.dumps(res, indent=2))
    print()

if __name__ == "__main__":
    asyncio.run(test_tools())
