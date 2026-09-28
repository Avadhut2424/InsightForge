"""
Item 4: Revision control comparison across 3 sub-questions.
Forces a poor first pass (background-only selection), then runs the second
Synthesizer pass twice:
- Option A: WITH the Critic's missing note
- Option B: WITHOUT the Critic's missing note (plain re-run)
Compares selected IDs and Critic verdicts.
"""

import sys
import asyncio
from app.agents.graph.state import ResearchState
from app.agents.graph.nodes import retriever_node, synthesizer_node, critic_node
from app.core.llm.client import call_llm
from app.agents.synthesizer import split_sentences, is_bad_sentence, starts_with_dangling_referent
from app.agents.critic import CriticAgent
from app.agents.base import Task

SUB_QUESTIONS = [
    "What are the primary environmental impacts of AI adoption, and how do they vary across different industries and applications?",
    "How do AI-driven automation and efficiency gains affect the labor market, and what are the resulting economic implications for workers and businesses?",
    "What are the long-term economic benefits and costs of investing in AI research and development, and how do they compare to traditional forms of economic growth?"
]

# Background-only sentences from chunk 4 that discuss general debate/framing without directly answering
BG_IDS = ["c4-s2", "c4-s3", "c4-s4"]

async def synthesize_single_sq(sq, chunks, revision_reason=None):
    """Runs synthesizer selection logic for a single sub-question with or without revision reason."""
    sentence_map = {}
    candidates = []
    sorted_chunks = sorted(chunks, key=lambda c: c.get("distance", 0.0))
    
    for c_idx, chunk in enumerate(sorted_chunks):
        chunk_num = c_idx + 1
        title = chunk.get("title", f"Source {chunk_num}")
        content = chunk.get("content", chunk.get("snippet", ""))
        sentences = split_sentences(content)
        for s_idx, sentence in enumerate(sentences):
            s_id = f"c{chunk_num}-s{s_idx+1}"
            if is_bad_sentence(sentence):
                continue
            if starts_with_dangling_referent(sentence):
                if s_idx > 0 and not is_bad_sentence(sentences[s_idx - 1]):
                    final_text = f"{sentences[s_idx - 1]} {sentence}"
                else:
                    continue
            else:
                final_text = sentence
            sentence_map[s_id] = {"text": final_text, "citation": title}
            candidates.append((s_id, final_text))
            
    candidates = candidates[:25]
    numbered_sentences_text = "".join(f"[{s_id}] {text}\n" for s_id, text in candidates)
    
    prompt = (
        f"You are a strict, evidence-based research writer. Your task is to select the most relevant sentences "
        f"that directly help answer the sub-question. You MUST NOT write any text yourself.\n\n"
        f"Sub-question: {sq}\n\n"
    )
    if revision_reason:
        prompt += f"NOTE: This is a revision pass. The previous draft was rejected for this reason: {revision_reason}. Select sentences that address this missing aspect.\n\n"
        
    prompt += (
        f"Available Sentences:\n{numbered_sentences_text}\n\n"
        f"CRITICAL RULES:\n"
        f"1. Select a maximum of 6 sentence IDs that best answer the question, in a logical order.\n"
        f"2. You MUST output ONLY a JSON list of strings (the sentence IDs, e.g. [\"c1-s3\", \"c2-s1\"]).\n"
        f"3. Do not include markdown formatting or explanation.\n"
    )
    
    import json
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
        
    valid_ids = [s_id for s_id in selected_ids if s_id in sentence_map]
    draft_sentences = [
        {"sentence": sentence_map[s_id]["text"], "citation": sentence_map[s_id]["citation"]}
        for s_id in valid_ids
    ]
    assembled_text = " ".join(f"{item['sentence']} ({item['citation']})." for item in draft_sentences)
    return valid_ids, draft_sentences, assembled_text

