"""
Types for agent run results: what the agent produces for each turn.
Used by both the app (runner, API) and evals.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCallRecord:
    """One tool invocation from an agent run."""
    name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentRunResult:
    """
    Result of running the agent on one user message.
    The agent (or LangGraph) must produce this shape so evals can score it.
    """
    route: str
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    raw_output: Any = None
