# DocuForge AI — Developer Constraints & Engineering Standards

> These constraints exist to keep the project professional, maintainable, and impressive to any senior AI/ML engineer reviewing your GitHub. Read this before writing a single line of code.

---

## 🏗️ Architecture Constraints

### 1. Hard Module Boundaries — The 7 Agents Are Isolated

Each agent (Ingestion, RAG, Research, Analyst, Writer, Verifier, Supervisor) must be **completely self-contained** inside its own file.

- No agent imports directly from another agent's file
- Agents communicate only through the **LangGraph shared state object** — nothing else
- All shared data shapes live in `orchestration/state.py` as Pydantic models
- This means you can swap, remove, or rewrite any agent without touching any other

```python
# ❌ Wrong — agent directly calling another agent
from agents.rag_agent import retrieve_chunks

class WriterAgent:
    def run(self, state):
        chunks = retrieve_chunks(state.query)   # direct coupling

# ✅ Correct — agent reads only from shared state
class WriterAgent:
    def run(self, state: DocuForgeState) -> DocuForgeState:
        chunks = state.retrieved_chunks         # reads from state
        ...
```

**Why:** Clean agent boundaries signal architectural maturity. A tangled agent graph where every agent calls every other agent is the single most common mistake in agentic AI projects. Interviewers who have built these systems in production will spot it instantly.

---

### 2. LangGraph State Is the Only Communication Channel

The `DocuForgeState` TypedDict in `orchestration/state.py` is the **single source of truth** for everything passing between agents.

- No function arguments passed directly between agent nodes
- No global variables used as inter-agent communication
- No shared mutable objects outside the state schema
- Every field the Supervisor reads or writes must be declared in the state schema first

```python
# orchestration/state.py — declare everything here
class DocuForgeState(TypedDict):
    query: str
    uploaded_file_path: str
    ingested_text: str
    retrieved_chunks: list[str]
    web_context: str
    analysis_result: AnalysisResult
    draft_report: str
    verified_report: str
    hallucination_score: float
    routing_decision: str
    agent_trace: Annotated[list[str], operator.add]
    error_log: Annotated[list[str], operator.add]
```

---

### 3. No Business Logic Inside API Routes

Your `api/routers/` files must contain only request parsing, service calls, and response formatting. Zero agent logic, zero LLM calls, zero database queries allowed inside router files.

```python
# ❌ Wrong — logic inside route
@router.post("/analyze")
async def analyze_document(file: UploadFile):
    text = extract_text(file)
    embeddings = embed(text)
    vectordb.add(embeddings)
    result = llm.invoke(text)
    return {"result": result}

# ✅ Correct — route just delegates
@router.post("/analyze")
async def analyze_document(
    file: UploadFile,
    service: DocumentService = Depends()
):
    return await service.run_analysis_pipeline(file)
```

---

### 4. Configuration Is Declarative — Never Hardcoded

Every configurable value lives in `config/docuforge_config.yaml`. No hardcoded model names, thresholds, chunk sizes, API endpoints, or retry counts anywhere in the codebase.

```yaml
# config/docuforge_config.yaml
llm:
  primary_model: "gemini-1.5-flash"
  fallback_model: "llama3"
  temperature: 0.2
  max_tokens: 4096

rag:
  chunk_size: 512
  chunk_overlap: 50
  top_k_results: 4
  semantic_weight: 0.6
  keyword_weight: 0.4

verifier:
  min_faithfulness_score: 0.85
  max_reflection_loops: 3
  hallucination_threshold: 0.75

ingestion:
  supported_formats: ["pdf", "png", "jpg", "mp3", "wav", "xlsx", "pptx"]
  max_file_size_mb: 50

eval:
  golden_dataset_path: "eval/test_dataset.json"
  min_accuracy_threshold: 0.80
  bias_similarity_threshold: 0.95
```

---

### 5. One Responsibility Per File — No "And" Files

No file should do more than one thing. If the file name requires the word "and", split it immediately.

| Too Broad — Split It | Correct |
|---|---|
| `rag_and_embeddings.py` | `chunker.py` + `embedder.py` |
| `agent_tools_and_memory.py` | `mcp_tools.py` + `memory_store.py` |
| `ingest_and_parse.py` | `file_ingester.py` + `multimodal_parser.py` |
| `eval_and_benchmark.py` | `accuracy_evaluator.py` + `benchmark_runner.py` |
| `llm_router_and_config.py` | `llm_router.py` + read from `docuforge_config.yaml` |

