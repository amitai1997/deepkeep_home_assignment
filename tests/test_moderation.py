import pytest
from unittest.mock import patch

from src.services.moderation import ModerationService

pytestmark = pytest.mark.asyncio


async def test_check_content_violation_detects_other_user(user_store):
    service = ModerationService(user_store)
    await user_store.get_user("bob")
    result = await service.check_content_violation("hi bob", "alice")
    assert result is True


async def test_process_message_blocks_after_three(user_store):
    service = ModerationService(user_store)
    await user_store.get_user("bob")
    for _ in range(4):
        with patch.object(service, "check_content_violation", return_value=True):
            v, blocked = await service.process_message("hi bob", "alice")
    assert blocked is True
