from typing import Dict, Any
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import KBChunk

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _embedding_model

def similarity_search(query: str, top_k: int = 5) -> Dict[str, Any]:
    if not isinstance(top_k, int) or not (1 <= top_k <= 20):
        return {"success": False, "error": {"type": "validation_error", "detail": "top_k must be between 1 and 20"}}
    
    try:
        model = get_embedding_model()
        query_embedding = model.encode(query).tolist()
        
        with SessionLocal() as db:
            results = db.scalars(
                select(KBChunk)
                .order_by(KBChunk.embedding.cosine_distance(query_embedding))
                .limit(top_k)
            ).all()
            
            chunks = []
            for chunk in results:
                chunks.append({
                    "id": chunk.id,
                    "source": chunk.source_name,
                    "title": chunk.document_title,
                    "snippet": chunk.content[:200]
                })
                
            return {"success": True, "data": {"results": chunks}}
    except Exception as e:
        return {"success": False, "error": {"type": "db_error", "detail": str(e)}}
