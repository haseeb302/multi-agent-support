"""
Shared helpers: email validation/normalization, message extraction, retention reason,
conversation summary, tool records, tier extraction.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas import AgentState

MAX_HISTORY_MESSAGES = 20


def last_user_message(messages: list) -> str | None:
    """Last human message content, or None if none."""
    for m in reversed(messages):
        if getattr(m, "type", None) == "human":
            content = getattr(m, "content", None)
            return (
                content
                if isinstance(content, str)
                else str(content) if content is not None else None
            )
    return None


def last_assistant_message(messages: list) -> str:
    """Last AI message content, or empty string."""
    for m in reversed(messages):
        if getattr(m, "type", None) == "ai":
            content = getattr(m, "content", None)
            return (
                content
                if isinstance(content, str)
                else str(content) if content is not None else ""
            )
    return ""


def conversation_summary(messages: list, max_turns: int = 10) -> str:
    """Build a compact text summary of recent conversation for injection into LLM context."""
    lines: list[str] = []
    for m in messages[-(max_turns * 2):]:
        role = getattr(m, "type", "unknown")
        content = getattr(m, "content", "") or ""
        if isinstance(content, str):
            text = content[:300]
        else:
            text = str(content)[:300]
        if role == "human":
            lines.append(f"Customer: {text}")
        elif role == "ai":
            lines.append(f"Agent: {text}")
    return "\n".join(lines) if lines else "No prior conversation."


def build_retention_reason(category: str, sub: str | None) -> str:
    """Build reason string for calculate_retention_offer from schema category + sub."""
    c = (category or "").strip().lower()
    if c == "financial_hardship":
        return "financial_hardship"
    if c == "product_issues":
        s = (sub or "overheating").strip().lower()
        if s not in ("overheating", "battery_issues"):
            s = "overheating"
        return f"product_issues:{s}"
    if c == "service_value":
        s = (sub or "care_plus_premium").strip().lower()
        if s not in ("care_plus_premium", "care_plus_basic"):
            s = "care_plus_premium"
        return f"service_value:{s}"
    return "financial_hardship"


def normalize_email(email: str | None) -> str:
    """Return trimmed, lowercased email or empty string."""
    return (email or "").strip().lower()


def has_valid_email(email: str | None) -> bool:
    """True if value looks like an email (non-empty and contains @)."""
    if not email or not isinstance(email, str):
        return False
    return "@" in normalize_email(email)


def has_valid_email_in_state(state: "AgentState") -> bool:
    """True if state has a valid customer_email."""
    email = state.get("customer_email") if state else None
    return has_valid_email(email)


def extract_tier(customer_data: dict | None, default: str = "regular") -> str:
    """Safely extract and normalize the tier from customer data."""
    if not customer_data or not isinstance(customer_data, dict):
        return default
    raw = customer_data.get("tier")
    if isinstance(raw, str) and raw.strip():
        return raw.strip().lower()
    return default


def tool_record(name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a standardised tool-call record dict for state.tool_calls."""
    return {"name": name, "args": args or {}}
