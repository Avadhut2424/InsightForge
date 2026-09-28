"""
Step 7c: Forced revision tests with real Critic and real second Synthesizer pass.
"""

import sys
import json
import asyncio
from app.agents.graph.state import ResearchState
from app.agents.graph.nodes import retriever_node, synthesizer_node, critic_node
from app.agents.synthesizer import split_sentences, is_bad_sentence
from app.mcp_servers.db_lookup import similarity_search
from app.db.session import SessionLocal
from app.db.models import KBChunk
from sqlalchemy import select

async def test_tampered_draft():
    print("\n--- Step 7c Part (i): Tampered Draft Code Check ---")
    sq = "What are the primary environmental impacts of AI adoption, and how do they vary across different industries and applications?"
    
    # Retrieve real chunks
    res = similarity_search(query=sq, top_k=5)
    snippets = res.get("data", {}).get("results", [])
    chunk_ids = [s["id"] for s in snippets]
    full_chunks = []
    with SessionLocal() as db:
        db_chunks = db.scalars(select(KBChunk).where(KBChunk.id.in_(chunk_ids))).all()
        id_to_content = {c.id: c.content for c in db_chunks}
        for s in snippets:
            full_chunks.append({
                "id": s["id"],
                "source": s.get("source"),
                "title": s.get("title"),
                "content": id_to_content.get(s["id"], s.get("snippet", ""))[:1500],
                "distance": float(s.get("distance", 0.0))
            })

    # Legitimate sentence from chunk 1
    legit_sentence = (
        "The environmental effects of AI are similarly ambivalent: AI systems consume energy, water, "
        "materials, and comput ing hardware, but may also improve energy efficiency, climate modelling, "
        "renewable -energy integration, and environmental monitoring."
    )
    # Tampered sentence with added clause "globally across all sectors"
    tampered_sentence = legit_sentence + " globally across all sectors."
    
    tampered_draft = [
        {"sentence": tampered_sentence, "citation": "Artificial Intelligence as an Economic, Environmental, Geopolitical, and Social Transformation"}
    ]
    
    state: ResearchState = {
        "run_id": "test-tamper",
        "topic": "AI environmental impact",
        "sub_questions": [sq],
        "evidence": {sq: full_chunks},
        "sections": {
            sq: {
                "draft": tampered_draft,
                "assembled_text": f"{tampered_sentence} (Artificial Intelligence as an Economic, Environmental, Geopolitical, and Social Transformation).",
                "status": "synthesized",
                "revision_count": 0,
                "verdict": None,
                "reason": None
            }
        },
        "max_revisions": 1,
        "critique_history": []
    }
    
    diff = await critic_node(state)
    sec = diff["sections"][sq]
    
    print(f"Verdict: {sec.get('verdict')}")
    print(f"Reason: {sec.get('reason')}")
    print(f"Status: {sec.get('status')}")
    
    assert sec.get("verdict") == "revise", f"Expected verdict revise, got {sec.get('verdict')}"
    assert "unsupported by the evidence" in sec.get("reason", "").lower() or "unsupported claims" in sec.get("reason", "").lower(), (
        f"Expected literal check failure in reason, got {sec.get('reason')}"
    )
    print("Assertion passed: Literal code check caught tampered draft clause.\n")