---

## 💻 Code Quality Constraints

### 6. Type Hints on Every Function — No Exceptions

Every function signature must have complete input and return type hints. `Any` is not acceptable unless you can justify it in a comment.

```python
# ❌ Wrong
def embed_chunks(chunks, model=None):
    ...

# ✅ Correct
def embed_chunks(
    chunks: list[str],
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> np.ndarray:
    ...
```

---

### 7. Pydantic Models for All Data Shapes

Any structured data passed between functions, returned from agents, or stored in the database must have a corresponding Pydantic model. No raw dicts as function arguments or return values.

```python
# ❌ Wrong
def run_verification(draft: dict) -> dict:
    ...

# ✅ Correct
def run_verification(draft: DraftReport) -> VerificationResult:
    ...

# models/agent_models.py
class DraftReport(BaseModel):
    content: str
    citations: list[str]
    agent_name: str
    confidence: float

class VerificationResult(BaseModel):
    verified_content: str
    faithfulness_score: float
    hallucination_detected: bool
    failed_claims: list[str]
    regenerate: bool
```

---

### 8. Docstrings on All Public Functions

Every public function (no underscore prefix) must have a docstring explaining what it does, what it takes, and what it returns. One concise paragraph maximum.

```python
def compute_hybrid_retrieval(
    query: str,
    vectordb: Chroma,
    bm25: BM25Retriever,
    top_k: int = 4
) -> list[Document]:
    """
    Retrieve relevant document chunks using a weighted combination of semantic
    vector search and BM25 keyword search.

    Returns the top-k most relevant Document objects ranked by the ensemble
    score, where semantic search contributes 60% and BM25 contributes 40%
    of the final relevance score.
    """
```

---

### 9. No Magic Numbers Anywhere

Every constant must be named and pulled from config or a dedicated constants file. A bare number sitting in business logic is always a bug waiting to happen.

```python
# ❌ Wrong
if faithfulness_score < 0.85:
    regenerate = True

# ✅ Correct
MIN_FAITHFULNESS = config.verifier.min_faithfulness_score
if faithfulness_score < MIN_FAITHFULNESS:
    regenerate = True
```

---

### 10. Use `logging` — Never `print()`

All diagnostic output in production code must go through Python's `logging` module with the appropriate level. `print()` anywhere outside of a test or example script is a red flag to every senior engineer who reviews your code.

```python
# ❌ Wrong
print(f"RAG retrieved {len(chunks)} chunks")
print("Verifier passed!")

# ✅ Correct
logger = logging.getLogger(__name__)
logger.info("RAG retrieved %d chunks for query: %s", len(chunks), query[:50])
logger.info("Verifier passed with faithfulness score: %.3f", score)
```

---

## 🤖 Agent & LangGraph Constraints

### 11. Every Agent Node Must Return a Full State Update

LangGraph agent nodes must always return the complete state changes they made. Never mutate state in place — return the updated fields explicitly.

```python
# ❌ Wrong — mutating state in place
def rag_agent(state: DocuForgeState):
    state["retrieved_chunks"] = retrieve(state["query"])

# ✅ Correct — return explicit update dict
def rag_agent(state: DocuForgeState) -> dict:
    chunks = retrieve(state["query"])
    return {
        "retrieved_chunks": chunks,
        "agent_trace": [f"RAG: retrieved {len(chunks)} chunks"]
    }
```

---

### 12. Supervisor Routing Logic Lives in One File Only

All conditional routing decisions must be in `orchestration/router.py`. No routing logic scattered inside individual agent files or API routes.

```python
# orchestration/router.py — routing lives here and only here
def route_from_supervisor(state: DocuForgeState) -> str:
    """
    Determine the next agent to invoke based on current task state.
    Returns the name of the next LangGraph node to execute.
    """
    if not state.get("ingested_text"):
        return "ingestion_agent"
    if not state.get("retrieved_chunks"):
        return "rag_agent"
    if state.get("routing_decision") == "needs_research":
        return "research_agent"
    if not state.get("analysis_result"):
        return "analyst_agent"
    ...
```

---

### 13. The Reflection Loop Has a Hard Maximum

The Verifier → Writer reflection loop must have a configurable maximum iteration count pulled from config. Never allow infinite regeneration loops.

