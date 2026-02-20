"""
Problem Solver node: structured output (schema) + tools (get_customer_data, calculate_retention_offer)
+ RAG for retention offers + conversation history for multi-turn context.
Greeter guarantees email and intent before routing here; tier from customers.csv.
"""
from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.prompts import (
    PROBLEM_SOLVER_SYSTEM,
    TROUBLESHOOTING_SETTING_EXPECTATIONS,
    TROUBLESHOOTING_WHEN_ESCALATING,
)
from app.core.config import get_settings
from app.helpers import (
    build_retention_reason,
    conversation_summary,
    extract_tier,
    last_user_message,
    tool_record,
)
from app.schemas import AgentState, ProblemSolverOutput
from app.services.rag import query_policy
from app.tools.customer import get_customer_data_impl
from app.tools.retention import calculate_retention_offer_impl


def problem_solver_node(state: AgentState) -> dict:
    """Use structured output, customer data from CSV, retention tool, RAG, and conversation history."""
    messages = state.get("messages") or []
    last_user = last_user_message(messages)
    if not last_user:
        return {"current_agent": "problem_solver", "tool_calls": [], "final_route": "retention"}

    customer_data = state.get("customer_data")
    customer_id = state.get("customer_id")
    customer_email = state.get("customer_email")

    settings = get_settings()
    tool_calls: list[dict] = []

    # 1) Get customer data from CSV if not already in state
    if customer_data is None:
        out = get_customer_data_impl(customer_email, customers_csv_path=settings.customers_csv_path)
        tool_calls.append(tool_record("get_customer_data", {"email": customer_email}))
        if out.get("ok") and out.get("found"):
            customer_data = out.get("customer")
            customer_id = (customer_data or {}).get("customer_id")
        else:
            customer_data = {}
            customer_id = None

    tier = extract_tier(customer_data)

    # 2) Personalized offers from retention_rules.json for each category
    reasons_for_context = [
        "financial_hardship",
        "product_issues:overheating",
        "product_issues:battery_issues",
        "service_value:care_plus_premium",
    ]
    offers_by_category: list[str] = []
    for r in reasons_for_context:
        o = calculate_retention_offer_impl(
            customer_tier=tier,
            reason=r,
            retention_rules_path=settings.retention_rules_path,
        )
        if o.get("ok") and o.get("offers"):
            descs = [x.get("description", str(x)) for x in o["offers"]]
            offers_by_category.append(f"  {r}:\n    " + "\n    ".join(descs))

    # 3) RAG context for policy / Care+
    policy_docs = query_policy(last_user, k=4)
    policy_text = "\n\n".join(d.page_content for d in policy_docs) if policy_docs else "No policy context found."
    if policy_text:
        policy_text = policy_text[:3500]

    # 4) Conversation history so the LLM has multi-turn context
    conv_summary = conversation_summary(messages)

    # 5) Assemble full context
    offers_block = "\n".join(offers_by_category) if offers_by_category else "No offers in rules for this tier."
    context_parts = [
        "## Conversation history:",
        conv_summary,
        "\n## Customer data:",
        str(customer_data) if customer_data else "Not found.",
        "\n## Personalized offers (from retention_rules.json for this customer's tier):",
        offers_block,
        "\n## Policy / RAG context:",
        policy_text or "None",
        "\n## Customer message:",
        last_user,
    ]
    context = "\n".join(context_parts)
    system = PROBLEM_SOLVER_SYSTEM + "\n\nContext for this turn:\n" + context

    llm = get_llm().with_structured_output(ProblemSolverOutput)
    out: ProblemSolverOutput = llm.invoke([
        SystemMessage(content=system),
        HumanMessage(content=last_user),
    ])

    category = (out.retention_reason_category or "financial_hardship").strip().lower()
    sub = out.retention_reason_sub.strip() if out.retention_reason_sub else None
    reason = build_retention_reason(category, sub)
    tool_calls.append(tool_record("calculate_retention_offer", {"customer_tier": tier, "reason": reason}))

    reply_message = (out.reply_message or "").strip()
    if not reply_message:
        reply_message = "I'm sorry, I couldn't generate a reply. Could you tell me a bit more about what you need?"

    action = (out.action or "offer_retention").strip().lower()
    if action == "direct_to_tech_support":
        tech_handling = (out.tech_handling or "").strip().lower()
        if tech_handling in ("escalate_immediate", "schedule_appointment"):
            reply_message = TROUBLESHOOTING_WHEN_ESCALATING + "\n\n" + reply_message
        else:
            reply_message = TROUBLESHOOTING_SETTING_EXPECTATIONS + "\n\n" + reply_message

    return {
        "messages": [AIMessage(content=reply_message)],
        "customer_data": customer_data,
        "customer_id": customer_id,
        "current_agent": "problem_solver",
        "tool_calls": tool_calls,
        "final_route": "retention",
    }
