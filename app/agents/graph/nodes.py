import re
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.agents.graph.state import ResearchState, SectionData, SentenceCitation
from app.agents.graph.routing import (
    should_skip_to_end_after_retriever,
    determine_final_status,
    get_next_sub_question_to_process,
)
from app.agents.graph.tracking import record_agent_step, record_revision
from app.agents.synthesizer import split_sentences, is_bad_sentence, starts_with_dangling_referent
from app.agents.critic import CriticAgent
from app.agents.base import Task
from app.core.llm.client import call_llm
from app.mcp_servers.db_lookup import similarity_search
from app.db.session import SessionLocal
from app.db.models import KBChunk
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Calibrated distance cutoff: In-domain <= 0.245; Software engineering >= 0.261; OOD >= 0.440
DISTANCE_CUTOFF = 0.255
MIN_CHUNKS_UNDER_CUTOFF = 3
MIN_CANDIDATE_SENTENCES = 2
RELEVANCE_FLOOR = 0.50

def truncate_at_sentence_boundary(text: str, max_chars: int = 1500) -> str:
    """Truncates text at the last complete sentence boundary within max_chars."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    matches = list(re.finditer(r'[.!?][\'"”’\)\]]?(\s|$)', truncated))
    if matches:
        return truncated[:matches[-1].end()].strip()
    return truncated


async def planner_node(state: ResearchState) -> Dict[str, Any]:
    """Generates up to 3 sub-questions for the topic."""
    started_at = datetime.utcnow()
    topic = state.get("topic", "")
    run_id = state.get("run_id")
    
    if state.get("sub_questions"):
        sub_questions = state["sub_questions"]
    else:
        prompt = (
            f"You are a research planner. Break down the following topic into 2-3 well-scoped, "
            f"non-redundant sub-questions that collectively cover the topic.\n\n"
            f"Topic: {topic}\n\n"
            f"Return ONLY a valid JSON array of strings containing at most 3 sub-questions. "
            f"Do not include markdown code blocks, just the raw JSON array."
        )
        
        response = await call_llm(role="planner", prompt=prompt)
        text = response.text.strip()
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
                sub_questions = [topic]
        except Exception:
            sub_questions = [topic]
            
        sub_questions = [str(sq).strip() for sq in sub_questions if str(sq).strip()][:3]
        if not sub_questions:
            sub_questions = [topic]
        
    completed_at = datetime.utcnow()
    record_agent_step(
        run_id=int(run_id) if run_id and str(run_id).isdigit() else None,
        agent_name="planner",
        step_index=1,
        status="completed",
        started_at=started_at,
        completed_at=completed_at,
        input_summary={"topic": topic},
        output_summary={"sub_questions": sub_questions}
    )
    
    sections = state.get("sections", {})
    for sq in sub_questions:
        if sq not in sections:
            sections[sq] = {
                "draft": [],
                "assembled_text": "",
                "verdict": None,
                "reason": None,
                "revision_count": 0,
                "status": "pending"
            }
            
    return {
        "sub_questions": sub_questions,
        "sections": sections
    }

async def retriever_node(state: ResearchState) -> Dict[str, Any]:
    """
    Retrieves evidence chunks from KB and evaluates evidence sufficiency in code.
    Requires at least 3 chunks under DISTANCE_CUTOFF, at least 2 candidate sentences after filtering,
    and domain keyword match.
    """
    started_at = datetime.utcnow()
    run_id = state.get("run_id")
    sub_questions = state.get("sub_questions", [])
    evidence = state.get("evidence", {})
    sections = state.get("sections", {})
    
    for sq in sub_questions:
        if sq not in sections:
            sections[sq] = {
                "draft": [],
                "assembled_text": "",
                "verdict": None,
                "reason": None,
                "revision_count": 0,
                "status": "pending"
            }
        res = similarity_search(query=sq, top_k=5)
        snippets = res.get("data", {}).get("results", []) if res.get("success") else []
        
        if not snippets:
            sections[sq] = {
                "draft": [],
                "assembled_text": "Insufficient evidence found in knowledge base.",
                "verdict": "revise",
                "reason": "No evidence chunks returned from database lookup",
                "revision_count": 0,
                "status": "insufficient_evidence"
            }
            evidence[sq] = []
            continue
            
        chunk_ids = [s["id"] for s in snippets]
        full_chunks = []
        with SessionLocal() as db:
            db_chunks = db.scalars(select(KBChunk).where(KBChunk.id.in_(chunk_ids))).all()
            id_to_content = {c.id: c.content for c in db_chunks}
            for s in snippets:
                content = id_to_content.get(s["id"], s.get("snippet", ""))
                full_chunks.append({
                    "id": s["id"],
                    "source": s.get("source"),
                    "title": s.get("title"),
                    "content": truncate_at_sentence_boundary(content, 1500),
                    "snippet": s.get("snippet"),
                    "distance": float(s.get("distance", 0.0))
                })
                
        # 1. Count chunks under calibrated distance cutoff
        chunks_under_cutoff = [c for c in full_chunks if c["distance"] <= DISTANCE_CUTOFF]
        
        # 2. Count candidate sentences after filtering
        candidate_count = 0
        all_text = ""
        for c in full_chunks:
            all_text += " " + c["content"]
            for sentence in split_sentences(c["content"]):
                if not is_bad_sentence(sentence):
                    candidate_count += 1
                    
        # 3. Check for topic-specific terminology match
        stop_words = {"what", "how", "why", "when", "where", "does", "are", "and", "the", "for", "with", "from", "that", "this"}
        sq_keywords = [w.lower() for w in re.findall(r'\b[A-Za-z]{4,}\b', sq) if w.lower() not in stop_words]
        keyword_hits = sum(1 for kw in sq_keywords if kw in all_text.lower())
        
        has_sufficient_chunks = len(chunks_under_cutoff) >= MIN_CHUNKS_UNDER_CUTOFF
        has_sufficient_candidates = candidate_count >= MIN_CANDIDATE_SENTENCES
        has_topic_match = keyword_hits > 0 if sq_keywords else True
        
        if not (has_sufficient_chunks and has_sufficient_candidates and has_topic_match):
            reason_parts = []
            if not has_sufficient_chunks:
                reason_parts.append(f"only {len(chunks_under_cutoff)} chunks under distance cutoff {DISTANCE_CUTOFF}")
            if not has_sufficient_candidates:
                reason_parts.append(f"only {candidate_count} candidate sentences after filtering")
            if not has_topic_match:
                reason_parts.append("zero topical keyword overlap in retrieved content")
            fail_reason = "Insufficient evidentiary support: " + ", ".join(reason_parts)
            
            sections[sq] = {
                "draft": [],
                "assembled_text": "Insufficient evidence found in knowledge base.",
                "verdict": "revise",
                "reason": fail_reason,
                "revision_count": 0,
                "status": "insufficient_evidence"
            }
            evidence[sq] = full_chunks
        else:
            evidence[sq] = full_chunks
            sections[sq]["status"] = "pending"
            sections[sq]["reason"] = None
            
    completed_at = datetime.utcnow()
    record_agent_step(
        run_id=int(run_id) if run_id and str(run_id).isdigit() else None,
        agent_name="retriever",
        step_index=2,
        status="completed",
        started_at=started_at,
        completed_at=completed_at,
        input_summary={"sub_questions": sub_questions},
        output_summary={
            "evidence_count": {sq: len(chunks) for sq, chunks in evidence.items()},
            "statuses": {sq: sec["status"] for sq, sec in sections.items()}
        }
    )
    
    return {
        "evidence": evidence,
        "sections": sections
    }

async def synthesizer_node(state: ResearchState) -> Dict[str, Any]:
    """
    Select-and-assemble synthesizer. Returns separate sentence and citation fields.
    Processes the next sub-question needing synthesis or revision.
    """
    started_at = datetime.utcnow()
    run_id = state.get("run_id")
    sub_questions = state.get("sub_questions", [])
    evidence = state.get("evidence", {})
    sections = dict(state.get("sections", {}))
    
    sq = get_next_sub_question_to_process(sub_questions, sections)
    if not sq:
        return {"sections": sections}
        
    sec = dict(sections.get(sq, {}))
    chunks = evidence.get(sq, [])
    is_revision = sec.get("status") == "needs_revision"
    revision_reason = sec.get("reason") if is_revision else None
    
    # Check for Step 7 test injection: test_synthesizer_override (used once on first pass)
    test_override = state.get("_test_synthesizer_override")
    test_override_cleared = False
    
    # Build candidate sentence map
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
    
    if test_override and not is_revision:
        # Step 7c test injection for first pass
        selected_ids = test_override.get("selected_ids", [])
        custom_draft = test_override.get("custom_draft")
        test_override_cleared = True
    else:
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
            
        custom_draft = None

    valid_selections = [s_id for s_id in selected_ids if s_id in sentence_map]
    
    if custom_draft is not None:
        initial_sentences = custom_draft
    else:
        # 1. Antecedent stitching: skip stitch if antecedent is already selected
        initial_sentences = []
        for s_id in valid_selections:
            item = sentence_map[s_id]
            if item["has_dangling"] and item["prev_text"]:
                if item["prev_id"] in valid_selections:
                    # Antecedent is already selected as its own item: skip stitch
                    final_text = item["raw_text"]
                else:
                    final_text = f"{item['prev_text']} {item['raw_text']}"
            else:
                final_text = item["raw_text"]
                
            initial_sentences.append({
                "sentence": final_text,
                "citation": item["citation"],
                "s_id": s_id
            })

    # 2. Never emit two selected items where one is a substring of the other
    non_substring_sentences = []
    for i, item_i in enumerate(initial_sentences):
        norm_i = re.sub(r'\s+', ' ', item_i["sentence"]).strip().lower()
        is_sub = False
        for j, item_j in enumerate(initial_sentences):
            if i != j:
                norm_j = re.sub(r'\s+', ' ', item_j["sentence"]).strip().lower()
                if norm_i in norm_j and len(norm_i) < len(norm_j):
                    is_sub = True
                    break
        if not is_sub:
            non_substring_sentences.append(item_i)
            
    # 3. Sentence-level relevance floor (0.50) using BAAI/bge-small-en-v1.5
    from app.mcp_servers.db_lookup import get_embedding_model
    import numpy as np
    emb_model = get_embedding_model()
    q_emb = emb_model.encode(sq, normalize_embeddings=True)
    
    surviving_sentences = []
    for item in non_substring_sentences:
        s_emb = emb_model.encode(item["sentence"], normalize_embeddings=True)
        sim = float(np.dot(q_emb, s_emb))
        if sim >= RELEVANCE_FLOOR:
            item_copy = dict(item)
            item_copy["relevance_score"] = sim
            surviving_sentences.append(item_copy)
            
    if len(surviving_sentences) < 2:
        sec["draft"] = []
        sec["assembled_text"] = "Insufficient relevant evidence found above relevance floor."
        sec["verdict"] = "revise"
        sec["reason"] = f"Fewer than 2 sentences met relevance floor {RELEVANCE_FLOOR} (survived: {len(surviving_sentences)})"
        sec["status"] = "insufficient_evidence"
    else:
        assembled_text = " ".join(f"{item['sentence']} ({item['citation']})." for item in surviving_sentences)
        sec["draft"] = [
            {"sentence": item["sentence"], "citation": item["citation"]}
            for item in surviving_sentences
        ]
        sec["assembled_text"] = assembled_text
        sec["status"] = "synthesized"
        sec["selected_ids"] = [item.get("s_id") for item in surviving_sentences if item.get("s_id")]
        
    sections[sq] = sec
    
    completed_at = datetime.utcnow()
    record_agent_step(
        run_id=int(run_id) if run_id and str(run_id).isdigit() else None,
        agent_name="synthesizer",
        step_index=3,
        status="completed",
        started_at=started_at,
        completed_at=completed_at,
        input_summary={"sub_question": sq, "is_revision": is_revision},
        output_summary={"selected_ids": valid_selections, "sentence_count": len(surviving_sentences)}
    )
    
    diff: Dict[str, Any] = {"sections": sections}
    if test_override_cleared:
        diff["_test_synthesizer_override"] = None
    return diff

async def critic_node(state: ResearchState) -> Dict[str, Any]:
    """
    Evaluates the newly synthesized sub-question:
    1. Literal substring check on sentence fields.
    2. LLM completeness/on-topic check.
    Manages revision tracking and unverified status at max revisions.
    """
    started_at = datetime.utcnow()
    run_id = state.get("run_id")
    sub_questions = state.get("sub_questions", [])
    evidence = state.get("evidence", {})
    sections = dict(state.get("sections", {}))
    max_revisions = state.get("max_revisions", 1)
    critique_history = list(state.get("critique_history", []))
    
    # Find the section that was just synthesized
    sq_to_eval = None
    for sq in sub_questions:
        if sections.get(sq, {}).get("status") == "synthesized":
            sq_to_eval = sq
            break
            
    if not sq_to_eval:
        return {"sections": sections}
        
    sec = dict(sections[sq_to_eval])
    chunks = evidence.get(sq_to_eval, [])
    
    # Test injection 2 of 2: forced critic revision
    if state.get("_test_force_critic_revise"):
        verdict = "revise"
        reason = "Forced revision for revision cap testing"
    else:
        critic = CriticAgent()
        res = await critic.run(Task(input_data={
            "sub_question": sq_to_eval,
            "sentences": sec.get("draft", []),
            "draft": sec.get("assembled_text", ""),
            "evidence": chunks
        }))
        verdict = res.get("verdict", "revise")
        reason = res.get("reason", "Critic returned no reason")
        
    critique_entry = {
        "sub_question": sq_to_eval,
        "revision_number": sec.get("revision_count", 0),
        "verdict": verdict,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    }
    critique_history.append(critique_entry)
    
    if verdict == "approve":
        sec["verdict"] = "approve"
        sec["reason"] = reason
        sec["status"] = "approved"
    else:
        sec["verdict"] = "revise"
        sec["reason"] = reason
        current_rev = sec.get("revision_count", 0)
        if current_rev < max_revisions:
            sec["revision_count"] = current_rev + 1
            record_revision(
                run_id=int(run_id) if run_id and str(run_id).isdigit() else None,
                revision_number=sec["revision_count"],
                reason=reason
            )
            sec["status"] = "needs_revision"
        else:
            # Reached max_revisions: keep latest draft, mark unverified
            sec["status"] = "unverified"
            
    sections[sq_to_eval] = sec
    
    completed_at = datetime.utcnow()
    record_agent_step(
        run_id=int(run_id) if run_id and str(run_id).isdigit() else None,
        agent_name="critic",
        step_index=4,
        status="completed",
        started_at=started_at,
        completed_at=completed_at,
        input_summary={"evaluated_sub_question": sq_to_eval},
        output_summary={"verdict": verdict, "status": sec["status"], "revision_count": sec.get("revision_count", 0)}
    )
    
    return {
        "sections": sections,
        "critique_history": critique_history
    }
