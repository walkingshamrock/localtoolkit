"""
Tests for reminders create_reminder functionality.
"""

import pytest
from unittest.mock import Mock, patch
from localtoolkit.reminders.create_reminder import create_reminder_logic, reminders_create_reminder


@pytest.fixture
def mock_applescript_success():
    """Mock successful AppleScript execution returning reminder JSON."""
    return {
        "success": True,
        "data": '{"title":"Test Reminder","id":"test-id-123","completed":false,"due_date":"2024-01-15T10:00:00Z","notes":"Test notes","priority":5,"list_id":"test-list-id"}'
    }


@pytest.fixture
def mock_applescript_error():
    """Mock failed AppleScript execution."""
    return {
        "success": True,
        "data": "ERROR: Reminder list with ID 'invalid-id' not found"
    }


class TestCreateReminderLogic:
    """Test cases for create_reminder_logic function."""
    
    def test_create_reminder_missing_list_id(self):
        """Test create_reminder_logic with missing list_id."""
        result = create_reminder_logic("", "Test Title")
        
        assert result["success"] is False
        assert "list_id and title are required" in result["error"]
        assert "missing required parameters" in result["message"]
    
    def test_create_reminder_missing_title(self):
        """Test create_reminder_logic with missing title."""
        result = create_reminder_logic("test-list-id", "")
        
        assert result["success"] is False
        assert "list_id and title are required" in result["error"]
        assert "missing required parameters" in result["message"]
    
    @patch('localtoolkit.reminders.create_reminder.applescript_execute')
    def test_create_reminder_success(self, mock_execute, mock_applescript_success):
        """Test successful reminder creation."""
        mock_execute.return_value = mock_applescript_success
        
        result = create_reminder_logic(
            list_id="test-list-id",
            title="Test Reminder",
            notes="Test notes",
            due_date="2024-01-15T10:00:00",
            priority=5
        )
        
        assert result["success"] is True
        assert "Successfully created reminder 'Test Reminder'" in result["message"]
        assert mock_execute.called
        
        # Verify AppleScript was called with proper parameters
        call_args = mock_execute.call_args
        script = call_args[0][0]
        assert 'set targetListId to "test-list-id"' in script
        assert 'make new reminder at end of targetList with properties {name:"Test Reminder"}' in script
        assert 'set body of newReminder to "Test notes"' in script
        assert 'set priority of newReminder to 5' in script
    
    @patch('localtoolkit.reminders.create_reminder.applescript_execute')
    def test_create_reminder_list_not_found(self, mock_execute, mock_applescript_error):
        """Test reminder creation with invalid list ID."""
        mock_execute.return_value = mock_applescript_error
        
        result = create_reminder_logic("invalid-id", "Test Reminder")
        
        assert result["success"] is False
        assert "Reminder list with ID 'invalid-id' not found" in result["error"]
        assert "Failed to create reminder" in result["message"]
    
    @patch('localtoolkit.reminders.create_reminder.applescript_execute')
    def test_create_reminder_applescript_failure(self, mock_execute):
        """Test reminder creation with AppleScript execution failure."""
        mock_execute.return_value = {
            "success": False,
            "error": "AppleScript execution failed"
        }
        
        result = create_reminder_logic("test-list-id", "Test Reminder")
        
        assert result["success"] is False
        assert "Failed to create reminder" in result["message"]
    
    @patch('localtoolkit.reminders.create_reminder.applescript_execute')
    def test_create_reminder_exception(self, mock_execute):
        """Test reminder creation with unexpected exception."""
        mock_execute.side_effect = Exception("Unexpected error")
        
        result = create_reminder_logic("test-list-id", "Test Reminder")
        
        assert result["success"] is False
        assert "Unexpected error" in result["error"]
        assert "Failed to create reminder due to unexpected error" in result["message"]
    
    @patch('localtoolkit.reminders.create_reminder.applescript_execute')
    def test_create_reminder_minimal_parameters(self, mock_execute, mock_applescript_success):
        """Test reminder creation with minimal parameters."""
        mock_execute.return_value = mock_applescript_success
        
        result = create_reminder_logic("test-list-id", "Simple Reminder")
        
        assert result["success"] is True
        assert mock_execute.called
        
        # Verify script contains only required parameters
        call_args = mock_execute.call_args
        script = call_args[0][0]
        assert 'make new reminder at end of targetList with properties {name:"Simple Reminder"}' in script
        assert 'set body of newReminder' not in script  # No notes
        assert 'set priority of newReminder' not in script  # No priority


class TestRemindersCreateReminder:
    """Test cases for reminders_create_reminder function."""
    
    @patch('localtoolkit.reminders.create_reminder.create_reminder_logic')
    def test_reminders_create_reminder_delegation(self, mock_logic):
        """Test that reminders_create_reminder properly delegates to create_reminder_logic."""
        mock_logic.return_value = {"success": True, "message": "Created"}
        
        result = reminders_create_reminder(
            list_id="test-list",
            title="Test",
            notes="Notes",
            due_date="2024-01-15T10:00:00",
            priority=5
        )
        
        # Verify delegation
        mock_logic.assert_called_once_with("test-list", "Test", "Notes", "2024-01-15T10:00:00", 5)
        assert result == {"success": True, "message": "Created"}