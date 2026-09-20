import sys
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "").replace("db:5432", "localhost:5432")

from app.db.session import SessionLocal
from app.db.models import KBChunk, ResearchRun, AgentStep, ToolCall, Revision

def test_db():
    db = SessionLocal()
    try:
        # Create Research Run
        run = ResearchRun(status="pending", query="Test Query")
        db.add(run)
        db.commit()
        db.refresh(run)
        print(f"Created ResearchRun: id={run.id}, status={run.status}")

        # Create Agent Step
        step = AgentStep(run_id=run.id, agent_name="planner", step_index=0, status="completed")
        db.add(step)
        db.commit()
        db.refresh(step)
        print(f"Created AgentStep: id={step.id}, agent_name={step.agent_name}")

        # Create Tool Call
        tool_call = ToolCall(run_id=run.id, step_id=step.id, tool_name="search", status="success")
        db.add(tool_call)
        db.commit()
        db.refresh(tool_call)
        print(f"Created ToolCall: id={tool_call.id}, tool_name={tool_call.tool_name}")

        # Create Revision
        revision = Revision(run_id=run.id, revision_number=1, reason="Test reason")
        db.add(revision)
        db.commit()
        db.refresh(revision)
        print(f"Created Revision: id={revision.id}, reason={revision.reason}")

        # Create KB Chunk
        dummy_vector = [0.1] * 1536
        chunk = KBChunk(content="Test content", embedding=dummy_vector, source_name="Test doc", chunk_index=0)
        db.add(chunk)
        db.commit()
        db.refresh(chunk)
        print(f"Created KBChunk: id={chunk.id}, source={chunk.source_name}, vector_dim={len(chunk.embedding)}")
        print("All schema operations successful!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    test_db()