```python
MAX_LOOPS = config.verifier.max_reflection_loops  # default: 3

if state["reflection_count"] >= MAX_LOOPS:
    logger.warning("Max reflection loops reached — returning best available draft")
    return {"verified_report": state["draft_report"], "routing_decision": "done"}
```

---

### 14. All LLM Calls Are Routed Through the LLM Router

No agent calls a specific LLM directly by name. All LLM invocations go through `core/llm_router.py` which handles model selection, fallback logic, and retry behaviour.

```python
# ❌ Wrong — hard-coupled to one provider
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# ✅ Correct — routed through the abstraction layer
from core.llm_router import get_llm
llm = get_llm(task_type="multimodal", has_image=True)
```

This means swapping your primary LLM from Gemini to Claude or LLaMA 3 is a single config change, not a codebase refactor.

---

## 🗄️ Database & Storage Constraints

### 15. All SQL and Vector Queries in Dedicated Query Files

No raw SQL strings or vectordb query logic scattered across business logic files. Every database interaction lives in a dedicated query file per module.

```
core/
├── rag/
│   └── vector_queries.py        ← all ChromaDB operations
├── memory/
│   └── db_queries.py            ← all PostgreSQL operations
└── eval/
    └── eval_queries.py          ← all evaluation data queries
```

---

### 16. Schema Migrations Are Versioned

The PostgreSQL schema must be defined in numbered migration files. Never alter the schema by running raw SQL manually or through ORM `create_all()` in production code.

```
db/
└── migrations/
    ├── 001_create_sessions_table.sql
    ├── 002_create_documents_table.sql
    ├── 003_create_agent_traces_table.sql
    └── 004_create_eval_results_table.sql
```

---

### 17. Secrets Never Live in Committed Files

All API keys, database URLs, and credentials live in `.env` which is gitignored. The repo contains only `.env.example` with placeholder values.

```bash
# .env.example — commit this
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
LANGCHAIN_API_KEY=your_langsmith_api_key_here
UPSTASH_REDIS_URL=your_upstash_redis_url_here

# .env — never commit this (in .gitignore)
```

An interviewer will clone your repo. If a real API key is in the git history, it is a hard disqualification.

---

## 🧪 Testing Constraints

### 18. Every Agent Must Have Unit Tests

Each agent file must have a corresponding test file that covers the main success path, a graceful failure path (bad input, LLM timeout), and the state update it returns.

```
tests/
├── agents/
│   ├── test_ingestion_agent.py
│   ├── test_rag_agent.py
│   ├── test_research_agent.py
│   ├── test_analyst_agent.py
│   ├── test_writer_agent.py
│   └── test_verifier_agent.py
├── rag/
│   ├── test_chunker.py
│   ├── test_embedder.py
│   └── test_hybrid_retriever.py
└── eval/
    ├── test_accuracy_evaluator.py
    └── test_bias_detector.py
```

---

### 19. The Eval Pipeline Must Have a Golden Dataset

The `eval/test_dataset.json` must contain a minimum of 20 question-answer pairs covering:
- Factual retrieval from a PDF
- Cross-document reasoning across two files
- A multimodal query (image or audio)
- A question that requires external research
- A trick question the agent should decline to answer or flag as uncertain

This dataset is used in CI to catch regression. If you change a prompt and accuracy drops below the configured threshold, CI fails.

---

### 20. Minimum Test Coverage: 70% Overall, 80% for RAG and Eval Core

```bash
# Run before every commit
pytest tests/ --cov=core --cov-report=term-missing --cov-fail-under=70
```

The RAG pipeline and evaluation pipeline are the technical heart of this project and must stay above 80% coverage because they are the most complex and failure-prone.

---

### 21. Bias Tests Are Paired and Automated

The bias test suite must contain a minimum of 10 paired test cases. Each pair asks the same question with only one variable changed (gender, document length, date, company size). The test asserts the agent's response does not differ suspiciously between the two.

```python
# tests/eval/test_bias_detector.py
BIAS_PAIRS = [
    ("What salary is appropriate for a male engineer?",
     "What salary is appropriate for a female engineer?"),
    ("Summarize the 2020 annual report",
     "Summarize the 2024 annual report"),
]
```

---

## 📁 File & Naming Constraints

### 22. Naming Conventions — Non-Negotiable

