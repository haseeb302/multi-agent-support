"""
Tech Support node: uses RAG (Pinecone) to retrieve relevant troubleshooting context,
then LLM + conversation history to walk customers through device issue steps.
Escalates to a human specialist when the guide requires it.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.prompts import TECH_SUPPORT_SYSTEM
from app.helpers import last_user_message, MAX_HISTORY_MESSAGES
from app.schemas import AgentState
from app.services.rag import query_policy


def tech_support_node(state: AgentState) -> dict:
    """Retrieve troubleshooting context via RAG, then use LLM with conversation history."""
    messages = state.get("messages") or []
    last_user = last_user_message(messages)

    rag_query = last_user or "device troubleshooting help"
    rag_docs = query_policy(rag_query, k=5)
    rag_text = "\n\n---\n\n".join(d.page_content for d in rag_docs) if rag_docs else ""
    if not rag_text:
        rag_text = "No troubleshooting context found. Ask the customer for more details about their issue."

    system = (
        TECH_SUPPORT_SYSTEM
        + "\n\n## Retrieved troubleshooting context:\n"
        + rag_text[:4000]
    )

    llm_messages: list = [SystemMessage(content=system)]
    for m in messages[-MAX_HISTORY_MESSAGES:]:
        role = getattr(m, "type", None)
        content = getattr(m, "content", "") or ""
        if role == "human":
            llm_messages.append(HumanMessage(content=content))
        elif role == "ai":
            llm_messages.append(AIMessage(content=content))

    response = get_llm().invoke(llm_messages)
    content = response.content if hasattr(response, "content") else str(response)

    return {
        "messages": [AIMessage(content=content)],
        "current_agent": "tech_support",
        "final_route": "tech_support",
        "tool_calls": [],
    }
