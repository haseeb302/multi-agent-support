"""
Customer data tool: load customer profile from customers.csv.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from app.core import config
from app.helpers import normalize_email


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    v = str(value).strip()
    if v == "":
        return None
    return int(float(v))


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    v = str(value).strip()
    if v == "":
        return None
    return float(v)


def _parse_customer_row(row: dict[str, str]) -> dict[str, Any]:
    # Keep original columns but add typed numeric fields where helpful.
    parsed: dict[str, Any] = dict(row)
    parsed["monthly_charge"] = _to_float(row.get("monthly_charge"))
    parsed["total_spent"] = _to_float(row.get("total_spent"))
    parsed["support_tickets_count"] = _to_int(row.get("support_tickets_count"))
    parsed["account_health_score"] = _to_int(row.get("account_health_score"))
    parsed["tenure_months"] = _to_int(row.get("tenure_months"))
    return parsed


def get_customer_data_impl(email: str, *, customers_csv_path: str) -> dict[str, Any]:
    """
    Implementation for get_customer_data tool.
    Returns a stable dict that includes:
      - ok: bool
      - found: bool
      - customer: dict (when found)
      - error: str (when ok is False)
    """
    normalized = normalize_email(email)
    if not normalized:
        return {"ok": False, "found": False, "error": "email is required"}

    path = Path(customers_csv_path)
    if not path.exists():
        return {"ok": False, "found": False, "error": f"customers.csv not found at {path}"}

    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if normalize_email(row.get("email", "")) == normalized:
                    customer = _parse_customer_row(row)
                    return {"ok": True, "found": True, "customer": customer}
            return {"ok": True, "found": False}
    except (OSError, csv.Error, ValueError) as e:
        return {"ok": False, "found": False, "error": f"failed to read customers.csv: {e!s}"}


@tool
def get_customer_data(email: str) -> dict:
    """Load customer profile from customers.csv"""
    settings = config.get_settings()
    return get_customer_data_impl(email, customers_csv_path=settings.customers_csv_path)

