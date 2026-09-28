"""
Step 4: Honest measurement of Critic revision note impact on 5 sub-questions.
Forces background-only first pass, then tests Pass 2 WITH note vs WITHOUT note.
"""

import sys
import json
import asyncio
from app.agents.graph.state import ResearchState
from app.agents.graph.nodes import retriever_node, synthesizer_node, critic_node
from app.agents.critic import CriticAgent
from app.agents.base import Task
from app.core.llm.client import call_llm
from app.agents.synthesizer import split_sentences, is_bad_sentence, starts_with_dangling_referent
from app.mcp_servers.db_lookup import get_embedding_model
import numpy as np

SUB_QUESTIONS = [
    "What are the primary environmental impacts of AI adoption, and how do they vary across different industries and applications?",
    "How do AI-driven automation and efficiency gains affect the labor market, and what are the resulting economic implications for workers and businesses?",
    "What are the long-term economic benefits and costs of investing in AI research and development, and how do they compare to traditional forms of economic growth?",
    "How do power grid capacity limits constrain the geographical expansion of AI computing facilities?",
    "What institutional and regulatory frameworks are necessary to mitigate local water and energy strains from AI data centers?"
]

BG_IDS = ["c4-s2", "c4-s3", "c4-s4"]

async def synthesize_single(sq, chunks, revision_reason=None):
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
            has_dangling = starts_with_dangling_referent(sentence)
            prev_sentence = sentences[s_idx - 1] if s_idx > 0 and not is_bad_sentence(sentences[s_idx - 1]) else None
            prev_id = f"c{chunk_num}-s{s_idx}" if s_idx > 0 else None
            
            if has_dangling:
                if prev_sentence:
                    display_text = f"{prev_sentence} {sentence}"
                else:
                    continue
            else:
                display_text = sentence
                
            sentence_map[s_id] = {
                "raw_text": sentence,
                "display_text": display_text,
                "has_dangling": has_dangling,
                "prev_id": prev_id,
                "prev_text": prev_sentence,
                "citation": title
            }
            candidates.append((s_id, display_text))
            
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
        
    valid_selections = [s_id for s_id in selected_ids if s_id in sentence_map]
    
    # Antecedent stitch skipping
    initial_sentences = []
    for s_id in valid_selections:
        item = sentence_map[s_id]
        if item["has_dangling"] and item["prev_text"]:
            if item["prev_id"] in valid_selections:
                final_text = item["raw_text"]
            else:
                final_text = f"{item['prev_text']} {item['raw_text']}"
        else:
            final_text = item["raw_text"]
        initial_sentences.append({"sentence": final_text, "citation": item["citation"], "s_id": s_id})
        
    # Deduplicate substrings
    non_sub = []
    for i, item_i in enumerate(initial_sentences):
        norm_i = item_i["sentence"].strip().lower()
        if not any(norm_i in item_j["sentence"].strip().lower() and len(norm_i) < len(item_j["sentence"].strip().lower()) for j, item_j in enumerate(initial_sentences) if i != j):
            non_sub.append(item_i)
            
    # Relevance floor (0.50)
    emb_model = get_embedding_model()
    q_emb = emb_model.encode(sq, normalize_embeddings=True)
    surviving = []
    for item in non_sub:
        s_emb = emb_model.encode(item["sentence"], normalize_embeddings=True)
        if float(np.dot(q_emb, s_emb)) >= 0.50:
            surviving.append(item)
            
    assembled = " ".join(f"{item['sentence']} ({item['citation']})." for item in surviving)
    return [item["s_id"] for item in surviving], surviving, assembled

