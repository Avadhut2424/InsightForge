"""
Unit tests for pure routing functions in app/agents/graph/routing.py.
"""

from app.agents.graph.routing import (
    should_skip_to_end_after_retriever,
    can_revise_section,
    determine_final_status,
    get_next_sub_question_to_process,
    route_after_retriever,
    route_after_critic,
)
from app.agents.graph.state import SectionData, ResearchState

def test_should_skip_to_end_after_retriever():
    # Empty sections -> skip
    assert should_skip_to_end_after_retriever({}) is True
    
    # All insufficient -> skip
    sections_all_insuf = {
        "sq1": {"status": "insufficient_evidence"},
        "sq2": {"status": "insufficient_evidence"}
    }
    assert should_skip_to_end_after_retriever(sections_all_insuf) is True
    
    # Mixed -> do not skip
    sections_mixed = {
        "sq1": {"status": "pending"},
        "sq2": {"status": "insufficient_evidence"}
    }
    assert should_skip_to_end_after_retriever(sections_mixed) is False
    
    # All pending -> do not skip
    sections_pending = {
        "sq1": {"status": "pending"}
    }
    assert should_skip_to_end_after_retriever(sections_pending) is False

def test_can_revise_section():
    # Verdict approve -> cannot revise
    assert can_revise_section({"verdict": "approve", "revision_count": 0}, max_revisions=1) is False
    
    # Verdict revise and revision_count < max_revisions -> can revise
    assert can_revise_section({"verdict": "revise", "revision_count": 0}, max_revisions=1) is True
    
    # Verdict revise and revision_count >= max_revisions -> cannot revise
    assert can_revise_section({"verdict": "revise", "revision_count": 1}, max_revisions=1) is False
    assert can_revise_section({"verdict": "revise", "revision_count": 2}, max_revisions=2) is False

def test_determine_final_status():
    # Empty
    assert determine_final_status({}) == "failed"
    
    # All approved
    assert determine_final_status({
        "sq1": {"status": "approved"},
        "sq2": {"status": "approved"}
    }) == "approved"
    
    # All insufficient
    assert determine_final_status({
        "sq1": {"status": "insufficient_evidence"},
        "sq2": {"status": "insufficient_evidence"}
    }) == "insufficient_evidence"
    
    # Mixed approved and insufficient -> partial
    assert determine_final_status({
        "sq1": {"status": "approved"},
        "sq2": {"status": "insufficient_evidence"}
    }) == "partial"
    
    # Mixed approved and unverified -> partial
    assert determine_final_status({
        "sq1": {"status": "approved"},
        "sq2": {"status": "unverified"}
    }) == "partial"
    
    # All unverified -> partial (do NOT present unverified as approved)
    assert determine_final_status({
        "sq1": {"status": "unverified"}
    }) == "partial"

def test_get_next_sub_question_to_process():
    sub_questions = ["sq1", "sq2", "sq3"]
    
    # Priority 1: needs_revision takes precedence
    sections = {
        "sq1": {"status": "approved"},
        "sq2": {"status": "pending"},
        "sq3": {"status": "needs_revision"}
    }
    assert get_next_sub_question_to_process(sub_questions, sections) == "sq3"
    
    # Priority 2: first pending
    sections2 = {
        "sq1": {"status": "approved"},
        "sq2": {"status": "pending"},
        "sq3": {"status": "insufficient_evidence"}
    }
    assert get_next_sub_question_to_process(sub_questions, sections2) == "sq2"
    
    # All finished
    sections3 = {
        "sq1": {"status": "approved"},
        "sq2": {"status": "unverified"},
        "sq3": {"status": "insufficient_evidence"}
    }
    assert get_next_sub_question_to_process(sub_questions, sections3) is None

def test_graph_conditional_edges():
    # After retriever: all insufficient -> finalize
    state_insuf: ResearchState = {
        "sections": {
            "sq1": {"status": "insufficient_evidence"}
        }
    }
    assert route_after_retriever(state_insuf) == "finalize"
    
    # After retriever: some pending -> synthesizer
    state_has_pending: ResearchState = {
        "sections": {
            "sq1": {"status": "pending"},
            "sq2": {"status": "insufficient_evidence"}
        }
    }
    assert route_after_retriever(state_has_pending) == "synthesizer"
    
    # After critic: still have pending or needs_revision -> synthesizer
    state_critic_loop: ResearchState = {
        "sub_questions": ["sq1", "sq2"],
        "sections": {
            "sq1": {"status": "approved"},
            "sq2": {"status": "pending"}
        }
    }
    assert route_after_critic(state_critic_loop) == "synthesizer"
    
    # After critic: all finished -> finalize
    state_critic_done: ResearchState = {
        "sub_questions": ["sq1", "sq2"],
        "sections": {
            "sq1": {"status": "approved"},
            "sq2": {"status": "approved"}
        }
    }
    assert route_after_critic(state_critic_done) == "finalize"

if __name__ == "__main__":
    test_should_skip_to_end_after_retriever()
    test_can_revise_section()
    test_determine_final_status()
    test_get_next_sub_question_to_process()
    test_graph_conditional_edges()
    print("All routing unit tests passed successfully!")