| Type | Convention | Example |
|---|---|---|
| Python modules | `snake_case.py` | `hybrid_retriever.py` |
| Classes | `PascalCase` | `RAGAgent`, `LLMRouter` |
| Functions | `snake_case` | `compute_faithfulness_score()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_CHUNK_SIZE` |
| Pydantic models | `PascalCase` + descriptive suffix | `DraftReport`, `VerificationResult` |
| Config keys | `snake_case` | `max_reflection_loops` |
| Test files | `test_` prefix | `test_verifier_agent.py` |

---

### 23. No `utils.py` Dumping Grounds

If you feel the urge to create a `utils.py`, stop and ask: "Which module does this actually belong to?" Every helper function belongs in a specific, named helper file. `utils.py` is where code goes to die.

```
❌ utils.py
✅ core/rag/text_cleaner.py
✅ core/ingestion/format_normalizer.py
✅ core/eval/scoring_helpers.py
```

---

### 24. No File Longer Than 300 Lines — No Function Longer Than 40 Lines

If a file exceeds 300 lines, it is doing too many things. Split it. If a function exceeds 40 lines, extract a helper. These are hard limits, not suggestions.

---

## 🌿 Git & Workflow Constraints

### 25. Commit Message Format — Conventional Commits

Every commit must start with a type prefix. No vague messages like "fix stuff" or "update code."

```bash
feat: add hybrid BM25 + semantic retriever to RAG agent
fix: handle empty chunk list in embedder gracefully
test: add golden dataset eval for verifier agent
docs: add architecture diagram to README
refactor: extract LLM routing logic into dedicated router file
chore: pin sentence-transformers to 2.6.1 in requirements
config: add max_reflection_loops to docuforge_config.yaml
```

---

### 26. Branch Strategy — Never Commit Directly to Main

```
main          — always working, always demo-ready, CI always green
develop       — integration branch for merging features
feature/xxx   — individual agent or pipeline features
fix/xxx       — bug fixes
eval/xxx      — evaluation and benchmarking work
```

Every merge to `main` must pass the full GitHub Actions CI pipeline. If CI is red, the branch does not merge.

---

### 27. GitHub Actions CI Must Pass on Every Push to Main

Your `.github/workflows/ci.yml` must run all four of these on every push:

```yaml
steps:
  - name: Lint
    run: ruff check .

  - name: Type Check
    run: mypy core/

  - name: Tests with Coverage
    run: pytest tests/ --cov=core --cov-fail-under=70

  - name: Eval Regression Check
    run: python eval/accuracy_evaluator.py --fail-below=0.80
```

If CI is failing, do not show the repo to anyone.

---

## 🤖 Copilot / AI Coding Assistant Constraints

### 28. Never Let Copilot Create Unsolicited Markdown Files

Copilot has a strong habit of generating `README.md`, `NOTES.md`, `TODO.md`, `PLAN.md`, `AGENT_GUIDE.md`, `SUMMARY.md`, and similar files automatically when you describe the project in natural language. These files do not belong in the repo unless you explicitly decided they do.

**Rule:** If your prompt does not say "create a markdown file" or "write a README", Copilot is not allowed to generate any `.md` file. If it does, delete it before committing.

**The only `.md` files that may exist in this repo:**
```
README.md          ← one file, written by you at the end
CONSTRAINTS.md     ← this file
CONTRIBUTING.md    ← optional
```

---

### 29. No Phase Numbers or Build Sequence References Anywhere

The project is built in phases internally. That is a build strategy — not part of the project. The final codebase must show zero evidence of phased construction.

**Never allowed** — in file names, folder names, variable names, comments, docstrings, or commit messages:

```
❌ phase1_ingestion.py
❌ step2_rag_setup.py
❌ stage3_agents.py
❌ part4_frontend.py
❌ /build_phase_2/
❌ # Phase 1: Set up ingestion
❌ # TODO: complete in phase 3
❌ feat(phase2): add RAG agent
```

A hiring manager cloning this repo should see a mature, complete system — not a construction site.

---

### 30. File Names Must Describe Function — Not Creation Order

Every file name must answer: **"What does this file do?"** — not "When was it made?"

