"""
Retention offer tool: generate offers using retention_rules.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from app.core import config


def _normalize_reason(reason: str) -> str:
    return (reason or "").strip().lower()


def _normalize_tier(customer_tier: str) -> str:
    return (customer_tier or "").strip().lower()


def _tier_to_rules_key(tier: str) -> str | None:
    if tier in {"premium", "premier"}:
        return "premium_customers"
    if tier in {"regular", "standard"}:
        return "regular_customers"
    if tier in {"new"}:
        return "new_customers"
    return None


def _split_reason(reason: str) -> tuple[str, str | None]:
    """
    Accepts formats like:
      - financial_hardship
      - product_issues:overheating
      - product_issues.overheating
      - service_value:care_plus_premium
      - overheating (alias for product_issues:overheating)
      - care_plus_premium (alias for service_value:care_plus_premium)
    """
    r = _normalize_reason(reason)
    if ":" in r:
        a, b = r.split(":", 1)
        return a, (b or None)
    if "." in r:
        a, b = r.split(".", 1)
        return a, (b or None)

    # Aliases for convenience
    if r in {"overheating", "battery_issues", "battery"}:
        return "product_issues", (
            "overheating" if r == "overheating" else "battery_issues"
        )
    if r in {"care_plus_premium", "care_plus_basic"}:
        return "service_value", r

    return r, None


def calculate_retention_offer_impl(
    customer_tier: str,
    reason: str,
    *,
    retention_rules_path: str,
) -> dict[str, Any]:
    """
    Implementation for calculate_retention_offer tool.

    Returns:
      - ok: bool
      - offers: list[dict]
      - category: str
      - reason: str
      - error: str (if ok is False)
    """
    tier = _normalize_tier(customer_tier)
    r = _normalize_reason(reason)
    if not r:
        return {"ok": False, "error": "reason is required"}

    path = Path(retention_rules_path)
    if not path.exists():
        return {"ok": False, "error": f"retention_rules.json not found at {path}"}

    try:
        rules = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError) as e:
        return {"ok": False, "error": f"failed to read retention_rules.json: {e!s}"}

    category, sub = _split_reason(r)

    # financial_hardship depends on tier
    if category == "financial_hardship":
        key = _tier_to_rules_key(tier)
        if key is None:
            return {
                "ok": False,
                "error": f"unknown customer_tier '{customer_tier}' for financial_hardship",
            }
        offers = (rules.get("financial_hardship", {}) or {}).get(key, [])
        return {
            "ok": True,
            "category": "financial_hardship",
            "reason": r,
            "customer_tier": tier,
            "offers": offers,
            "authorization_levels": rules.get("authorization_levels", {}),
        }

    # product_issues uses a subreason like overheating/battery_issues
    if category == "product_issues":
        if not sub:
            return {
                "ok": False,
                "error": "product_issues requires a subreason (e.g. 'product_issues:overheating')",
            }
        offers = (rules.get("product_issues", {}) or {}).get(sub, [])
        if not offers:
            return {
                "ok": False,
                "error": f"no offers configured for product_issues:{sub}",
            }
        return {
            "ok": True,
            "category": "product_issues",
            "reason": f"product_issues:{sub}",
            "customer_tier": tier,
            "offers": offers,
            "authorization_levels": rules.get("authorization_levels", {}),
        }

    # service_value uses a plan key like care_plus_premium
    if category == "service_value":
        plan_key = sub or "care_plus_premium"
        offers = (rules.get("service_value", {}) or {}).get(plan_key, [])
        if not offers:
            return {
                "ok": False,
                "error": f"no offers configured for service_value:{plan_key}",
            }
        return {
            "ok": True,
            "category": "service_value",
            "reason": f"service_value:{plan_key}",
            "customer_tier": tier,
            "offers": offers,
            "authorization_levels": rules.get("authorization_levels", {}),
        }

    return {
        "ok": False,
        "error": f"unknown reason '{reason}'. Supported: financial_hardship, product_issues:<sub>, service_value:<plan>",
    }


@tool
def calculate_retention_offer(customer_tier: str, reason: str) -> dict:
    """Generate offers using retention_rules.json"""
    settings = config.get_settings()
    return calculate_retention_offer_impl(
        customer_tier=customer_tier,
        reason=reason,
        retention_rules_path=settings.retention_rules_path,
    )
