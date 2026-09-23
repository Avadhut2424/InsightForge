import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import KBChunk

async def search(query: str):
    print(f"Query: {query}\n")
    print("Loading local embedding model: BAAI/bge-small-en-v1.5...")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    
    # 1. Embed query
    query_embedding = model.encode(query).tolist()
    
    # 2. Search database (using cosine distance: <=>)
    with SessionLocal() as db:
        # L2 distance: <->, Cosine distance: <=>, Inner product: <#>
        # Text embeddings usually use cosine distance
        results = db.scalars(
            select(KBChunk)
            .order_by(KBChunk.embedding.cosine_distance(query_embedding))
            .limit(5)
        ).all()
        
        # 3. Print results
        for i, chunk in enumerate(results, 1):
            print(f"--- Result {i} ---")
            print(f"Source: {chunk.source_name}")
            print(f"Title: {chunk.document_title}")
            print(f"Snippet: {chunk.content[:200]}...")
            print("-" * 40)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "What are the latest advancements in solar power technology?"
        
    asyncio.run(search(query))
