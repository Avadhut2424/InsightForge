import httpx
import asyncio
import logging
from typing import List
from app.ingestion.sources.base import BaseSource, RawDocument

logger = logging.getLogger(__name__)

class WikipediaSource(BaseSource):
    def __init__(self):
        self.source_name = "Wikipedia"
        self.base_url = "https://en.wikipedia.org/w/api.php"
        # Coherent topics around Renewable Energy
        self.topics = [
            "Renewable energy",
            "Solar power",
            "Wind power",
            "Geothermal energy",
            "Hydropower",
            "Biofuel",
            "Tidal power",
            "Wave power",
            "Solar thermal energy",
            "Sustainable energy"
        ]

    async def fetch(self) -> List[RawDocument]:
        documents = []
        
        async with httpx.AsyncClient(headers={"User-Agent": "InsightForgeBot/1.0 (https://github.com/insightforge)"}) as client:
            tasks = [self._fetch_page(client, topic) for topic in self.topics]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, RawDocument):
                    documents.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Wikipedia fetch failed: {result}")
                    
        return documents

    async def _fetch_page(self, client: httpx.AsyncClient, title: str) -> RawDocument:
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "titles": title,
            "explaintext": 1,
            "exsectionformat": "plain"
        }
        
        response = await client.get(self.base_url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        if not pages or "-1" in pages:
            raise ValueError(f"Page not found: {title}")
            
        page = list(pages.values())[0]
        content = page.get("extract", "")
        
        if not content:
            raise ValueError(f"No content for page: {title}")
            
        return RawDocument(
            title=page.get("title", title),
            content=content,
            source_name=self.source_name,
            metadata={"url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"}
        )
