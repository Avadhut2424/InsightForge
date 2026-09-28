"""
Item 5: Graph-level revision with tracking.
Runs a full graph run where sub-question 1's first pass is overridden with the background-only selection.
Executes the real Critic, real second Synthesizer pass, and processes all sub-questions to completion.
Then queries and prints the DB tracking records (research_runs, agent_steps, revisions).
"""

import sys
import time
import asyncio
from datetime import datetime

from app.core.llm.client import call_llm
from app.agents.graph.state import ResearchState
from app.agents.graph.graph import graph
from app.agents.graph.tracking import start_research_run, complete_research_run
from app.db.session import SessionLocal
from app.db.models import ResearchRun, AgentStep, Revision

async def main():
    topic = "the environmental and economic impact of AI"
    print("=== Item 5: Graph-Level Revision with Tracking ===")
    print(f"Topic: {topic}")
    
    # Warm-up call
    await call_llm(role="planner", prompt="Ready check.")
    
    run_id = start_research_run(topic=topic, metadata={"test": "item_5_graph_revision"})
    print(f"Tracking run initialized: run_id={run_id}")
    
    # Candidate IDs for background-only override on first sub-question
    bg_ids = ["c4-s2", "c4-s3", "c4-s4"]
    
    initial_state: ResearchState = {
        "run_id": str(run_id),
        "topic": topic,
        "sub_questions": [],
        "evidence": {},
        "sections": {},
        "max_revisions": 1,
        "final_status": "partial",
        "critique_history": [],
        "_test_synthesizer_override": {
            "selected_ids": bg_ids
        }
    }
    
    start_time = time.time()
    final_state = await graph.ainvoke(initial_state)
    elapsed = time.time() - start_time
    
    print("\n" + "="*70)
    print("FINAL STATE SUMMARY (Item 5)")
    print("="*70)
    print(f"Run ID: {final_state.get('run_id')}")
    print(f"Final Status: {final_state.get('final_status')}")
    print(f"Elapsed Time: {elapsed:.2f}s")
    print(f"Sub-questions ({len(final_state.get('sub_questions', []))}):")
    for idx, sq in enumerate(final_state.get("sub_questions", []), 1):
        print(f"  {idx}. {sq}")
        
    sections = final_state.get("sections", {})
    for sq, sec in sections.items():
        print(f"\n--- Sub-question: {sq} ---")
        print(f"Status: {sec.get('status')}")
        print(f"Verdict: {sec.get('verdict')}")
        print(f"Revision Count: {sec.get('revision_count')}")
        print(f"Selected IDs: {sec.get('selected_ids')}")
        if sec.get("reason"):
            print(f"Reason: {sec.get('reason')}")
        print(f"Assembled Text:\n{sec.get('assembled_text')[:200]}...")
        
    print("\n" + "="*70)
    print("DATABASE TRACKING ROWS FOR RUN", run_id)
    print("="*70)
    
    with SessionLocal() as db:
        run_row = db.query(ResearchRun).filter(ResearchRun.id == run_id).first()
        print(f"ResearchRun: ID={run_row.id} | Status={run_row.status} | Started={run_row.started_at} | Completed={run_row.completed_at}")
        
        step_rows = db.query(AgentStep).filter(AgentStep.run_id == run_id).order_by(AgentStep.id).all()
        print(f"\nAgent Steps ({len(step_rows)} rows):")
        for s in step_rows:
            print(f"  Step ID {s.id}: [{s.agent_name.upper():11}] Index={s.step_index} | Status={s.status} | Duration={(s.completed_at - s.started_at).total_seconds():.2f}s")
            print(f"      Input:  {s.input_summary}")
            print(f"      Output: {s.output_summary}")
            
        rev_rows = db.query(Revision).filter(Revision.run_id == run_id).order_by(Revision.id).all()
        print(f"\nRevisions ({len(rev_rows)} rows):")
        for r in rev_rows:
            print(f"  Rev ID {r.id}: Cycle={r.revision_number} | Reason: {r.reason}")

if __name__ == "__main__":
    asyncio.run(main())
