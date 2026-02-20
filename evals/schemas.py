"""
Types for evals: what the agent must return and what each case expects.
AgentRunResult and ToolCallRecord are canonical in app.schemas.run_result.
"""
from dataclasses import dataclass, field

from app.schemas.run_result import AgentRunResult, ToolCallRecord

__all__ = [
    "AgentRunResult",
    "ToolCallRecord",
    "EvalCase",
    "EvalResult",
]


@dataclass
class EvalCase:
    """One eval test case (from the 5 required conversations)."""
    id: str
    user_message: str
    expected_route: str
    expected_tools_any: list[str]
    forbidden_tools: list[str]
    description: str


@dataclass
class EvalResult:
    """Result of evaluating one case."""
    case_id: str
    passed: bool
    details: str
    actual_route: str | None = None
    actual_tool_names: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
