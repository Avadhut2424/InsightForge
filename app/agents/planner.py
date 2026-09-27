import json
from typing import List
from app.agents.base import Agent, Task, MemoryStore
from app.core.llm.client import call_llm

class PlannerAgent(Agent):
    """
    Takes a research topic and breaks it down into a structured list of sub-questions.
    """
    async def run(self, task: Task, memory: MemoryStore) -> List[str]:
        topic = task.input_data
        if not isinstance(topic, str):
            raise ValueError("PlannerAgent expects a string topic as input")
            
        prompt = (
            f"You are a research planner. Break down the following topic into 3-6 well-scoped, "
            f"non-redundant sub-questions that collectively cover the topic comprehensively.\n\n"
            f"Topic: {topic}\n\n"
            f"Return ONLY a valid JSON array of strings containing the sub-questions. "
            f"Do not include markdown code blocks (like ```json), just the raw JSON array."
        )
        
        response = await call_llm(role="planner", prompt=prompt)
        text = response.text.strip()
        
        # Strip markdown formatting if the model still includes it
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
            
        try:
            sub_questions = json.loads(text)
            if not isinstance(sub_questions, list):
                raise ValueError("LLM did not return a JSON array")
            return sub_questions
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM output as JSON. Output was: {text}") from e
