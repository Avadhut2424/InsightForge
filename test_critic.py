import asyncio
from app.agents.graph.nodes import critic_node

async def main():
    sq = "What are the primary environmental impacts of AI adoption, and how do they vary across different industries and applications?"
    sentences = [
        "AI-related investment may increase productivity but also reinforce market concentration.",
        "Control over semiconductor and cloud -computing bottlenecks may gener ate geopolitical leverage while simultaneously exposing controlling states to reciprocal dependencies.",
        "In the labour market, AI -enabled robotics is likely to reduce demand for some traditional industrial occupations, particularly those dominated by routine physical tasks in structured environments."
    ]
    
    draft = " ".join(sentences)
    
    state = {
        "run_id": "test",
        "topic": "the environmental and economic impact of AI",
        "sub_questions": [sq],
        "evidence": {
            sq: [
                {"id": 1529, "content": draft} # Just mock the evidence so it passes literal check
            ]
        },
        "sections": {
            sq: {
                "draft": [{"sentence": s, "citation": "Source"} for s in sentences],
                "assembled_text": draft,
                "status": "synthesized",
                "revision_count": 0,
                "verdict": None,
                "reason": None
            }
        },
        "max_revisions": 1,
        "critique_history": []
    }
    
    new_state = await critic_node(state)
    sec = new_state["sections"][sq]
    print("Verdict:", sec["verdict"])
    print("Reason:", sec["reason"])
    
if __name__ == "__main__":
    asyncio.run(main())
