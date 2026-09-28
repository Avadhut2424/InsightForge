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
            
        from app.db.session import SessionLocal
        from app.db.models import KBChunk
        from sqlalchemy import select
        
        result = similarity_search(query=sub_question, top_k=5)
        
        if not result.get("success"):
            error_detail = result.get("error", {}).get("detail", "Unknown error")
            raise RuntimeError(f"Database lookup failed: {error_detail}")
            
        snippets = result.get("data", {}).get("results", [])
        if not snippets:
            return []
            
        chunk_ids = [s["id"] for s in snippets]
        full_chunks = []
        with SessionLocal() as db:
            db_chunks = db.scalars(select(KBChunk).where(KBChunk.id.in_(chunk_ids))).all()
            id_to_content = {c.id: c.content for c in db_chunks}
            
            for s in snippets:
                content = id_to_content.get(s["id"], s.get("snippet", ""))
                full_chunks.append({
                    "id": s["id"],
                    "source": s.get("source"),
                    "title": s.get("title"),
                    # Add full text capped at 1500 chars for agents to use
                    "content": content[:1500],
                    "snippet": s.get("snippet")
                })
        
        return full_chunks

