"""
Health check endpoints for deployment and testing.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health_check():
    """Basic liveness check."""
    return {"status": "ok", "service": "techflow-chat"}


@router.get("/ready")
async def readiness_check():
    """
    Readiness: verify dependencies (Pinecone, optional LLM) are reachable.
    Will be extended as we add RAG and agents.
    """
    # TODO: ping Pinecone index when RAG is ready
    return {"status": "ready", "checks": {"api": "ok"}}
