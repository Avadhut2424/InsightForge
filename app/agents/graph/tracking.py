import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import func
from app.db.session import SessionLocal
from app.db.models import ResearchRun, AgentStep, ToolCall, Revision

logger = logging.getLogger(__name__)

def start_research_run(topic: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[int]:
    """Start tracking a research run in the DB. Returns run_id (int) or None if DB fails."""
    try:
        with SessionLocal() as db:
            run = ResearchRun(
                query=topic,
                status="running",
                started_at=datetime.utcnow(),
                metadata_=metadata or {}
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            return run.id
    except Exception as e:
        logger.warning(f"Failed to start tracking research run in DB: {e}")
        return None

def complete_research_run(run_id: Optional[int], final_status: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Mark a research run as finished."""
    if not run_id:
        return
    try:
        with SessionLocal() as db:
            run = db.query(ResearchRun).filter(ResearchRun.id == run_id).first()
            if run:
                run.status = final_status
                run.completed_at = datetime.utcnow()
                if metadata:
                    merged = dict(run.metadata_ or {})
                    merged.update(metadata)
                    run.metadata_ = merged
                db.commit()
    except Exception as e:
        logger.warning(f"Failed to complete research run {run_id} in DB: {e}")

def record_agent_step(
    run_id: Optional[int],
    agent_name: str,
    step_index: Optional[int] = None,
    status: str = "completed",
    started_at: Optional[datetime] = None,
    completed_at: Optional[datetime] = None,
    input_summary: Optional[Dict[str, Any]] = None,
    output_summary: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """Record an individual agent execution step with strictly sequential step_index."""
    if not run_id:
        return None
    try:
        with SessionLocal() as db:
            max_idx = db.query(func.max(AgentStep.step_index)).filter(AgentStep.run_id == run_id).scalar()
            seq_index = (max_idx or 0) + 1
            step = AgentStep(
                run_id=run_id,
                agent_name=agent_name,
                step_index=seq_index,
                status=status,
                started_at=started_at or datetime.utcnow(),
                completed_at=completed_at or datetime.utcnow(),
                input_summary=input_summary or {},
                output_summary=output_summary or {}
            )
            db.add(step)
            db.commit()
            db.refresh(step)
            return step.id
    except Exception as e:
        logger.warning(f"Failed to record agent step in DB: {e}")
        return None

def record_tool_call(
    run_id: Optional[int],
    tool_name: str,
    input_payload: Optional[Dict[str, Any]] = None,
    output_payload: Optional[Dict[str, Any]] = None,
    status: str = "completed",
    duration_ms: Optional[int] = None,
    step_id: Optional[int] = None
) -> Optional[int]:
    """Record a tool execution (e.g. db_lookup.similarity_search) in DB."""
    if not run_id:
        return None
    try:
        with SessionLocal() as db:
            tc = ToolCall(
                run_id=run_id,
                step_id=step_id,
                tool_name=tool_name,
                input_payload=input_payload or {},
                output_payload=output_payload or {},
                status=status,
                called_at=datetime.utcnow(),
                duration_ms=duration_ms
            )
            db.add(tc)
            db.commit()
            db.refresh(tc)
            return tc.id
    except Exception as e:
        logger.warning(f"Failed to record tool call in DB: {e}")
        return None

def record_revision(run_id: Optional[int], revision_number: int, reason: str, sub_question: Optional[str] = None) -> Optional[int]:
    """Record a revision cycle initiated by the Critic with sub-question context."""
    if not run_id:
        return None
    try:
        with SessionLocal() as db:
            formatted_reason = f"[{sub_question}] {reason}" if sub_question else reason
            rev = Revision(
                run_id=run_id,
                revision_number=revision_number,
                reason=formatted_reason,
                created_at=datetime.utcnow()
            )
            db.add(rev)
            db.commit()
            db.refresh(rev)
            return rev.id
    except Exception as e:
        logger.warning(f"Failed to record revision in DB: {e}")
        return None
