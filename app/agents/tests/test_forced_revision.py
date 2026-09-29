import pytest
from app.agents.graph.graph import graph
from app.agents.graph.nodes import critic_node
from app.agents.graph.state import ResearchState
from app.db.session import SessionLocal

@pytest.mark.asyncio
async def test_end_to_end_real_revision_loop():
    """
    Test the full end-to-end graph on a sub-question that naturally triggers
    a revision cycle. This proves that a real Synthesizer draft can pass
    the 0.50 relevance floor but still fail the Critic's coverage check.
    """
    topic = "the long-term economic benefits and costs of investing in AI research and development"
    run_id = "test-real-revision"
    sq = "How do the long-term economic benefits and costs of investing in AI research and development vary across different industries and sectors?"
    
    # Start graph from retriever (bypassing planner to force this specific sub-question)
    initial_state = {
        "run_id": run_id,
        "topic": topic,
        "sub_questions": [sq],
        "evidence": {},
        "sections": {},
        "max_revisions": 1,
        "final_status": "in_progress",
        "critique_history": []
    }
    
    final_state = await graph.ainvoke(initial_state, config={"configurable": {"start_node": "retriever_node"}})
    
    assert final_state["final_status"] in ["completed", "partial"]
    
    # Check that a revision occurred
    section = final_state["sections"][sq]
    assert section["revision_count"] > 0, "Expected the graph to trigger a natural revision for this sub-question"
    
    # In this specific case, the LLM usually fails both passes because the corpus 
    # lacks sufficient specific information about different industries. 
    # Whether it eventually passes or hits the cap, we proved the loop works.
    assert section["status"] in ["approved", "unverified"]

@pytest.mark.asyncio
async def test_critic_requires_comprehensive_coverage():
    """
    SECONDARY UNIT TEST:
    Explicitly test the Critic node's ability to reject an incomplete draft.
    """
    sq = "What are the primary environmental impacts of AI adoption, and how do they vary across different industries and applications?"
    sentences = [
        "AI-related investment may increase productivity but also reinforce market concentration.",
        "In the labour market, AI -enabled robotics is likely to reduce demand for some traditional industrial occupations."
    ]
    draft_text = " ".join(sentences)
    
    initial_state: ResearchState = {
        "run_id": "test-forced",
        "topic": "the environmental and economic impact of AI",
        "sub_questions": [sq],
        "evidence": {sq: [{"id": 1529, "content": draft_text}]},
        "sections": {
            sq: {
                "draft": [{"sentence": s, "citation": "Source"} for s in sentences],
                "assembled_text": draft_text,
                "status": "synthesized",
                "revision_count": 0,
                "verdict": None,
                "reason": None
            }
        },
        "max_revisions": 1,
        "final_status": "partial",
        "critique_history": []
    }
    
    new_state = await critic_node(initial_state)
    sec = new_state["sections"][sq]
    
    assert sec.get("verdict") == "revise"
    assert sec.get("status") == "needs_revision"
