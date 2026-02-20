"""
FastAPI application entry point.
Multi-agent customer support chat for TechFlow Electronics.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, health

app = FastAPI(
    title="TechFlow Customer Support Chat API",
    description="Multi-agent chat for cancellation/retention, technical support, and billing routing",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])


@app.get("/")
async def root():
    return {
        "service": "TechFlow Customer Support Chat API",
        "docs": "/docs",
        "health": "/health",
        "chat": "POST /chat",
    }
