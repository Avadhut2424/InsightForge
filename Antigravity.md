# InsightForge AI — Agentic Research & Report Generation Platform

> **Purpose of this document:** This file is written to brief an AI coding agent on everything needed to build this project from scratch — the motive, architecture, tech stack, data flow, and a phase-by-phase implementation plan with clear "definition of done" criteria for each phase. Treat each phase as a self-contained task with its own acceptance test before moving to the next.

---

## 1. Project Overview

**Name:** InsightForge AI
**Type:** Multi-agent research assistant that autonomously researches a topic and drafts a structured, fact-grounded report.
**Core stack:** Python, LangGraph, MCP (Model Context Protocol), OpenAI/Claude APIs, PostgreSQL + pgvector, FastAPI, Docker.

### Motive

A single LLM call asked to "write a report on X" tends to hallucinate facts, gives shallow/unstructured output, and has no way to verify its own claims. InsightForge AI replaces that single-shot approach with a **team of specialized AI agents** that mimic a human research team: one plans the research, one gathers sources, one writes the synthesis, and one critiques it for accuracy before it ships. This agent-team approach is designed to:
- Improve factual grounding (target: ~88% grounding accuracy)
- Reduce hallucinated claims (target: ~40% reduction) by giving agents live tool access via MCP
- Cut manual research time (target: ~65% reduction) versus a human doing the same research by hand

### Input

- A **research topic or question** submitted by the user (via API or simple UI), e.g. *"Write a report on the impact of tariffs on the semiconductor industry."*
- A **pre-indexed knowledge base** of 300+ source documents (~10,000+ chunks), embedded and stored ahead of time.
- Live access to external tools (web search, calculator, DB lookup) via MCP, used on-demand during a run.

### Output

- A **structured, multi-section research report** (Markdown-formatted), with claims grounded in and citing the source material.
- A **run log** in the database: which agent did what, how many tool calls were made, how many revision cycles occurred, and whether the run succeeded — this is the evaluation data source.

### Supported query types

| Works well | Doesn't fit this system |
|---|---|
| Broad topic requests ("Write a report on X") | Single-fact lookups ("What's the capital of France?") |
| Comparative questions ("Compare X's policy vs Y's") | Casual chat / conversation |
| Explanatory/analytical questions ("Causes and effects of X") | Purely subjective/opinion questions |
| Multi-part questions | Topics with zero source coverage and no web search fallback |
| Questions needing historical + current context | Real-time/streaming data requests |

---

## 2. Architecture

### 2.1 Tech stack and role of each piece

| Technology | Role |
|---|---|
| **FastAPI** | Entry point — receives the research request, returns the final report |
| **LangGraph** | Orchestrator — runs the 4 agents as a state graph, with a conditional loop for revisions |
| **OpenAI / Claude API** | The "brain" — each agent is an LLM call with a distinct system prompt/role |
| **PostgreSQL + pgvector** | Single database for both: (a) vector search over the knowledge base, (b) structured run/agent/tool logs |
| **MCP (Model Context Protocol) tool servers** | Gives agents standardized access to external tools (web search, calculator, DB lookup) mid-reasoning |
| **Docker + Docker Compose** | Packages the whole system (API, DB) so it runs identically anywhere |

> **Note on vector store choice:** This project uses **pgvector** (not a standalone FAISS index) so that both the embeddings and their metadata (source, text, tags) live in one queryable table, avoiding a separate ID-mapping layer between two systems. Vector search becomes a normal SQL query using the `<->` distance operator.

### 2.2 OOP structure

- `Agent` — base class with shared LLM-call logic; each of Planner/Retriever/Synthesizer/Critic subclasses or configures this.
- `Task` — a unit of work passed between agents (holds input, expected output shape, status).
- `MemoryStore` — shared state object agents read/write to, so e.g. the Synthesizer can see what the Retriever found without re-fetching it.

### 2.3 The 4-agent LangGraph workflow

```
User topic
    |
    v
[Planner]  -- breaks topic into sub-questions
    |
    v
[Retriever] -- pgvector search + MCP tool calls (web search, calculator, DB lookup)
    |
    v
[Synthesizer] -- drafts the report from retrieved evidence
    |
    v
[Critic] -- checks claims against sources
    |
    +-- if unsupported claims found --> loop back to [Synthesizer] (revise)
    |
    +-- if approved --> Final report returned
```

**Nodes:** `planner`, `retriever`, `synthesizer`, `critic` (4 total — `START`/`END` are graph entry/exit points, not agent nodes).
**Edges:** linear `planner -> retriever -> synthesizer -> critic`, plus one **conditional edge** from `critic`: either back to `synthesizer` (revise) or to `END` (approved). This conditional/cyclic edge is the reason LangGraph is used instead of a plain linear LangChain chain — plain chains execute forward only and cannot natively loop back a step.

