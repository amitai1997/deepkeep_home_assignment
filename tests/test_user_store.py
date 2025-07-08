import pytest
from datetime import datetime, timezone, timedelta

from src.store.user_store import UserStore
from src.db.models import User

pytestmark = pytest.mark.asyncio


async def test_get_user_creates_new(user_store: UserStore):
    user = await user_store.get_user("alice")
    assert user.user_id == "alice"
    assert user.violation_count == 0


async def test_add_violation_blocks_after_three(user_store: UserStore):
    for _ in range(3):
        user = await user_store.add_violation("bob")
    assert user.is_blocked is True
    assert user.violation_count == 3
    assert user.blocked_until is not None


async def test_auto_unblock(user_store: UserStore):
    for _ in range(3):
        await user_store.add_violation("charlie")
    user = await user_store.unblock_user("charlie")
    assert user.is_blocked is False
    assert user.violation_count == 0


async def test_is_user_blocked_checks_expiry(user_store: UserStore):
    for _ in range(3):
        await user_store.add_violation("dave")
    async with user_store._session_factory() as session:  # type: ignore[attr-defined]
        user = await session.get(User, "dave")
        user.blocked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
        await session.commit()
    blocked = await user_store.is_user_blocked("dave")
    assert blocked is False
