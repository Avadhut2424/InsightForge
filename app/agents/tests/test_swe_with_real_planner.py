"""
Item 6: SWE test with real Planner (no hard-coded sub-questions).
"""

import sys
import asyncio
from app.agents.graph.state import ResearchState
from app.agents.graph.nodes import planner_node, retriever_node
from app.agents.graph.tracking import start_research_run

async def main():
    topic = "software engineering jobs"
    print(f"=== Item 6: Software Engineering Jobs Case with Real Planner ===")
    print(f"Topic: {topic}")
    
    run_id = start_research_run(topic=topic, metadata={"test": "item_6_real_planner_swe"})
    print(f"Tracking run initialized: run_id={run_id}")
    
    initial_state: ResearchState = {
        "run_id": str(run_id) if run_id else "test-swe-planner",
        "topic": topic,
        "sub_questions": [],
        "evidence": {},
        "sections": {},
        "max_revisions": 1,
        "critique_history": []
    }
    
    # 1. Run real planner
    print("Running Planner LLM...")
    planner_diff = await planner_node(initial_state)
    initial_state.update(planner_diff)
    sub_questions = initial_state["sub_questions"]
    print(f"\nPlanner Generated Sub-questions ({len(sub_questions)}):")
    for idx, sq in enumerate(sub_questions, 1):
        print(f"  {idx}. {sq}")
        
    # 2. Run retriever
    print("\nRunning Retriever node...")
    retriever_diff = await retriever_node(initial_state)
    initial_state.update(retriever_diff)
    
    evidence = initial_state["evidence"]
    sections = initial_state["sections"]
    
    print("\n" + "="*70)
    print("RETRIEVAL & SUFFICIENCY RESULTS PER SUB-QUESTION")
    print("="*70)
    for idx, sq in enumerate(sub_questions, 1):
        sec = sections.get(sq, {})
        chunks = evidence.get(sq, [])
        distances = [round(c.get("distance", 0.0), 4) for c in chunks]
        chunks_under_0255 = sum(1 for d in distances if d <= 0.255)
        print(f"\n[{idx}] Sub-question: {sq}")
        print(f"    5 Distances: {distances}")
        print(f"    Chunks under 0.255: {chunks_under_0255}")
        print(f"    Section Status: {sec.get('status')}")
        print(f"    Section Reason: {sec.get('reason')}")

if __name__ == "__main__":
    asyncio.run(main())
