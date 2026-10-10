# ⚡ QuantBuild

**An AI-Powered Full-Stack Architecture Designer and Intelligent Web Application Builder**

> *Describe the application. QuantBuild designs, builds, tests and evolves it.*

QuantBuild transforms natural-language application requirements into complete,
production-oriented full-stack web applications. Instead of a simple
prompt-to-code generator, it models the software development lifecycle as a
**multi-agent AI workflow**:

```
Requirement → Architecture → Database → API → UI/UX → Code
           → Testing → Debugging → Security → Deployment → Continuous Modification
```

---

## ✨ What it does

Given a plain-English request like:

> *"Build an e-commerce platform where customers can browse products, add items
> to a cart, make payments and track their orders."*

QuantBuild automatically produces:

| Artifact | Description |
| --- | --- |
| 📋 Structured specification | App type, user roles, features, entities, security model |
| 🏗️ System architecture | Style selection (monolith / modular monolith / microservices) with rationale + Mermaid diagram |
| 🗄️ Database design | Typed schema, relationships, ER diagram, SQL DDL migrations, indexes |
| 🔌 API contract | Full OpenAPI 3.0 spec (auth + CRUD per resource) |
| 🖥️ Frontend | React 18 + TypeScript + Tailwind SPA (pages, routing, auth, API client) |
| ⚙️ Backend | FastAPI + SQLAlchemy + JWT auth + RBAC + rate limiting |
| 🧪 Test suite | pytest: auth, CRUD, RBAC, validation — **executed automatically** |
| 🐞 Debug loop | Validation pipeline (syntax → deps → static → build → tests) with autonomous repair |
| 🛡️ Security report | 0–100 score, findings and suggested fixes |
| 📚 Documentation | README, architecture, API, database and deployment docs |
| 🚀 Deployment | Dockerfiles, docker-compose, nginx, GitHub Actions CI |
| 💬 NL modification | *"Add a wishlist feature"* — impact analysis across all layers, then re-generation + re-validation |

A **Central Project Context** (architecture memory) is shared by every agent,
which keeps the frontend, backend, database and API contract consistent with
each other.

---

## 🤖 The 12 agents

| Agent | Responsibility |
| --- | --- |
| 🧠 Project Manager Agent | Central orchestrator — coordinates the entire pipeline |
| 📝 Requirement Agent | NL requirement → structured specification |
| 🏗️ Architecture Agent | System design, style selection + rationale, diagrams |
| 🗄️ Database Agent | Entities, relationships, ER diagram, SQL DDL |
| 🔌 API Design Agent | OpenAPI contract synchronized with all layers |
| 🎨 UI/UX Agent | Screens, components, navigation |
| 🖥️ Frontend Agent | React + TypeScript + Tailwind code |
| ⚙️ Backend Agent | FastAPI routes, services, models, auth |
| 🧪 Testing Agent | Test generation + execution, requirement traceability |
| 🐞 Debugging Agent | Validation pipeline + autonomous repair loop |
| 🛡️ Security Agent | Vulnerability analysis + security score |
| 📚 Documentation Agent | Technical documentation |
| 🚀 Deployment Agent | Docker / CI-CD configuration |

Agents retrieve relevant engineering knowledge before working through a built-in
**RAG knowledge system** (TF-IDF retrieval over architecture, FastAPI, React,
security, database and coding-standards documents).

---

## 🚀 Quick start

### Prerequisites

- Python 3.11+ and Node 20+
- Nothing else — QuantBuild works out of the box in **offline mode** (deterministic
  heuristic agents). Plug in an LLM later for the full AI experience.

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (proxies /api + /ws to :8000)
```

…or build it and let the backend serve it at `http://localhost:8000`:

```bash
cd frontend && npm run build
```

### 3. Build an app

1. Open the UI and describe your application in natural language.
2. Watch the 12 agents work live in the pipeline console.
3. Explore the generated spec, architecture diagram, ER diagram, API contract,
   files, test results, security report, docs and deployment configs.
