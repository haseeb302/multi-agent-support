"""
LangGraph: multi-agent support flow with tool-calling loop for the Processor.
Greeter is context-aware (uses previous route for follow-ups).
Tech support uses RAG + LLM. Processor uses LLM tool-calling via ToolNode.
"""
from __future__ import annotations

from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from app.agents.end_nodes import billing_end_node
from app.agents.greeter import greeter_node
from app.agents.processor import PROCESSOR_TOOLS, processor_node
from app.agents.problem_solver import problem_solver_node
from app.agents.tech_support import tech_support_node
from app.helpers import has_valid_email_in_state
from app.schemas import AgentState


def _route_after_greeter(state: AgentState) -> str:
    """
    If greeter added a message (final_route == greeter), we're done.
    Otherwise route to the specialist based on intent.
    """
    if state.get("final_route") == "greeter":
        return "__end__"
    intent = (state.get("intent") or "need_help").strip().lower()
    has_email = has_valid_email_in_state(state)

    if intent == "tech_support":
        return "tech_support"
    if intent == "billing":
        return "billing_end"
    if intent == "process_cancellation" and has_email:
        return "processor"
    if intent == "retention" and has_email:
        return "problem_solver"
    return "__end__"


def _route_after_processor(state: AgentState) -> str:
    """Continue the tool-calling loop if the last AI message has tool_calls."""
    messages = state.get("messages") or []
    if messages:
        last = messages[-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "processor_tools"
    return "__end__"


def build_graph():
    """Build and compile the support graph."""
    builder = StateGraph(AgentState)

    builder.add_node("greeter", greeter_node)
    builder.add_node("problem_solver", problem_solver_node)
    builder.add_node("processor", processor_node)
    builder.add_node("processor_tools", ToolNode(PROCESSOR_TOOLS))
    builder.add_node("tech_support", tech_support_node)
    builder.add_node("billing_end", billing_end_node)

    builder.set_entry_point("greeter")

    builder.add_conditional_edges(
        "greeter",
        _route_after_greeter,
        {
            "__end__": END,
            "problem_solver": "problem_solver",
            "processor": "processor",
            "tech_support": "tech_support",
            "billing_end": "billing_end",
        },
    )

    # Processor tool-calling loop: processor → tools → processor → … → END
    builder.add_conditional_edges(
        "processor",
        _route_after_processor,
        {"processor_tools": "processor_tools", "__end__": END},
    )
    builder.add_edge("processor_tools", "processor")

    builder.add_edge("problem_solver", END)
    builder.add_edge("tech_support", END)
    builder.add_edge("billing_end", END)

    return builder.compile()


_compiled: object = None


def get_compiled_graph():
    """Return the compiled graph (lazy singleton)."""
    global _compiled
    if _compiled is None:
        _compiled = build_graph()
    return _compiled
