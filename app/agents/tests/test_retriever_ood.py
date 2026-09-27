import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.agents.base import Task, MemoryStore
from app.agents.retriever import RetrieverAgent

async def test_retriever_ood():
    print("=== Testing Retriever Agent on Out-of-Domain Sub-questions ===")
    retriever = RetrieverAgent()
    memory = MemoryStore()
    
    ood_questions = [
        "How did the political landscape of Italy influence Renaissance art?",
        "Who were the primary patrons of the arts during the Italian Renaissance?",
        "What were the key techniques developed by Italian Renaissance painters?"
    ]
    
    # Keywords that would indicate a truly relevant chunk for these OOD questions
    target_keywords = ["renaissance", "italy", "art", "patrons", "painters"]
    
    for i, sq in enumerate(ood_questions):
        task = Task(input_data=sq)
        try:
            result = await retriever.run(task, memory)
            print(f"Sub-question {i+1}: {sq}")
            print(f"Retrieved {len(result)} chunks.")
            
            # Since db_lookup currently returns top_k regardless of distance,
            # we assert that none of the returned chunks are actually relevant.
            relevant_chunks = []
            for j, chunk in enumerate(result):
                text = (chunk.get('title', '') + " " + chunk.get('snippet', '')).lower()
                import re
                if any(re.search(r'\b' + kw + r'\b', text) for kw in target_keywords):
                    relevant_chunks.append(chunk)
                print(f"  Chunk {j+1}: {chunk.get('title')} - {chunk.get('snippet', '')[:100]}...")
            
            assert len(relevant_chunks) == 0, f"Expected 0 relevant chunks for OOD query, got {len(relevant_chunks)}"
            print("Assertion passed: No relevant chunks found for OOD query.\n")
            
        except Exception as e:
            print(f"Retriever error on sub-question '{sq}': {e}")
            raise e

if __name__ == "__main__":
    asyncio.run(test_retriever_ood())
