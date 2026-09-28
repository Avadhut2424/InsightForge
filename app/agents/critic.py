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
        if not isinstance(data, dict) or ("draft" not in data and "sentences" not in data) or "evidence" not in data:
            raise ValueError("CriticAgent expects input_data to be a dict with 'draft' (or 'sentences') and 'evidence'")
            
        draft_input = data.get("draft")
        evidence_chunks = data.get("evidence", [])
        topic = data.get("topic", "the sub-question")
        
        # Priority 1: Direct 'sentences' list in data or inside draft dict/list
        sentence_items = []
        if "sentences" in data and isinstance(data["sentences"], list):
            sentence_items = data["sentences"]
        elif isinstance(draft_input, dict) and "sentences" in draft_input and isinstance(draft_input["sentences"], list):
            sentence_items = draft_input["sentences"]
        elif isinstance(draft_input, list):
            sentence_items = draft_input
            
        if sentence_items:
            sentences_to_check = [
                item["sentence"] if isinstance(item, dict) and "sentence" in item else str(item)
                for item in sentence_items
            ]
            if isinstance(draft_input, dict) and "draft" in draft_input:
                draft_text = str(draft_input["draft"])
            else:
                draft_text = " ".join(sentences_to_check)
        else:
            draft_text = str(draft_input or "")
            sentences_to_check = []
            if "The provided evidence does not contain enough information" not in draft_text:
                raw_splits = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', draft_text.strip())
                for s in raw_splits:
                    s_clean = s.strip()
                    if not s_clean or len(s_clean) < 15:
                        continue
                    # Strip citation at end of sentence if present (e.g. " (Source)."), keeping any internal parentheticals
                    s_clean = re.sub(r'\s*\([A-Za-z0-9\s,\.\-–—\']+\)\.?$', '', s_clean).strip()
                    sentences_to_check.append(s_clean)
        
        # a) Literal substring check (per sentence)
        unsupported_sentences = []
        if "The provided evidence does not contain enough information" not in draft_text:
            for s_clean in sentences_to_check:
                if not s_clean or len(s_clean) < 15:
                    continue
                s_norm = re.sub(r'\s+', ' ', s_clean)
                
                found = False
                for chunk in evidence_chunks:
                    content = chunk.get("content", chunk.get("snippet", ""))
                    content_norm = re.sub(r'\s+', ' ', content)
                    if s_norm in content_norm:
                        found = True
                        break
                        
                if not found:
                    unsupported_sentences.append(s_clean)
                    
        if unsupported_sentences:
            return {
                "verdict": "revise",
                "reason": "The following claims are unsupported by the evidence: " + " | ".join(unsupported_sentences)
            }
            
        # b) Completeness check via LLM
        prompt = (
            f"Evaluate if the following draft report section is on-topic and addresses the core sub-question.\n\n"
            f"Sub-question: {topic}\n\n"
            f"Draft:\n{draft_text}\n\n"
            f"EVALUATION INSTRUCTIONS:\n"
            f"1. Set 'answers' to true if the draft is on-topic and directly covers the main topic asked by the sub-question. A partial answer built from cited evidence is acceptable as long as the core is covered.\n"
            f"2. Set 'answers' to false if the draft is off-topic, discusses a different subject, or contains only general background without addressing the main question.\n"
            f"3. Return ONLY a JSON object with keys 'answers' (boolean) and 'missing' (string or null).\n"
            f"Example valid JSON:\n"
            f'{{"answers": true, "missing": null}}\n'
        )
        
        response = await call_llm(
            role="critic",
            prompt=prompt,
            response_format={"type": "json_object"}
        )
        text = response.text.strip()
        
        try:
            cleaned_text = text
            if "```json" in cleaned_text:
                cleaned_text = cleaned_text.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_text:
                cleaned_text = cleaned_text.split("```")[1].split("```")[0].strip()
                
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                cleaned_text = json_match.group(0)
                
            result = json.loads(cleaned_text)
            if not isinstance(result, dict) or "answers" not in result:
                raise ValueError("critic output unparseable")
                
            answers = bool(result["answers"])
            missing = result.get("missing", None)
        except Exception:
            return {
                "verdict": "revise",
                "reason": "critic output unparseable"
            }
            
        if answers:
            return {
                "verdict": "approve",
                "reason": "Draft adequately answers the sub-question."
            }
        else:
            reason_msg = "Draft fails to fully answer the sub-question."
            if missing:
                reason_msg += f" Missing aspect: {missing}"
            return {
                "verdict": "revise",
                "reason": reason_msg
            }

