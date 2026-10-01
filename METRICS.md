# Phase 10 Evaluation Metrics & Analysis

This document reports measured performance metrics for InsightForge AI across 15 fresh, unforced research graph executions conducted via the Phase 9 `POST /research` HTTP endpoint on the fixed research graph.

> **Evaluation Dataset Provenance:** Runs 5–19 represent the active, verified evaluation dataset executed through the Phase 9 FastAPI endpoint against the fixed routing graph (zero sections left unevaluated in `synthesized`). Earlier historical runs (40–54) are preserved in [Section 4](#4-historical-evaluation-runs-4054--routing-gap-resolution) for complete traceability and auditability.
>
> **Knowledge Base Chunk Count Notice:** Re-running the ingestion pipeline (`python -m app.ingestion.run_ingestion`) from scratch can legitimately produce slightly different total chunk counts across runs (e.g., 972 chunks in earlier phases vs. 988 chunks following clean-restart re-ingestion). This variance occurs because the pipeline pulls from live external web endpoints (Wikipedia revisions, live RSS news feeds, and ArXiv papers) where new articles or feed entries are continually published. This is expected real-world behavior, not a defect.

---

## 1. Verified Evaluation Dataset Composition (Runs 5–19)

| Run ID | Category | Topic | Final Status | Duration (s) | Approved Sec. | Unverified Sec. | Insufficient Sec. | Synthesized (Unevaluated) | Revisions |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **5** | In-Domain | the environmental impact of AI computing hardware and energy consumption | `approved` | 191.25 | 3 | 0 | 0 | **0** | 1 |
| **6** | In-Domain | economic transformation and labor market disruption from artificial intelligence | `partial` | 48.53 | 1 | 0 | 2 | **0** | 0 |
| **7** | In-Domain | geopolitical competition and national sovereignty in artificial intelligence | `partial` | 46.47 | 1 | 0 | 2 | **0** | 0 |
| **8** | In-Domain | the energy consumption and water requirements of artificial intelligence data centers | `approved` | 127.04 | 3 | 0 | 0 | **0** | 0 |
| **9** | In-Domain | workforce displacement and productivity effects of artificial intelligence automation | `partial` | 78.60 | 2 | 0 | 1 | **0** | 0 |
| **10** | In-Domain | geopolitical governance and technological sovereignty challenges in artificial intelligence | `insufficient_evidence` | 11.36 | 0 | 0 | 3 | **0** | 0 |
| **11** | In-Domain | carbon emissions and environmental sustainability of artificial intelligence infrastructure | `partial` | 83.96 | 2 | 0 | 1 | **0** | 0 |
| **12** | In-Domain | economic productivity and structural labor reallocation driven by artificial intelligence | `partial` | 162.93 | 2 | 1 | 0 | **0** | 1 |
| **13** | Out-of-Domain | history of ancient Egyptian pyramid construction and architecture | `insufficient_evidence` | 11.96 | 0 | 0 | 3 | **0** | 0 |
| **14** | Out-of-Domain | traditional fermentation methods and culinary history of French cheeses | `insufficient_evidence` | 11.63 | 0 | 0 | 3 | **0** | 0 |
| **15** | Out-of-Domain | deep sea bioluminescence mechanisms in cephalopods and marine invertebrates | `insufficient_evidence` | 14.88 | 0 | 0 | 3 | **0** | 0 |
| **16** | Out-of-Domain | quantum electrodynamics and Feynman diagram calculations in particle physics | `insufficient_evidence` | 12.49 | 0 | 0 | 3 | **0** | 0 |
| **17** | Borderline | artificial intelligence energy consumption compared to traditional data processing methods | `partial` | 87.49 | 1 | 0 | 2 | **0** | 1 |
| **18** | Borderline | economic impact of artificial intelligence on wage inequality and union collective bargaining | `partial` | 79.91 | 2 | 0 | 1 | **0** | 0 |
| **19** | Borderline | national artificial intelligence sovereignty initiatives in developing countries | `insufficient_evidence` | 10.42 | 0 | 0 | 3 | **0** | 0 |

*Every run sums to exactly 3 sub-questions. Exactly zero sections remain in `synthesized` status.*

---

## 2. Measured Metrics Summary (`app/evaluation/compute_metrics.py --run-ids 5-19`)

```
======================================================================
           INSIGHTFORGE AI — PHASE 10 EVALUATION REPORT
======================================================================
Evaluated Runs (15 total): [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
----------------------------------------------------------------------
1. RUN STATUS COUNTS
   - approved                 : 2 (13.3%)
   - partial                  : 7 (46.7%)
   - insufficient_evidence    : 6 (40.0%)
----------------------------------------------------------------------
2. SECTION BREAKDOWN (Runs reaching Synthesizer & Critic)
   Total sections across synthesis runs: 27
   - Approved without revision:          15 (55.6%)
   - Approved after 1+ revisions:         2 (7.4%)
   - Hit revision cap (unverified):       1 (3.7%)
   - Insufficient evidence at floor:      9 (33.3%)
   - Synthesized (unevaluated by critic): 0 (0.0%)
   >> Reconciled Category Sum:           27 / 27 (100.0%)
   CRITIC APPROVAL RATE:
   - Sections evaluated by Critic:       18 (17 approved, 1 unverified)
   >> Critic Approval Rate (Evaluated):  94.4% (17 / 18)
   >> Overall Planned Sub-Q Approval Rate: 63.0% (17 / 27)

   [IMPORTANT NOTE ON GROUND TRUTH]
   The 'Critic Approval Rate' measures deterministic literal substring validation
   plus the Critic LLM completeness verdict. It is an automated internal consistency
   check and does NOT constitute human ground truth or external factual accuracy.
----------------------------------------------------------------------
3. REVISION CYCLES PER SECTION (Sections reaching Critic)
   - Evaluated sections: 18
   - Average revision cycles: 0.1667
   - Median revision cycles:  0.0
----------------------------------------------------------------------
4. RUN DURATION & REVISION LOOP COST
   - Average duration (all completed runs):    65.26s
   - Average duration (0 revision cycles):     44.77s
   - Average duration (>= 1 revision cycles):  147.23s
   - Revision loop latency overhead:           +102.46s (+228.9%)
----------------------------------------------------------------------
5. RETRIEVAL DISTANCE STATISTICS (pgvector cosine distance)
   Insufficient Evidence Runs (OOD or failed cutoff):
     Tool calls: 18, Mean Min Distance: 0.3437, Mean Avg Distance: 0.3626
   Approved Runs (In-Domain):
     Tool calls: 6, Mean Min Distance: 0.2138, Mean Avg Distance: 0.2329
   Partial Runs:
     Tool calls: 21, Mean Min Distance: 0.2241, Mean Avg Distance: 0.2457
   Reference Cutoff Threshold: 0.255 (chunks <= 0.255 qualify as candidate evidence)
   Sentence Relevance Floor:   0.500 (cosine similarity against sub-question)
======================================================================
```

---

## 3. Honest Interpretation of Results

### 1. Run Status Distribution
- **Approved (13.3%, 2/15):** Only runs where *every* sub-question has ample evidence and passes Critic validation without leaving unverified or ungrounded sections receive full approval (Runs 5 and 8).
- **Partial (46.7%, 7/15):** In-domain and borderline topics with mixed corpus coverage settle honestly into `partial`. Sub-questions with insufficient evidence are cleanly cordoned off while grounded sections are preserved and cited.
- **Insufficient Evidence (40.0%, 6/15):** All 4 out-of-domain topics (100%) were blocked at retrieval without invoking the LLM Synthesizer or Critic. In addition, 1 in-domain topic (Run 10) and 1 borderline topic (Run 19) failed retrieval because their sub-questions diverged from corpus vocabulary.

### 2. Critic Approval Rate & Dual Denominators
- **94.4% (17 / 18 sections):** Among sections presented to the Critic LLM and deterministic string-matcher, 17 were approved and 1 reached the revision cap as unverified.
- **63.0% (17 / 27 sections):** Across all 27 planned sub-questions in synthesis-active runs, 17 were approved (15 without revision, 2 after revision), 1 was unverified, 9 had insufficient evidence at floor, and **0 were left unevaluated**.
- **Automated Validation vs. Ground Truth:** The Critic's approve verdict confirms verbatim source chunk containment and question completeness. It is an automated internal consistency check, not external factual ground truth.

### 3. Revision Behavior & Latency Overhead
- **Zero Revisions (44.77s avg) vs. With Revisions (147.23s avg):** Executing an iterative revision loop introduces an average latency overhead of **+102.46 seconds (+228.9%)** on local CPU inference.

---

## 4. Historical Evaluation Runs (40–54) & Routing Gap Resolution

Prior to the routing gap fix, runs 40–54 were recorded on the live database. In that dataset, an asymmetric state-matching defect left 4 sections in intermediate status `synthesized`:
- **Run 41 (Sub-Q 3), Run 42 (Sub-Q 3), Run 52 (Sub-Q 3), Run 53 (Sub-Q 2)** were drafted by the Synthesizer but bypassed Critic evaluation because `get_next_sub_question_to_process` only looked for `needs_revision` or `pending` sections.
- When `determine_final_status` evaluated these runs, all 4 correctly received `partial` status; none were falsely labeled `approved`.
- The fix updated `get_next_sub_question_to_process` to queue `synthesized` sections, updated `synthesizer_node` to pass already-drafted sections straight to `critic_node`, and updated `critic_node` to prioritize `synthesized` sections.
- In verified runs 5–19 above, **`Synthesized (Unevaluated)` is exactly 0**.

