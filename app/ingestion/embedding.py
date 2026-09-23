import asyncio
import logging
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from app.ingestion.chunking import Chunk

logger = logging.getLogger(__name__)

class Embedder:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", batch_size: int = 100):
        self.model_name = model_name
        self.batch_size = batch_size
        logger.info(f"Loading local embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)

    async def embed_batch(self, chunks: List[Chunk], retries: int = 3) -> List[Tuple[Chunk, List[float]]]:
        if not chunks:
            return []
            
        texts = [chunk.content.replace("\n", " ") for chunk in chunks]
        
        try:
            # Run the synchronous encode operation in a thread pool so we don't block the async event loop
            embeddings = await asyncio.to_thread(self.model.encode, texts)
            return [(chunk, emb.tolist()) for chunk, emb in zip(chunks, embeddings)]
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return []
