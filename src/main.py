"""Application entry point."""

from __future__ import annotations

from fastapi import FastAPI

from .api import chat, admin
from .core.config import get_settings


def create_app() -> FastAPI:
    """Create FastAPI application."""

    _ = get_settings()  # pragma: no cover

    tags_metadata = [
        {"name": "chat", "description": "Send messages through the OpenAI proxy."},
        {"name": "admin", "description": "Administrative operations."},
    ]

    app = FastAPI(
        title="Chat Gateway",
        description="An intelligent chat gateway with content moderation and blocking",
        version="0.1.0",
        openapi_tags=tags_metadata,
    )

    # Include routers
    app.include_router(chat.router)
    app.include_router(admin.router)

    return app


app = create_app()