### 2.4 Why MCP (not just direct API calls in code)

- Gives every external tool (web search, calculator, DB lookup) the same standardized interface, so agents don't need tool-specific logic.
- Lets the LLM decide **mid-reasoning** when to call a tool, rather than a hardcoded fixed sequence.
- Decouples tool implementation from agent logic — swap or add tools without touching agent code.

### 2.5 Data flow summary

```
Static ingestion (once, offline):
  Wikipedia / NewsAPI / arXiv PDFs / gov data
        |  (parallel fetch, ThreadPoolExecutor)
        v
   chunk -> embed (batched, rate-limited)
        v
   Postgres + pgvector table `chunks` (text + source + embedding together)

Live run (per user request):
  User topic -> Planner -> Retriever
        |                     |
        |         pgvector similarity search (SQL)
        |                     |
        |          MCP web search / calculator / DB tool (if needed)
        v                     v
              Synthesizer -> Critic -> (loop or) Final report
                                  |
                     every step logged to Postgres (`runs`, `agent_steps`, `tool_calls`)
```

---

## 3. Prerequisites (install before starting)

| Tool | Purpose |
|---|---|
| Docker Desktop / Docker Engine + Compose | Runs all services in containers |
| Git | Version control |
| Python 3.11 | Local dev/testing |
| VS Code (Docker + Python extensions) | Editor |
| Postman or curl | API testing |
| OpenAI and/or Anthropic API key | LLM access |
| Tavily / SerpAPI / Brave Search API key | Web search MCP tool |

Do **not** install Postgres/pgvector locally — it runs as a Docker service (`pgvector/pgvector:pg16` image).

---

## 4. Project folder structure (target)

```
insightforge-ai/
├── api/
│   ├── main.py                # FastAPI app, /research endpoint
│   └── schemas.py             # Pydantic request/response models
├── agents/
│   ├── base.py                # Agent, Task, MemoryStore classes
│   ├── planner.py
│   ├── retriever.py
│   ├── synthesizer.py
│   └── critic.py
├── graph/
│   └── workflow.py            # LangGraph StateGraph definition
├── mcp_servers/
│   ├── web_search_server.py
│   ├── calculator_server.py
│   └── db_lookup_server.py
├── ingestion/
│   ├── fetch_wikipedia.py
│   ├── fetch_newsapi.py
│   ├── fetch_pdfs.py
│   ├── chunk_and_embed.py
│   └── run_ingestion.py       # parallel fetch orchestrator
├── db/
│   ├── models.py               # SQLAlchemy models
│   └── migrations/
├── llm/
│   └── llm_client.py           # ask_llm(), ask_llm_safe()
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
├── .dockerignore
└── README.md
```

---

## 5. Phase-wise implementation plan

Each phase should be built and verified independently before moving to the next. Suggested execution order: **1 → 2 → 3 → 4 → 6 → 5 → 7 → 8 → 9 → 10** (agents are built and tested against static sample data in Phase 6 *before* MCP and LangGraph wiring, to avoid debugging multiple layers at once).

---

### Phase 1 — Environment & skeleton

**Goal:** A container that starts and responds; no intelligence yet.

**Tasks:**
- Create folder structure as in Section 4.
- Write `Dockerfile` (base: `python:3.11-slim`).
- Write `docker-compose.yml` with an `api` service.
- Write `.env` and `.dockerignore`.
- Build a bare FastAPI app with a single `GET /health` endpoint returning `{"status": "ok"}`.

**Definition of done:** `docker compose up` starts the container; `curl http://localhost:8000/health` returns `200 OK`.

---

### Phase 2 — Database (Postgres + pgvector) & schema

**Goal:** Database is running, schema exists, pgvector extension is enabled.

**Tasks:**
- Add a `db` service to `docker-compose.yml` using image `pgvector/pgvector:pg16`.
- Run `CREATE EXTENSION IF NOT EXISTS vector;` on startup (via an init SQL script mounted into the container).
- Define SQLAlchemy models / raw SQL for:
  - `chunks (id, text, source, embedding VECTOR(1536))`
  - `runs (id, topic, status, started_at, finished_at)`
  - `agent_steps (id, run_id, agent_name, input, output, started_at, finished_at)`
  - `tool_calls (id, run_id, tool_name, input, output, called_at)`
  - `revisions (id, run_id, revision_number, reason, created_at)`
- Add `pgvector` and `psycopg2-binary` to `requirements.txt`.

**Definition of done:** You can insert a chunk row with a dummy `VECTOR(1536)` embedding and query it back with a `SELECT ... ORDER BY embedding <-> '[...]' LIMIT 5;` query.

