"""
Custom evals for the 5 test conversations.
Evaluates routing and tool usage only (no content checks).
"""
from evals.dataset import EVAL_CASES, get_eval_cases
from evals.runner import run_evals, EvalResult, AgentRunResult

__all__ = [
    "EVAL_CASES",
    "get_eval_cases",
    "run_evals",
    "EvalResult",
    "AgentRunResult",
]