4. Click **▶ Run in Sandbox** to boot the generated backend and use its live API.
5. Type *"Add a wishlist feature"* to modify the app in natural language.
6. **Download .zip** — the project is deployment-ready.

---

## 🧠 LLM configuration (optional)

QuantBuild auto-detects providers. Create `.env` in the project root:

```bash
# OpenAI or any OpenAI-compatible API (Azure, Groq, OpenRouter, local servers)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
# OPENAI_BASE_URL=https://api.openai.com/v1
# LLM_MODEL=gpt-4o-mini

# Anthropic
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-...

# Local Ollama
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434
# LLM_MODEL=llama3.1
```

Without keys, every agent falls back to deterministic offline heuristics — the
whole pipeline (generation, testing, debugging, security, modification) still
works end-to-end, which also makes demos and CI completely reproducible.

---

## 🏛️ Platform architecture

```
quantbuild/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI API + WebSocket event stream
│   │   ├── config.py               # settings / LLM provider auto-detection
│   │   ├── agents/                 # the 12 specialized agents + orchestrator
│   │   ├── core/
│   │   │   ├── llm.py              # OpenAI / Anthropic / Ollama / offline client
│   │   │   ├── nlp.py              # offline requirement-understanding engine
│   │   │   ├── context.py          # Central Project Context (architecture memory)
│   │   │   ├── rag.py              # RAG knowledge system (TF-IDF retrieval)
│   │   │   ├── validation.py       # syntax → deps → static → build → tests
│   │   │   ├── sandbox.py          # isolated preview runner for generated apps
│   │   │   └── events.py           # pipeline event bus (live UI streaming)
│   │   ├── generators/             # backend / frontend / tests / docs / deploy codegen
│   │   └── knowledge/              # RAG knowledge base (markdown)
│   └── tests/                      # QuantBuild's own test suite
├── frontend/                       # QuantBuild UI (React + TS + Tailwind + Mermaid)
└── workspace/                      # generated projects land here (gitignored)
```

### API surface

| Endpoint | Purpose |
| --- | --- |
| `POST /api/projects` | Create a project from a natural-language requirement (pipeline starts) |
| `GET /api/projects` / `GET /api/projects/{id}` | List / full project state |
| `POST /api/projects/{id}/modify` | Natural-language modification with impact analysis |
| `GET /api/projects/{id}/files` · `…/files/content` | Browse the generated codebase |
| `GET /api/projects/{id}/download` | Download the generated app as a zip |
| `POST` / `GET` / `DELETE …/preview` | Sandbox lifecycle for the generated backend |
| `WS /ws/projects/{id}` | Live multi-agent pipeline events |
| `GET /api/config` | Active LLM provider / mode |

---

## 🧪 Running QuantBuild's own tests

```bash
cd backend
python -m pytest tests -q
```

The suite covers the NLP engine, RAG retrieval, the REST API, and a full
end-to-end pipeline run (including executing the *generated* app's tests).

---

## 🔐 Security & reliability design

- Generated apps use PBKDF2-HMAC-SHA256 password hashing, signed JWTs, RBAC and
  auth rate limiting; CORS and secrets are environment-driven.
- The Security Agent statically scans generated code for hardcoded secrets,
  SQL injection, XSS, insecure CORS, eval/exec and dependency issues.
- Validation never trusts generated code: syntax, dependencies, static analysis,
  import verification and the generated test suite must all pass.
- The sandbox runs generated apps in an isolated subprocess with their own
  database and port; sensitive deployment operations are left to the user.

## 🛣️ Future scope

Voice-based development · multilingual requirements · AI-generated UI
prototypes · mobile/desktop generation · microservice generation · cost
estimation · performance prediction · self-healing apps · git integration ·
autonomous CI/CD · RL-based architecture optimization.
