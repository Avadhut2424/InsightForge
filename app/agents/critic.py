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
            content = chunk.get("content", chunk.get("snippet", ""))
            evidence_text += f"--- Evidence {i+1} ({title}) ---\\n{content}\\n\\n"
            
        import re
        # Basic sentence splitting (naive, but enough for this check)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', draft) if s.strip()]
        
        unsupported_sentences = []
        
        for sentence in sentences:
            prompt = (
                f"You are a strict research critic. Determine if the following sentence is supported by the evidence.\\n\\n"
                f"Evidence:\\n{evidence_text}\\n"
                f"Sentence:\\n{sentence}\\n\\n"
                f"If the sentence is supported, extract the EXACT substring from the evidence that supports it.\\n"
                f"Return a JSON object: {{\"supported\": true/false, \"evidence_quote\": \"<exact quote or null>\"}}."
            )
            
            response = await call_llm(
                role="critic", 
                prompt=prompt,
                response_format={"type": "json_object"}
            )
            
            try:
                result = json.loads(response.text.strip())
                is_supported = result.get("supported", False)
                quote = result.get("evidence_quote")
            except Exception:
                is_supported = False
                quote = None
                
            # If the LLM says supported, verify the quote actually exists in the evidence text (case-insensitive for safety)
            if is_supported:
                if not quote:
                    is_supported = False
                else:
                    normalized_quote = re.sub(r'\s+', '', str(quote).lower())
                    normalized_evidence = re.sub(r'\s+', '', evidence_text.lower())
                    if normalized_quote not in normalized_evidence:
                        is_supported = False
                        
            import os
            if is_supported and os.environ.get("STRICT_CRITIC") == "1":
                # a) Quote length cap
                if len(str(quote)) > 250:
                    is_supported = False
                else:
                    # b) Strip citations
                    stripped_quote = re.sub(r'\([^)]*\)', '', str(quote))
                    
                    # c/d) Claim-critical token check
                    def get_critical_tokens(txt: str):
                        toks = set()
                        # numbers (strip commas)
                        clean_txt = txt.replace(",", "")
                        toks.update(re.findall(r'\b\d+\b', clean_txt))
                        # acronyms
                        toks.update(a.lower() for a in re.findall(r'\b[A-Z]{2,}\b', txt))
                        # capitalized proper nouns
                        toks.update(p.lower() for p in re.findall(r'\b[A-Z][a-z]+\b', txt))
                        # negations and hedges
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
                        
                    sent_tokens = get_critical_tokens(sentence)
                    quote_lower = stripped_quote.lower()
                    quote_clean = quote_lower.replace(",", "")
                    
                    for t in sent_tokens:
                        # light normalization: just check substring in cleaned quote
                        if t not in quote_clean and t not in quote_lower:
                            # try stripping plural 's'
                            if t.endswith('s') and t[:-1] in quote_lower:
                                continue
                            is_supported = False
                            break
                    
                    # Reverse negation check
                    if is_supported:
                        if has_neg(sentence) != has_neg(stripped_quote):
                            is_supported = False
            
            if not is_supported:
                unsupported_sentences.append(sentence)
                
        if unsupported_sentences:
            return {
                "verdict": "revise",
                "reason": f"The following claims are unsupported by the evidence: {' | '.join(unsupported_sentences)}"
            }
        else:
            return {
                "verdict": "approve",
                "reason": "All claims are supported by the provided evidence."
            }
