"""
End nodes: billing only. Tech support is now a real LLM-powered node in tech_support.py.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage

from app.agents.prompts import BILLING_REPLY
from app.schemas import AgentState


def billing_end_node(state: AgentState) -> dict:
    """Set route to billing and append standard reply."""
    return {
        "messages": [AIMessage(content=BILLING_REPLY)],
        "current_agent": "billing",
        "final_route": "billing",
        "tool_calls": [],
    }
