# Build Plan: TechFlow Customer Support Chat API

This document lists **in sequence** what we will build for the API, and **how to test** after each step so we can verify everything works before moving on. Frontend is planned after backend + AI integration and all tests pass.

---

## Tech choices

- **Vector DB:** Pinecone (not FAISS)
- **API:** FastAPI
- **Orchestration:** LangChain / LangGraph
- **Data:** `docs/customers.csv`, `docs/retention_rules.json`, policy docs in `docs/`
- **LLM:** Google Gemini (free tier) with function calling

---

## Project structure (current)

```
multi-agent-chat/
├── app/
│   ├── main.py              # FastAPI app
│   ├── api/                 # Routers
│   │   └── health.py
│   ├── core/                # Config
│   │   └── config.py
│   ├── schemas/             # Request/response models
│   ├── services/            # RAG, agent orchestration
│   ├── tools/               # LangChain tools (customer, offer, update)
│   └── agents/              # LangGraph agents
├── docs/                    # Policy docs + customers.csv, retention_rules.json
├── data/                    # customer_updates.log
├── evals/                   # Custom evals (5 conversations, routing + tools)
│   ├── dataset.py           # Eval cases
│   ├── runner.py            # run_evals(agent_runner)
│   ├── schemas.py           # AgentRunResult, EvalCase, EvalResult
│   └── README.md            # Contract and usage
├── tests/
│   └── test_evals.py        # Eval tests (mock agent)
├── requirements.txt
├── .env.example
└── BUILD_PLAN.md            # This file
```

---

## Build sequence (API + AI)

### Phase 1: Foundation and data access

| Step | What we build | How to test |
|------|----------------|-------------|
| **1.1** | FastAPI app with health endpoints | `pytest tests/` and `GET /health`, `GET /health/ready` |
| **1.2** | **Tools:** `get_customer_data(email)` reading `docs/customers.csv` | Unit test: call tool with known email (e.g. `sarah.chen@email.com`), assert profile returned |
| **1.3** | **Tools:** `calculate_retention_offer(customer_tier, reason)` using `docs/retention_rules.json` | Unit test: e.g. `premium` + `financial_hardship` → pause/discount options returned |
| **1.4** | **Tools:** `update_customer_status(customer_id, action)` writing to `data/customer_updates.log` | Unit test: call tool, then read log file and assert line appended |
| **1.5** | Optional **tools API:** `GET /tools/customer?email=...` (and/or internal only) | Request from API or test client, verify response matches tool output |

**Checkpoint:** All three tools work with real files; tests pass.

---

### Phase 2: RAG with Pinecone

| Step | What we build | How to test |
|------|----------------|-------------|
| **2.1** | Script or startup step: chunk policy docs (`return_policy.md`, `care_plus_benefits.md`, `troubleshooting_guide.md`), embed, upsert to **Pinecone** index | Run script; check Pinecone dashboard for vectors; or call a small “index docs” CLI/endpoint |
| **2.2** | **RAG service:** query Pinecone by user message (or intent), return top-k chunks | Unit test: query e.g. “refund policy for premium customers” → chunks from return_policy.md |
| **2.3** | Optional **RAG API:** `POST /rag/query` with `{"query": "..."}` for manual verification | curl/Postman; assert response contains relevant policy text |

**Checkpoint:** Policy documents are in Pinecone; RAG returns relevant chunks for sample queries.

---

### Phase 3: Agents and LangGraph

