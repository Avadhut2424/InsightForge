"""
LangGraph research workflow graph implementation with conditional edges.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, START, END

from app.agents.graph.state import ResearchState
from app.agents.graph.nodes import (
    planner_node,
    retriever_node,
    synthesizer_node,
    critic_node,
)
from app.agents.graph.routing import (
    determine_final_status,
    route_after_retriever,
    route_after_critic,
)
from app.agents.graph.tracking import complete_research_run

async def finalize_node(state: ResearchState) -> Dict[str, Any]:
    """Finalizes research run and records final status and report metadata."""
    sections = state.get("sections", {})
    final_status = determine_final_status(sections)
    run_id = state.get("run_id")
    if run_id and str(run_id).isdigit():
        metadata = {
            "sub_question_count": len(sections),
            "sections": {
                sq: {
                    "status": sec.get("status"),
                    "verdict": sec.get("verdict"),
                    "revision_count": sec.get("revision_count", 0),
                    "assembled_text": sec.get("assembled_text", ""),
                    "draft": sec.get("draft", [])
                }
                for sq, sec in sections.items()
            }
        }
        complete_research_run(int(run_id), final_status, metadata=metadata)
    return {"final_status": final_status}

def build_research_graph():
    """
    Constructs the full LangGraph workflow:
    START -> planner -> retriever -> [conditional: route_after_retriever]
      ├──> finalize -> END (if all sub-questions have insufficient evidence)
      └──> synthesizer -> critic -> [conditional: route_after_critic]
             ├──> synthesizer (revision cycle or next sub-question)
             └──> finalize -> END (all sub-questions processed)
    """
    builder = StateGraph(ResearchState)
    
    builder.add_node("planner", planner_node)
    builder.add_node("retriever", retriever_node)
    builder.add_node("synthesizer", synthesizer_node)
    builder.add_node("critic", critic_node)
    builder.add_node("finalize", finalize_node)
    
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "retriever")
    
    builder.add_conditional_edges(
        "retriever",
        route_after_retriever,
        {
            "synthesizer": "synthesizer",
            "finalize": "finalize"
        }
    )
    
    builder.add_edge("synthesizer", "critic")
    
    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "synthesizer": "synthesizer",
            "finalize": "finalize"
        }
    )
    
    builder.add_edge("finalize", END)
    
    return builder.compile()

# Active graph
graph = build_research_graph()
