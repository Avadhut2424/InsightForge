from typing import List, Dict, Any
from app.agents.base import Agent, Task, MemoryStore
from app.mcp_servers.db_lookup import similarity_search

class RetrieverAgent(Agent):
    """
    Takes a sub-question and retrieves relevant evidence chunks from the knowledge base.
    """
    async def run(self, task: Task, memory: MemoryStore) -> List[Dict[str, Any]]:
        sub_question = task.input_data
        if not isinstance(sub_question, str):
            raise ValueError("RetrieverAgent expects a string sub-question as input")
            
        # Call the Phase 5 db_lookup tool's similarity_search function directly.
        # Note: Tool-augmented retrieval (e.g. web_search) is deferred to Phase 7 
        # as requested, to keep this phase's Retriever knowledge-base-only and its
        # behavior easy to isolate and verify.
        result = similarity_search(query=sub_question, top_k=5)
        
        if not result.get("success"):
            error_detail = result.get("error", {}).get("detail", "Unknown error")
            raise RuntimeError(f"Database lookup failed: {error_detail}")
            
        return result.get("data", {}).get("results", [])
