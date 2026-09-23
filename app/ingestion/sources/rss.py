import logging
import asyncio
import feedparser
from bs4 import BeautifulSoup
from typing import List
from app.ingestion.sources.base import BaseSource, RawDocument

logger = logging.getLogger(__name__)

class RssSource(BaseSource):
    def __init__(self):
        self.source_name = "RSS"
        # Example RSS feed for Renewable Energy (CleanTechnica)
        self.feed_urls = [
            "https://cleantechnica.com/feed/",
            "https://www.renewableenergyworld.com/feed/"
        ]

    async def fetch(self) -> List[RawDocument]:
        documents = []
        
        for feed_url in self.feed_urls:
            try:
                # feedparser doesn't have an async API out of the box, so we run it in a thread
                feed = await asyncio.to_thread(feedparser.parse, feed_url)
                
                if feed.bozo:
                    logger.warning(f"Error parsing feed {feed_url}: {feed.bozo_exception}")
                    continue
                    
                for entry in feed.entries:
                    title = entry.get('title', 'Unknown Title')
                    html_content = entry.get('content', [{'value': entry.get('summary', '')}])[0]['value']
                    
                    # Strip HTML tags
                    soup = BeautifulSoup(html_content, "html.parser")
                    text_content = soup.get_text(separator='\n').strip()
                    
                    if text_content:
                        documents.append(
                            RawDocument(
                                title=title,
                                content=text_content,
                                source_name=self.source_name,
                                metadata={
                                    "url": entry.get('link', ''),
                                    "published_date": entry.get('published', '')
                                }
                            )
                        )
            except Exception as e:
                logger.error(f"Failed to fetch RSS {feed_url}: {e}")
                
        return documents
