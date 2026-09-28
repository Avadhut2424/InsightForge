"""
Step 7e: Out-of-domain topic (Renaissance art) and software engineering jobs case.
"""

import sys
import asyncio
from app.agents.graph.state import ResearchState
from app.agents.graph.graph import graph
from app.agents.graph.tracking import start_research_run

async def test_ood_renaissance():
    print("=== Step 7e Part 1: Out-of-Domain Topic (Renaissance Art) ===")
    topic = "Italian Renaissance art, techniques, and patronage"
    run_id = start_research_run(topic=topic, metadata={"test": "step_7e_ood"})
    print(f"Tracking run initialized: run_id={run_id}")
    
    initial_state: ResearchState = {
        "run_id": str(run_id) if run_id else "test-ood",
        "topic": topic,
        "sub_questions": [
            "How did the political landscape of Italy influence Renaissance art?",
            "Who were the primary patrons of the arts during the Italian Renaissance?",
            "What were the key techniques developed by Italian Renaissance painters?"
        ],
        "evidence": {},
        "sections": {},
        "max_revisions": 1,
        "final_status": "partial",
        "critique_history": []
    }
    
    final_state = await graph.ainvoke(initial_state)
    
    print(f"Final Status: {final_state.get('final_status')}")
    sections = final_state.get("sections", {})
    for sq, sec in sections.items():
        print(f"Sub-question: {sq}")
        print(f"  Status: {sec.get('status')}")
        print(f"  Reason: {sec.get('reason')}")
        assert sec.get("status") == "insufficient_evidence", f"Expected insufficient_evidence, got {sec.get('status')}"
        assert len(sec.get("draft", [])) == 0, f"Expected 0 draft sentences, got {len(sec.get('draft', []))}"
        
    assert final_state.get("final_status") == "insufficient_evidence", (
        f"Expected final_status 'insufficient_evidence', got {final_state.get('final_status')}"
    )
    print("Assertion passed: OOD Renaissance art exited via insufficient_evidence without calling Synthesizer.\n")

async def test_software_engineering_case():
    print("=== Step 7e Part 2: Software Engineering Jobs Case ===")
    topic = "the impact of generative AI on software engineering jobs and programming practices"
    run_id = start_research_run(topic=topic, metadata={"test": "step_7e_swe"})
    print(f"Tracking run initialized: run_id={run_id}")
    
    initial_state: ResearchState = {
        "run_id": str(run_id) if run_id else "test-swe",
        "topic": topic,
        "sub_questions": [
            "How does generative AI impact software engineering jobs and developer employment?",
            "What programming practices and software development workflows are changing due to AI?",
        ],
        "evidence": {},
        "sections": {},
        "max_revisions": 1,
        "final_status": "partial",
        "critique_history": []
    }
    
    final_state = await graph.ainvoke(initial_state)
    
    print(f"Final Status: {final_state.get('final_status')}")
    sections = final_state.get("sections", {})
    for sq, sec in sections.items():
        print(f"\nSub-question: {sq}")
        print(f"Status: {sec.get('status')}")
        print(f"Verdict: {sec.get('verdict')}")
        print(f"Reason: {sec.get('reason')}")
        print(f"Draft Sentences Count: {len(sec.get('draft', []))}")
        if sec.get("assembled_text"):
            print(f"Text snippet: {sec.get('assembled_text')[:150]}...")
            
    print("\nSoftware engineering test complete.")

if __name__ == "__main__":
    asyncio.run(test_ood_renaissance())
    asyncio.run(test_software_engineering_case())
