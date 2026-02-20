"""
LLM factory for agents. Uses config (OPENAI_API_KEY / LLM_API_KEY, LLM_MODEL).
"""
from __future__ import annotations

import os

from app.core.config import get_settings
from langchain_openai import ChatOpenAI


def get_llm(**kwargs):
    """Return a ChatOpenAI instance using env config. Override with kwargs."""
    s = get_settings()
    api_key = s.llm_api_key or os.environ.get("OPENAI_API_KEY") or None
    return ChatOpenAI(
        model=s.llm_model,
        api_key=api_key,
        temperature=0.2,
        **kwargs,
    )
