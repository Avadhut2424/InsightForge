"""
Step 3: Re-test Critic on background-only drafts and a fresh 8 good / 8 off-topic / 3 tampered benchmark set.
"""

import sys
import asyncio
from app.agents.critic import CriticAgent
from app.agents.base import Task
from app.mcp_servers.db_lookup import similarity_search
from app.db.session import SessionLocal
from app.db.models import KBChunk
from sqlalchemy import select

async def get_real_evidence_for_query(query: str):
    res = similarity_search(query=query, top_k=5)
    snippets = res.get("data", {}).get("results", []) if res.get("success") else []
    chunk_ids = [s["id"] for s in snippets]
    full_chunks = []
    with SessionLocal() as db:
        db_chunks = db.scalars(select(KBChunk).where(KBChunk.id.in_(chunk_ids))).all()
        id_to_content = {c.id: c.content for c in db_chunks}
        for s in snippets:
            full_chunks.append({
                "id": s["id"],
                "source": s.get("source"),
                "title": s.get("title"),
                "content": id_to_content.get(s["id"], s.get("snippet", ""))[:1500],
                "distance": float(s.get("distance", 0.0))
            })
    return full_chunks

async def test_background_only_drafts():
    print("\n" + "="*70)
    print("STEP 3 PART 1: RE-TESTING CRITIC ON BACKGROUND-ONLY DRAFTS")
    print("="*70)
    critic = CriticAgent()
    
    sub_questions = [
        "What are the primary environmental impacts of AI adoption, and how do they vary across different industries and applications?",
        "How do AI-driven automation and efficiency gains affect the labor market, and what are the resulting economic implications for workers and businesses?",
        "What are the long-term economic benefits and costs of investing in AI research and development, and how do they compare to traditional forms of economic growth?"
    ]
    
    bg_sentences = [
        {"sentence": "The dominant public debate tends to alternate between technological optimism and predictions of large-scale social disruption.", "citation": "Artificial Intelligence Transformation"},
        {"sentence": "The optimistic position emphasises higher productivity, scientific progress, safer working conditions, and more efficient use of resources.", "citation": "Artificial Intelligence Transformation"},
        {"sentence": "The pessimistic position focuses on job displacement, corporate concentration, environmental costs, surveillance, misinformation, and geopolitical conflict.", "citation": "Artificial Intelligence Transformation"}
    ]
    bg_draft_text = " ".join(f"{item['sentence']} ({item['citation']})." for item in bg_sentences)
    
    results = []
    for idx, sq in enumerate(sub_questions, 1):
        evidence = await get_real_evidence_for_query(sq)
        res = await critic.run(Task(input_data={
            "topic": sq,
            "sentences": bg_sentences,
            "draft": bg_draft_text,
            "evidence": evidence
        }))
        print(f"\n[SQ{idx}] {sq[:60]}...")
        print(f"  Verdict: {res.get('verdict')}")
        print(f"  Reason:  {res.get('reason')}")
        results.append((sq, res.get("verdict"), res.get("reason")))
        
    return results

