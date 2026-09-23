# Switch to Local Embedding Model (BAAI/bge-small-en-v1.5)

This plan outlines the steps to replace the OpenAI embeddings with a free, local embedding model (`BAAI/bge-small-en-v1.5`) via the `sentence-transformers` library, as requested, while keeping the OpenAI library for the remaining agents.

## User Review Required

> [!IMPORTANT]
> The database migration will clear (truncate) the `kb_chunks` table to avoid conflicts between the old 1536-dimensional vectors and the new 384-dimensional vectors. This is necessary and safe since we can easily re-ingest the documents, but please confirm this is acceptable.

## Open Questions

None. The requirements are clear.

## Proposed Changes

### Dependencies

#### [MODIFY] [requirements.txt](file:///c:/Users/Avadhut%20Jadhav/OneDrive/Desktop/InsightForge/requirements.txt)
- Add `sentence-transformers` to the list of dependencies. (OpenAI will remain installed).

### Database Schema

#### [MODIFY] [app/db/models.py](file:///c:/Users/Avadhut%20Jadhav/OneDrive/Desktop/InsightForge/app/db/models.py)
- Change `embedding = Column(Vector(1536), nullable=False)` to `Vector(384)`.

#### [NEW] Alembic Migration
- Generate a new Alembic migration script.
- In the `upgrade()` function, add a raw SQL command to `TRUNCATE TABLE kb_chunks;` to clear out any old incompatible vectors.
- Then, alter the `embedding` column to type `VECTOR(384)`.

### Ingestion Pipeline

#### [MODIFY] [app/ingestion/embedding.py](file:///c:/Users/Avadhut%20Jadhav/OneDrive/Desktop/InsightForge/app/ingestion/embedding.py)
- Replace `AsyncOpenAI` with `SentenceTransformer`.
- Load the model `BAAI/bge-small-en-v1.5` once in the `__init__` method.
- Update `embed_batch` to become a synchronous wrapper around `model.encode(texts)`, dropping the HTTP retry logic since it runs locally. We will keep the `async def` signature to avoid breaking the `pipeline.py` contract, and use `asyncio.to_thread` to prevent blocking the event loop.

#### [MODIFY] [app/ingestion/verify_search.py](file:///c:/Users/Avadhut%20Jadhav/OneDrive/Desktop/InsightForge/app/ingestion/verify_search.py)
- Update the script to use `SentenceTransformer` to generate the query embedding instead of the OpenAI client.

## Verification Plan

### Execution Steps
1. Make the code changes locally.
2. Run `docker-compose up -d --build` to rebuild the image with `sentence-transformers` installed.
3. Generate and apply the new Alembic migration locally against the DB (`alembic revision` -> edit -> `alembic upgrade head`).
4. Re-run `python -m app.ingestion.run_ingestion` and confirm it succeeds and doesn't hit the OpenAI API.
5. Re-run `python -m app.ingestion.verify_search.py` and print the top 5 results.
6. Verify the exact row count of `kb_chunks` via SQL.
