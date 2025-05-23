"""
Unit tests for the Reminders app's list_reminders functionality.

This module contains tests for listing reminders from a specific list in the macOS Reminders app.
"""

import pytest
from unittest.mock import patch
from tests.utils.assertions import assert_valid_reminders_response


@pytest.mark.unit
def test_list_reminders_success(mock_reminder_lists_response, mock_get_reminders_response):
    """Test successful retrieval of reminders from a list."""
    # Use unittest.mock.patch to mock the get_reminders function
    with patch('localtoolkit.reminders.list_reminders.get_reminders') as mock_get_reminders:
        # Configure the mock to return our mock response
        mock_get_reminders.return_value = mock_get_reminders_response
        
        # Import the function we're testing
        from localtoolkit.reminders.list_reminders import list_reminders_logic
        
        # Test with default parameters
        list_id = "x-apple-reminder://F0A0F342-FC00-1234-B630-CFBE2EB928A1"
        result = list_reminders_logic(list_id)
        
        # Check if our mock was called with the correct parameters
        mock_get_reminders.assert_called_once_with(list_id, limit=50)
        
        # Assertions
        assert_valid_reminders_response(result)
        assert result["success"] == True
        assert len(result["data"]) == 3  # Based on mock data
        assert result["data"][0]["title"] is not None
        assert "metadata" in result
        assert "execution_time_ms" in result["metadata"]
        assert "sort_by" in result["metadata"]
        assert result["metadata"]["sort_by"] == "title"  # Default sort
        assert "incomplete_count" in result["metadata"]


@pytest.mark.unit
def test_list_reminders_sort_by_due_date(mock_get_reminders_response):
    """Test sorting reminders by due date."""
    with patch('localtoolkit.reminders.list_reminders.get_reminders') as mock_get_reminders:
        # Configure the mock to return our mock response
        mock_get_reminders.return_value = mock_get_reminders_response
        
        from localtoolkit.reminders.list_reminders import list_reminders_logic
        
        # Test with sorting by due_date
        list_id = "x-apple-reminder://F0A0F342-FC00-1234-B630-CFBE2EB928A1"
        result = list_reminders_logic(list_id, sort_by="due_date")
        
        # Assertions
        assert result["success"] == True
        assert result["metadata"]["sort_by"] == "due_date"


@pytest.mark.unit
def test_list_reminders_sort_by_priority(mock_get_reminders_response):
    """Test sorting reminders by priority."""
    with patch('localtoolkit.reminders.list_reminders.get_reminders') as mock_get_reminders:
        # Configure the mock to return our mock response
        mock_get_reminders.return_value = mock_get_reminders_response
        
        from localtoolkit.reminders.list_reminders import list_reminders_logic
        
        # Test with sorting by priority
        list_id = "x-apple-reminder://F0A0F342-FC00-1234-B630-CFBE2EB928A1"
        result = list_reminders_logic(list_id, sort_by="priority")
        
        # Assertions
        assert result["success"] == True
        assert result["metadata"]["sort_by"] == "priority"


@pytest.mark.unit
def test_list_reminders_hide_completed(mock_get_reminders_response):
    """Test filtering out completed reminders."""
    with patch('localtoolkit.reminders.list_reminders.get_reminders') as mock_get_reminders:
        # Create a filtered response that simulates AppleScript-level filtering
        filtered_response = mock_get_reminders_response.copy()
        filtered_response["data"] = [r for r in mock_get_reminders_response["data"] if not r.get("completed", False)]
        
        # Configure the mock to return the filtered response
        mock_get_reminders.return_value = filtered_response
        
        from localtoolkit.reminders.list_reminders import list_reminders_logic
        
        # Test with show_completed=False
        list_id = "x-apple-reminder://F0A0F342-FC00-1234-B630-CFBE2EB928A1"
        result = list_reminders_logic(list_id, show_completed=False)
        
        # Verify the mock was called with double limit when show_completed=False
        mock_get_reminders.assert_called_once_with(list_id, limit=100)
        
        # Assertions
        assert result["success"] == True
        # Verify no completed reminders are returned
        for reminder in result["data"]:
            assert reminder["completed"] == False
        # Metadata should indicate show_completed=False
        assert result["metadata"]["show_completed"] == False


@pytest.mark.unit
def test_list_reminders_invalid_sort(mock_get_reminders_response):
    """Test handling of invalid sort parameter."""
    with patch('localtoolkit.reminders.list_reminders.get_reminders') as mock_get_reminders:
        mock_get_reminders.return_value = mock_get_reminders_response
        
        from localtoolkit.reminders.list_reminders import list_reminders_logic
        
        # Test with invalid sort parameter
        list_id = "x-apple-reminder://F0A0F342-FC00-1234-B630-CFBE2EB928A1"
        result = list_reminders_logic(list_id, sort_by="invalid_sort")
        
        # Assertions
        assert result["success"] == False
        assert "error" in result
        assert "Invalid sort_by parameter" in result["message"]
        assert "valid_sort_fields" in result["metadata"]


@pytest.mark.unit
def test_list_reminders_error(mock_reminder_lists_error_response):
    """Test handling error response from get_reminders."""
    with patch('localtoolkit.reminders.list_reminders.get_reminders',
               return_value=mock_reminder_lists_error_response):
        
        from localtoolkit.reminders.list_reminders import list_reminders_logic
        
        # Test with error response
        list_id = "x-apple-reminder://F0A0F342-FC00-1234-B630-CFBE2EB928A1"
        result = list_reminders_logic(list_id)
        
        # Assertions
        assert result["success"] == False
        assert "error" in result
        assert result["data"] is None


@pytest.mark.unit
def test_list_reminders_empty(monkeypatch):
    """Test handling of empty reminder list."""
    # Create an empty list response
    empty_response = {
        "success": True,
        "data": [],
        "metadata": {
            "execution_time_ms": 120
        },
        "error": None
    }
    
    # Use patch to mock get_reminders
    with patch('localtoolkit.reminders.list_reminders.get_reminders') as mock_get_reminders:
        # Configure the mock to return our empty response
        mock_get_reminders.return_value = empty_response
        
        from localtoolkit.reminders.list_reminders import list_reminders_logic
        
        # Test with empty list
        list_id = "x-apple-reminder://F0A0F342-FC00-1234-B630-CFBE2EB928A1"
        result = list_reminders_logic(list_id)
        
        # Assertions
        assert result["success"] == True
        assert result["data"] == []
        assert "count" in result["metadata"]
        assert result["metadata"]["count"] == 0
        assert result["metadata"]["incomplete_count"] == 0