import json
import re
from typing import Dict, Any, List
from app.agents.base import Agent, Task, MemoryStore
from app.core.llm.client import call_llm

def split_sentences(text: str) -> List[str]:
    # Basic sentence splitter
    text = re.sub(r'\\s+', ' ', text).strip()
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', text)
    return [s.strip() for s in sentences if s.strip()]

class SynthesizerAgent(Agent):
    """
    Selects relevant sentences from evidence and assembles them into a grounded draft.
    """
    async def run(self, task: Task, memory: MemoryStore) -> str:
        data = task.input_data
        if not isinstance(data, dict) or "topic" not in data or "evidence" not in data:
            raise ValueError("SynthesizerAgent expects input_data to be a dict with 'topic' and 'evidence'")
            
        topic = data["topic"]
        evidence_chunks = data["evidence"]
        revision_reason = data.get("revision", None)
        
        sentence_map = {}
        numbered_sentences_text = ""
        
        for c_idx, chunk in enumerate(evidence_chunks):
            chunk_num = c_idx + 1
            title = chunk.get("title", f"Source {chunk_num}")
            content = chunk.get("content", chunk.get("snippet", ""))
            
            sentences = split_sentences(content)
            for s_idx, sentence in enumerate(sentences):
                s_id = f"c{chunk_num}-s{s_idx+1}"
                sentence_map[s_id] = {
                    "text": sentence,
                    "citation": title
                }
                numbered_sentences_text += f"[{s_id}] {sentence}\\n"
                
        prompt = (
            f"You are a strict, evidence-based research writer. Your task is to select the most relevant sentences "
            f"that directly help answer the sub-question. You MUST NOT write any text yourself.\\n\\n"
            f"Sub-question: {topic}\\n\\n"
        )
        if revision_reason:
            prompt += f"NOTE: This is a revision. The previous draft was rejected for this reason: {revision_reason}. Select sentences that address this issue.\\n\\n"
            
        prompt += (
            f"Available Sentences:\\n{numbered_sentences_text}\\n\\n"
            f"CRITICAL RULES:\\n"
            f"1. Select a maximum of 6 sentence IDs that best answer the question, in a logical order.\\n"
            f"2. You MUST output ONLY a JSON list of strings (the sentence IDs, e.g. [\"c1-s3\", \"c2-s1\"]).\\n"
            f"3. Do not include markdown formatting or explanation.\\n"
        )
        
        response = await call_llm(role="writer", prompt=prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
            
        try:
            selected_ids = json.loads(text.strip())
            if not isinstance(selected_ids, list):
                selected_ids = []
        except Exception:
            selected_ids = []
            
        valid_selections = []
        for s_id in selected_ids:
            if s_id in sentence_map:
                valid_selections.append(s_id)
                
        if len(valid_selections) < 2:
            return "The provided evidence does not contain enough information to fully address this topic."
            
        draft_parts = []
        for s_id in valid_selections:
            item = sentence_map[s_id]
            draft_parts.append(f"{item['text']} ({item['citation']}).")
            
        return " ".join(draft_parts)
