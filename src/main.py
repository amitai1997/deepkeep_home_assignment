"""Application entry point."""

from __future__ import annotations

from fastapi import FastAPI

from .api import chat, admin
from .core.config import get_settings


def create_app() -> FastAPI:
    """Create FastAPI application."""

    _ = get_settings()  # pragma: no cover
    app = FastAPI(
        title="Chat Gateway",
        description="An intelligent chat gateway with content moderation and blocking",
        version="0.1.0"
    )
    
    # Include routers
    app.include_router(chat.router)
    app.include_router(admin.router)
    
    return app


app = create_app()
