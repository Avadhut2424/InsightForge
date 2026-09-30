import asyncio
import logging
from typing import Any, Optional, Dict
from pydantic import BaseModel, ConfigDict
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import func

from app.db.session import SessionLocal
from app.db.models import ResearchRun, AgentStep, Revision
from app.agents.graph.state import ResearchState
from app.agents.graph.graph import graph
from app.agents.graph.tracking import start_research_run, complete_research_run

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Research"])

# Serial lock to ensure sequential runs inside container
_run_lock = asyncio.Lock()

class ResearchCreateRequest(BaseModel):
    topic: Any = None
    model_config = ConfigDict(extra="ignore")

async def _execute_research_workflow(run_id: int, topic: str):
    """
    Background worker that runs the LangGraph workflow.
    Guarantees sequential execution via _run_lock and handles all uncaught exceptions
    by marking the DB row as failed with error details.
    """
    async with _run_lock:
        logger.info(f"Starting research workflow: run_id={run_id}, topic={topic!r}")
        initial_state: ResearchState = {
            "run_id": str(run_id),
            "topic": topic,
            "sub_questions": [],
            "evidence": {},
            "sections": {},
            "max_revisions": 1,
            "final_status": "partial",
            "critique_history": []
        }
        try:
            await graph.ainvoke(initial_state)
            logger.info(f"Research workflow finished for run_id={run_id}")
        except Exception as e:
            logger.exception(f"Unhandled error during research execution for run_id={run_id}: {e}")
            complete_research_run(
                run_id=run_id,
                final_status="failed",
                metadata={"error": str(e), "error_type": type(e).__name__}
            )

@router.post("/research", status_code=status.HTTP_202_ACCEPTED, summary="Initiate Research Run")
async def create_research_run(request: ResearchCreateRequest, background_tasks: BackgroundTasks):
    """
    Submits a research topic for execution via the LangGraph workflow.
    Fast, deterministic input validation occurs before any database or LLM call.
    Returns 202 Accepted with run_id and status='running'.
    """
    # 1. Edge validation (fast, deterministic, LLM-free)
    if not isinstance(request.topic, str) or not request.topic.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic cannot be empty or whitespace only."
        )
    
    clean_topic = request.topic.strip()
    if len(clean_topic) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic is too short. Minimum length is 3 characters."
        )
    if len(clean_topic) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic is too long. Maximum allowed length is 500 characters."
        )

    # 2. Initialize tracking in DB (ResearchRun with status='running')
    run_id = start_research_run(topic=clean_topic, metadata={"entrypoint": "api"})
    if not run_id:
        logger.error("Failed to insert research run into database.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize research run in database."
        )

    # 3. Dispatch sequential background execution
    background_tasks.add_task(_execute_research_workflow, run_id=run_id, topic=clean_topic)

    # 4. Immediate 202 Accepted response
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"run_id": run_id, "status": "running"}
    )

@router.get("/research/{run_id}", summary="Get Research Run Status & Report")
async def get_research_run(run_id: int):
    """
    Polls the current status or fetches the final report for a given research run.
    Surfaces 'approved', 'partial', and 'insufficient_evidence' honest outcomes.
    Returns 404 if the run_id does not exist, and 500 with a safe message if the run failed.
    """
    with SessionLocal() as db:
        run = db.query(ResearchRun).filter(ResearchRun.id == run_id).first()
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research run {run_id} not found."
            )

        status_val = run.status
        topic_val = run.query
        started_at_str = run.started_at.isoformat() if run.started_at else None
        completed_at_str = run.completed_at.isoformat() if run.completed_at else None
        meta = dict(run.metadata_ or {})

        # If run is still actively running
        if status_val == "running":
            steps_count = db.query(func.count(AgentStep.id)).filter(AgentStep.run_id == run_id).scalar() or 0
            revisions_count = db.query(func.count(Revision.id)).filter(Revision.run_id == run_id).scalar() or 0
            return {
                "run_id": run.id,
                "topic": topic_val,
                "status": "running",
                "started_at": started_at_str,
                "completed_at": None,
                "summary": {
                    "steps_completed": steps_count,
                    "revision_count": revisions_count
                },
                "report": None
            }

        # If run encountered an unhandled exception or crash
        if status_val == "failed":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Research execution failed due to an internal service error."
            )

        # Terminal outcomes: approved, partial, insufficient_evidence
        sections_meta = meta.get("sections", {})
        total_sq = len(sections_meta)
        approved_cnt = sum(1 for s in sections_meta.values() if s.get("status") == "approved")
        unverified_cnt = sum(1 for s in sections_meta.values() if s.get("status") == "unverified")
        insufficient_cnt = sum(1 for s in sections_meta.values() if s.get("status") == "insufficient_evidence")
        total_revs = sum(s.get("revision_count", 0) for s in sections_meta.values())

        summary = {
            "total_sub_questions": total_sq,
            "approved_sections": approved_cnt,
            "unverified_sections": unverified_cnt,
            "insufficient_evidence_sections": insufficient_cnt,
            "total_revisions": total_revs
        }

        response_payload = {
            "run_id": run.id,
            "topic": topic_val,
            "status": status_val,
            "started_at": started_at_str,
            "completed_at": completed_at_str,
            "summary": summary,
            "sections": sections_meta
        }

        if status_val == "insufficient_evidence":
            response_payload["explanation"] = (
                "No sufficiently grounded evidence was found in the knowledge base for this topic. "
                "All sub-questions failed retrieval thresholds."
            )
        elif status_val == "partial":
            response_payload["explanation"] = (
                f"Research completed partially: {unverified_cnt} section(s) unverified (revision cap reached) "
                f"and {insufficient_cnt} section(s) with insufficient evidence."
            )

        return response_payload
