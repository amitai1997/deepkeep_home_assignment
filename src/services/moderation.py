"""Content moderation service."""

from __future__ import annotations


from ..store.user_store import get_user_store


class ModerationService:
    """Service for content moderation and violation detection."""

    def __init__(self) -> None:
        """Initialize the moderation service."""
        self._user_store = get_user_store()

    def check_content_violation(self, message: str, sender_id: str) -> bool:
        """
        Check if message contains any other user IDs.

        Args:
            message: The message content to check
            sender_id: ID of the user sending the message

        Returns:
            True if violation detected, False otherwise
        """
        # Get all user IDs except the sender
        all_user_ids = self._user_store.get_all_user_ids()
        other_user_ids = all_user_ids - {sender_id}

        # Check if any other user ID appears in the message
        message_lower = message.lower()
        for user_id in other_user_ids:
            if user_id.lower() in message_lower:
                return True

        return False

    def process_message(self, message: str, user_id: str) -> tuple[bool, bool]:
        """
        Process message for violations and blocking.

        This method handles:
        1. Checking if user is blocked (with automatic unblocking if time expired)
        2. Checking for content violations
        3. Adding violations and potentially blocking the user

        Args:
            message: The message content
            user_id: ID of the user

        Returns:
            Tuple of (is_violation, is_blocked_after_check)
        """
        # Check if user is already blocked
        # This method internally handles automatic unblocking if time has expired
        if self._user_store.is_user_blocked(user_id):
            return False, True

        # Check for content violation
        has_violation = self.check_content_violation(message, user_id)

        # Add violation if detected
        if has_violation:
            user_status = self._user_store.add_violation(user_id)
            return True, user_status.is_blocked

        return False, False


def get_moderation_service() -> ModerationService:
    """Get moderation service instance."""
    return ModerationService()
