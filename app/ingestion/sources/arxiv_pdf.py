import httpx
import asyncio
import logging
import io
import xml.etree.ElementTree as ET
from pypdf import PdfReader
from typing import List
from app.ingestion.sources.base import BaseSource, RawDocument

logger = logging.getLogger(__name__)

class ArxivPdfSource(BaseSource):
    def __init__(self):
        self.source_name = "ArXiv"
        self.search_url = "https://export.arxiv.org/api/query"
        self.search_query = "all:\"renewable energy\" OR all:\"solar power\" OR all:\"wind energy\""
        self.max_results = 20 # Aiming for 20 PDFs

    async def fetch(self) -> List[RawDocument]:
        documents = []
        
        try:
            headers = {"User-Agent": "insightforge-ingestion/1.0 (mailto:avadhut@example.com)"}
            async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
                params = {
                    "search_query": self.search_query,
                    "start": 0,
                    "max_results": self.max_results,
                    "sortBy": "submittedDate",
                    "sortOrder": "descending"
                }
                response = await client.get(self.search_url, params=params, timeout=15.0)
                response.raise_for_status()
                logger.info(f"ArXiv metadata response status={response.status_code} bytes={len(response.content)}")
                
                # Parse ATOM XML
                root = ET.fromstring(response.text)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                tasks = []
                for entry in root.findall('atom:entry', ns):
                    title = entry.find('atom:title', ns).text
                    title = title.replace('\n', ' ').strip()
                    
                    pdf_url = None
                    for link in entry.findall('atom:link', ns):
                        if link.attrib.get('title') == 'pdf':
                            pdf_url = link.attrib.get('href')
                            break
                            
                    if pdf_url:
                        tasks.append(self._fetch_and_parse_pdf(client, title, pdf_url))
                
                for task in tasks:
                    try:
                        documents.append(await task)
                    except Exception as e:
                        logger.warning(f"ArXiv PDF fetch failed: {type(e).__name__}: {e}")
                    await asyncio.sleep(1.0)  # respect arXiv ~1 req/sec guidance
                        
        except Exception:
            logger.exception("Failed to fetch ArXiv metadata")
            
        return documents

    async def _fetch_and_parse_pdf(self, client: httpx.AsyncClient, title: str, pdf_url: str) -> RawDocument:
        # Download PDF in memory
        response = await client.get(pdf_url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        
        pdf_file = io.BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
        text_content = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
                
        full_text = "\n".join(text_content).strip()
        if not full_text:
            raise ValueError(f"No extractable text in PDF: {title}")
            
        return RawDocument(
            title=title,
            content=full_text,
            source_name=self.source_name,
            metadata={"url": pdf_url}
        )