```
❌ Bad
first_agent.py
new_retriever.py
updated_router.py
helper2.py
final_verifier.py
rag_v2.py

✅ Good
ingestion_agent.py          ← parses and normalizes uploaded files
hybrid_retriever.py         ← runs BM25 + semantic retrieval
llm_router.py               ← selects and routes LLM calls
multimodal_parser.py        ← extracts content from images and audio
hallucination_scorer.py     ← scores output faithfulness vs source
```

---

### 31. No Scratch Files, Exploratory Scripts, or Notebooks in Main Branch

Exploration and experimentation stay local. The only notebooks allowed are inside `examples/` with a clear, complete walkthrough purpose.

```
❌ Never commit these
scratch.py
try_rag.py
test_gemini_quick.py
debug_agent.py
explore_langraph.ipynb
notebook_v2.ipynb

✅ Allowed in examples/ only
examples/rag_walkthrough.py        ← complete, documented demo
examples/multiagent_demo.py        ← complete, documented demo
```

---

### 32. Copilot Prompt Template — Use This Before Every Generation

```
Build [specific class or function] in [exact file path].

Requirements:
- [functional requirement 1]
- [functional requirement 2]

Constraints:
- Do not create any new files other than [exact file path]
- Do not create any markdown files
- Do not add TODOs, placeholder comments, or pass statements
- Every function must have type hints and a one-paragraph docstring
- No hardcoded values — read everything from the config object
- Follow the project naming conventions in CONSTRAINTS.md
```

Being explicit about what Copilot should NOT create is as important as what it should create.

---

## 📖 Documentation Constraints

### 33. README Must Include These Sections — Nothing More, Nothing Less

- One paragraph "What is DocuForge AI?" for a non-technical reader
- One paragraph "Why does this matter?" explaining the document intelligence problem
- Quickstart: exactly 3 commands to get a working demo running
- Screenshot or GIF of the React dashboard with the live agent graph
- Architecture diagram showing all 7 agents and the LangGraph flow
- "How to run the evaluation suite" section
- A skill-to-feature mapping table linking each feature to the JD skills it covers

---

### 34. Every Module Directory Must Have a Module-Level Docstring in `__init__.py`

```python
# agents/__init__.py
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
```

---

## 🚫 Hard Rules — Never Break These

| Rule | Reason |
|---|---|
| No API keys hardcoded anywhere in the repo | An interviewer will clone your repo |
| No `print()` in production code — use `logging` | Shows engineering maturity |
| No `except Exception: pass` — always handle or re-raise with context | Silently swallowing errors is a senior engineer red flag |
| No commented-out code committed — use git branches | Dead code is noise |
| No file longer than 300 lines | Forces clean single-responsibility modules |
| No function longer than 40 lines | Forces readable, testable code |
| No `utils.py` — use specific named helpers | Prevents dumping grounds |
| `docker-compose up` must work on a fresh clone | This is your first impression |
| No raw dicts passed between agent functions — use Pydantic | Type safety across the full pipeline |
| No LLM called directly by name outside `llm_router.py` | Keeps provider swapping a one-line config change |
| The reflection loop must have a hard max iteration cap | Prevents infinite loops in production |
| Every `.env` value must have a matching entry in `.env.example` | Documents required credentials for collaborators |

---

## ✅ Pre-Demo Checklist

Before recording your demo video or showing this to anyone, verify every item below.

- [ ] `docker-compose up` works from a fresh clone with zero manual steps
- [ ] All 7 agents execute successfully on a sample PDF upload
- [ ] Multimodal ingestion works for at least PDF, one image format, and one audio file
- [ ] The React dashboard loads and shows the live LangGraph agent execution graph
- [ ] The Verifier Agent triggers at least one reflection loop visibly in the dashboard
- [ ] LangSmith tracing dashboard shows full agent traces with latency breakdown
- [ ] `pytest tests/ --cov=core` passes with 70%+ coverage
- [ ] `ruff check .` returns zero errors
- [ ] `mypy core/` returns zero errors
- [ ] GitHub Actions CI is green on the `main` branch
- [ ] The eval suite runs and prints accuracy, hallucination rate, and bias scores
- [ ] README has a dashboard screenshot and architecture diagram
- [ ] No hardcoded secrets anywhere — confirmed with `git grep "sk-"` and `git grep "AIza"`
- [ ] `.env.example` has an entry for every credential the project uses
- [ ] All 7 agents appear in the README skill-to-feature mapping table

If any item is unchecked, fix it before showing the project. A broken demo is worse than no demo.