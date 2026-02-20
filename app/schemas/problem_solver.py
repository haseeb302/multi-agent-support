"""
Structured output schema for the Problem Solver agent (LLM).
Maps to retention_rules.json categories and troubleshooting/tech-support handling.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RetentionReasonCategory = Literal[
    "financial_hardship",
    "product_issues",
    "service_value",
]

RetentionReasonSub = Literal[
    "overheating",
    "battery_issues",
    "care_plus_premium",
]

ProblemSolverAction = Literal[
    "offer_retention",
    "direct_to_tech_support",
    "user_insisted_cancellation",
]

TechHandling = Literal[
    "help_in_chat",
    "escalate_immediate",
    "schedule_appointment",
    "customer_can_handle",
]


class ProblemSolverOutput(BaseModel):
    """Single structured output: analysis (reason, action) and reply text."""

    retention_reason_category: RetentionReasonCategory = Field(
        default="financial_hardship",
        description="Category for retention_rules.json: financial_hardship, product_issues, or service_value.",
    )
    retention_reason_sub: str | None = Field(
        default=None,
        description="Sub-key: overheating, battery_issues, or care_plus_premium. Use null for financial_hardship.",
    )
    action: ProblemSolverAction = Field(
        default="offer_retention",
        description="offer_retention = present offers; direct_to_tech_support = send to tech support; user_insisted_cancellation = customer said to cancel now, acknowledge briefly.",
    )
    tech_handling: TechHandling | None = Field(
        default=None,
        description="When device issue: help_in_chat (use guide steps), escalate_immediate, schedule_appointment, or customer_can_handle. Null when not a device issue.",
    )
    reply_message: str = Field(
        default="",
        description="Your reply to the customer. Use policy/offers/troubleshooting context and the support scripts when appropriate.",
    )
