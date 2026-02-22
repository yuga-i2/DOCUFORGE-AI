# DocuForge AI

**Intelligent Multi-Agent Document Intelligence Platform**

> Upload any document. 7 specialized AI agents collaborate to analyze, retrieve, reason, and generate a verified, hallucination-controlled report — in under 60 seconds.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange)](https://langchain-ai.github.io/langgraph)
[![React](https://img.shields.io/badge/React-18+-61DAFB)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---


## What is DocuForge AI?

DocuForge AI is a production-grade multi-agent document intelligence system built to demonstrate advanced AI engineering skills. It accepts any document format and deploys a coordinated pipeline of 7 AI agents that parse, retrieve, analyze, write, and verify a structured report — with built-in hallucination control and full observability.

**Built for:** Agentic AI Engineer interviews, AI/ML Engineer roles, LLM application portfolios

---

## Demo

[![DocuForge AI Demo](https://img.youtube.com/vi/iMASmk7Rky8/maxresdefault.jpg)](https://youtu.be/iMASmk7Rky8)

> Click the thumbnail above to watch the full demo — live document upload, 7 agents executing in real time, 
> ReAct pattern visualization, prompt versioning, and hallucination scoring.

---

## Architecture

```
User Upload (PDF/PNG/JPG/MP3/WAV/XLSX/PPTX)
        │
        ▼
┌─────────────────────────────────────────────────┐
│              LangGraph StateGraph               │
│                                                 │
│  🧭 Supervisor → decides routing at each step  │
│        │                                        │
│        ├──▶ 📥 Ingestion Agent                 │
│        │       PyMuPDF / Gemini Vision /        │
│        │       Whisper / pandas / pptx          │
│        │                                        │
│        ├──▶ 📚 RAG Agent                       │
│        │       Hybrid BM25 + Semantic Search    │
│        │       ChromaDB + HuggingFace Embeddings│
│        │                                        │
│        ├──▶ 🌐 Research Agent (optional)       │
│        │       DuckDuckGo web search            │
│        │                                        │
│        ├──▶ 📊 Analyst Agent                   │
│        │       Groq LLaMA + Code Executor       │
│        │                                        │
│        ├──▶ ✍️  Writer Agent                   │
│        │       ReAct-grounded prompt (v1/v2/v3) │
│        │       Anti-hallucination rules         │
│        │                                        │
│        └──▶ 🛡️  Verifier Agent               │
│                Claim-level faithfulness scoring │
│                Reflection loop (max 1 retry)    │
└─────────────────────────────────────────────────┘
        │
        ▼
React Dashboard (Real-time agent visualization)
├── Report Tab      — Structured sections with confidence bars
├── ReAct Pattern   — Thought / Action / Observation per agent
├── Prompt Versions — v1 / v2 / v3 selectable before analysis
└── Metrics Tab     — Faithfulness %, Hallucination %, Stage checklist
```

---

## Key Features

| Feature | Implementation |
|---|---|
| **Multi-agent orchestration** | LangGraph StateGraph with 7 nodes + conditional routing |
| **Hallucination control** | Claim-level verifier scoring + anti-hallucination prompt rules |
| **Hybrid RAG** | BM25 keyword + semantic vector search with ensemble weighting |
| **Multimodal ingestion** | PDF, PNG/JPG (Gemini Vision), MP3/WAV (Whisper), XLSX, PPTX |
| **Prompt versioning** | v1/v2/v3 selectable per request, visible in UI |
| **ReAct pattern** | Every agent exposes Thought/Action/Observation in UI |
| **Background processing** | Celery + Upstash Redis for async pipeline execution |
| **Real-time UI** | React + ReactFlow agent graph with live trace polling |
| **Observability** | LangSmith tracing (optional), full agent trace in UI |
| **Memory systems** | Short-term (session), long-term (Supabase), episodic (ChromaDB) |
| **Zero cost** | Groq free tier + local embeddings + Upstash free Redis |

---

## Tech Stack

**Backend**
- Python 3.11+, FastAPI, LangChain, LangGraph
- Groq (LLaMA 3.1) — primary LLM, free tier
- Google Gemini 1.5 Flash — multimodal fallback
- ChromaDB — vector store (in-memory per session)
- HuggingFace sentence-transformers/all-MiniLM-L6-v2 — local embeddings
- Celery + Upstash Redis — async task queue
- Whisper base — audio transcription

**Frontend**
- React 18, Vite, ReactFlow
- Tailwind CSS, Radix UI, lucide-react

**Deployment**
- Docker + docker-compose
- FastAPI + Uvicorn
- PostgreSQL (Supabase) for session storage
- Redis (Upstash) for task queue

---

## Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API key (free at [console.groq.com](https://console.groq.com))
- Upstash Redis URL (free at [upstash.com](https://upstash.com))

### Setup

```bash
# 1. Clone and create environment
git clone https://github.com/yourusername/docuforge-ai
cd docuforge-ai
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 3. Configure environment
copy .env.example .env
# Edit .env and set:
# GROQ_API_KEY=your_groq_key
# UPSTASH_REDIS_URL=rediss://default:...@....upstash.io:6379
# GEMINI_API_KEY=your_gemini_key (optional, for image analysis)

# 4. Start everything
make start
# or: python run.py
```

Dashboard opens automatically at **http://localhost:3000**

---

## Project Structure

```
docuforge-ai/
├── agents/                     # 7 specialized AI agents
│   ├── supervisor_agent.py     # Query routing and pipeline control
│   ├── ingestion_agent.py      # Document parsing orchestration
│   ├── rag_agent.py            # Chunk + embed + retrieve
│   ├── research_agent.py       # Optional web search
│   ├── analyst_agent.py        # Numerical analysis + code execution
│   ├── writer_agent.py         # ReAct-grounded report generation
│   └── verifier_agent.py       # Claim-level faithfulness scoring
│
├── core/
│   ├── ingestion/              # Multimodal parsers (PDF/image/audio/xlsx/pptx)
│   ├── rag/                    # Chunker, embedder, vectorstore, retriever
│   ├── memory/                 # Short-term, long-term, episodic memory
│   ├── eval/                   # Accuracy, hallucination, bias evaluation
│   └── llm_router.py           # LLM provider routing with fallback chain
│
├── orchestration/
│   ├── graph.py                # LangGraph StateGraph definition
│   ├── router.py               # Stage-based routing logic
│   └── state.py                # DocuForgeState TypedDict
│
├── api/
│   ├── main.py                 # FastAPI app with lifespan
│   ├── routes/                 # analysis_router with all endpoints
│   └── workers/                # Celery app + analysis task
│
├── prompts/
│   ├── v1/writer_prompt.txt    # Basic — minimal instructions
│   ├── v2/writer_prompt.txt    # Structured — JSON schema
│   └── v3/writer_prompt.txt    # Advanced — ReAct + anti-hallucination
│
├── frontend/src/
│   ├── App.jsx                 # Main shell with tab state management
│   ├── components/
│   │   ├── UploadView.jsx      # File drop + query + prompt version selector
│   │   ├── ProcessingView.jsx  # Live agent graph + execution log
│   │   ├── ResultsView.jsx     # 4-tab results (Report/ReAct/Prompts/Metrics)
│   │   └── EvalDashboard.jsx   # Evaluation history and trends
│
├── tests/                      # pytest suite (70%+ coverage)
├── eval/                       # Golden dataset + benchmark results
├── config/docuforge_config.yaml
├── run.py                      # Single-command launcher
├── Makefile                    # Dev shortcuts
└── .env.example                # Environment template
```

---

## How It Works

### 1. Document Ingestion
Upload a PDF, image, audio file, spreadsheet, or presentation. The Ingestion Agent detects the format and routes to the appropriate parser — PyMuPDF for PDFs, Gemini Vision for images, Whisper for audio, pandas for Excel, python-pptx for presentations.

### 2. RAG Pipeline
The RAG Agent chunks the document into 600-character segments, embeds them using local sentence-transformers (no API cost), stores them in an in-memory ChromaDB collection, and retrieves the top-12 most relevant chunks using hybrid BM25 + semantic search.

### 3. Analysis
The Analyst Agent scans the retrieved chunks for numerical data. If found, it generates Python analysis code and executes it in a sandboxed subprocess, extracting key metrics.

### 4. Report Generation
The Writer Agent receives up to 7000 characters of grounded context (ranked chunks + full document text) and a versioned prompt template. The v3 prompt enforces 7 anti-hallucination rules, requiring every sentence to trace back to the document context with an evidence quote.

### 5. Verification
The Verifier Agent extracts 3 specific claims from the generated report and checks each one individually against the source document chunks, returning a per-claim faithfulness array averaged into a final score.

---

## Prompt Engineering

Three prompt versions are available and selectable in the UI before each analysis:

| Version | Strategy | Use Case |
|---|---|---|
| **v1** | Minimal instructions, basic JSON | Quick prototyping |
| **v2** | JSON schema + grounding rules | Standard analysis |
| **v3** | ReAct framework + 7 anti-hallucination rules + evidence fields | Production / interviews |

The selected version is logged in the agent trace and visible in the Prompt Versions tab of the results.

---

## Development

```bash
# Start individual services
make dev         # FastAPI backend only
make worker      # Celery worker only
make frontend    # React frontend only

# Quality checks
make lint        # Ruff linter
make typecheck   # mypy type checking
make test        # pytest with 70% coverage requirement
make check       # Run all checks (lint + typecheck + test)

# Evaluation
make eval        # Run evaluation suite
make benchmark   # Run performance benchmarks

# Cleanup
make clean       # Remove all build artifacts
```

---

## Evaluation

The project includes a comprehensive evaluation framework:

```bash
# Run full eval suite
make eval

# Run benchmark (latency per agent)
make benchmark

# Run specific test file
pytest tests/agents/test_writer_agent.py -v
```

Evaluation covers:
- **Accuracy** — LLM-as-judge scoring against golden QA dataset (20 pairs)
- **Faithfulness** — Unsupported claim detection against source documents
- **Bias** — Response consistency across demographic variants (10 test pairs)
- **Latency** — Per-agent benchmark (5 runs each)

---

## Interview Talking Points

**On multi-agent architecture:**
> "Every agent communicates exclusively through a shared DocuForgeState TypedDict — no direct imports between agents. This means any agent can be replaced or upgraded independently without touching the rest of the pipeline."

**On hallucination control:**
> "The Verifier Agent doesn't ask the LLM to rate the whole report — it extracts 3 specific claims and checks each one individually against source chunks, returning a per-claim support score. The writer prompt has 7 numbered rules that explicitly forbid using general knowledge."

**On RAG design:**
> "Rather than storing in a persistent database, each session gets its own in-memory ChromaDB collection that's destroyed after the task. This prevents cross-session contamination and keeps storage costs at zero."

**On prompt versioning:**
> "Three prompt versions are tracked like software versions. v3 adds the ReAct framework and anti-hallucination rules. The version used is logged in the agent trace so you can reproduce any result exactly."

**On observability:**
> "Every agent appends to a shared agent_trace list. The frontend polls this and renders it as a ReAct Thought/Action/Observation timeline. In production you'd also have LangSmith tracing enabled for token-level visibility."

---

## Cost

| Component | Provider | Cost |
|---|---|---|
| LLM inference | Groq LLaMA 3.1 8B | Free tier |
| Embeddings | HuggingFace all-MiniLM-L6-v2 | Local, free |
| Vector store | ChromaDB in-memory | Free |
| Task queue | Upstash Redis | Free tier (500k ops/month) |
| Image analysis | Google Gemini 1.5 Flash | Free tier |
| Audio transcription | Whisper base | Local, free |

**Total monthly cost: $0**

---

## Performance

- **End-to-end pipeline:** ~45-60 seconds (full analysis with verification)
- **RAG retrieval:** ~1-2 seconds (hybrid search over 50-100 chunks)
- **Report generation:** ~8-12 seconds (writer + verifier LLM calls)
- **Token usage:** ~2,500-3,500 tokens per analysis (Groq free tier: 15 requests/minute)

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-thing`)
3. Make your changes
4. Run tests and linting (`make check`)
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built with:
- [LangChain](https://langchain.com) — Agent framework
- [LangGraph](https://langchain-ai.github.io/langgraph) — Orchestration
- [Groq](https://groq.com) — Free LLM inference
- [ChromaDB](https://www.trychroma.com/) — Vector database
- [FastAPI](https://fastapi.tiangolo.com) — Web framework
- [React](https://react.dev) — Frontend framework

---

**Live Demo:** https://youtu.be/iMASmk7Rky8  
**Questions?** Open an issue or reach out on LinkedIn!

