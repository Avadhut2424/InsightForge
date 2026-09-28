"""
CLI Entrypoint for running the InsightForge LangGraph workflow.
Usage: python -m app.agents.graph.run_graph "<topic>"
"""

import sys
import time
import asyncio
from datetime import datetime

from app.core.llm.client import call_llm
from app.agents.graph.state import ResearchState
from app.agents.graph.graph import graph
from app.agents.graph.tracking import start_research_run, complete_research_run

async def main():
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:]).strip()
    else:
        topic = "the environmental and economic impact of AI"

    print(f"=== InsightForge LangGraph Workflow ===")
    print(f"Topic: {topic}")
    
    # Step 1: Warm-up call_llm() at graph startup
    print("Performing LLM warm-up call...")
    warm_start = time.time()
    try:
        warm_res = await call_llm(role="planner", prompt="System warm-up check. Respond with 'ready'.")
        print(f"LLM warm-up complete in {time.time() - warm_start:.2f}s: {warm_res.text.strip()[:30]}")
    except Exception as e:
        print(f"Warning: warm-up call failed ({e}), continuing...")

    # Step 5: Start tracking run in DB
    run_id = start_research_run(topic=topic, metadata={"entrypoint": "run_graph"})
    print(f"Tracking run initialized in DB: run_id={run_id}")

    initial_state: ResearchState = {
        "run_id": str(run_id) if run_id else "untracked",
        "topic": topic,
        "sub_questions": [],
        "evidence": {},
        "sections": {},
        "max_revisions": 1,
        "final_status": "partial",
        "critique_history": []
    }

    start_time = time.time()
    try:
        final_state = await graph.ainvoke(initial_state)
    except Exception as e:
        print(f"Error during graph execution: {e}")
        if run_id:
            complete_research_run(run_id, "failed", {"error": str(e)})
        raise e

    elapsed = time.time() - start_time

    # Print final state summary
    print("\n" + "="*60)
    print("FINAL STATE SUMMARY")
    print("="*60)
    print(f"Run ID: {final_state.get('run_id')}")
    print(f"Topic: {final_state.get('topic')}")
    print(f"Final Status: {final_state.get('final_status')}")
    print(f"Elapsed Time: {elapsed:.2f}s")
    print(f"Sub-questions ({len(final_state.get('sub_questions', []))}):")
    for idx, sq in enumerate(final_state.get("sub_questions", []), 1):
        print(f"  {idx}. {sq}")

    print("\nSections Detail:")
    sections = final_state.get("sections", {})
    for sq, sec in sections.items():
        print(f"\n--- Sub-question: {sq} ---")
        print(f"Status: {sec.get('status')}")
        print(f"Verdict: {sec.get('verdict')}")
        print(f"Revision Count: {sec.get('revision_count')}")
        if sec.get("reason"):
            print(f"Reason: {sec.get('reason')}")
        
        draft_items = sec.get("draft", [])
        print(f"Draft Sentences ({len(draft_items)}):")
        for d_idx, d in enumerate(draft_items, 1):
            print(f"  [{d_idx}] {d.get('sentence')} -- Citation: {d.get('citation')}")
            
        print(f"Assembled Text:\n{sec.get('assembled_text')}")

    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
