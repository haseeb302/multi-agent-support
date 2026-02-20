"""
Structured output schema for the Greeter agent (LLM).
Aligns with assignment: identify customer (email) and classify intent.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# Intent values per assignment: retention, tech support, billing, and process cancellation
GreeterIntent = Literal[
    "retention",           # Wants to cancel/downgrade/question value → Problem Solver
    "process_cancellation", # Insisted on canceling → Processor
    "tech_support",        # Device issue, not cancellation → Tech Support
    "billing",             # Charge/bill question → Billing
    "need_help",           # Has email but no clear need stated yet
]


class GreeterOutput(BaseModel):
    """LLM must respond with this structure only."""

    email: str | None = Field(
        default=None,
        description="Customer email if present in the message or conversation. Null if not found or not provided.",
    )
    intent: GreeterIntent = Field(
        default="need_help",
        description="One of: retention (cancel/downgrade/question value), process_cancellation (user insisted cancel), tech_support (device issue), billing (charge question), need_help (email given but need unclear).",
    )
