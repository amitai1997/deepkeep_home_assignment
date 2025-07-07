"""In-memory user store for managing user states and violations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, Set

from ..core.config import get_settings
from ..models.schemas import UserStatus


# Module-level logger (uses the root configuration; callers may configure handlers).
logger = logging.getLogger(__name__)


class UserStore:
    """In-memory store for user violation tracking and blocking."""

    def __init__(self) -> None:
        """Initialize the user store."""
        self._users: Dict[str, UserStatus] = {}
        self._settings = get_settings()

    def get_user(self, user_id: str) -> UserStatus:
        """Get user status, creating new user if not exists."""
        if user_id not in self._users:
            now = datetime.now(timezone.utc)
            self._users[user_id] = UserStatus(
                user_id=user_id, created_at=now, updated_at=now
            )
        return self._users[user_id]

    def add_violation(self, user_id: str) -> UserStatus:
        """Add a violation to *user_id* and update blocking state.

        This increments the user's ``violation_count`` and sets
        ``last_violation`` and ``updated_at`` to *now*.

        When the counter reaches **three**, the user is marked as blocked and a
        ``blocked_until`` timestamp is assigned (``now + block_minutes``).

        Returns
        -------
        UserStatus
            The up-to-date status object *after* mutation.  Callers can inspect
            ``is_blocked`` to know whether the user crossed the threshold on
            this call.
        """
        user = self.get_user(user_id)
        now = datetime.now(timezone.utc)

        user.violation_count += 1
        user.last_violation = now
        user.updated_at = now

        # Block user after 3 violations
        if user.violation_count >= 3:
            user.is_blocked = True
            user.blocked_until = now + timedelta(minutes=self._settings.block_minutes)

            # Informational log for observability during local runs.
            logger.info("User '%s' blocked until %s (%d strikes)", user_id, user.blocked_until.isoformat(), user.violation_count)

        return user

    def is_user_blocked(self, user_id: str) -> bool:
        """Check if user is currently blocked, auto-unblock if time expired."""
        user = self.get_user(user_id)

        if not user.is_blocked:
            return False

        # Check if block period has expired
        if user.blocked_until and datetime.now(timezone.utc) >= user.blocked_until:
            self._auto_unblock_user(user)
            return False

        return True

    def unblock_user(self, user_id: str) -> UserStatus:
        """Manually unblock user and reset violations."""
        user = self.get_user(user_id)
        user.is_blocked = False
        user.blocked_until = None
        user.violation_count = 0
        user.updated_at = datetime.now(timezone.utc)
        return user

    def get_all_user_ids(self) -> Set[str]:
        """Get all user IDs in the system."""
        return set(self._users.keys())

    def _auto_unblock_user(self, user: UserStatus) -> None:
        """Automatically unblock user when time expires."""
        user.is_blocked = False
        user.blocked_until = None
        user.violation_count = 0
        user.updated_at = datetime.now(timezone.utc)


# Singleton instance
_user_store = UserStore()


def get_user_store() -> UserStore:
    """Get the singleton user store instance."""
    return _user_store
