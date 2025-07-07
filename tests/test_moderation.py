"""Tests for moderation service."""

import pytest
from unittest.mock import Mock, patch

from src.services.moderation import ModerationService
from src.store.user_store import UserStore


class TestModerationService:
    """Test cases for ModerationService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.moderation_service = ModerationService()
    
    def test_check_content_violation_no_other_users(self):
        """Test content check when no other users exist."""
        message = "Hello world"
        sender_id = "user1"
        
        # Mock empty user store
        with patch.object(self.moderation_service._user_store, 'get_all_user_ids', return_value=set()):
            result = self.moderation_service.check_content_violation(message, sender_id)
            assert result is False
    
    def test_check_content_violation_no_violation(self):
        """Test content check with no violations."""
        message = "Hello world, how are you?"
        sender_id = "user1"
        other_users = {"user2", "user3"}
        
        # Mock user store with other users
        with patch.object(self.moderation_service._user_store, 'get_all_user_ids', return_value=other_users | {sender_id}):
            result = self.moderation_service.check_content_violation(message, sender_id)
            assert result is False
    
    def test_check_content_violation_with_violation(self):
        """Test content check with violation detected."""
        message = "Hey user2, how are you?"
        sender_id = "user1"
        other_users = {"user2", "user3"}
        
        # Mock user store with other users
        with patch.object(self.moderation_service._user_store, 'get_all_user_ids', return_value=other_users | {sender_id}):
            result = self.moderation_service.check_content_violation(message, sender_id)
            assert result is True
    
    def test_check_content_violation_case_insensitive(self):
        """Test that violation detection is case insensitive."""
        message = "Hello USER2, nice to meet you!"
        sender_id = "user1"
        other_users = {"user2", "user3"}
        
        # Mock user store with other users
        with patch.object(self.moderation_service._user_store, 'get_all_user_ids', return_value=other_users | {sender_id}):
            result = self.moderation_service.check_content_violation(message, sender_id)
            assert result is True
    
    def test_check_content_violation_sender_id_in_message_not_violation(self):
        """Test that sender's own ID in message is not a violation."""
        message = "I am user1 and this is my message"
        sender_id = "user1"
        other_users = {"user2", "user3"}
        
        # Mock user store with other users  
        with patch.object(self.moderation_service._user_store, 'get_all_user_ids', return_value=other_users | {sender_id}):
            result = self.moderation_service.check_content_violation(message, sender_id)
            assert result is False
    
    def test_process_message_user_already_blocked(self):
        """Test processing message when user is already blocked."""
        message = "Hello world"
        user_id = "user1"
        
        # Mock user store to return blocked status
        with patch.object(self.moderation_service._user_store, 'is_user_blocked', return_value=True):
            has_violation, is_blocked = self.moderation_service.process_message(message, user_id)
            assert has_violation is False
            assert is_blocked is True
    
    def test_process_message_no_violation(self):
        """Test processing message with no violation."""
        message = "Hello world"
        user_id = "user1"
        
        # Mock user store methods
        with patch.object(self.moderation_service._user_store, 'is_user_blocked', return_value=False), \
             patch.object(self.moderation_service, 'check_content_violation', return_value=False):
            
            has_violation, is_blocked = self.moderation_service.process_message(message, user_id)
            assert has_violation is False
            assert is_blocked is False
    
    def test_process_message_with_violation_not_blocked(self):
        """Test processing message with violation but user not blocked yet."""
        message = "Hello user2"
        user_id = "user1"
        
        # Mock user status with violation but not blocked
        mock_user_status = Mock()
        mock_user_status.is_blocked = False
        
        with patch.object(self.moderation_service._user_store, 'is_user_blocked', return_value=False), \
             patch.object(self.moderation_service, 'check_content_violation', return_value=True), \
             patch.object(self.moderation_service._user_store, 'add_violation', return_value=mock_user_status):
            
            has_violation, is_blocked = self.moderation_service.process_message(message, user_id)
            assert has_violation is True
            assert is_blocked is False
    
    def test_process_message_with_violation_gets_blocked(self):
        """Test processing message with violation that results in blocking."""
        message = "Hello user2"
        user_id = "user1"
        
        # Mock user status with violation and now blocked
        mock_user_status = Mock()
        mock_user_status.is_blocked = True
        
        with patch.object(self.moderation_service._user_store, 'is_user_blocked', return_value=False), \
             patch.object(self.moderation_service, 'check_content_violation', return_value=True), \
             patch.object(self.moderation_service._user_store, 'add_violation', return_value=mock_user_status):
            
            has_violation, is_blocked = self.moderation_service.process_message(message, user_id)
            assert has_violation is True
            assert is_blocked is True