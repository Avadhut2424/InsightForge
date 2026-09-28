"""
Step 2: Fresh data evaluation on 5 new in-domain sub-questions.
Evaluates each sub-question independently through retriever, synthesizer, and critic.
Measures sentence-level relevance before and after the 0.50 floor.
"""

import sys
import asyncio
from sentence_transformers import SentenceTransformer
import numpy as np

from app.agents.graph.state import ResearchState
from app.agents.graph.nodes import retriever_node, synthesizer_node, critic_node, RELEVANCE_FLOOR
from app.mcp_servers.db_lookup import get_embedding_model

FRESH_QUESTIONS = [
    "How do power grid capacity limits constrain the geographical expansion of AI computing facilities?",
    "In what ways does generative AI investment drive market concentration among cloud hyperscalers?",
    "How does the deployment of intelligent industrial robots impact employment demand across manufacturing sectors?",
    "What structural leverage do advanced semiconductor manufacturing bottlenecks grant to nations?",
    "What institutional and regulatory frameworks are necessary to mitigate local water and energy strains from AI data centers?"
]

async def evaluate_single_question(sq: str, idx: int):
    print(f"\n{'='*75}")
    print(f"[{idx}] Sub-question: {sq}")
    print(f"{'='*75}")
    
    state: ResearchState = {
        "run_id": f"fresh-{idx}",
        "topic": sq,
        "sub_questions": [sq],
        "evidence": {},
        "sections": {},
        "max_revisions": 1,
        "critique_history": []
    }
    
    # 1. Retriever pass
    ret_diff = await retriever_node(state)
    state.update(ret_diff)
    sec = state["sections"][sq]
    
    if sec.get("status") == "insufficient_evidence":
        print(f"Retriever Verdict: INSUFFICIENT EVIDENCE")
        print(f"Reason: {sec.get('reason')}")
        return {
            "sq": sq,
            "status": "insufficient_evidence",
            "before_count": 0,
            "after_count": 0,
            "sentences": []
        }
        
    # 2. Synthesizer pass
    synth_diff = await synthesizer_node(state)
    state["sections"] = synth_diff["sections"]
    sec = state["sections"][sq]
    
    status = sec.get("status")
    draft = sec.get("draft", [])
    print(f"Synthesizer Status: {status}")
    print(f"Draft Length: {len(draft)} sentences")
    
    model = get_embedding_model()
    q_emb = model.encode(sq, normalize_embeddings=True)
    
    sentence_records = []
    for s_idx, d in enumerate(draft, 1):
        s_text = d.get("sentence", "")
        s_emb = model.encode(s_text, normalize_embeddings=True)
        sim = float(np.dot(q_emb, s_emb))
        print(f"  Sentence {s_idx} [Sim: {sim:.4f}]: {s_text}")
        sentence_records.append({"text": s_text, "sim": sim, "citation": d.get("citation")})
        
    # 3. Critic pass
    crit_diff = await critic_node(state)
    state["sections"] = crit_diff["sections"]
    sec_after_critic = state["sections"][sq]
    print(f"Critic Verdict: {sec_after_critic.get('verdict')}")
    print(f"Critic Reason:  {sec_after_critic.get('reason')}")
    print(f"Final Section Status: {sec_after_critic.get('status')}")
    
    return {
        "sq": sq,
        "status": sec_after_critic.get("status"),
        "draft_length": len(draft),
        "sentences": sentence_records
    }

async def main():
    print("=== Step 2: Fresh Data Evaluation (5 New In-Domain Sub-questions) ===")
    results = []
    for idx, sq in enumerate(FRESH_QUESTIONS, 1):
        res = await evaluate_single_question(sq, idx)
        results.append(res)
        
    print("\n" + "="*75)
    print("SUMMARY OF FRESH EVALUATION")
    print("="*75)
    total_draft_len = 0
    valid_sections = 0
    insufficient_count = 0
    for r in results:
        status = r["status"]
        if status == "insufficient_evidence":
            insufficient_count += 1
            print(f"SQ: {r['sq'][:50]}... -> INSUFFICIENT EVIDENCE")
        else:
            valid_sections += 1
            total_draft_len += r["draft_length"]
            print(f"SQ: {r['sq'][:50]}... -> Status={status}, Length={r['draft_length']}")
            
    avg_len = (total_draft_len / valid_sections) if valid_sections > 0 else 0
    print(f"\nAverage draft length for synthesized sections: {avg_len:.2f}")
    print(f"Sub-questions fell to insufficient_evidence: {insufficient_count}/{len(FRESH_QUESTIONS)}")

if __name__ == "__main__":
    asyncio.run(main())
