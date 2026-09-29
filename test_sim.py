import numpy as np
import asyncio
from app.mcp_servers.db_lookup import get_embedding_model

def main():
    model = get_embedding_model()
    sq = "What are the primary environmental impacts of AI adoption, and how do they vary across different industries and applications?"
    q_emb = model.encode(sq, normalize_embeddings=True)
    
    sentences = [
        "Automation can consequently spread from welding, painting, and machine loading to warehouses, food processing, agriculture, construction, cleaning, inspection, delivery, health care, and domestic assistance.",
        "Traditional industrial robots were best suited to repetitive operations in structured environments.",
        "AI expands the range of feasible activities by enabling machine vision, adaptive control, autonomous navigation, predictive maintenance, natural -language in struction, and learning from demonstration.",
        "The important social change is not only that more tasks become technically automatable, but also that robots can operate closer to people and in environments that are less predictable than a fenced production cell.",
        "Investment in generative AI and computing infrastructure is increasing rapidly and is increasingly concentrated among a small number of corporations and countries."
    ]
    
    for i, s in enumerate(sentences):
        s_emb = model.encode(s, normalize_embeddings=True)
        sim = float(np.dot(q_emb, s_emb))
        print(f"Sentence {i+1} sim: {sim:.3f}")

if __name__ == "__main__":
    main()