---

### Phase 3 — Data ingestion (parallel fetch → chunk → embed → store)

**Goal:** The knowledge base exists and is searchable via pgvector.

**Tasks:**
- Write one fetch function per source:
  - `fetch_wikipedia.py` — via `wikipedia-api` package or REST API
  - `fetch_newsapi.py` — via NewsAPI `/everything` endpoint
  - `fetch_pdfs.py` — download + parse with `pdfplumber`/`PyPDF2` (arXiv, gov reports)
  - (optional) `fetch_gov_data.py` — data.gov / SEC EDGAR
- Run all fetch functions **concurrently** using `concurrent.futures.ThreadPoolExecutor` (I/O-bound, safe to parallelize) — do **not** parallelize the embedding step; batch it sequentially to respect API rate limits.
- Chunk text using `langchain.text_splitter.RecursiveCharacterTextSplitter` (~500 tokens, 50-token overlap).
- Generate embeddings in batches (e.g. OpenAI `text-embedding-3-small`).
- Insert each chunk (text + source + embedding) directly into the `chunks` table — pgvector stores metadata and vector together, no separate index file needed.

**Reference pattern for parallel fetch:**
```python
from concurrent.futures import ThreadPoolExecutor

sources = [fetch_wikipedia, fetch_newsapi, fetch_pdfs]
with ThreadPoolExecutor(max_workers=len(sources)) as executor:
    results = executor.map(lambda fn: fn(), sources)
all_docs = [doc for source_docs in results for doc in source_docs]
```

**Definition of done:** `SELECT COUNT(*) FROM chunks;` returns 10,000+ rows; a manual similarity query against a test embedding returns topically relevant chunks.

---

### Phase 4 — LLM connectivity

**Goal:** Prove the app can reliably call the LLM API in isolation, before any agent logic is built.

**Tasks:**
- Store API key(s) in `.env` (`OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY`); never commit `.env`.
- Install the relevant SDK (`openai` or `anthropic`) and add to `requirements.txt`.
- Build one reusable wrapper module `llm/llm_client.py`:
  - `ask_llm(prompt, system, model, temperature)` — makes the raw API call.
  - `ask_llm_safe(...)` — wraps `ask_llm` with retries and exponential backoff.
- Define a per-role model config so cost/quality can be tuned per agent later:
  ```python
  MODEL_CONFIG = {
      "planner": "gpt-4o-mini",
      "retriever_rewrite": "gpt-4o-mini",
      "synthesizer": "gpt-4o",
      "critic": "gpt-4o",
  }
  ```
- Set `max_tokens` and a client-side `timeout` on every call.
- Log token usage (`response.usage`) from the start.
- Add a temporary `POST /test-llm` FastAPI route for connectivity testing.

**Definition of done:** `/test-llm` returns a real LLM response when called through Docker (not just locally — confirms `.env` variables are correctly passed into the container). A deliberately bad request (e.g. missing key) fails with a clear, handled error rather than crashing the process.

---

### Phase 5 — MCP tool servers

**Goal:** Agents can call external tools mid-reasoning via a standardized protocol.

**Tasks:**
- Build/wire three MCP tool servers:
  - **Web search** — wraps Tavily/SerpAPI/Brave Search API.
  - **Calculator** — evaluates expressions safely (e.g. via `sympy`, not raw `eval`).
  - **DB lookup** — runs parameterized queries against the Postgres tables.
- Test each tool server **standalone**, outside the agent loop, before connecting it to any agent.
- Register the MCP servers so LangGraph/agent code can discover and call them (e.g. via `langchain-mcp-adapters` or the official `mcp` Python SDK).

**Definition of done:** Each tool can be called directly (e.g. via a test script) and returns correctly structured data.

---

### Phase 6 — Build agents individually (test in isolation before wiring the graph)

**Goal:** Each agent's logic is correct on its own, using saved sample inputs, before LangGraph is introduced.

**Tasks:**
- `Planner` — input: topic string; output: list of sub-questions. Test with 3–5 varied sample topics.
- `Retriever` — input: sub-question; output: retrieved chunks (pgvector search) + optional tool results (test with retrieval only first, MCP tools after Phase 5 is done).
- `Synthesizer` — input: retrieved evidence; output: a structured draft report. Test using saved retrieval output (not live).
- `Critic` — input: draft report + sources; output: approve/revise verdict + reasons. Test using saved draft output (not live).
- Each agent should subclass/use the shared `Agent` base class and call `ask_llm_safe()` from Phase 4 — no agent should make its own raw API call.

**Definition of done:** Each of the 4 agent functions runs correctly and predictably against static test inputs, independent of the graph or live tool calls.

---

