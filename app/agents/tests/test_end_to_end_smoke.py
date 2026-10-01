"""
Phase 10 Automated Test 2: Full Graph End-to-End Execution Smoke Test.
Runs a known-good in-domain topic through the full live LangGraph pipeline
without injected test overrides, asserting execution reaches completion.
"""

import pytest
import asyncio
from app.agents.graph.graph import graph
from app.agents.graph.state import ResearchState
from app.agents.graph.tracking import start_research_run

@pytest.mark.asyncio
async def test_end_to_end_smoke_pipeline():
    """
    Executes a complete unforced graph run on a known-good in-domain topic.
    Asserts final_status is 'approved' or 'partial' (never 'failed' or 'insufficient_evidence').
    """
    topic = "the environmental impact of AI computing hardware and energy consumption"
    run_id = start_research_run(topic=topic, metadata={"test": "phase10_smoke_test"})
    
    initial_state: ResearchState = {
        "run_id": str(run_id) if run_id else "smoke-test",
        "topic": topic,
        "sub_questions": [],
        "evidence": {},
        "sections": {},
        "max_revisions": 1,
        "final_status": "partial",
        "critique_history": []
    }
    
    final_state = await graph.ainvoke(initial_state)
    
    final_status = final_state.get("final_status")
    assert final_status in ["approved", "partial"], (
        f"Smoke test failed: unexpected final_status '{final_status}'"
    )
    assert final_status != "failed", "Pipeline crashed with status 'failed'"
    assert final_status != "insufficient_evidence", "Pipeline incorrectly classified known in-domain topic as insufficient evidence"
    
    sections = final_state.get("sections", {})
    assert len(sections) > 0, "No sections generated in final report"
    
    # Confirm every section has assembled content
    for sq, sec in sections.items():
        assert len(sec.get("assembled_text", "")) > 0, f"Section '{sq}' has empty assembled text"
        
    print(f"\n[PASS] End-to-end smoke test passed: final_status='{final_status}', {len(sections)} sections generated.")

if __name__ == "__main__":
    asyncio.run(test_end_to_end_smoke_pipeline())