async def main():
    print("=== Step 4: Honest Measurement of Revision Note Impact (5 Sub-questions) ===")
    critic = CriticAgent()
    
    # Retrieve evidence for the 5 sub-questions
    state: ResearchState = {
        "run_id": "test-step4",
        "topic": "AI impacts",
        "sub_questions": SUB_QUESTIONS,
        "evidence": {},
        "sections": {},
        "max_revisions": 1,
        "critique_history": []
    }
    ret_diff = await retriever_node(state)
    evidence = ret_diff["evidence"]
    
    results = []
    
    bg_draft_sentences = [
        {"sentence": "The dominant public debate tends to alternate between technological optimism and predictions of large-scale social disruption.", "citation": "Artificial Intelligence Transformation"},
        {"sentence": "The optimistic position emphasises higher productivity, scientific progress, safer working conditions, and more efficient use of resources.", "citation": "Artificial Intelligence Transformation"},
        {"sentence": "The pessimistic position focuses on job displacement, corporate concentration, environmental costs, surveillance, misinformation, and geopolitical conflict.", "citation": "Artificial Intelligence Transformation"}
    ]
    bg_assembled = " ".join(f"{item['sentence']} ({item['citation']})." for item in bg_draft_sentences)
    
    for idx, sq in enumerate(SUB_QUESTIONS, 1):
        print(f"\n{'='*75}")
        print(f"[{idx}] Sub-question: {sq}")
        print(f"{'='*75}")
        chunks = evidence.get(sq, [])
        
        # 1. Critic on background pass
        res_bg = await critic.run(Task(input_data={
            "topic": sq,
            "sentences": bg_draft_sentences,
            "draft": bg_assembled,
            "evidence": chunks
        }))
        verdict_bg = res_bg.get("verdict")
        reason_bg = res_bg.get("reason")
        print(f"Pass 1 Background Verdict: {verdict_bg}")
        print(f"Pass 1 Background Reason:  {reason_bg}")
        
        # 2. Pass 2A: WITH Note
        print("\nRunning Pass 2A (WITH Critic Note)...")
        ids_with, sent_with, text_with = await synthesize_single(sq, chunks, revision_reason=reason_bg)
        crit_with = await critic.run(Task(input_data={"topic": sq, "sentences": sent_with, "draft": text_with, "evidence": chunks}))
        verdict_with = crit_with.get("verdict")
        print(f"  Pass 2A IDs: {ids_with}")
        print(f"  Pass 2A Verdict: {verdict_with}")
        
        # 3. Pass 2B: WITHOUT Note (plain re-run)
        print("\nRunning Pass 2B (WITHOUT Critic Note)...")
        ids_without, sent_without, text_without = await synthesize_single(sq, chunks, revision_reason=None)
        crit_without = await critic.run(Task(input_data={"topic": sq, "sentences": sent_without, "draft": text_without, "evidence": chunks}))
        verdict_without = crit_without.get("verdict")
        print(f"  Pass 2B IDs: {ids_without}")
        print(f"  Pass 2B Verdict: {verdict_without}")
        
        identical = (ids_with == ids_without)
        print(f"  ID lists identical? {identical}")
        if not identical:
            print(f"    Only in WITH note:    {[i for i in ids_with if i not in ids_without]}")
            print(f"    Only in WITHOUT note: {[i for i in ids_without if i not in ids_with]}")
            
        results.append({
            "sq": sq,
            "reason_bg": reason_bg,
            "ids_with": ids_with,
            "verdict_with": verdict_with,
            "ids_without": ids_without,
            "verdict_without": verdict_without,
            "identical": identical
        })

    print("\n" + "="*75)
    print("STEP 4 HONEST SUMMARY TABLE")
    print("="*75)
    change_count = sum(1 for r in results if not r["identical"])
    for idx, r in enumerate(results, 1):
        print(f"[{idx}] SQ: {r['sq'][:50]}...")
        print(f"    WITH note:    IDs={r['ids_with']} | Verdict={r['verdict_with']}")
        print(f"    WITHOUT note: IDs={r['ids_without']} | Verdict={r['verdict_without']}")
        print(f"    Identical: {r['identical']}")
        
    print(f"\nTotal Sub-questions where note changed selection: {change_count}/{len(results)} ({change_count/len(results)*100:.1f}%)")
    print("="*75)

if __name__ == "__main__":
    asyncio.run(main())
