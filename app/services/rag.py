"""
RAG service: query Pinecone index for policy document chunks.

Uses Pinecone only (no external embeddings). The index must have integrated
embedding configured on the platform; we search with query text and Pinecone
converts it to vectors. See: https://docs.pinecone.io/guides/search/semantic-search
"""
from __future__ import annotations

import logging

from app.core.config import get_settings
from langchain_core.documents import Document
from pinecone import Pinecone

logger = logging.getLogger(__name__)

SOURCE_FIELD = "source"


def get_pinecone_index():
    """
    Return Pinecone Index for the configured index name.
    Uses API key + index name; host is resolved via describe_index.
    """
    settings = get_settings()
    settings.require_pinecone()
    pc = Pinecone(api_key=settings.pinecone_api_key)
    return pc.Index(name=settings.pinecone_index_name)


def query_policy(query: str, k: int = 4) -> list[Document]:
    """
    Search the policy index with query text (Pinecone integrated embedding).
    Returns top-k relevant chunks as LangChain Documents.
    """
    try:
        settings = get_settings()
        settings.require_pinecone()
    except ValueError:
        return []

    try:
        index = get_pinecone_index()
        namespace = settings.pinecone_namespace or "__default__"
        response = index.search(
            namespace=namespace,
            query={
                "inputs": {"text": query},
                "top_k": k,
            },
            fields=[settings.pinecone_text_field, SOURCE_FIELD],
        )
    except Exception:
        logger.exception("Pinecone search failed for query: %s", query[:120])
        return []

    docs: list[Document] = []
    result = getattr(response, "result", response) if response else None
    hits = getattr(result, "hits", None) if result else None
    if not hits and hasattr(response, "hits"):
        hits = response.hits
    hits = hits or []
    text_field = settings.pinecone_text_field
    for hit in hits:
        fields = getattr(hit, "fields", None) or {}
        if not isinstance(fields, dict):
            fields = getattr(fields, "__dict__", {}) or {}
        text = (fields.get(text_field) or "").strip()
        if not text:
            continue
        rec_id = getattr(hit, "_id", None) or getattr(hit, "id", "") or ""
        metadata = {"source": fields.get(SOURCE_FIELD, ""), "_id": rec_id}
        docs.append(Document(page_content=text, metadata=metadata))
    return docs
