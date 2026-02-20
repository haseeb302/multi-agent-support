"""
Run the support graph for one user message and return reply + AgentRunResult.
Supports multi-turn via prior_messages and session_context (including final_route/intent).
"""

from __future__ import annotations

from langchain_core.messages import BaseMessage, HumanMessage

from app.agents.graph import get_compiled_graph
from app.schemas import AgentRunResult, AgentState, ToolCallRecord


def run_agent(
    user_message: str,
    *,
    prior_messages: list[BaseMessage] | None = None,
    session_context: dict | None = None,
) -> tuple[str, AgentRunResult, list[BaseMessage], dict]:
    """
    Run the graph for one turn and return (reply_text, AgentRunResult, updated_messages, session_update).

    session_context may include: customer_email, customer_id, customer_data, final_route, intent.
    final_route and intent from the previous turn are passed into the graph so the Greeter
    can route follow-ups to the correct specialist without re-classifying from scratch.
    """
    graph = get_compiled_graph()
    messages: list[BaseMessage] = list(prior_messages) if prior_messages else []
    messages.append(HumanMessage(content=user_message))
    ctx = session_context or {}
    initial: AgentState = {
        "messages": messages,
        "customer_email": ctx.get("customer_email"),
        "customer_id": ctx.get("customer_id"),
        "customer_data": ctx.get("customer_data"),
        # Carry over from previous turn for context-aware routing
        "final_route": ctx.get("final_route") or "",
        "intent": ctx.get("intent") or "",
        # Reset transient fields so previous-turn values don't leak
        "tool_calls": [],
        "current_agent": "",
    }
    final_state = graph.invoke(initial)
    route = final_state.get("final_route") or "retention"
    tool_calls_raw = final_state.get("tool_calls") or []
    tool_calls = [
        ToolCallRecord(name=t.get("name", ""), args=t.get("args", {}))
        for t in tool_calls_raw
    ]
    result = AgentRunResult(route=route, tool_calls=tool_calls, raw_output=final_state)

    final_messages = final_state.get("messages") or []
    reply = ""
    for m in reversed(final_messages):
        if getattr(m, "type", None) != "ai":
            continue
        # Skip tool-calling AI messages (no user-facing content)
        if hasattr(m, "tool_calls") and m.tool_calls:
            continue
        content = m.content if isinstance(m.content, str) else str(m.content)
        if content.strip():
            reply = content
            break

    session_update = {
        "customer_email": final_state.get("customer_email"),
        "customer_id": final_state.get("customer_id"),
        "customer_data": final_state.get("customer_data"),
        "final_route": final_state.get("final_route"),
        "intent": final_state.get("intent"),
    }
    return reply, result, final_messages, session_update


def agent_runner_for_evals(user_message: str) -> AgentRunResult:
    """Thin wrapper: run_agent(user_message) and return only AgentRunResult (for run_evals)."""
    _, result, _, _ = run_agent(user_message)
    return result
