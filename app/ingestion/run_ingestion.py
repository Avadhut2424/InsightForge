import asyncio
import logging
import sys
from dotenv import load_dotenv

# Load environment variables before anything else
load_dotenv()


from app.ingestion.pipeline import IngestionPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

async def main():
    pipeline = IngestionPipeline()
    await pipeline.run()

if __name__ == "__main__":
    asyncio.run(main())
