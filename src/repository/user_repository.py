"""Database-backed user repository."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..core.config import get_settings
from ..db.models import User
from ..db.session import async_session_maker

logger = logging.getLogger(__name__)


class UserRepository:
    """User violation tracking backed by a database."""

    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession] | None = None
    ) -> None:
        self._session_factory = session_factory or async_session_maker
        self._settings = get_settings()

    async def get_user(self, user_id: str) -> User:
        async with self._session_factory() as session:
            user = await session.get(User, user_id)
            if user is None:
                now = datetime.now(timezone.utc)
                user = User(
                    user_id=user_id,
                    violation_count=0,
                    is_blocked=False,
                    blocked_until=None,
                    last_violation=None,
                    created_at=now,
                    updated_at=now,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
            assert user is not None
            return user

    async def add_violation(self, user_id: str) -> User:
        async with self._session_factory() as session:
            user = await session.get(User, user_id)
            if user is None:
                now = datetime.now(timezone.utc)
                user = User(
                    user_id=user_id,
                    violation_count=0,
                    is_blocked=False,
                    blocked_until=None,
                    last_violation=None,
                    created_at=now,
                    updated_at=now,
                )
                session.add(user)

            now = datetime.now(timezone.utc)
            user.violation_count += 1
            user.last_violation = now
            user.updated_at = now

            if user.violation_count >= 3:
                user.is_blocked = True
                user.blocked_until = now + timedelta(
                    minutes=self._settings.block_minutes
                )
                blocked_until_str = (
                    str(user.blocked_until) if user.blocked_until else ""
                )
                logger.info(
                    "User '%s' blocked until %s (%d strikes)",
                    user_id,
                    blocked_until_str,
                    user.violation_count,
                )

            await session.commit()
            await session.refresh(user)
            assert user is not None
            return user

    async def is_user_blocked(self, user_id: str) -> bool:
        async with self._session_factory() as session:
            user = await session.get(User, user_id)
            if user is None or not user.is_blocked:
                return False
            if user.blocked_until:
                ts = user.blocked_until
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) >= ts:
                    await self._auto_unblock_user(session, user)
                    await session.commit()
                    return False
            return True

    async def unblock_user(self, user_id: str) -> User:
        async with self._session_factory() as session:
            user = await session.get(User, user_id)
            if user is None:
                now = datetime.now(timezone.utc)
                user = User(
                    user_id=user_id,
                    violation_count=0,
                    is_blocked=False,
                    blocked_until=None,
                    last_violation=None,
                    created_at=now,
                    updated_at=now,
                )
                session.add(user)
            user.is_blocked = False
            user.blocked_until = None
            user.violation_count = 0
            user.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(user)
            assert user is not None
            return user

    async def get_all_user_ids(self) -> Set[str]:
        async with self._session_factory() as session:
            result = await session.scalars(select(User.user_id))
            return set(result.all())

    async def user_exists(self, user_id: str) -> bool:
        async with self._session_factory() as session:
            result = await session.get(User, user_id)
            return result is not None

    async def _auto_unblock_user(self, session: AsyncSession, user: User) -> None:
        user.is_blocked = False
        user.blocked_until = None
        user.violation_count = 0
        user.updated_at = datetime.now(timezone.utc)


_user_repository = UserRepository()


def get_user_repository() -> UserRepository:  # noqa: D401
    """Return singleton UserRepository instance."""

    return _user_repository