| Step | What we build | How to test |
|------|----------------|-------------|
| **3.1** | **State schema:** conversation messages, `customer_id`, `intent` (cancel/tech/billing/unknown), `current_agent`, etc. | N/A (used in graph) |
| **3.2** | **Greeter agent:** identify customer (from message or ask email), classify intent (cancel vs tech vs billing), output routing decision | Unit test: mock LLM or use real LLM; feed “I want to cancel” vs “phone won’t charge”; assert intent and route |
| **3.3** | **Problem Solver agent:** has access to tools + RAG; offers retention (discount/pause/replacement) using customer data and rules; hands off to Processor only when user insists on canceling | Test with a short conversation: “can’t afford care+, need to cancel” → expect offer (tool calls + RAG), not immediate cancel |
| **3.4** | **Processor agent:** calls `update_customer_status` and confirms cancellation/change | Unit test: after “confirm cancel”, assert tool called and log updated |
| **3.5** | **LangGraph workflow:** Greeter → conditional edges → Problem Solver / Processor / “tech support” / “billing” end states; state passed between nodes | Integration test: run graph with 2–3 sample messages; assert correct node sequence and final state |
| **3.6** | **Prompts:** system prompts for each agent (from retention_playbook / assignment); ensure empathy and correct use of tools/RAG | Manual + 5 conversation tests below |

**Checkpoint:** Full graph runs; intent classification and handoffs work; tools and RAG are used inside the graph.

---

### Phase 4: Chat API and 5 conversation tests

| Step | What we build | How to test |
|------|----------------|-------------|
| **4.1** | **Chat API:** `POST /chat` (or `POST /chat/message`) with `session_id`, `message`; run LangGraph; return assistant reply and optionally updated state | `POST /chat` with test message; assert 200 and reply text |
| **4.2** | Session handling: in-memory (or simple store) by `session_id` so multi-turn state is preserved | Two requests with same `session_id`; second message has context from first |
| **4.3** | **Official 5 tests:** run the 5 required conversations (money problems, phone problems, questioning value, technical help, billing question) | **Evals:** `run_evals(real_agent_runner)` must pass all 5 cases (routing + tool usage). See `evals/README.md` for agent contract. |

**Checkpoint:** All 5 assignment conversations pass (evals green); API is ready for a frontend.

---

### Phase 5: Polish and readiness

| Step | What we build | How to test |
|------|----------------|-------------|
| **5.1** | **Readiness:** `GET /health/ready` checks Pinecone (and optionally LLM) reachable | Call `/health/ready`; if Pinecone is down, return 503 or `ready: false` |
| **5.2** | Error handling and fallbacks in tools and graph (missing customer, missing index, LLM errors) | Trigger missing email, invalid tier; assert graceful response |
| **5.3** | README: how to run (uvicorn), env vars, how to run tests and the 5 conversations | Follow README from clean clone; run tests and one chat |

**Checkpoint:** Production-ready API; clear instructions for reviewers.

---

## How to test during development

1. **Run all tests**
   ```bash
   pytest tests/ -v
   ```

2. **Run API locally**
   ```bash
   uvicorn app.main:app --reload
   ```
   - Open http://127.0.0.1:8000/docs for Swagger.
   - Call `GET /` and `GET /health`, `GET /health/ready`.

3. **After each phase:** run the “How to test” items for that phase; fix any failures before moving on.

4. **Evals:** Custom evals are in `evals/`. Run with `pytest tests/test_evals.py -v`. Once the agent exists, wire it into `run_evals()` so the 5 cases are scored automatically (routing + tool usage; no content check). See `evals/README.md`.

5. **Before frontend:** ensure the 5 evals pass and chat API is stable.

---

## Frontend (after backend is done)

- **When:** After Phase 4 (and preferably Phase 5) are complete and all tests pass.
- **Scope:** Small frontend (e.g. one page: chat input + message list) that calls `POST /chat` and displays replies.
- **Stack:** Your choice (e.g. React, Vue, or simple HTML + fetch). We can add a `frontend/` directory and document it in the README.

---

## Summary order

1. **Phase 1:** Tools (customer, retention offer, update status) + tests.  
2. **Phase 2:** Pinecone RAG (index docs, query service) + tests.  
3. **Phase 3:** LangGraph agents (Greeter, Problem Solver, Processor) and workflow + tests.  
4. **Phase 4:** Chat API + session + 5 conversation tests.  
5. **Phase 5:** Readiness, errors, README.  
6. **Frontend:** Once backend and all tests pass.

This order keeps each step testable and ensures we can verify behavior at every stage.