async def main():
    print("=== Item 4: Revision Control Comparison (With vs Without Critic Note) ===")
    
    # 1. Retrieve evidence
    state: ResearchState = {
        "run_id": "test-item4",
        "topic": "AI environmental and economic impact",
        "sub_questions": SUB_QUESTIONS,
        "evidence": {},
        "sections": {},
        "max_revisions": 1,
        "critique_history": []
    }
    retriever_res = await retriever_node(state)
    evidence = retriever_res["evidence"]
    critic = CriticAgent()
    
    results = []
    
    for idx, sq in enumerate(SUB_QUESTIONS, 1):
        print(f"\n{'='*70}")
        print(f"[{idx}] Sub-question: {sq}")
        print(f"{'='*70}")
        chunks = evidence.get(sq, [])
        
        # Build Pass 1 draft using background-only selection
        bg_draft_sentences = [
            {"sentence": "The dominant public debate tends to alternate between technological optimism and predictions of large-scale social disruption.", "citation": "Artificial Intelligence Transformation"},
            {"sentence": "The optimistic position emphasises higher productivity, scientific progress, safer working conditions, and more efficient use of resources.", "citation": "Artificial Intelligence Transformation"},
            {"sentence": "The pessimistic position focuses on job displacement, corporate concentration, environmental costs, surveillance, misinformation, and geopolitical conflict.", "citation": "Artificial Intelligence Transformation"}
        ]
        bg_assembled = " ".join(f"{item['sentence']} ({item['citation']})." for item in bg_draft_sentences)
        
        # Pass 1 Critic call
        print("Running Critic on Pass 1 (background-only draft)...")
        res1 = await critic.run(Task(input_data={
            "topic": sq,
            "sentences": bg_draft_sentences,
            "draft": bg_assembled,
            "evidence": chunks
        }))
        verdict1 = res1.get("verdict")
        reason1 = res1.get("reason")
        print(f"Pass 1 Critic Verdict: {verdict1}")
        print(f"Pass 1 Critic Reason:  {reason1}")
        
        # Pass 2A: WITH Critic note
        print("\nRunning Pass 2A (WITH Critic missing note)...")
        ids_with, sentences_with, text_with = await synthesize_single_sq(sq, chunks, revision_reason=reason1)
        res_with = await critic.run(Task(input_data={
            "topic": sq,
            "sentences": sentences_with,
            "draft": text_with,
            "evidence": chunks
        }))
        verdict_with = res_with.get("verdict")
        reason_with = res_with.get("reason")
        print(f"  Pass 2A Selected IDs: {ids_with}")
        print(f"  Pass 2A Critic Verdict: {verdict_with} ({reason_with[:60]}...)")
        
        # Pass 2B: WITHOUT Critic note (plain re-run)
        print("\nRunning Pass 2B (WITHOUT Critic missing note - plain re-run)...")
        ids_without, sentences_without, text_without = await synthesize_single_sq(sq, chunks, revision_reason=None)
        res_without = await critic.run(Task(input_data={
            "topic": sq,
            "sentences": sentences_without,
            "draft": text_without,
            "evidence": chunks
        }))
        verdict_without = res_without.get("verdict")
        reason_without = res_without.get("reason")
        print(f"  Pass 2B Selected IDs: {ids_without}")
        print(f"  Pass 2B Critic Verdict: {verdict_without} ({reason_without[:60]}...)")
        
        # Comparison
        identical = (ids_with == ids_without)
        print(f"\nID Lists Identical? {identical}")
        if not identical:
            diff_with = [i for i in ids_with if i not in ids_without]
            diff_without = [i for i in ids_without if i not in ids_with]
            print(f"  Only in 2A (with note):    {diff_with}")
            print(f"  Only in 2B (without note): {diff_without}")
            
        results.append({
            "sq": sq,
            "pass1_reason": reason1,
            "ids_with": ids_with,
            "verdict_with": verdict_with,
            "ids_without": ids_without,
            "verdict_without": verdict_without,
            "identical": identical
        })

    print("\n" + "="*70)
    print("ITEM 4 SUMMARY TABLE")
    print("="*70)
    for r in results:
        print(f"SQ: {r['sq'][:50]}...")
        print(f"  WITH note:    IDs={r['ids_with']} | Verdict={r['verdict_with']}")
        print(f"  WITHOUT note: IDs={r['ids_without']} | Verdict={r['verdict_without']}")
        print(f"  Identical: {r['identical']}")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
