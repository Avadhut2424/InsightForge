import logging
from datetime import datetime
from typing import Optional, Dict, Any
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
    step_index: int,
    status: str,
    started_at: datetime,
    completed_at: datetime,
    input_summary: Optional[Dict[str, Any]] = None,
    output_summary: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """Record an individual agent execution step."""
    if not run_id:
        return None
    try:
        with SessionLocal() as db:
            step = AgentStep(
                run_id=run_id,
                agent_name=agent_name,
                step_index=step_index,
                status=status,
                started_at=started_at,
                completed_at=completed_at,
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

def record_revision(run_id: Optional[int], revision_number: int, reason: str) -> Optional[int]:
    """Record a revision cycle initiated by the Critic."""
    if not run_id:
        return None
    try:
        with SessionLocal() as db:
            rev = Revision(
                run_id=run_id,
                revision_number=revision_number,
                reason=reason,
                created_at=datetime.utcnow()
            )
            db.add(rev)
            db.commit()
            db.refresh(rev)
            return rev.id
    except Exception as e:
        logger.warning(f"Failed to record revision in DB: {e}")
        return None
