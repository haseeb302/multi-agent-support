"""
In-memory session store for chat history.
Keyed by session_id; each session holds messages, customer data, and routing state.
"""
from __future__ import annotations

from typing import Any

_store: dict[str, dict[str, Any]] = {}


def set_session(session_id: str, data: dict[str, Any]) -> None:
    """Save session data."""
    _store[session_id] = data


def get_or_create(session_id: str) -> tuple[dict[str, Any], bool]:
    """Return (session_data, created). Creates with empty messages if missing."""
    if session_id in _store:
        return _store[session_id], False
    data: dict[str, Any] = {"messages": []}
    _store[session_id] = data
    return data, True
