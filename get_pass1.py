import asyncio
from app.agents.graph.nodes import retriever_node, synthesizer_node
async def main():
    sq = "How do the long-term economic benefits and costs of investing in AI research and development vary across different sectors and industries?"
    state = {
        "run_id": "temp-123",
        "topic": "the long-term economic benefits and costs of investing in AI research and development",
        "sub_questions": [sq],
        "evidence": {},
        "sections": {},
        "max_revisions": 1,
        "final_status": "partial",
        "critique_history": []
    }
    state = await retriever_node(state)
    state = await synthesizer_node(state)
    print("Pass 1 Draft:", state["sections"][sq].get("assembled_text"))
    print("Pass 1 Sentences:", [d["sentence"] for d in state["sections"][sq].get("draft", [])])

if __name__ == "__main__":
    asyncio.run(main())
