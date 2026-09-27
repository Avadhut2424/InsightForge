import json
from typing import Dict, Any, List
from app.agents.base import Agent, Task, MemoryStore
from app.core.llm.client import call_llm

class CriticAgent(Agent):
    """
    Takes a draft and the evidence it was supposedly built from,
    and returns a structured verdict ("approve" or "revise") with specific reasons.
    """
    async def run(self, task: Task, memory: MemoryStore) -> Dict[str, str]:
        data = task.input_data
        if not isinstance(data, dict) or "draft" not in data or "evidence" not in data:
            raise ValueError("CriticAgent expects input_data to be a dict with 'draft' and 'evidence'")
            
        draft = data["draft"]
        evidence_chunks = data["evidence"]
        
        evidence_text = ""
        for i, chunk in enumerate(evidence_chunks):
            title = chunk.get("title", "Unknown Source")
            snippet = chunk.get("snippet", "")
            evidence_text += f"--- Evidence {i+1} ({title}) ---\n{snippet}\n\n"
            
        prompt = (
            f"You are a strict research critic. Your job is to verify if the provided draft is "
            f"FULLY supported by the provided evidence. \n\n"
            f"Evidence:\n"
            f"{evidence_text}\n\n"
            f"Draft:\n"
            f"{draft}\n\n"
            f"Task:\n"
            f"1. Break the draft down sentence by sentence.\n"
            f"2. Check if EACH sentence introduces ANY claims, facts, or statistics NOT explicitly present in the evidence.\n"
            f"3. If EVEN ONE claim is unsupported or extrapolated from general knowledge, your verdict must be 'revise', and you must provide a specific reason flagging the exact unsupported claim.\n"
            f"4. If and ONLY if ALL claims are completely and explicitly supported by the evidence, your verdict must be 'approve'.\n\n"
            f"Return ONLY a valid JSON object with two keys: 'verdict' (must be exactly 'approve' or 'revise') "
            f"and 'reason' (a string explaining the verdict, focusing on any unsupported claims found). "
            f"Do not include markdown blocks (like ```json), just the raw JSON object."
        )
        
        response = await call_llm(role="critic", prompt=prompt)
        text = response.text.strip()
        
        # Strip markdown formatting
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
            
        try:
            verdict_data = json.loads(text)
            if not isinstance(verdict_data, dict) or "verdict" not in verdict_data or "reason" not in verdict_data:
                raise ValueError("LLM did not return a correct JSON object structure")
            return verdict_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM output as JSON. Output was: {text}") from e
