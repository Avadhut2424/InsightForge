"""
Calibrate sentence-level relevance floor on 18 labelled sentences from Run 2.
"""

from sentence_transformers import SentenceTransformer, util
import numpy as np

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

sq1 = "What are the primary environmental impacts of AI adoption, and how do they vary across different industries and applications?"
sq2 = "How do AI-driven automation and optimization affect labor markets and economic productivity, and what are the implications for economic growth and inequality?"
sq3 = "Can AI systems be designed and deployed in ways that minimize their environmental footprint and maximize their economic benefits, and what are the key factors influencing their sustainability?"

sentences = [
    # Section 1
    (sq1, 1, "Relevant", "The environmental effects of AI are similarly ambivalent: AI systems consume energy, water, materials, and comput ing hardware, but may also improve energy efficiency, climate modelling, renewable -energy integration, and environmental monitoring."),
    (sq1, 2, "Marginal", "The relationship between AI and energy is nevertheless bidirectional."),
    (sq1, 3, "Relevant", "The IEA estimates that widespread adoptio n could unlock additional effective transmission capacity and produce energy savings in some industrial sectors (IEA, 2025)."),
    (sq1, 4, "Relevant", "Decl ining energy consumption per query can therefore coexist with rising total consumption."),
    (sq1, 5, "Marginal", "The first is the direct footprint of computing infrastructure."),
    (sq1, 6, "Relevant", "The second consists of the effects enabled by AI applications in energy, transport, buildings, industry, agriculture, and environmental monitoring."),
    
    # Section 2
    (sq2, 1, "Relevant", "In the labour market, AI -enabled robotics is likely to reduce demand for some traditional industrial occupations, particularly those dominated by routine physical tasks in structured environments."),
    (sq2, 2, "Marginal", "In the labour market, AI -enabled robotics is likely to reduce demand for some traditional industrial occupations, particularly those dominated by routine physical tasks in structured environments. This does not imply the disappearance of industrial labour or an inevitable decline in total employment."),
    (sq2, 3, "Relevant", "The consequences of AI are not determined by technical capabilities alone. They also depend on the ownership of infrastructure, access to energy and computing power, the structure of product and labour markets, public regulation, and the ability of social institutions to distribute the costs and benefits of technological change."),
    (sq2, 4, "Marginal", "They also depend on the ownership of infrastructure, access to energy and computing power, the structure of product and labour markets, public regulation, and the ability of social institutions to distribute the costs and benefits of technological change. This article advances the following argument: The development of artificial intelligence constitutes an accelerated reallocation of capital, energy, natural resources, labour, and political power."),
    (sq2, 5, "Marginal", "Its economic, environmental, geopolitical, and social balance is not predetermined but will depend on the institutions governing infrastructure, markets, employment, and international interdependence."),
    (sq2, 6, "Irrelevant", "The article examines five interconnected dimensions of this transformation: investment an"),
    
    # Section 3
    (sq3, 1, "Relevant", "The environmental effects of AI are similarly ambivalent: AI systems consume energy, water, materials, and comput ing hardware, but may also improve energy efficiency, climate modelling, renewable -energy integration, and environmental monitoring."),
    (sq3, 2, "Relevant", "Assessment should therefore monitor total sectoral outcomes after deployment, not stop at a laboratory benchmark or an engineering estimate."),
    (sq3, 3, "Relevant", "Avoid unnecessary computation first; use the least resource -intensive system capable of delivering the required result; improve hardware and software efficiency; schedule flexible workloads in environmentally favoura"),
    (sq3, 4, "Marginal", "The relationship between AI and energy is nevertheless bidirectional."),
    (sq3, 5, "Relevant", "The IEA estimates that widespread adoptio n could unlock additional effective transmission capacity and produce energy savings in some industrial sectors (IEA, 2025)."),
    (sq3, 6, "Marginal", "Decl ining energy consumption per query can therefore coexist with rising total consumption.")
]

print(f"{'#':2} | {'Label':10} | {'Cosine Sim':10} | {'Sub-question':15} | Sentence Preview")
print("-" * 80)

scores_by_label = {"Relevant": [], "Marginal": [], "Irrelevant": []}

for idx, (sq, s_idx, label, text) in enumerate(sentences, 1):
    q_emb = model.encode(sq, normalize_embeddings=True)
    s_emb = model.encode(text, normalize_embeddings=True)
    sim = float(np.dot(q_emb, s_emb))
    scores_by_label[label].append(sim)
    print(f"{idx:2} | {label:10} | {sim:.4f}     | SQ{1 if sq==sq1 else (2 if sq==sq2 else 3)}: S{s_idx:2}       | {text[:55]}...")

print("\n" + "="*50)
print("SCORE DISTRIBUTIONS BY LABEL")
print("="*50)
for label, scores in scores_by_label.items():
    print(f"{label:10}: Count={len(scores)} | Min={min(scores):.4f} | Max={max(scores):.4f} | Mean={np.mean(scores):.4f} | Median={np.median(scores):.4f}")