### Phase 7 — Wire agents into LangGraph

**Goal:** The full 4-node graph with the revision loop runs end-to-end.

**Tasks:**
- Define a `StateGraph` in `graph/workflow.py` with a shared state schema (topic, sub-questions, retrieved chunks, draft, critique verdict, revision count).
- Add the 4 nodes: `planner`, `retriever`, `synthesizer`, `critic`.
- Add linear edges: `planner -> retriever -> synthesizer -> critic`.
- Add the **conditional edge** from `critic`:
  - if verdict == "revise" and revision count < max_revisions: route back to `synthesizer`
  - else: route to `END`
- Set a `max_revisions` cap (e.g. 3) to prevent infinite loops.

**Definition of done:** Running one full topic through the graph produces a final report. Forcing a "bad draft" (e.g. via a test critic that always returns "revise" once) confirms the loop actually re-runs the Synthesizer before completing.

---

### Phase 8 — Logging to the database

**Goal:** Every run is fully traceable in Postgres.

**Tasks:**
- On each node's start/end, write a row to `agent_steps` (agent name, input summary, output summary, timestamps).
- On each MCP tool call, write a row to `tool_calls`.
- On each revision loop iteration, write a row to `revisions`.
- On run start/end, write/update a row in `runs` (topic, status, timestamps).

**Definition of done:** After running a topic end-to-end, querying `runs`, `agent_steps`, `tool_calls`, and `revisions` shows an accurate, complete trace of what happened during that run.

---

### Phase 9 — FastAPI endpoint (user-facing)

**Goal:** A real endpoint a user (or frontend) can call.

**Tasks:**
- `POST /research` — accepts `{"topic": "..."}`, invokes the LangGraph workflow, returns the final report (and optionally a short run summary: sources used, revision count).
- Add input validation (empty/too-short topic).
- Add error handling for LLM timeouts, empty retrieval results, and tool failures — return meaningful HTTP error responses, not raw stack traces.
- (Optional) Add `GET /research/{run_id}` to fetch a past run's report and log from the database.

**Definition of done:** Calling `POST /research` with a real topic via Postman/curl returns a complete, readable report within a reasonable time, and errors are handled gracefully.

---

### Phase 10 — Polish & evaluation

**Goal:** The project is demo-ready and shows measurable results.

**Tasks:**
- Build a small script or `GET /metrics` endpoint that computes, from the `runs`/`agent_steps`/`revisions` tables:
  - Average revision cycles per run
  - Task success rate
  - Approximate factual-grounding rate (e.g. % of claims the Critic approved without flags)
- Write a `README.md` covering: project overview, architecture diagram, setup instructions (`docker compose up`), environment variables needed, and example API calls.
- Add basic automated tests: pgvector retrieval returns expected results for a known query; one agent produces valid output for a fixed input; one full graph run completes successfully.

**Definition of done:** A new person can clone the repo, follow the README, run `docker compose up`, and get a working system — and can see quantitative run statistics via the metrics endpoint/script.

---

## 6. Key design decisions & rationale (for reference)

| Decision | Rationale |
|---|---|
| LangGraph over plain LangChain | The Critic → Synthesizer revision path is a cycle; plain chains execute forward-only and cannot natively loop back |
| pgvector over a separate FAISS index | Single database for vectors + metadata; avoids manual ID-mapping between two systems; SQL-native filtering |
| MCP for tools instead of hardcoded API calls in agent code | Standardized tool interface; lets the LLM decide mid-reasoning when to call a tool; easy to add/swap tools later |
| ThreadPoolExecutor for ingestion fetch, not a message queue | Ingestion is a one-time batch job at small scale (~300 docs); a queue (Celery/Redis) solves distributed/continuous-job problems this project doesn't have |
| Different model tiers per agent role (config-driven) | Cheaper model for Planner/query-rewriting, stronger model for Synthesizer/Critic — balances cost and output quality |

---

## 7. Notes for the AI coding agent building this

- Build and verify each phase independently before starting the next — do not skip ahead to LangGraph wiring (Phase 7) before individual agents (Phase 6) are verified against static data.
- Every LLM call must go through `llm/llm_client.py`'s `ask_llm_safe()` — do not let individual agent files make raw SDK calls.
- Every external tool call must go through an MCP server — do not let agents call search/calculator APIs directly in Python.
- All embeddings and their metadata must live in the single `chunks` table (pgvector) — do not introduce a second, separate vector index.
- Cap revision loops (`max_revisions`) to avoid infinite cycles in the LangGraph conditional edge.
- Log everything (`agent_steps`, `tool_calls`, `revisions`) as the graph runs, not as an afterthought — Phase 8 should hook into Phase 7's graph execution, not require rewriting it.