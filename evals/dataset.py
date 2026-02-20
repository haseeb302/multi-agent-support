"""
The 5 required test conversations as eval cases.
Criteria: routing + tool usage only (no content/reply checks).
"""
from evals.schemas import EvalCase

EVAL_CASES: list[EvalCase] = [
    EvalCase(
        id="money_problems",
        user_message="hey can't afford the $13/month care+ anymore, need to cancel",
        expected_route="retention",
        expected_tools_any=["get_customer_data", "calculate_retention_offer"],
        forbidden_tools=["update_customer_status"],
        description="Try payment pause or discount before canceling; use business rules + customer data",
    ),
    EvalCase(
        id="phone_problems",
        user_message="this phone keeps overheating, want to return it and cancel everything",
        expected_route="retention",
        expected_tools_any=["get_customer_data", "calculate_retention_offer"],
        forbidden_tools=["update_customer_status"],
        description="Offer phone replacement or upgrade before canceling; use return policy + tech guide",
    ),
    EvalCase(
        id="questioning_value",
        user_message="paying for care+ but never used it, maybe just get rid of it?",
        expected_route="retention",
        expected_tools_any=["get_customer_data", "calculate_retention_offer"],
        forbidden_tools=["update_customer_status"],
        description="Explain what they get for their money, offer cheaper options; use Care+ benefits",
    ),
    EvalCase(
        id="technical_help",
        user_message="my phone won't charge anymore, tried different cables",
        expected_route="tech_support",
        expected_tools_any=[],  # no specific tools required; must not try to retain/cancel
        forbidden_tools=["update_customer_status", "calculate_retention_offer"],
        description="Send directly to tech support; do not try to sell retention or cancel",
    ),
    EvalCase(
        id="billing_question",
        user_message="got charged $15.99 but thought care+ was $12.99, what's the extra?",
        expected_route="billing",
        expected_tools_any=[],
        forbidden_tools=["update_customer_status", "calculate_retention_offer"],
        description="Send directly to billing; recognize billing inquiry, not cancellation",
    ),
]


def get_eval_cases() -> list[EvalCase]:
    return list(EVAL_CASES)
