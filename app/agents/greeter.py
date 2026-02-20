"""
Greeter & Orchestrator: identifies customer (email) and intent. Context-aware: uses
the previous turn's route so follow-ups (e.g. "what are the steps?" after tech support)
route back to the same specialist instead of being re-classified as need_help.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.prompts import (
    GREETER_ASK_WHAT_HELP,
    GREETER_COULDNT_FIND,
    GREETER_SYSTEM,
    GREETER_WELCOME,
)
from app.helpers import (
    has_valid_email,
    last_assistant_message,
    last_user_message,
    normalize_email,
)
from app.schemas import AgentState, GreeterOutput

VALID_INTENTS = frozenset({
    "retention",
    "process_cancellation",
    "tech_support",
    "billing",
    "need_help",
})


def _greeter_only_response(content: str, intent: str) -> dict:
    """State update that adds one assistant message and signals end of greeter turn."""
    return {
        "messages": [AIMessage(content=content)],
        "intent": intent,
        "current_agent": "greeter",
        "final_route": "greeter",
        "tool_calls": [],
    }


def greeter_node(state: AgentState) -> dict:
    """
    Single greeter node: welcome, couldn't find, ask what help, or hand off to specialist.
    Uses the previous turn's final_route so follow-ups within a specialist flow are preserved.
    """
    messages = state.get("messages") or []
    last_user = last_user_message(messages)
    previous_route = state.get("final_route") or ""

    # First turn: no user message at all → show welcome
    if not last_user:
        return _greeter_only_response(GREETER_WELCOME, "greeter_welcome")

    # First turn: user sent something but there's no prior assistant message
    last_assistant = last_assistant_message(messages)
    if not last_assistant:
        return _greeter_only_response(GREETER_WELCOME, "greeter_welcome")

    # Build context for LLM: include previous route so follow-ups stay in the same flow
    context_lines = []
    if previous_route and previous_route != "greeter":
        context_lines.append(f"[Previous specialist flow: {previous_route}]")
    context_lines.append(f"[Previous assistant message: {last_assistant or '(none)'}]")
    context_lines.append(f"\nCurrent customer message: {last_user}")
    user_content = "\n".join(context_lines)

    llm = get_llm().with_structured_output(GreeterOutput)
    out: GreeterOutput = llm.invoke([
        SystemMessage(content=GREETER_SYSTEM),
        HumanMessage(content=user_content),
    ])

    raw_email = out.email.strip() if out.email and isinstance(out.email, str) else None
    email = normalize_email(raw_email) if raw_email else None
    if not has_valid_email(email):
        email = None
    customer_email = email if email else state.get("customer_email")
    intent = (out.intent or "need_help").strip().lower()
    if intent not in VALID_INTENTS:
        intent = "need_help"

    # Greeter-only responses: add message and signal end
    if not has_valid_email(customer_email):
        return {
            **_greeter_only_response(GREETER_COULDNT_FIND, intent),
            "customer_email": None,
        }
    if intent == "need_help":
        return {
            **_greeter_only_response(GREETER_ASK_WHAT_HELP, intent),
            "customer_email": customer_email,
        }

    # Specialist intent + valid email: hand off (clear final_route so the router uses intent)
    return {
        "intent": intent,
        "customer_email": customer_email,
        "current_agent": "greeter",
        "final_route": "",
    }
