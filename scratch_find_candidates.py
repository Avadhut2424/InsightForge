import asyncio
import json
import numpy as np
from app.agents.graph.state import ResearchState
from app.agents.graph.nodes import retriever_node, synthesizer_node
from app.agents.synthesizer import split_sentences, is_bad_sentence, starts_with_dangling_referent
from app.mcp_servers.db_lookup import get_embedding_model

async def main():
    sq = "What are the primary environmental impacts of AI adoption, and how do they vary across different industries and applications?"
    state = {
        "run_id": "test-scratch",
        "topic": "the environmental and economic impact of AI",
        "sub_questions": [sq],
        "evidence": {},
        "sections": {},
        "max_revisions": 1,
        "final_status": "partial",
        "critique_history": []
    }
    ret_diff = await retriever_node(state)
    chunks = ret_diff["evidence"][sq]
    
    emb_model = get_embedding_model()
    q_emb = emb_model.encode(sq, normalize_embeddings=True)
    
    sorted_chunks = sorted(chunks, key=lambda c: c.get("distance", 0.0))
    candidates = []
    
    for c_idx, chunk in enumerate(sorted_chunks):
        chunk_num = c_idx + 1
        content = chunk.get("content", chunk.get("snippet", ""))
        sentences = split_sentences(content)
        for s_idx, sentence in enumerate(sentences):
            s_id = f"c{chunk_num}-s{s_idx+1}"
            if is_bad_sentence(sentence): continue
            
            s_emb = emb_model.encode(sentence, normalize_embeddings=True)
            sim = float(np.dot(q_emb, s_emb))
            if sim >= 0.50:
                candidates.append((s_id, sim, sentence))
                
    # Print the candidates passing the floor
    candidates.sort(key=lambda x: x[1], reverse=True)
    for c in candidates:
        print(f"[{c[0]}] Sim: {c[1]:.4f} - {c[2]}")

if __name__ == "__main__":
    asyncio.run(main())
