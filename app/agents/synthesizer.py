import json
import re
from typing import Dict, Any, List
from app.agents.base import Agent, Task, MemoryStore
from app.core.llm.client import call_llm

def get_critical_tokens(txt: str):
    toks = set()
    clean_txt = txt.replace(",", "")
    toks.update(re.findall(r'\b\d+\b', clean_txt))
    toks.update(a.lower() for a in re.findall(r'\b[A-Z]{2,}\b', txt))
    toks.update(p.lower() for p in re.findall(r'\b[A-Z][a-z]+\b', txt))
    special = {'not', 'no', 'never', 'without', 'cannot', 'may', 'might', 'will', 'expects', 'could'}
    for w in re.findall(r'\b\w+\b', txt.lower()):
        if w in special:
            toks.add(w)
    if re.search(r"n't\b", txt.lower()):
        toks.add("not")
    return toks

def has_neg(txt: str):
    neg_words = {'not', 'no', 'never', 'without', 'cannot'}
    if re.search(r"n't\b", txt.lower()):
        return True
    return any(w in neg_words for w in re.findall(r'\b\w+\b', txt.lower()))

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
        chunk_map = {}
        for i, chunk in enumerate(evidence_chunks):
            chunk_id = f"chunk_{i+1}"
            title = chunk.get("title", "Unknown Source")
            content = chunk.get("content", chunk.get("snippet", ""))
            chunk_map[chunk_id] = content
            evidence_text += f"--- {chunk_id} ({title}) ---\\n{content}\\n\\n"
            
        prompt = (
            f"You are a strict, evidence-based research writer. Write a coherent draft report section "
            f"addressing the following topic, using ONLY the provided evidence.\\n\\n"
            f"Topic: {topic}\\n\\n"
            f"CRITICAL RULES:\\n"
            f"1. You MUST NOT introduce any claims, facts, statistics, or general knowledge that is absent from the provided evidence.\\n"
            f"2. Every single sentence you write must be directly traceable to a specific piece of evidence.\\n"
            f"3. You MUST output your response ONLY as a JSON list of objects. Do not wrap it in markdown block quotes. Each object represents one sentence in your draft and must have:\\n"
            f"   - 'sentence': The text of the sentence.\\n"
            f"   - 'chunk_id': The ID of the chunk that supports it (e.g. 'chunk_1'). If unsupported, use null.\\n"
            f"   - 'quote': A literal, verbatim substring from the chunk (max 250 chars) that proves the sentence.\\n"
            f"4. Synthesize the evidence smoothly rather than just listing it.\\n\\n"
            f"Evidence:\\n"
            f"{evidence_text}\\n\\n"
            f"Output JSON only:"
        )
        
        response = await call_llm(role="writer", prompt=prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        
        try:
            draft_items = json.loads(text)
        except json.JSONDecodeError:
            return "Error: Synthesizer did not output valid JSON."
            
        final_draft = []
        for item in draft_items:
            sentence = item.get("sentence", "")
            chunk_id = item.get("chunk_id")
            quote = item.get("quote", "")
            
            is_supported = True
            if not chunk_id or chunk_id not in chunk_map:
                is_supported = False
            else:
                chunk_content = chunk_map[chunk_id]
                normalized_quote = re.sub(r'\\s+', '', str(quote).lower())
                normalized_content = re.sub(r'\\s+', '', chunk_content.lower())
                
                if not quote or normalized_quote not in normalized_content:
                    is_supported = False
                elif len(str(quote)) > 250:
                    is_supported = False
                else:
                    stripped_quote = re.sub(r'\\([^)]*\\)', '', str(quote))
                    sent_tokens = get_critical_tokens(sentence)
                    quote_lower = stripped_quote.lower()
                    quote_clean = quote_lower.replace(",", "")
                    
                    for t in sent_tokens:
                        if t not in quote_clean and t not in quote_lower:
                            if t.endswith('s') and t[:-1] in quote_lower:
                                continue
                            is_supported = False
                            break
                            
                    if is_supported:
                        if has_neg(sentence) != has_neg(stripped_quote):
                            is_supported = False
                            
            if is_supported:
                final_draft.append(sentence)
            else:
                final_draft.append(f"[UNSUPPORTED: {sentence}]")
                
        return " ".join(final_draft)
