"""
Item 3: Cutoff robustness test across 10 new in-domain sub-questions and 10 new out-of-scope sub-questions.
"""

import sys
import asyncio
from app.mcp_servers.db_lookup import similarity_search
from app.db.session import SessionLocal
from app.db.models import KBChunk
from sqlalchemy import select
from app.agents.graph.nodes import retriever_node, DISTANCE_CUTOFF, MIN_CHUNKS_UNDER_CUTOFF
from app.agents.graph.state import ResearchState

IN_DOMAIN_QUESTIONS = [
    "What are the direct electricity and water requirements of expanding AI data centers?",
    "How does AI adoption contribute to grid balancing and renewable energy integration?",
    "What economic factors drive market concentration among frontier AI developers?",
    "How do high capital expenditure costs for AI infrastructure affect economic returns?",
    "What are the geopolitical risks associated with semiconductor supply chain bottlenecks in AI?",
    "How does structural power over AI cloud computing bottlenecks influence international relations?",
    "How does AI-enabled robotics reduce demand for routine physical labor in manufacturing?",
    "What mechanisms can distribute the economic productivity gains of AI to displaced workers?",
    "How do national digital sovereignty initiatives respond to foreign dominance in AI foundation models?",
    "What role does public regulation play in governing environmental and infrastructure impacts of AI?"
]

OUT_OF_SCOPE_QUESTIONS = [
    "What automated unit test generation frameworks are most effective for Python web applications?",
    "How do microservices architectures compare to monolithic backends for scalable web services?",
    "What are the clinical trial phases required for FDA approval of mRNA oncology drugs?",
    "How do modern immunotherapy protocols target metastatic melanoma tumors?",
    "What tactical formation adjustments led to success in recent Champions League soccer tournaments?",
    "How do high-altitude training regimens improve marathon runner VO2 max metrics?",
    "What economic factors caused the hyperinflation crisis in Weimar Germany in 1923?",
    "How did maritime trade routes through Venice influence early modern European finance?",
    "What fermentation temperatures produce optimal sourdough bread crumb structure?",
    "What standard of proof is required for copyright infringement under US federal intellectual property law?"
]

async def evaluate_sub_questions(questions, category_name):
    print(f"\n{'='*70}")
    print(f"EVALUATING: {category_name} ({len(questions)} sub-questions)")
    print(f"{'='*70}")
    
    state: ResearchState = {
        "run_id": "test-robustness",
        "topic": category_name,
        "sub_questions": questions,
        "evidence": {},
        "sections": {},
        "max_revisions": 1,
        "critique_history": []
    }
    
    diff = await retriever_node(state)
    sections = diff["sections"]
    evidence = diff["evidence"]
    
    passed_count = 0
    blocked_count = 0
    
    for idx, sq in enumerate(questions, 1):
        sec = sections.get(sq, {})
        chunks = evidence.get(sq, [])
        distances = [round(c.get("distance", 0.0), 4) for c in chunks]
        chunks_under = sum(1 for d in distances if d <= DISTANCE_CUTOFF)
        status = sec.get("status")
        verdict = "PASSED (sufficient)" if status == "pending" else "BLOCKED (insufficient)"
        
        if status == "pending":
            passed_count += 1
        else:
            blocked_count += 1
            
        print(f"\n[{idx}] Sub-question: {sq}")
        print(f"    5 Distances: {distances}")
        print(f"    Chunks under {DISTANCE_CUTOFF}: {chunks_under}")
        print(f"    Verdict: {verdict}")
        if sec.get("reason"):
            print(f"    Reason: {sec.get('reason')}")
            
    return passed_count, blocked_count

async def main():
    in_pass, in_block = await evaluate_sub_questions(IN_DOMAIN_QUESTIONS, "IN-DOMAIN SUB-QUESTIONS")
    out_pass, out_block = await evaluate_sub_questions(OUT_OF_SCOPE_QUESTIONS, "OUT-OF-SCOPE SUB-QUESTIONS")
    
    print("\n" + "="*70)
    print("ROBUSTNESS EVALUATION SUMMARY")
    print("="*70)
    print(f"In-domain:     {in_pass}/{len(IN_DOMAIN_QUESTIONS)} passed, {in_block} wrongly blocked")
    print(f"Out-of-scope:  {out_block}/{len(OUT_OF_SCOPE_QUESTIONS)} blocked, {out_pass} wrongly passed")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
