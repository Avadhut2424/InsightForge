"""
LangGraph state definitions for InsightForge research workflow.
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal

class SentenceCitation(TypedDict):
    sentence: str
    citation: str

class SectionData(TypedDict, total=False):
    draft: List[SentenceCitation]
    assembled_text: str
    verdict: Optional[Literal["approve", "revise"]]
    reason: Optional[str]
    revision_count: int
    status: Literal["pending", "approved", "unverified", "insufficient_evidence"]

class ResearchState(TypedDict, total=False):
    run_id: str
    topic: str
    sub_questions: List[str]
    evidence: Dict[str, List[Dict[str, Any]]]
    sections: Dict[str, SectionData]
    max_revisions: int
    final_status: Literal["approved", "partial", "insufficient_evidence", "failed"]
    critique_history: List[Dict[str, Any]]
    _test_force_critic_revise: Optional[bool]
    _test_synthesizer_override: Optional[Dict[str, Any]]

