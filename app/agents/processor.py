"""
Processor agent: cancels services via LLM tool-calling (bind_tools + ToolNode loop).
The LLM autonomously decides when to call get_customer_data and update_customer_status.
"""
from __future__ import annotations

import ast
import json

from langchain_core.messages import AIMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.prompts import PROCESSOR_SYSTEM
from app.helpers import MAX_HISTORY_MESSAGES, tool_record
from app.schemas import AgentState
from app.tools.customer import get_customer_data
from app.tools.status import update_customer_status

PROCESSOR_TOOLS = [get_customer_data, update_customer_status]


def processor_node(state: AgentState) -> dict:
    """LLM-driven processor: uses tool-calling to look up data and process cancellation."""
    messages = state.get("messages") or []
    customer_email = state.get("customer_email") or "unknown"
    customer_id = state.get("customer_id")
    customer_data = state.get("customer_data")

    context_lines = [PROCESSOR_SYSTEM, f"\nCustomer email: {customer_email}"]
    if customer_id:
        context_lines.append(f"Customer ID: {customer_id}")
    if customer_data:
        context_lines.append(f"Customer tier: {(customer_data or {}).get('tier', 'unknown')}")
    else:
        context_lines.append("Customer data not loaded yet — use get_customer_data first.")

    llm = get_llm().bind_tools(PROCESSOR_TOOLS)
    llm_input = [SystemMessage(content="\n".join(context_lines))] + list(messages[-MAX_HISTORY_MESSAGES:])
    response = llm.invoke(llm_input)

    result: dict = {"messages": [response]}

    if not response.tool_calls:
        tool_records = _collect_tool_records(messages)
        cid, cdata = _extract_customer_from_tool_results(messages)
        result.update({
            "current_agent": "processor",
            "final_route": "processor",
            "tool_calls": tool_records,
            "customer_id": cid or customer_id,
            "customer_data": cdata or customer_data,
        })
    return result


def _collect_tool_records(messages: list) -> list[dict]:
    """Extract tool call records from AIMessages generated during the Processor loop."""
    records: list[dict] = []
    for m in messages:
        if not hasattr(m, "tool_calls") or not m.tool_calls:
            continue
        for tc in m.tool_calls:
            records.append(tool_record(tc.get("name", ""), tc.get("args", {})))
    return records


def _extract_customer_from_tool_results(messages: list) -> tuple[str | None, dict | None]:
    """Parse get_customer_data results from ToolMessages to persist in state."""
    for m in messages:
        if getattr(m, "type", None) != "tool":
            continue
        if getattr(m, "name", None) != "get_customer_data":
            continue
        content = getattr(m, "content", "")
        data = _safe_parse(content)
        if isinstance(data, dict) and data.get("ok") and data.get("found"):
            customer = data.get("customer", {})
            return customer.get("customer_id"), customer
    return None, None


def _safe_parse(content: str):
    """Try JSON first, then Python literal eval for ToolNode dict output."""
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        pass
    try:
        return ast.literal_eval(content)
    except (ValueError, SyntaxError):
        return None
