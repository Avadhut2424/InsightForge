from typing import Dict, Any, List
from app.agents.base import Agent, Task, MemoryStore
from app.core.llm.client import call_llm

class SynthesizerAgent(Agent):
    """
    Takes a topic/sub-question and a set of retrieved evidence chunks,
    and synthesizes them into a readable draft report section.
    """
    async def run(self, task: Task, memory: MemoryStore) -> str:
        data = task.input_data
        if not isinstance(data, dict) or "topic" not in data or "evidence" not in data:
            raise ValueError("SynthesizerAgent expects input_data to be a dict with 'topic' and 'evidence'")
            
        topic = data["topic"]
        evidence_chunks = data["evidence"]
        
        evidence_text = ""
        for i, chunk in enumerate(evidence_chunks):
            title = chunk.get("title", "Unknown Source")
            snippet = chunk.get("snippet", "")
            evidence_text += f"--- Evidence {i+1} ({title}) ---\n{snippet}\n\n"
            
        prompt = (
            f"You are a strict, evidence-based research writer. Write a coherent draft report section "
            f"addressing the following topic, using ONLY the provided evidence.\n\n"
            f"Topic: {topic}\n\n"
            f"CRITICAL RULES:\n"
            f"1. You MUST NOT introduce any claims, facts, statistics, or general knowledge that is absent from the provided evidence.\n"
            f"2. Every single sentence you write must be directly traceable to a specific piece of evidence.\n"
            f"3. If the provided evidence is insufficient to answer the topic or lacks relevant details, you MUST state explicitly: 'The provided evidence does not contain enough information to fully address this topic.' Do not attempt to fill in the gaps with your own knowledge.\n"
            f"4. Synthesize the evidence smoothly rather than just listing it.\n\n"
            f"Evidence:\n"
            f"{evidence_text}\n\n"
            f"Draft Section:"
        )
        
        response = await call_llm(role="writer", prompt=prompt)
        return response.text.strip()
