"""Test configuration and database fixtures."""

import os
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.db.models import Base
from src.store.user_store import UserStore

os.environ.setdefault("OPENAI_API_KEY", "test-key-dummy")


@pytest.fixture(scope="function")
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_session
    await engine.dispose()


@pytest.fixture(scope="function")
async def user_store(session_factory):
    return UserStore(session_factory)


@pytest.fixture(autouse=True)
async def patch_user_store(user_store):
    with (
        patch("src.store.user_store._user_store", user_store),
        patch("src.store.user_store.get_user_store", return_value=user_store),
    ):
        yield
