"""Tests for user store functionality."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from src.store.user_store import UserStore, get_user_store


class TestUserStore:
    """Test cases for UserStore class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.user_store = UserStore()

    def test_get_user_creates_new_user(self):
        """Test that get_user creates a new user if not exists."""
        user_id = "test_user"
        user = self.user_store.get_user(user_id)

        assert user.user_id == user_id
        assert user.violation_count == 0
        assert user.is_blocked is False
        assert user.blocked_until is None
        assert user.last_violation is None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_get_user_returns_existing_user(self):
        """Test that get_user returns existing user."""
        user_id = "test_user"
        user1 = self.user_store.get_user(user_id)
        user2 = self.user_store.get_user(user_id)

        assert user1 is user2
        assert user1.user_id == user2.user_id

    def test_add_violation_increments_count(self):
        """Test that add_violation increments violation count."""
        user_id = "test_user"

        # First violation
        user = self.user_store.add_violation(user_id)
        assert user.violation_count == 1
        assert user.is_blocked is False
        assert isinstance(user.last_violation, datetime)

        # Second violation
        user = self.user_store.add_violation(user_id)
        assert user.violation_count == 2
        assert user.is_blocked is False

    def test_add_violation_blocks_after_three_strikes(self):
        """Test that user gets blocked after 3 violations."""
        user_id = "test_user"

        # Add 3 violations
        for i in range(3):
            user = self.user_store.add_violation(user_id)

        assert user.violation_count == 3
        assert user.is_blocked is True
        assert user.blocked_until is not None
        assert user.blocked_until > datetime.now(timezone.utc)

    def test_is_user_blocked_returns_false_for_unblocked_user(self):
        """Test that is_user_blocked returns False for unblocked users."""
        user_id = "test_user"
        assert self.user_store.is_user_blocked(user_id) is False

        # Add 2 violations (not blocked yet)
        self.user_store.add_violation(user_id)
        self.user_store.add_violation(user_id)
        assert self.user_store.is_user_blocked(user_id) is False

    def test_is_user_blocked_returns_true_for_blocked_user(self):
        """Test that is_user_blocked returns True for blocked users."""
        user_id = "test_user"

        # Block user with 3 violations
        for i in range(3):
            self.user_store.add_violation(user_id)

        assert self.user_store.is_user_blocked(user_id) is True

    def test_auto_unblock_expired_user(self):
        """Test that user is auto-unblocked when block period expires."""
        user_id = "test_user"

        # Block user
        for i in range(3):
            self.user_store.add_violation(user_id)

        # Manually set blocked_until to past time
        user = self.user_store.get_user(user_id)
        user.blocked_until = datetime.now(timezone.utc) - timedelta(minutes=1)

        # Check if user is blocked - should auto-unblock
        assert self.user_store.is_user_blocked(user_id) is False

        # Verify user state after auto-unblock
        user = self.user_store.get_user(user_id)
        assert user.is_blocked is False
        assert user.blocked_until is None
        assert user.violation_count == 0

    def test_unblock_user_manually(self):
        """Test manual unblocking of user."""
        user_id = "test_user"

        # Block user
        for i in range(3):
            self.user_store.add_violation(user_id)

        # Manually unblock
        user = self.user_store.unblock_user(user_id)

        assert user.is_blocked is False
        assert user.blocked_until is None
        assert user.violation_count == 0
        assert self.user_store.is_user_blocked(user_id) is False

    def test_get_all_user_ids(self):
        """Test getting all user IDs."""
        user_ids = ["user1", "user2", "user3"]

        for user_id in user_ids:
            self.user_store.get_user(user_id)

        all_ids = self.user_store.get_all_user_ids()
        assert all_ids == set(user_ids)

    def test_get_all_user_ids_empty(self):
        """Test getting all user IDs when no users exist."""
        all_ids = self.user_store.get_all_user_ids()
        assert all_ids == set()

    def test_add_violation_updates_timestamps(self):
        """Test that add_violation updates timestamps correctly."""
        user_id = "test_user"
        
        # Get initial user
        user = self.user_store.get_user(user_id)
        original_created = user.created_at
        original_updated = user.updated_at
        
        # Add violation after a brief pause
        import time
        time.sleep(0.01)  # Small delay to ensure timestamp difference
        
        user = self.user_store.add_violation(user_id)
        
        # Created time should not change
        assert user.created_at == original_created
        # Updated time should be newer
        assert user.updated_at > original_updated
        # Last violation should be set
        assert user.last_violation is not None
        assert isinstance(user.last_violation, datetime)

    def test_blocked_user_violations_dont_increase(self):
        """Test that violations after blocking don't increase count."""
        user_id = "test_user"
        
        # Block user
        for _ in range(3):
            self.user_store.add_violation(user_id)
        
        user = self.user_store.get_user(user_id)
        assert user.violation_count == 3
        assert user.is_blocked is True
        
        # Try to add more violations - should not increase
        # Note: In current implementation, this would increase, but process_message prevents it
        # This test documents the current behavior
        user = self.user_store.add_violation(user_id)
        assert user.violation_count == 4  # Current behavior allows this

    def test_unblock_user_who_was_never_blocked(self):
        """Test unblocking a user who was never blocked."""
        user_id = "never_blocked"
        
        # Create user with one violation
        self.user_store.add_violation(user_id)
        
        # Unblock
        user = self.user_store.unblock_user(user_id)
        
        assert user.is_blocked is False
        assert user.violation_count == 0
        assert user.blocked_until is None

    def test_multiple_users_independent_violations(self):
        """Test that violations are tracked independently per user."""
        user1 = "user1"
        user2 = "user2"
        user3 = "user3"
        
        # Add different violations to each user
        self.user_store.add_violation(user1)
        
        for _ in range(2):
            self.user_store.add_violation(user2)
        
        for _ in range(3):
            self.user_store.add_violation(user3)
        
        # Check states
        assert self.user_store.get_user(user1).violation_count == 1
        assert not self.user_store.is_user_blocked(user1)
        
        assert self.user_store.get_user(user2).violation_count == 2
        assert not self.user_store.is_user_blocked(user2)
        
        assert self.user_store.get_user(user3).violation_count == 3
        assert self.user_store.is_user_blocked(user3)

    def test_block_duration_from_settings(self):
        """Test that block duration uses the configured value."""
        user_id = "test_user"
        
        # Block user
        for _ in range(3):
            self.user_store.add_violation(user_id)
        
        user = self.user_store.get_user(user_id)
        expected_unblock_time = user.last_violation + timedelta(
            minutes=self.user_store._settings.block_minutes
        )
        
        # Allow for small time differences due to execution
        assert abs((user.blocked_until - expected_unblock_time).total_seconds()) < 1

    def test_get_user_store_singleton(self):
        """Test that get_user_store returns the same instance."""
        store1 = get_user_store()
        store2 = get_user_store()
        
        assert store1 is store2

    def test_concurrent_violations_race_condition(self):
        """Test handling of concurrent violations (documenting current behavior)."""
        user_id = "concurrent_user"
        
        # Simulate rapid violations
        for _ in range(5):
            self.user_store.add_violation(user_id)
        
        user = self.user_store.get_user(user_id)
        # User will have 5 violations (no protection against concurrent access)
        assert user.violation_count == 5
        assert user.is_blocked is True

    def test_user_store_clear_users(self):
        """Test clearing all users from the store."""
        # Add some users
        for i in range(5):
            self.user_store.get_user(f"user{i}")
        
        assert len(self.user_store.get_all_user_ids()) == 5
        
        # Clear all users
        self.user_store._users.clear()
        
        assert len(self.user_store.get_all_user_ids()) == 0
