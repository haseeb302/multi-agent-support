# Custom evals (5 test conversations)

Evals check **routing** and **tool usage** only (no content/reply checks).

## Dataset

- **money_problems** – "can't afford care+ anymore, need to cancel" → retention, use customer data + retention offer; must not cancel in first turn.
- **phone_problems** – "phone keeps overheating, want to return and cancel" → retention, offer replacement/upgrade; must not cancel in first turn.
- **questioning_value** – "never used care+, maybe get rid of it?" → retention, explain value + cheaper options; must not cancel in first turn.
- **technical_help** – "phone won't charge, tried different cables" → tech_support; must not call `update_customer_status` or `calculate_retention_offer`.
- **billing_question** – "charged $15.99 but thought care+ was $12.99" → billing; must not cancel or offer retention.

## Agent contract

The agent (or LangGraph run) must expose a result in this shape so evals can score it:

```python
from evals.schemas import AgentRunResult, ToolCallRecord

# After running the graph for one user message, produce:
result = AgentRunResult(
    route="retention" | "tech_support" | "billing" | "processor",
    tool_calls=[
        ToolCallRecord(name="get_customer_data", args={"email": "..."}),
        ToolCallRecord(name="calculate_retention_offer", args={...}),
    ],
)
```

- **route**: The path the conversation took: `retention` (Problem Solver), `tech_support`, `billing`, or `processor` (cancel executed).
- **tool_calls**: List of tool invocations during that turn (so we can assert required and forbidden tools).

You can also return a **dict** with keys `route` and `tool_calls` (list of `{"name": "...", "args": {...}}`); the runner will convert it.

## How to run evals

### In code

```python
from evals import run_evals
from evals.schemas import AgentRunResult

def my_agent_runner(user_message: str) -> AgentRunResult:
    # Run your LangGraph / agent and extract route + tool_calls
    ...

results = run_evals(my_agent_runner)
for r in results:
    print(r.case_id, "PASS" if r.passed else "FAIL", r.details)
```

### With pytest

```bash
pytest tests/test_evals.py -v
```

Current tests use a **mock agent**; once the real agent exists, add a test that calls `run_evals(real_agent_runner)` and assert all 5 pass.

### Run specific cases

```python
results = run_evals(my_agent_runner, case_ids=["money_problems", "technical_help"])
```

## Files

- `evals/dataset.py` – The 5 cases and criteria.
- `evals/schemas.py` – `EvalCase`, `AgentRunResult`, `EvalResult`, `ToolCallRecord`.
- `evals/runner.py` – `run_evals(agent_runner)` and criteria checking.
- `tests/test_evals.py` – Pytest tests for dataset and runner (with mocks).
