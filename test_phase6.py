import asyncio
import json
import os
import sys

# Ensure app is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.base import Task, MemoryStore
from app.agents.planner import PlannerAgent
from app.agents.retriever import RetrieverAgent
from app.agents.synthesizer import SynthesizerAgent
from app.agents.critic import CriticAgent

async def main():
    print("=== Testing Planner Agent ===")
    planner = PlannerAgent()
    topics = [
        "The economic impact of AI on software engineering jobs",
        "Environmental consequences of training large language models",
        "The history of Renaissance art in Italy"
    ]
    
    sub_questions = []
    memory = MemoryStore()
    
    for i, topic in enumerate(topics):
        task = Task(input_data=topic)
        try:
            result = await planner.run(task, memory)
            print(f"Topic {i+1}: {topic}")
            print(f"Sub-questions: {json.dumps(result, indent=2)}\n")
            if i == 0:
                sub_questions = result
        except Exception as e:
            print(f"Planner error on topic '{topic}': {e}")
            
    print("=== Testing Retriever Agent ===")
    retriever = RetrieverAgent()
    retrieved_results = []
    
    test_qs = sub_questions[:3] if len(sub_questions) >= 3 else sub_questions
    for i, sq in enumerate(test_qs):
        task = Task(input_data=sq)
        try:
            result = await retriever.run(task, memory)
            print(f"Sub-question {i+1}: {sq}")
            print(f"Retrieved {len(result)} chunks.")
            for j, chunk in enumerate(result):
                print(f"  Chunk {j+1}: {chunk.get('title')} - {chunk.get('snippet', '')[:100]}...")
            print()
            if i == 0:
                retrieved_results = result
        except Exception as e:
            print(f"Retriever error on sub-question '{sq}': {e}")
            
    # Save fixture
    os.makedirs("app/agents/test_fixtures", exist_ok=True)
    fixture_path = "app/agents/test_fixtures/sample_retrieval.json"
    with open(fixture_path, "w", encoding="utf-8") as f:
        json.dump(retrieved_results, f, indent=2)
    print(f"Saved retrieval fixture to {fixture_path}\n")
    
    print("=== Testing Synthesizer Agent ===")
    synthesizer = SynthesizerAgent()
    
    synth_task = Task(input_data={
        "topic": test_qs[0] if test_qs else "Unknown Topic",
        "evidence": retrieved_results
    })
    try:
        draft = await synthesizer.run(synth_task, memory)
        print(f"Draft for '{test_qs[0] if test_qs else ''}':\n{draft}\n")
        
        # Save well-supported draft fixture
        well_supported_draft_path = "app/agents/test_fixtures/draft_well_supported.txt"
        with open(well_supported_draft_path, "w", encoding="utf-8") as f:
            f.write(draft)
            
        # Fabricate flawed draft
        flawed_draft = draft + "\n\nFurthermore, recent studies explicitly show that AI has completely replaced 99% of all software engineers as of 2024, causing a total global economic collapse."
        flawed_draft_path = "app/agents/test_fixtures/draft_flawed.txt"
        with open(flawed_draft_path, "w", encoding="utf-8") as f:
            f.write(flawed_draft)
    except Exception as e:
        print(f"Synthesizer error: {e}")
        draft = ""
        flawed_draft = ""
        
    if draft and flawed_draft:
        print("=== Testing Critic Agent ===")
        critic = CriticAgent()
        
        print("Testing well-supported draft...")
        critic_task_good = Task(input_data={
            "draft": draft,
            "evidence": retrieved_results
        })
        try:
            verdict_good = await critic.run(critic_task_good, memory)
            print(f"Verdict: {json.dumps(verdict_good, indent=2)}\n")
        except Exception as e:
            print(f"Critic error on good draft: {e}")
        
        print("Testing flawed draft...")
        critic_task_flawed = Task(input_data={
            "draft": flawed_draft,
            "evidence": retrieved_results
        })
        try:
            verdict_flawed = await critic.run(critic_task_flawed, memory)
            print(f"Verdict: {json.dumps(verdict_flawed, indent=2)}\n")
        except Exception as e:
            print(f"Critic error on flawed draft: {e}")

if __name__ == "__main__":
    asyncio.run(main())