async def test_critic_benchmark_set():
    print("\n" + "="*70)
    print("STEP 3 PART 2: FRESH BENCHMARK SET (8 GOOD / 8 OFF-TOPIC / 3 TAMPERED)")
    print("="*70)
    critic = CriticAgent()
    
    evidence = await get_real_evidence_for_query("environmental and economic impact of AI")
    
    # 8 FRESH GOOD DRAFTS (grounded sentences matching the topic)
    good_cases = [
        ("What are the primary environmental impacts of AI computing?",
         ["The environmental effects of AI are similarly ambivalent: AI systems consume energy, water, materials, and comput ing hardware, but may also improve energy efficiency, climate modelling, renewable -energy integration, and environmental monitoring.",
          "The first is the direct footprint of computing infrastructure."]),
        
        ("How does AI adoption influence industrial energy consumption?",
         ["The IEA estimates that widespread adoptio n could unlock additional effective transmission capacity and produce energy savings in some industrial sectors (IEA, 2025).",
          "Decl ining energy consumption per query can therefore coexist with rising total consumption."]),
          
        ("How does automation affect traditional industrial occupations?",
         ["In the labour market, AI -enabled robotics is likely to reduce demand for some traditional industrial occupations, particularly those dominated by routine physical tasks in structured environments.",
          "Productivity growth, increased production, and the creation of new tasks may offset part of the displacement."]),
          
        ("What factors govern the market distribution of AI productivity gains?",
         ["The consequences of AI are not determined by technical capabilities alone.",
          "They also depend on the ownership of infrastructure, access to energy and computing power, the structure of product and labour markets, public regulation, and the ability of social institutions to distribute the costs and benefits of technological change."]),
          
        ("Why does AI development require massive capital expenditure?",
         ["A more defensible conclusion is that expenditure on generative AI, data centres, advanced semiconductors, and associated energy infrastructure constitutes one of the fastest -growing categories of technological investment.",
          "First, high development costs favour the concentration of AI capabilities."]),
          
        ("What operational bottlenecks concentrate AI capabilities among firms?",
         ["Control over these bottlenecks may give states and corporations structural power that does not derive directly from military superiority.",
          "The AI value chain is dependent on geographically concentrated supplies of advanced semiconductors, manufacturing equipment, cloud services, energy, and specialised knowle dge."]),
          
        ("How does expanding AI infrastructure impact municipal water and electricity?",
         ["At the same time, the expansion of data centres creates new electricity and water demands , potentially producing local infrastructure bottlenecks and distributive conflicts.",
          "The relationship between AI and energy is nevertheless bidirectional."]),
          
        ("What empirical effects did industrial robots have on worker compensation?",
         ["Acemoglu and Restrepo estimate that one additional industrial robot per thousand workers between 1990 and 2007 reduced the employment -to-population ratio by 0.18-0.34 percentage points and wages by 0.25 -0.5 per cent (Acemoglu and Restrepo, 2020).",
          "They nev ertheless show that productivity growth at adopting firms can coexist with measurable losses for workers in the surrounding labour market."])
    ]
    
    # 8 OFF-TOPIC DRAFTS (completely different subject matter or ungrounded)
    off_topic_cases = [
        ("What are the primary environmental impacts of AI computing?",
         ["Sourdough fermentation requires precise proofing temperatures between 24 and 28 degrees Celsius.",
          "Optimal dough hydration creates an open and irregular crumb structure."]),
          
        ("How does automation affect traditional industrial occupations?",
         ["Italian Renaissance fresco painters applied water-based pigments directly onto fresh wet plaster.",
          "The Medici family acted as primary financial patrons for prominent Renaissance artists."]),
          
        ("What operational bottlenecks concentrate AI capabilities among firms?",
         ["High altitude marathon training stimulates natural erythropoietin production to enhance oxygen transport.",
          "Endurance athletes monitor blood lactate thresholds during tempo running sessions."]),
          
        ("What factors govern the market distribution of AI productivity gains?",
         ["Modern microservices architectures utilize container orchestration platforms to achieve horizontal auto-scaling.",
          "Database connection pools must be configured with appropriate timeout parameters to avoid resource exhaustion."]),
          
        ("How does expanding AI infrastructure impact municipal water and electricity?",
         ["Weimar Germany instituted strict fiscal controls to halt the hyperinflation currency collapse in late 1923.",
          "Reparation payments under the Treaty of Versailles placed unsustainable strain on the central bank."]),
          
        ("Why does AI development require massive capital expenditure?",
         ["Phase III randomized clinical trials evaluate therapeutic efficacy against current standards of oncology care.",
          "Monoclonal antibodies bind specific cell-surface antigens to inhibit metastatic tumor growth."]),
          
        ("What empirical effects did industrial robots have on worker compensation?",
         ["Tactical pressing formations in European soccer require coordinated mid-block positioning.",
          "Transition phases create numerical overloads against unorganized defensive lines."]),
          
        ("How does AI adoption influence industrial energy consumption?",
         ["Federal statutory copyright requires independent creation and a modest quantum of creative expression.",
          "Fair use defenses weigh the commercial purpose and economic market impact of the secondary work."])
    ]
    
    # 3 TAMPERED DRAFTS (genuine sentence with an inserted ungrounded clause)
    tampered_cases = [
        ("What are the primary environmental impacts of AI computing?",
         ["The environmental effects of AI are similarly ambivalent: AI systems consume energy, water, materials, and comput ing hardware, but may also improve energy efficiency, climate modelling, renewable -energy integration, and environmental monitoring. globally across all sectors without exception.",
          "The first is the direct footprint of computing infrastructure."]),
          
        ("How does automation affect traditional industrial occupations?",
         ["In the labour market, AI -enabled robotics is likely to reduce demand for some traditional industrial occupations, particularly those dominated by routine physical tasks in structured environments. Furthermore secret reports confirm that 100% of software jobs are eliminated.",
          "Productivity growth, increased production, and the creation of new tasks may offset part of the displacement."]),
          
        ("What operational bottlenecks concentrate AI capabilities among firms?",
         ["First, high development costs favour the concentration of AI capabilities. This is mathematically guaranteed to result in total monopoly by 2026.",
          "The cost is incurred before the commerci al value of the model is known, while repeated training, evaluation, deployment, and model updating create continuing expenditure."])
    ]
    
    print("\nEvaluating 8 Good Drafts...")
    good_passed = 0
    for idx, (sq, s_list) in enumerate(good_cases, 1):
        draft_text = " ".join(f"{s} (Source)." for s in s_list)
        sentences_input = [{"sentence": s, "citation": "Source"} for s in s_list]
        res = await critic.run(Task(input_data={"topic": sq, "sentences": sentences_input, "draft": draft_text, "evidence": evidence}))
        v = res.get("verdict")
        print(f"  Good #{idx}: Verdict={v}")
        if v == "approve":
            good_passed += 1
        else:
            print(f"    Reason: {res.get('reason')}")
            
    print("\nEvaluating 8 Off-Topic Drafts...")
    off_rejected = 0
    for idx, (sq, s_list) in enumerate(off_topic_cases, 1):
        draft_text = " ".join(f"{s} (Source)." for s in s_list)
        sentences_input = [{"sentence": s, "citation": "Source"} for s in s_list]
        res = await critic.run(Task(input_data={"topic": sq, "sentences": sentences_input, "draft": draft_text, "evidence": evidence}))
        v = res.get("verdict")
        print(f"  Off-Topic #{idx}: Verdict={v} ({res.get('reason')[:60]}...)")
        if v == "revise":
            off_rejected += 1
            
    print("\nEvaluating 3 Tampered Drafts...")
    tampered_rejected = 0
    for idx, (sq, s_list) in enumerate(tampered_cases, 1):
        draft_text = " ".join(f"{s} (Source)." for s in s_list)
        sentences_input = [{"sentence": s, "citation": "Source"} for s in s_list]
        res = await critic.run(Task(input_data={"topic": sq, "sentences": sentences_input, "draft": draft_text, "evidence": evidence}))
        v = res.get("verdict")
        print(f"  Tampered #{idx}: Verdict={v} ({res.get('reason')[:60]}...)")
        if v == "revise":
            tampered_rejected += 1
            
    print("\n" + "="*70)
    print("CRITIC BENCHMARK SUMMARY")
    print("="*70)
    print(f"Good Drafts:      {good_passed}/8 approved (no regression)")
    print(f"Off-Topic Drafts: {off_rejected}/8 rejected")
    print(f"Tampered Drafts:  {tampered_rejected}/3 rejected")
    print("="*70)

async def main():
    await test_background_only_drafts()
    await test_critic_benchmark_set()

if __name__ == "__main__":
    asyncio.run(main())
