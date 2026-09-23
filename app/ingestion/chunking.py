import tiktoken
from dataclasses import dataclass
from typing import List
from app.ingestion.sources.base import RawDocument

@dataclass
class Chunk:
    content: str
    source_name: str
    document_title: str
    chunk_index: int
    metadata: dict

class TokenChunker:
    def __init__(self, model_name: str = "text-embedding-3-small", chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def chunk_documents(self, documents: List[RawDocument]) -> List[Chunk]:
        chunks = []
        for doc in documents:
            tokens = self.encoding.encode(doc.content)
            
            if not tokens:
                continue
                
            start = 0
            chunk_idx = 0
            
            while start < len(tokens):
                end = min(start + self.chunk_size, len(tokens))
                chunk_tokens = tokens[start:end]
                chunk_text = self.encoding.decode(chunk_tokens)
                
                chunks.append(
                    Chunk(
                        content=chunk_text,
                        source_name=doc.source_name,
                        document_title=doc.title,
                        chunk_index=chunk_idx,
                        metadata=doc.metadata
                    )
                )
                
                chunk_idx += 1
                start += self.chunk_size - self.overlap
                
        return chunks
