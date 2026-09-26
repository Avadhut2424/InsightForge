# InsightForge AI

A retrieval-augmented research system with local embeddings, multi-source ingestion, and pgvector-backed semantic search.

## Status

- **Phase 1** — Environment & Skeleton: ✅ complete
- **Phase 2** — PostgreSQL + pgvector schema: ✅ complete
- **Phase 3** — Data ingestion pipeline: ✅ complete
- **Phase 4** — LLM connectivity: ✅ complete
- **Phase 5** — MCP tool servers: ✅ complete
- **Phase 6** — Build agents individually: ⏳ pending
- **Phase 7** — Wire agents into LangGraph: ⏳ pending

## Architecture

| Layer | Technology |
|---|---|
| Ingestion sources | Wikipedia, RSS, ArXiv PDFs |
| Embedding | `BAAI/bge-small-en-v1.5` (local, 384-dim, no API calls) |
| Storage | PostgreSQL 16 + pgvector |
| Vector index | HNSW with cosine distance |
| Tools | web_search (Tavily API), calculator (simpleeval), db_lookup (pgvector similarity search) |
| API | FastAPI + Uvicorn |
| Container | Docker Compose (migrate / api / db services) |

## Quick Start

```bash
cp .env.example .env          # fill in POSTGRES_* values
docker-compose up -d          # runs migrate, then api, then db
docker-compose ps             # all services should be healthy

# Populate the knowledge base
docker-compose exec api python -m app.ingestion.run_ingestion

# Verify search
docker-compose exec api python -m app.ingestion.verify_search
```

## Database migrations

Migrations run automatically via the `migrate` service on `docker-compose up`.

To run manually:
```bash
docker-compose exec api alembic upgrade head
docker-compose exec api alembic current
```

Destructive migrations are guarded behind `ALLOW_DESTRUCTIVE_MIGRATIONS=1` in `.env`.

## Folder Structure

- `app/api` — FastAPI routes
- `app/agents` — Agent logic (Phase 4)
- `app/db` — SQLAlchemy models and session
- `app/ingestion` — Multi-source ingestion pipeline
- `app/mcp_servers` — MCP server implementations
- `app/core` — Configuration and settings
