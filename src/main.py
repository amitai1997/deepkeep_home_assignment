"""Application entry point."""

from __future__ import annotations

from fastapi import FastAPI

from .core.config import get_settings


def create_app() -> FastAPI:
    """Create FastAPI application."""

    _ = get_settings()  # pragma: no cover
    app = FastAPI(title="Chat Gateway")
    return app


app = create_app()
