import asyncio
import logging
from typing import List

from app.ingestion.sources import WikipediaSource, ArxivPdfSource, RssSource
from app.ingestion.chunking import TokenChunker
from app.ingestion.embedding import Embedder
from app.ingestion.store import Store

logger = logging.getLogger(__name__)

class IngestionPipeline:
    def __init__(self):
        self.sources = [
            WikipediaSource(),
            ArxivPdfSource(),
            RssSource()
        ]
        self.chunker = TokenChunker()
        self.embedder = Embedder()
        self.store = Store()

    async def run(self):
        logger.info("Starting ingestion pipeline...")
        
        # 1. Fetch concurrently
        fetch_tasks = [source.fetch() for source in self.sources]
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        
        all_documents = []
        for source, result in zip(self.sources, results):
            if isinstance(result, Exception):
                logger.error(f"Source {source.source_name} failed entirely: {result}")
            else:
                logger.info(f"Source {source.source_name} fetched {len(result)} documents.")
                all_documents.extend(result)
                
        logger.info(f"Total documents fetched: {len(all_documents)}")
        if not all_documents:
            logger.warning("No documents fetched. Aborting pipeline.")
            return

        # 2. Chunking
        logger.info("Chunking documents...")
        all_chunks = self.chunker.chunk_documents(all_documents)
        logger.info(f"Total chunks generated: {len(all_chunks)}")

        # 3 & 4. Embed and Store in batches
        logger.info("Embedding and storing chunks in batches...")
        batch_size = self.embedder.batch_size
        
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]
            
            logger.info(f"Processing batch {i // batch_size + 1}/{(len(all_chunks) + batch_size - 1) // batch_size} (size: {len(batch)})")
            embedded_batch = await self.embedder.embed_batch(batch)
            
            if embedded_batch:
                # Need to run SQLAlchemy sync code in a thread pool to avoid blocking the event loop
                # For simplicity in this script, we can just call it, but best practice is to_thread
                await asyncio.to_thread(self.store.store_batch, embedded_batch)
            else:
                logger.warning(f"Failed to embed batch {i // batch_size + 1}")

        logger.info("Ingestion pipeline completed successfully.")
