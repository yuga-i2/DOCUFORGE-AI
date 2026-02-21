"""
DocuForge AI — Agent Layer

This package contains all 7 specialized LangGraph agent nodes. Each agent
is a pure function that reads from DocuForgeState and returns a partial
state update. Agents never import from each other — all communication
happens through the shared LangGraph state object.

Agents:
    supervisor_agent.py   — Orchestrates routing between all other agents
    ingestion_agent.py    — Parses multimodal documents into clean text
    rag_agent.py          — Runs hybrid semantic + keyword retrieval
    research_agent.py     — Fetches real-time external context via MCP tools
    analyst_agent.py      — Computes statistics and generates charts
    writer_agent.py       — Synthesizes context into a structured report
    verifier_agent.py     — Scores faithfulness and triggers reflection loops
"""
