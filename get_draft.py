from app.db.session import SessionLocal
from app.db.models import AgentStep
import json

db = SessionLocal()
steps = db.query(AgentStep).filter(AgentStep.run_id == 15, AgentStep.agent_name == 'critic').order_by(AgentStep.step_index).all()
for s in steps:
    print(f"Step {s.step_index}")
    # print full output summary
    print(json.dumps(s.output_summary, indent=2))
    break
