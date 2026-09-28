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

    draft_a = (
        "542,000 new installations during that year (Source name)."
    )
    draft_b = (
        "AI is automating routine coding tasks, allowing engineers to focus on complex architecture (Source Name)."
    )
    draft_c = (
        "The provided evidence suggests that AI adoption is increasing. Recent studies explicitly show "
        "that AI has completely replaced 99% of all software engineers as of 2024, causing a total global economic collapse."
    )

    critic = CriticAgent()
    memory = MemoryStore()

    print("=== Testing Critic Agent ===")
    
    print("Testing Case (a) Grounded draft...")
    res_a = await critic.run(Task(input_data={"draft": draft_a, "evidence": evidence}), memory)
    print(f"Verdict: {res_a}")
    if res_a["verdict"] != "approve":
        print("ERROR: Expected approve for Case A")
        sys.exit(1)
        
    print("Testing Case (b) Ungrounded draft...")
    res_b = await critic.run(Task(input_data={"draft": draft_b, "evidence": evidence}), memory)
    print(f"Verdict: {res_b}")
    if res_b["verdict"] != "revise":
        print("ERROR: Expected revise for Case B")
        sys.exit(1)

    print("Testing Case (c) Fabricated draft...")
    res_c = await critic.run(Task(input_data={"draft": draft_c, "evidence": evidence}), memory)
    print(f"Verdict: {res_c}")
    if res_c["verdict"] != "revise":
        print("ERROR: Expected revise for Case C")
        sys.exit(1)
        
    print("All tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
