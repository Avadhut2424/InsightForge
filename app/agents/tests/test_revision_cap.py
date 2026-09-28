"""
Step 7d: Revision cap test.
Forces Critic verdict to "revise" using test injection 2 of 2.
Confirms graph stops at max_revisions, marks sections "unverified", and terminates without infinite loop.
"""

import sys
import asyncio
from app.agents.graph.state import ResearchState
from app.agents.graph.graph import graph
from app.agents.graph.tracking import start_research_run

async def test_revision_cap():
    print("=== Step 7d: Revision Cap Test ===")
    topic = "the environmental and economic impact of AI"
    run_id = start_research_run(topic=topic, metadata={"test": "step_7d_cap"})
    print(f"Tracking run initialized: run_id={run_id}")
    
    max_revisions = 1
    
    initial_state: ResearchState = {
        "run_id": str(run_id) if run_id else "test-cap",
        "topic": topic,
        "sub_questions": ["What are the primary environmental impacts of AI adoption?"],
        "evidence": {},
        "sections": {},
        "max_revisions": max_revisions,
        "final_status": "partial",
        "critique_history": [],
        "_test_force_critic_revise": True
    }
    
    print(f"Running graph with max_revisions={max_revisions} and forced Critic revise...")
    final_state = await graph.ainvoke(initial_state)
    
    print("\n--- Final State from Cap Test ---")
    print(f"Final Status: {final_state.get('final_status')}")
    sections = final_state.get("sections", {})
    
    for sq, sec in sections.items():
        print(f"Sub-question: {sq}")
        print(f"Status: {sec.get('status')}")
        print(f"Verdict: {sec.get('verdict')}")
        print(f"Revision Count: {sec.get('revision_count')}")
        print(f"Reason: {sec.get('reason')}")
        assert sec.get("revision_count") == max_revisions, (
            f"Expected revision_count={max_revisions}, got {sec.get('revision_count')}"
        )
        assert sec.get("status") == "unverified", (
            f"Expected section status 'unverified', got {sec.get('status')}"
        )
        assert len(sec.get("assembled_text", "")) > 0, "Expected latest draft to be retained"
        
    assert final_state.get("final_status") == "partial", (
        f"Expected final_status 'partial' when all sections unverified, got {final_state.get('final_status')}"
    )
    print("Assertion passed: Graph stopped at max_revisions, marked section unverified, retained latest draft, and set final_status to partial.\n")

if __name__ == "__main__":
    asyncio.run(test_revision_cap())
