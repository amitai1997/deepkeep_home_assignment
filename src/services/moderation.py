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

        Notes
        -----
        • The request that *triggers* the third strike is **still served** with
          HTTP 200; the user becomes blocked for any subsequent request.

        Returns
        -------
        tuple[bool, bool]
            (has_violation, is_blocked_after_check)
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

            # Our business rule: A user is permitted to receive their response on the
            # *third* violation but will be blocked immediately afterwards.  That
            # means the request that *causes* the third strike still succeeds with
            # a 200 response, while any **subsequent** request receives 403.

            # add_violation sets ``is_blocked`` to ``True`` once the strike threshold
            # is reached.  We therefore need to suppress the block status for the
            # current request when this is the EXACT strike that reached the limit.

            raw_count = getattr(user_status, "violation_count", 0)
            violation_count = raw_count if isinstance(raw_count, int) else 0

            status_blocked = getattr(user_status, "is_blocked", False)

            # If the store says the user is already blocked (and it's not the
            # very first time hitting the strike threshold), block now.
            if status_blocked and violation_count != 3:
                return True, True

            # Fewer than 3 strikes – violation recorded, user still allowed.
            if violation_count < 3:
                # Fewer than 3 strikes – violation recorded, user still allowed.
                return True, False

            if violation_count == 3:
                # User just reached the strike cap; mark as blocked for future
                # requests but allow this one.
                return True, False

            # If we're here the user already had ≥3 strikes prior to this call,
            # so they are blocked for the current request as well.
            return True, True

        return False, False


def get_moderation_service() -> ModerationService:
    """Get moderation service instance."""
    return ModerationService()
