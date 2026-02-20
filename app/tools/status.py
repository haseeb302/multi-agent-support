"""
Customer status tool: process cancellations/changes (log to file).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from app.core import config


def update_customer_status_impl(
    customer_id: str,
    action: str,
    *,
    customer_updates_log_path: str,
) -> dict[str, Any]:
    """
    Implementation for update_customer_status tool.
    Appends a JSONL record to the log file.
    """
    cid = (customer_id or "").strip()
    act = (action or "").strip()
    if not cid:
        return {"ok": False, "error": "customer_id is required"}
    if not act:
        return {"ok": False, "error": "action is required"}

    log_path = Path(customer_updates_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "customer_id": cid,
        "action": act,
    }

    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return {"ok": True, "logged_to": str(log_path), "record": record}
    except Exception as e:
        return {"ok": False, "error": f"failed to write update log: {e!s}"}


@tool
def update_customer_status(customer_id: str, action: str) -> dict:
    """Process cancellations/changes (log to file)"""
    settings = config.get_settings()
    return update_customer_status_impl(
        customer_id=customer_id,
        action=action,
        customer_updates_log_path=settings.customer_updates_log_path,
    )

