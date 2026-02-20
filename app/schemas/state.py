"""
LangGraph agent state: shared state passed between Greeter, Problem Solver, and Processor.
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """State passed between Greeter, Problem Solver, and Processor."""

    messages: Annotated[list, add_messages]
    intent: str
    customer_email: str | None
    customer_id: str | None
    customer_data: dict | None
    current_agent: str
    final_route: str
    tool_calls: list[dict]
