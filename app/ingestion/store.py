import logging
import re
from typing import List, Tuple
from app.db.session import SessionLocal
from app.db.models import KBChunk
from app.ingestion.chunking import Chunk

logger = logging.getLogger(__name__)

class Store:
    def __init__(self):
        pass

    def store_batch(self, embedded_chunks: List[Tuple[Chunk, List[float]]]):
        if not embedded_chunks:
            return
            
        with SessionLocal() as db:
            saved = 0
            for chunk, embedding in embedded_chunks:
                content = chunk.content.replace("\x00", "").replace("\u0000", "")
                content = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", content)
                
                db_chunk = KBChunk(
                    content=content,
                    embedding=embedding,
                    source_name=chunk.source_name,
                    document_title=chunk.document_title,
                    chunk_index=chunk.chunk_index,
                    metadata_=chunk.metadata
                )
                
                try:
                    db.add(db_chunk)
                    db.commit()
                    saved += 1
                except Exception as e:
                    db.rollback()
                    logger.warning(f"Skipped chunk {chunk.chunk_index} from {chunk.source_name}/{chunk.document_title}: {type(e).__name__}: {e}")
            logger.info(f"Stored {saved}/{len(embedded_chunks)} chunks in this batch")
