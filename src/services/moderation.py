"""Content moderation service."""

from __future__ import annotations

from ..repository.user_repository import get_user_repository, UserRepository


class ModerationService:
    """Service for content moderation and violation detection."""

    def __init__(self, store: UserRepository | None = None) -> None:
        self._user_store = store or get_user_repository()

    async def check_content_violation(self, message: str, sender_id: str) -> bool:
        all_user_ids = await self._user_store.get_all_user_ids()
        other_user_ids = all_user_ids - {sender_id}
        message_lower = message.lower()
        for user_id in other_user_ids:
            if user_id.lower() in message_lower:
                return True
        return False

    async def process_message(self, message: str, user_id: str) -> tuple[bool, bool]:
        if await self._user_store.is_user_blocked(user_id):
            return False, True

        has_violation = await self.check_content_violation(message, user_id)

        if has_violation:
            user_status = await self._user_store.add_violation(user_id)
            violation_count = int(getattr(user_status, "violation_count", 0))
            status_blocked = getattr(user_status, "is_blocked", False)
            if status_blocked and violation_count != 3:
                return True, True
            if violation_count < 3:
                return True, False
            if violation_count == 3:
                return True, False
            return True, True

        return False, False


def get_moderation_service() -> ModerationService:
    return ModerationService()
