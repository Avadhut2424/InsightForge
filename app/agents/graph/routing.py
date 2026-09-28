"""
Pure routing and decision functions for InsightForge LangGraph workflow.
Contains no side-effects or external dependencies so they can be unit-tested directly.
"""

from typing import Dict, List, Optional
from app.agents.graph.state import ResearchState, SectionData

def should_skip_to_end_after_retriever(sections: Dict[str, SectionData]) -> bool:
    """
    Returns True if ALL sub-questions have insufficient evidence.
    """
    if not sections:
        return True
    return all(s.get("status") == "insufficient_evidence" for s in sections.values())

def can_revise_section(section: SectionData, max_revisions: int = 1) -> bool:
    """
    Returns True if the section verdict is 'revise' and revision_count < max_revisions.
    """
    if section.get("verdict") != "revise":
        return False
    return section.get("revision_count", 0) < max_revisions

def determine_final_status(sections: Dict[str, SectionData]) -> str:
    """
    Computes overall final status:
    - 'insufficient_evidence' if all sections have insufficient evidence.
    - 'approved' if all sections are approved.
    - 'partial' if at least one is approved or unverified or insufficient, but not all approved.
    - 'failed' if no sections exist.
    """
    if not sections:
        return "failed"
    
    statuses = [s.get("status") for s in sections.values()]
    
    if all(st == "insufficient_evidence" for st in statuses):
        return "insufficient_evidence"
    
    if all(st == "approved" for st in statuses):
        return "approved"
    
    # If any section is unverified or insufficient_evidence, or mixed approved/unverified:
    return "partial"

def get_next_sub_question_to_process(sub_questions: List[str], sections: Dict[str, SectionData]) -> Optional[str]:
    """
    Returns the next sub-question that needs processing:
    First priority: a section that needs revision ('needs_revision').
    Second priority: a pending sub-question ('pending').
    Returns None if all sub-questions are in a terminal section state
    ('approved', 'unverified', or 'insufficient_evidence').
    """
    # 1. Any section waiting for revision pass
    for sq in sub_questions:
        sec = sections.get(sq, {})
        if sec.get("status") == "needs_revision":
            return sq
            
    # 2. Any section waiting for initial pass
    for sq in sub_questions:
        sec = sections.get(sq, {})
        if sec.get("status") == "pending":
            return sq
            
    return None

def route_after_retriever(state: ResearchState) -> str:
    """
    Conditional routing after retriever node.
    If all sub-questions have insufficient evidence, skip directly to finalize.
    Otherwise proceed to synthesizer.
    """
    sections = state.get("sections", {})
    if should_skip_to_end_after_retriever(sections):
        return "finalize"
    return "synthesizer"

def route_after_critic(state: ResearchState) -> str:
    """
    Conditional routing after critic node.
    If any sub-question needs revision or is pending, loop back to synthesizer.
    Otherwise, if all sections have finished, route to finalize.
    """
    sub_questions = state.get("sub_questions", [])
    sections = state.get("sections", {})
    next_sq = get_next_sub_question_to_process(sub_questions, sections)
    if next_sq is not None:
        return "synthesizer"
    return "finalize"
