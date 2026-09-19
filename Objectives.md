# InsightForge AI — Project Objectives

## Primary objective

Build an end-to-end, multi-agent research assistant that takes a research topic as input and autonomously produces a structured, fact-grounded report as output — replacing manual, single-shot LLM prompting with a coordinated team of specialized agents that plan, retrieve, write, and critique.

## Core objectives

1. **Automate multi-step research**
   Design a 4-stage agent workflow (plan → retrieve → synthesize → critique) using LangGraph, so a single user query is automatically broken down, researched, drafted, and reviewed without manual intervention at each step.

2. **Ground outputs in real sources**
   Build a Retrieval-Augmented Generation pipeline (pgvector-based) over a 10,000+ chunk knowledge base drawn from 300+ source documents, so report claims are backed by retrievable evidence rather than the model's unverified memory.
   - Target: ~88% factual-grounding accuracy.

3. **Reduce hallucinated claims via live tool access**
   Integrate MCP (Model Context Protocol) tool servers — web search, calculator, database lookup — so agents can verify facts and pull current information mid-reasoning instead of relying solely on static training knowledge.
   - Target: ~40% reduction in hallucinated claims versus a no-tool baseline.

4. **Cut manual research time**
   Demonstrate that the automated pipeline meaningfully reduces the time a person would spend manually researching and drafting the same report.
   - Target: ~65% reduction in manual research time.

5. **Self-correct through critique and revision**
   Implement a Critic agent that checks the Synthesizer's draft against retrieved sources and triggers a revision loop when claims are unsupported, so quality control happens automatically rather than only at the end by a human reviewer.

6. **Track and evaluate agent performance**
   Log every run to a normalized SQL schema (500+ agent runs) capturing task success, tool calls, and revision cycles, so the system's reliability can be measured quantitatively rather than judged anecdotally.

7. **Follow sound software engineering practice**
   Structure the codebase around clear OOP abstractions (`Agent`, `Task`, `MemoryStore`) so agent logic, task state, and shared memory are cleanly separated and extensible — not a single monolithic script.

8. **Package for reliable, portable deployment**
   Containerize the full system (API, database, MCP tool servers) with Docker and Docker Compose, so the application runs identically in any environment with a single `docker compose up`.

9. **Expose the system as a usable service**
   Provide a FastAPI-based API (`POST /research`) so the pipeline can be triggered programmatically or through a simple UI, returning a complete report per request.

## Secondary / stretch objectives

- Support per-agent model tiering (cheaper models for planning, stronger models for synthesis/critique) to balance cost and output quality.
- Provide a metrics endpoint/script summarizing grounding accuracy, average revision count, and run success rate from the logged data.
- Keep the architecture modular enough that individual components (vector store, LLM provider, tool servers) can be swapped without rewriting the rest of the system.

## What this project is explicitly *not* trying to do

- It is not a general-purpose chatbot — it is scoped to research/report-generation queries (see supported query types).
- It is not designed for real-time/streaming data or single-fact lookups, where a full 4-agent pipeline would be unnecessary overhead.
- It is not built for large-scale distributed/production traffic — the objective is a correct, well-architected single-instance system, not a horizontally scaled production deployment.