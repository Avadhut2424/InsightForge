import asyncio
import json
import numpy as np
from app.mcp_servers.db_lookup import get_embedding_model
from app.agents.graph.nodes import retriever_node

async def main():
    sq = "What are the primary environmental impacts of AI adoption, and how do they vary across different industries and applications?"
    initial_state = {
        "run_id": "temp",
        "topic": "the environmental and economic impact of AI",
        "sub_questions": [sq],
        "evidence": {},
        "sections": {},
        "max_revisions": 1,
        "final_status": "partial",
        "critique_history": []
    }
    
    state = await retriever_node(initial_state)
    chunks = state["evidence"][sq]
    
    model = get_embedding_model()
    q_emb = model.encode(sq, normalize_embeddings=True)
    
    print(f"SQ: {sq}\n")
    
    for chunk in chunks:
        cid = chunk["id"]
        content = chunk.get("content", chunk.get("snippet", ""))
        import re
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', content) if len(s.strip()) >= 15]
        
        for i, s in enumerate(sentences):
            s_emb = model.encode(s, normalize_embeddings=True)
            sim = float(np.dot(q_emb, s_emb))
            sid = f"c{cid}-s{i+1}"
            if sim >= 0.50:
                print(f"[{sid}] Sim: {sim:.3f}")
                print(f"Text: {s}\n")

if __name__ == "__main__":
    asyncio.run(main())
