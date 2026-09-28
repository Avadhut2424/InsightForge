import asyncio
import json
import os
import sys

# Ensure app is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.agents.critic import CriticAgent
from app.agents.base import Task, MemoryStore

async def main():
    fixture_path = "app/agents/test_fixtures/sample_retrieval.json"
    if not os.path.exists(fixture_path):
        print(f"Fixture {fixture_path} not found.")
        sys.exit(1)
        
    with open(fixture_path, "r", encoding="utf-8") as f:
        evidence = json.load(f)

    topic = "What factors influence annual global industrial robot deployments?"

    draft_a = (
        "542,000 new installations during that year. China accounted for 54 per cent of new deployments, "
        "and the IFR expects annual global installations to exceed 700,000 by 2028 ( IFR, 2025). "
        "These figures establish the scale of factory automation, but they should not be read as a count of fully autonomous AI systems."
    )
    draft_b = (
        "AI is automating routine coding tasks, allowing engineers to focus on complex architecture."
    )
    draft_c = (
        "542,000 new installations during that year. Furthermore, recent secret reports show that AI has completely "
        "replaced 99% of all software engineers as of 2024, causing total global economic collapse."
    )

    critic = CriticAgent()
    memory = MemoryStore()

    print("=== Testing Critic Agent ===")
    
    print("Testing Case (a) Grounded draft...")
    res_a = await critic.run(Task(input_data={"topic": topic, "draft": draft_a, "evidence": evidence}), memory)
    print(f"Verdict: {res_a}")
    if res_a["verdict"] != "approve":
        print("ERROR: Expected approve for Case A")
        sys.exit(1)
        
    print("Testing Case (b) Ungrounded draft...")
    res_b = await critic.run(Task(input_data={"topic": topic, "draft": draft_b, "evidence": evidence}), memory)
    print(f"Verdict: {res_b}")
    if res_b["verdict"] != "revise":
        print("ERROR: Expected revise for Case B")
        sys.exit(1)

    print("Testing Case (c) Fabricated draft...")
    res_c = await critic.run(Task(input_data={"topic": topic, "draft": draft_c, "evidence": evidence}), memory)
    print(f"Verdict: {res_c}")
    if res_c["verdict"] != "revise":
        print("ERROR: Expected revise for Case C")
        sys.exit(1)
        
    print("All tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
