"""
Tests for reminders complete_reminder functionality.
"""

import pytest
from unittest.mock import patch
from localtoolkit.reminders.complete_reminder import complete_reminder_logic, reminders_complete_reminder


@pytest.fixture
def mock_applescript_success():
    """Mock successful AppleScript execution returning completed reminder JSON."""
    return {
        "success": True,
        "data": '{"title":"Test Reminder","id":"test-id-123","completed":true,"due_date":"2024-01-15T10:00:00Z","notes":"Test notes","priority":5,"list_id":"test-list-id"}'
    }


@pytest.fixture
def mock_applescript_error():
    """Mock failed AppleScript execution."""
    return {
        "success": True,
        "data": "ERROR: Reminder with ID 'invalid-id' not found"
    }


class TestCompleteReminderLogic:
    """Test cases for complete_reminder_logic function."""
    
    def test_complete_reminder_missing_id(self):
        """Test complete_reminder_logic with missing reminder_id."""
        result = complete_reminder_logic("")
        
        assert result["success"] is False
        assert "reminder_id is required" in result["error"]
        assert "missing required parameter" in result["message"]
    
    @patch('localtoolkit.reminders.complete_reminder.applescript_execute')
    def test_complete_reminder_success(self, mock_execute, mock_applescript_success):
        """Test successful reminder completion."""
        mock_execute.return_value = mock_applescript_success
        
        result = complete_reminder_logic("test-id-123", True)
        
        assert result["success"] is True
        assert "Successfully marked reminder ID: test-id-123 as completed" in result["message"]
        assert mock_execute.called
        
        # Verify AppleScript was called with proper parameters
        call_args = mock_execute.call_args
        script = call_args[0][0]
        assert 'set targetReminderId to "test-id-123"' in script
        assert 'set completed of targetReminder to true' in script
    
    @patch('localtoolkit.reminders.complete_reminder.applescript_execute')
    def test_uncomplete_reminder_success(self, mock_execute):
        """Test successful reminder un-completion."""
        # Mock response for uncompleted reminder
        mock_response = {
            "success": True,
            "data": '{"title":"Test Reminder","id":"test-id-123","completed":false,"due_date":"2024-01-15T10:00:00Z","notes":"Test notes","priority":5,"list_id":"test-list-id"}'
        }
        mock_execute.return_value = mock_response
        
        result = complete_reminder_logic("test-id-123", False)
        
        assert result["success"] is True
        assert "Successfully marked reminder ID: test-id-123 as incomplete" in result["message"]
        assert mock_execute.called
        
        # Verify AppleScript was called with proper parameters
        call_args = mock_execute.call_args
        script = call_args[0][0]
        assert 'set targetReminderId to "test-id-123"' in script
        assert 'set completed of targetReminder to false' in script
    
    @patch('localtoolkit.reminders.complete_reminder.applescript_execute')
    def test_complete_reminder_not_found(self, mock_execute, mock_applescript_error):
        """Test reminder completion with invalid reminder ID."""
        mock_execute.return_value = mock_applescript_error
        
        result = complete_reminder_logic("invalid-id")
        
        assert result["success"] is False
        assert "Reminder with ID 'invalid-id' not found" in result["error"]
        assert "Failed to update reminder completion status" in result["message"]
    
    @patch('localtoolkit.reminders.complete_reminder.applescript_execute')
    def test_complete_reminder_applescript_failure(self, mock_execute):
        """Test reminder completion with AppleScript execution failure."""
        mock_execute.return_value = {
            "success": False,
            "error": "AppleScript execution failed"
        }
        
        result = complete_reminder_logic("test-id-123")
        
        assert result["success"] is False
        assert "Failed to update reminder completion status" in result["message"]
    
    @patch('localtoolkit.reminders.complete_reminder.applescript_execute')
    def test_complete_reminder_exception(self, mock_execute):
        """Test reminder completion with unexpected exception."""
        mock_execute.side_effect = Exception("Unexpected error")
        
        result = complete_reminder_logic("test-id-123")
        
        assert result["success"] is False
        assert "Unexpected error" in result["error"]
        assert "Failed to update reminder completion status due to unexpected error" in result["message"]


class TestRemindersCompleteReminder:
    """Test cases for reminders_complete_reminder function."""
    
    @patch('localtoolkit.reminders.complete_reminder.complete_reminder_logic')
    def test_reminders_complete_reminder_delegation(self, mock_logic):
        """Test that reminders_complete_reminder properly delegates to complete_reminder_logic."""
        mock_logic.return_value = {"success": True, "message": "Completed"}
        
        result = reminders_complete_reminder("test-id", True)
        
        # Verify delegation
        mock_logic.assert_called_once_with("test-id", True)
        assert result == {"success": True, "message": "Completed"}
    
    @patch('localtoolkit.reminders.complete_reminder.complete_reminder_logic')
    def test_reminders_complete_reminder_default_completed(self, mock_logic):
        """Test that reminders_complete_reminder uses default completed=True."""
        mock_logic.return_value = {"success": True, "message": "Completed"}
        
        result = reminders_complete_reminder("test-id")
        
        # Verify delegation with default completed=True
        mock_logic.assert_called_once_with("test-id", True)
        assert result == {"success": True, "message": "Completed"}