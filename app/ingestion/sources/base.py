import asyncio
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class RawDocument:
    title: str
    content: str
    source_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseSource:
    """Base interface for all ingestion sources."""
    
    async def fetch(self) -> list[RawDocument]:
        """
        Fetch documents from the source.
        Should handle its own errors gracefully and return an empty list on failure.
        """
        raise NotImplementedError("Each source must implement fetch()")
