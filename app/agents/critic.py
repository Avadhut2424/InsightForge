import json
import re
from typing import Dict, Any, List
from app.agents.base import Agent, Task, MemoryStore
from app.core.llm.client import call_llm

class CriticAgent(Agent):
    """
    Evaluates whether the drafted report section answers the sub-question,
    and independently verifies that every sentence is a literal substring of the evidence.
    """
    async def run(self, task: Task, memory: MemoryStore) -> Dict[str, Any]:
        data = task.input_data
        if not isinstance(data, dict) or "draft" not in data or "evidence" not in data:
            raise ValueError("CriticAgent expects input_data to be a dict with 'draft' and 'evidence'")
            
        draft = data["draft"]
        evidence_chunks = data.get("evidence", [])
        
        # We need the sub-question topic for the completeness check
        topic = data.get("topic", "the sub-question")
        
        # a) Literal substring check
        unsupported_sentences = []
        if "The provided evidence does not contain enough information" not in draft:
            parts = draft.split("). ")
            for part in parts:
                if not part.strip():
                    continue
                if part.endswith("."):
                    part = part[:-1]
                if part.endswith(")"):
                    part = part[:-1]
                    
                raw_sentence = part.rsplit(" (", 1)[0].strip()
                if not raw_sentence:
                    continue
                    
                found = False
                for chunk in evidence_chunks:
                    content = chunk.get("content", chunk.get("snippet", ""))
                    content_normalized = re.sub(r'\s+', ' ', content)
                    raw_normalized = re.sub(r'\s+', ' ', raw_sentence)
                    if raw_normalized in content_normalized:
                        found = True
                        break
                        
                if not found:
                    unsupported_sentences.append(raw_sentence)
                    
        if unsupported_sentences:
            return {
                "verdict": "revise",
                "reason": "The following claims are unsupported by the evidence: " + " | ".join(unsupported_sentences)
            }
            
        # b) Completeness check via LLM
        prompt = (
            f"Review the following draft report section and determine if it is on-topic and covers the main point of the sub-question.\n\n"
            f"Sub-question: {topic}\n\n"
            f"Draft:\n{draft}\n\n"
            f"CRITICAL RULES:\n"
            f"1. A partial answer built from cited evidence is acceptable as long as the core of the sub-question is addressed. Do not reject a draft just because it lacks exhaustive detail.\n"
            f"2. You MUST output your response ONLY as a JSON object.\n"
            f"3. The JSON object must have exactly two keys:\n"
            f"   - 'answers': true or false (boolean) depending on whether the draft covers the main thing the sub-question asks.\n"
            f"   - 'missing': A short string phrase explaining what core aspect is missing, or null if nothing is missing.\n"
            f"4. Do not wrap it in markdown block quotes. Output JSON only."
        )
        
        response = await call_llm(role="critic", prompt=prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
            
        try:
            result = json.loads(text.strip())
            answers = result.get("answers", False)
            missing = result.get("missing", None)
        except json.JSONDecodeError:
            answers = False
            missing = "Critic failed to parse JSON output."
            
        if answers:
            return {
                "verdict": "approve",
                "reason": "Draft adequately answers the sub-question."
            }
        else:
            return {
                "verdict": "revise",
                "reason": f"Draft fails to fully answer the sub-question. Missing aspect: {missing}"
            }