async def test_background_only_and_real_second_pass():
    print("\n--- Step 7c Part (ii): Background-only draft and real second pass ---")
    sq = "What are the primary environmental impacts of AI adoption, and how do they vary across different industries and applications?"
    
    # 1. Run retriever first to get evidence and candidate sentences
    initial_state: ResearchState = {
        "run_id": "test-revision-7c",
        "topic": "the environmental and economic impact of AI",
        "sub_questions": [sq],
        "evidence": {},
        "sections": {},
        "max_revisions": 1,
        "final_status": "partial",
        "critique_history": []
    }
    
    retriever_res = await retriever_node(initial_state)
    initial_state["evidence"] = retriever_res["evidence"]
    initial_state["sections"] = retriever_res["sections"]
    
    # Candidate sentences from Chunk 4 that represent general public debate / framing
    # and completely miss the specific environmental impacts question
    bg_ids = ["c4-s2", "c4-s6", "c4-s8"]
    print(f"Identified Background-Only Candidate IDs for Pass 1 injection: {bg_ids}")
    
    initial_state["_test_synthesizer_override"] = {
        "selected_ids": bg_ids
    }
    
    # 2. Pass 1 Synthesizer (uses background-only injection)
    synth_res1 = await synthesizer_node(initial_state)
    initial_state["sections"] = synth_res1["sections"]
    if "_test_synthesizer_override" in synth_res1:
        initial_state["_test_synthesizer_override"] = synth_res1["_test_synthesizer_override"]
    
    pass1_sec = initial_state["sections"][sq]
    pass1_ids = pass1_sec.get("selected_ids", [])
    print(f"Pass 1 Injected Selected IDs: {pass1_ids}")
    print(f"Pass 1 Draft Text:\n{pass1_sec.get('assembled_text')}\n")
    
    # 3. Pass 1 Critic (real LLM call evaluating coverage)
    critic_res1 = await critic_node(initial_state)
    initial_state["sections"] = critic_res1["sections"]
    initial_state["critique_history"] = critic_res1["critique_history"]
    
    sec_after_critic1 = initial_state["sections"][sq]
    verdict1 = sec_after_critic1.get("verdict")
    reason1 = sec_after_critic1.get("reason")
    print(f"Pass 1 Critic Verdict: {verdict1}")
    print(f"Pass 1 Critic Reason: {reason1}")
    print(f"Pass 1 Revision Count: {sec_after_critic1.get('revision_count')}")
    print(f"Pass 1 Status: {sec_after_critic1.get('status')}")
    
    assert verdict1 == "revise", f"Expected Critic to reject background draft with 'revise', got {verdict1}"
    assert "missing" in reason1.lower() or "fails" in reason1.lower() or "environmental" in reason1.lower(), (
        f"Expected missing note in reason, got {reason1}"
    )
    assert sec_after_critic1.get("status") == "needs_revision", f"Expected status needs_revision, got {sec_after_critic1.get('status')}"
    print("Assertion passed: Real Critic rejected background-only draft with missing aspect note.\n")
    
    # 4. Pass 2 Synthesizer (REAL LLM call with Critic reason)
    print("Running Real Second Synthesizer Pass with Critic feedback...")
    synth_res2 = await synthesizer_node(initial_state)
    initial_state["sections"] = synth_res2["sections"]
    
    pass2_sec = initial_state["sections"][sq]
    pass2_ids = pass2_sec.get("selected_ids", [])
    print(f"Pass 2 Real Selected IDs: {pass2_ids}")
    print(f"Pass 2 Draft Text:\n{pass2_sec.get('assembled_text')}\n")
    
    # 5. Pass 2 Critic (real LLM call on revised draft)
    print("Running Real Critic Pass on Second Draft...")
    critic_res2 = await critic_node(initial_state)
    initial_state["sections"] = critic_res2["sections"]
    initial_state["critique_history"] = critic_res2["critique_history"]
    
    sec_after_critic2 = initial_state["sections"][sq]
    verdict2 = sec_after_critic2.get("verdict")
    reason2 = sec_after_critic2.get("reason")
    print(f"Pass 2 Critic Verdict: {verdict2}")
    print(f"Pass 2 Critic Reason: {reason2}")
    print(f"Pass 2 Revision Count: {sec_after_critic2.get('revision_count')}")
    print(f"Pass 2 Status: {sec_after_critic2.get('status')}")
    
    print("\n--- Summary of ID Comparison ---")
    print(f"Pass 1 IDs: {pass1_ids}")
    print(f"Pass 2 IDs: {pass2_ids}")
    new_ids = [s_id for s_id in pass2_ids if s_id not in pass1_ids]
    print(f"New IDs selected in Pass 2: {new_ids}")

if __name__ == "__main__":
    asyncio.run(test_tampered_draft())
    asyncio.run(test_background_only_and_real_second_pass())
