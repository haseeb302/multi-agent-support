"""
Chat API: POST /chat for single- and multi-turn support chat; GET /welcome for first message.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)

from app.agents.prompts import GREETER_WELCOME
from app.agents.runner import run_agent
from app.schemas import ChatRequest, ChatResponse
from app.services.session_store import get_or_create, set_session

router = APIRouter()


@router.get("/welcome", response_model=ChatResponse)
async def welcome() -> ChatResponse:
    """
    Return the initial Greeter welcome message and a new session_id.
    Stores the welcome AIMessage in the session so the backend sees it on the next request.
    """
    session_id = str(uuid.uuid4())
    data, _ = get_or_create(session_id)
    data["messages"] = [AIMessage(content=GREETER_WELCOME)]
    data["final_route"] = "greeter"
    data["intent"] = "greeter_welcome"
    set_session(session_id, data)
    return ChatResponse(
        reply=GREETER_WELCOME,
        session_id=session_id,
        route="greeter",
        tool_calls=[],
    )


@router.post("")
async def chat(body: ChatRequest) -> ChatResponse:
    """
    Send a message and get an assistant reply. Optionally pass session_id for multi-turn.
    If session_id is omitted, a new one is generated and returned.
    """
    message = (body.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    session_id = body.session_id or str(uuid.uuid4())
    data, _ = get_or_create(session_id)
    prior_messages = data.get("messages") or []
    session_context = {
        "customer_email": data.get("customer_email"),
        "customer_id": data.get("customer_id"),
        "customer_data": data.get("customer_data"),
        "final_route": data.get("final_route"),
        "intent": data.get("intent"),
    }

    try:
        reply, result, final_messages, session_update = run_agent(
            message,
            prior_messages=prior_messages,
            session_context=session_context,
        )
    except Exception as e:
        logger.exception("Agent run failed for session %s", session_id)
        raise HTTPException(status_code=500, detail=f"Agent error: {e!s}") from e

    data["messages"] = final_messages
    data["customer_email"] = session_update.get("customer_email")
    data["customer_id"] = session_update.get("customer_id")
    data["customer_data"] = session_update.get("customer_data")
    data["final_route"] = session_update.get("final_route")
    data["intent"] = session_update.get("intent")
    set_session(session_id, data)

    return ChatResponse(
        reply=reply,
        session_id=session_id,
        route=result.route,
        tool_calls=[{"name": t.name, "args": t.args} for t in result.tool_calls],
    )
