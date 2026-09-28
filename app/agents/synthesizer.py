import json
import re
from typing import Dict, Any, List
from app.agents.base import Agent, Task, MemoryStore
from app.core.llm.client import call_llm

def split_sentences(text: str) -> List[str]:
    text = re.sub(r'\s+', ' ', text).strip()
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', text)
    return [s.strip() for s in sentences if s.strip()]

def is_bad_sentence(s: str) -> bool:
    # 1. Drop fragments under 40 characters
    if len(s) < 40:
        return True
    
    # 2. Headings / Table of Contents lines
    if re.match(r'^\d+(\.\d+)*\s+[A-Z]', s) and len(s) < 90:
        return True
    if re.match(r'^[0-9A-Z\s\-]{3,40}$', s) and not any(c in s for c in '.,;:'):
        return True
        
    # 3. Reference list entries / URLs / Citations
    if "http" in s or "doi.org" in s or "www." in s or "sec.gov" in s or "http://" in s or "https://" in s:
        return True
            
    if re.search(r'^[A-Z][a-zA-Z\s\-\.]+(?:\([^)]+\))?\.\s*\(\d{4}[a-z]?\)', s):
        return True
    if re.search(r'^[A-Z][a-z]+,\s+[A-Z]\.,', s):
        return True
    if re.search(r'\b(OECD\.|Research Policy|Science,|Demography,|sec\.gov|Annual Report|OECD Publishing)\b', s):
        return True
    if re.search(r'\(\d{4}[a-z]?\)\.', s) or re.search(r'No\.\s*\d+', s):
        return True
    
    # 4. Email addresses, author/affiliation lines, and Abstract-prefixed title blocks
    if re.search(r'[\w\.-]+@[\w\.-]+\.\w+', s):
        return True
    if re.search(r'\b(Institute of|University of|Department of|Faculty of|School of|Email:)\b', s, re.IGNORECASE):
        return True
    if re.search(r'\bAbstract\b', s) and (any(kw in s for kw in ["Institute", "University", "Email", "Author", "Transformation", "@"]) or len(s) < 120):
        return True
    
    return False

def starts_with_dangling_referent(s: str) -> bool:
    words = s.split()
    if not words:
        return False
    first_word = words[0].rstrip(',.:;!?').lower()
    return first_word in {"this", "these", "it", "they", "such", "those"}

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
        candidates = []
        
        # Sort chunks by distance (assuming smaller is better, default to 0 if not present to prioritize top chunks)
        sorted_chunks = sorted(evidence_chunks, key=lambda c: c.get("distance", 0.0))
        
        for c_idx, chunk in enumerate(sorted_chunks):
            dist = chunk.get("distance", None)
            if dist is not None and dist > 1.35:
                continue

            chunk_num = c_idx + 1
            title = chunk.get("title", f"Source {chunk_num}")
            content = chunk.get("content", chunk.get("snippet", ""))
            
            sentences = split_sentences(content)
            for s_idx, sentence in enumerate(sentences):
                s_id = f"c{chunk_num}-s{s_idx+1}"
                
                if is_bad_sentence(sentence):
                    continue
                    
                if starts_with_dangling_referent(sentence):
                    if s_idx > 0:
                        prev_sentence = sentences[s_idx - 1]
                        if not is_bad_sentence(prev_sentence):
                            final_text = f"{prev_sentence} {sentence}"
                        else:
                            continue
                    else:
                        continue
                else:
                    final_text = sentence
                        
                sentence_map[s_id] = {
                    "text": final_text,
                    "citation": title
                }
                candidates.append((s_id, final_text))
                
        # Limit to top 25 candidates
        candidates = candidates[:25]

        
        numbered_sentences_text = ""
        for s_id, text in candidates:
            numbered_sentences_text += f"[{s_id}] {text}\n"
            
        prompt = (
            f"You are a strict, evidence-based research writer. Your task is to select the most relevant sentences "
            f"that directly help answer the sub-question. You MUST NOT write any text yourself.\n\n"
            f"Sub-question: {topic}\n\n"
        )
        if revision_reason:
            prompt += f"NOTE: This is a revision. The previous draft was rejected for this reason: {revision_reason}. Select sentences that address this issue.\n\n"
            
        prompt += (
            f"Available Sentences:\n{numbered_sentences_text}\n\n"
            f"CRITICAL RULES:\n"
            f"1. Select a maximum of 6 sentence IDs that best answer the question, in a logical order.\n"
            f"2. You MUST output ONLY a JSON list of strings (the sentence IDs, e.g. [\"c1-s3\", \"c2-s1\"]).\n"
            f"3. Do not include markdown formatting or explanation.\n"
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
            draft = "The provided evidence does not contain enough information to fully address this topic."
            sentences = []
        else:
            draft_parts = []
            sentences = []
            for s_id in valid_selections:
                item = sentence_map[s_id]
                draft_parts.append(f"{item['text']} ({item['citation']}).")
                sentences.append({
                    "sentence": item["text"],
                    "citation": item["citation"]
                })
            draft = " ".join(draft_parts)

        return {
            "draft": draft,
            "sentences": sentences,
            "selected_ids": valid_selections
        }

