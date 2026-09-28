# InsightForge AI

A retrieval-augmented research system with local embeddings, multi-source ingestion, and pgvector-backed semantic search.

## Status

- **Phase 1** — Environment & Skeleton: ✅ complete
- **Phase 2** — PostgreSQL + pgvector schema: ✅ complete
- **Phase 3** — Data ingestion pipeline: ✅ complete
- **Phase 4** — LLM connectivity: ✅ complete
- **Phase 5** — MCP tool servers: ✅ complete
- **Phase 6** — Build agents individually: ✅ complete (select-and-assemble grounding & verified local LLM evaluation)
- **Phase 7** — Wire agents into LangGraph: ⏳ pending

## Architecture

| Layer | Technology |
|---|---|
| Ingestion sources | Wikipedia, RSS, ArXiv PDFs |
| Embedding | `BAAI/bge-small-en-v1.5` (local, 384-dim, no API calls) |
| Storage | PostgreSQL 16 + pgvector |
| Vector index | HNSW with cosine distance |
| LLM Provider | Configurable via `LLM_PROVIDER` in `.env` (Ollama local or OpenAI) |
| Local Model | `llama3.1-8k` (custom Ollama Modelfile with 8192 context window) |
| Tools | web_search (Tavily API), calculator (simpleeval), db_lookup (pgvector similarity search) |
| API | FastAPI + Uvicorn |
| Container | Docker Compose (migrate / api / db services) |

## Phase 6: Select-and-Assemble Agent Grounding

Drafts produced by the Synthesizer are strictly **cited extracts, not free-form prose**. The synthesizer parses evidence chunks into candidate sentences, removes fragments, headings, and reference lists, pairs dangling referents ("This/It") with their immediate antecedent, caps candidates to 25, and prompts the LLM to return only sentence IDs. Code assembles the verbatim sentences with explicit citations.

The CriticAgent conducts:
1. **Deterministic code-level substring verification**: Checks each extracted sentence directly against normalized retrieved chunks to guarantee 100% evidentiary grounding without regex distortion.
2. **LLM completeness & on-topic check**: Evaluates whether the draft directly addresses the core sub-question, requesting JSON mode (`{"answers": bool, "missing": str | null}`). Unparseable critic outputs strictly default to `revise`.

## Local LLM Setup (Ollama)

1. **Pull the base model**:
   ```bash
   ollama pull llama3.1:8b
   ```
2. **Build the 8k context model**:
   ```bash
   cd ollama
   ollama create llama3.1-8k -f Modelfile
   ```
3. **Model Keep-Alive (`OLLAMA_KEEP_ALIVE`)**:
   By default, Ollama unloads inactive models after 5 minutes, resulting in ~10s cold-start model load times. To keep weights resident in memory, set:
   ```powershell
   # Windows PowerShell
   $env:OLLAMA_KEEP_ALIVE="30m"; ollama serve
   ```
   ```bash
   # Linux / macOS
   export OLLAMA_KEEP_ALIVE="30m"
   ```
4. **Execution & CPU Latency**:
   Local LLM inference runs sequentially on host CPU. Warm calls execute in ~0.6s for small queries and ~4–6s for synthesis prompts, compared to ~10–15s for cold start. A `warm_up_llm()` helper in `app.core.llm.client` primes the model at system startup.

## Quick Start

```bash
cp .env.example .env          # fill in POSTGRES_* values
docker compose up -d          # runs migrate, then api, then db
docker compose ps             # all services should be healthy

# Populate the knowledge base
docker compose exec api python -m app.ingestion.run_ingestion

# Verify search
docker compose exec api python -m app.ingestion.verify_search
```

## Database migrations

Migrations run automatically via the `migrate` service on `docker compose up`.

To run manually:
```bash
docker compose exec api alembic upgrade head
docker compose exec api alembic current
```

Destructive migrations are guarded behind `ALLOW_DESTRUCTIVE_MIGRATIONS=1` in `.env`.

## Folder Structure

- `app/api` — FastAPI routes
- `app/agents` — Individual agents: Planner, Retriever, Synthesizer, Critic
- `app/db` — SQLAlchemy models and session
- `app/ingestion` — Multi-source ingestion pipeline
- `app/mcp_servers` — MCP server implementations
- `app/core` — Configuration and LLM client
- `ollama` — Custom Modelfile and Ollama operational instructions

