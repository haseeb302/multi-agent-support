# TechFlow Customer Support Chat

Multi-agent customer support system built with **FastAPI**, **LangGraph**, and **Next.js**. Routes customers through Greeter, Problem Solver (retention), Tech Support, Processor (cancellation), and Billing agents using structured LLM output, RAG (Pinecone), and tool-calling.

## Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key
- Pinecone account (API key + index with integrated embedding)

## Setup

### 1. Clone and install

```bash
git clone <repo-url> && cd multi-agent-chat

# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd web/web-support
npm install
cd ../..
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in your keys in `.env`:

| Variable | Required | Description |
|---|---|---|
| `LLM_API_KEY` | Yes | OpenAI API key |
| `LLM_MODEL` | No | Defaults to `gpt-4o-mini` |
| `PINECONE_API_KEY` | Yes | Pinecone API key |
| `PINECONE_INDEX_NAME` | Yes | Your Pinecone index name |

### 3. Index documents into Pinecone

Your Pinecone index must have an integrated embedding model configured (e.g. `llama-text-embed-v2`). Then run:

```bash
python scripts/embed_and_upload.py
```

This chunks and uploads `docs/return_policy.md`, `docs/care_plus_benefits.md`, and `docs/troubleshooting_guide.md`.

## Run

### Backend (FastAPI)

```bash
uvicorn app.main:app --reload --port 8000
```

API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

### Frontend (Next.js)

```bash
cd web/web-support
npm run dev
```

Opens at [http://localhost:3000](http://localhost:3000).

## Run Evals

```bash
python -c "
from evals import run_evals
from app.agents.runner import agent_runner_for_evals
run_evals(agent_runner_for_evals)
"
```

## Project Structure

```
app/
├── agents/          # LangGraph nodes: greeter, problem_solver, tech_support, processor
├── api/             # FastAPI routes: /chat, /health
├── core/            # Config (env, paths)
├── helpers.py       # Shared utilities
├── schemas/         # Pydantic models and state
├── services/        # RAG (Pinecone), session store
└── tools/           # LangChain tools: customer data, retention offers, status updates
docs/                # Policy docs, customer CSV, retention rules
evals/               # Eval harness and test cases
scripts/             # Pinecone embed script, CLI runner
web/web-support/     # Next.js frontend
```
