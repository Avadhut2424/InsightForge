import asyncio
from app.db.session import SessionLocal
from app.db.models import AgentStep, ResearchRun
import json

def main():
    db = SessionLocal()
    run = db.query(ResearchRun).filter(ResearchRun.id == 15).first()
    if not run:
        print('Run 15 not found')
        return

    steps = db.query(AgentStep).filter(AgentStep.run_id == 15).order_by(AgentStep.step_index).all()
    
    print(f'Query: {run.query}')
    print('-'*50)
    
    for step in steps:
        if step.agent_name == 'critic_node':
            out = step.output_summary.get('sections', {})
            for sq, sec in out.items():
                if sec.get('verdict') == 'revise':
                    print(f"SQ: {sq}")
                    print(f"Step Index: {step.step_index}")
                    print(f"Verdict: {sec.get('verdict')}")
                    print(f"Reason: {sec.get('reason')}")
                    print(f"Revision Count: {sec.get('revision_count')}")
                    print(f"Draft: {sec.get('assembled_text')}")
                    print('-'*50)

if __name__ == "__main__":
    main()
