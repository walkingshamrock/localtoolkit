"""Tests for the list_events module."""

import pytest
from unittest.mock import patch, Mock
import json

from localtoolkit.calendar.list_events import list_events_logic, register_to_mcp
from tests.utils.assertions import assert_valid_response_format


class TestListEventsLogic:
    """Test cases for list_events_logic function."""
    
    def test_list_events_success(self, mock_applescript, mock_calendar_data, mock_event_data):
        """Test successful event listing."""
        # Configure mock to return calendar data first, then event data
        mock_applescript.side_effect = [
            # First call for get_calendars to verify calendar exists
            {
                "success": True,
                "data": mock_calendar_data,
                "metadata": {},
                "error": None
            },
            # Second call for get_events
            {
                "success": True,
                "data": mock_event_data,
                "metadata": {},
                "error": None
            }
        ]
        
        result = list_events_logic("Work")
        
        # Verify response format
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["data"]) == 3
        assert "Successfully retrieved 3 events from calendar ID: Work" in result["message"]
        assert result["metadata"]["count"] == 3
        assert result["metadata"]["calendar_id"] == "Work"
        assert result["metadata"]["sort_by"] == "start_date"
        assert result["metadata"]["limit"] == 50
        assert "execution_time_ms" in result["metadata"]
        
        # Verify events are sorted by start_date
        events = result["data"]
        assert events[0]["summary"] == "Team Meeting"  # 2024-01-15T10:00:00
        assert events[1]["summary"] == "Lunch Break"   # 2024-01-15T12:00:00
        assert events[2]["summary"] == "Birthday Party" # 2024-01-16T18:00:00
    
    def test_list_events_with_date_filters(self, mock_applescript, mock_calendar_data, mock_event_data):
        """Test event listing with date filters."""
        mock_applescript.side_effect = [
            {"success": True, "data": mock_calendar_data, "metadata": {}, "error": None},
            {"success": True, "data": [mock_event_data[0], mock_event_data[1]], "metadata": {}, "error": None}
        ]
        
        result = list_events_logic("Work", start_date="2024-01-15", end_date="2024-01-15")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["metadata"]["start_date"] == "2024-01-15"
        assert result["metadata"]["end_date"] == "2024-01-15"
    
    def test_list_events_with_limit(self, mock_applescript, mock_calendar_data, mock_event_data):
        """Test event listing with custom limit."""
        mock_applescript.side_effect = [
            {"success": True, "data": mock_calendar_data, "metadata": {}, "error": None},
            {"success": True, "data": [mock_event_data[0]], "metadata": {}, "error": None}
        ]
        
        result = list_events_logic("Work", limit=1)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["metadata"]["limit"] == 1
    
    def test_list_events_sort_by_summary(self, mock_applescript, mock_calendar_data, mock_event_data):
        """Test event listing sorted by summary."""
        mock_applescript.side_effect = [
            {"success": True, "data": mock_calendar_data, "metadata": {}, "error": None},
            {"success": True, "data": mock_event_data, "metadata": {}, "error": None}
        ]
        
        result = list_events_logic("Work", sort_by="summary")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["metadata"]["sort_by"] == "summary"
        
        # Verify events are sorted alphabetically by summary
        events = result["data"]
        assert events[0]["summary"] == "Birthday Party"
        assert events[1]["summary"] == "Lunch Break"
        assert events[2]["summary"] == "Team Meeting"
    
    def test_list_events_invalid_sort_field(self, mock_applescript):
        """Test event listing with invalid sort field."""
        result = list_events_logic("Work", sort_by="invalid_field")
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert "Invalid sort_by parameter" in result["message"]
        assert result["error"] == "sort_by must be one of ['start_date', 'summary', 'end_date']"
        assert result["metadata"]["valid_sort_fields"] == ["start_date", "summary", "end_date"]
    
    def test_list_events_calendar_not_found(self, mock_applescript, mock_calendar_data):
        """Test event listing for non-existent calendar."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_calendar_data,
            "metadata": {},
            "error": None
        }
        
        result = list_events_logic("NonExistentCalendar")
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["message"] == "Failed to retrieve events from calendar ID: NonExistentCalendar"
        assert "Calendar with name 'NonExistentCalendar' not found" in result["error"]
    
    def test_list_events_empty_result(self, mock_applescript, mock_calendar_data):
        """Test handling of empty event list."""
        mock_applescript.side_effect = [
            {"success": True, "data": mock_calendar_data, "metadata": {}, "error": None},
            {"success": True, "data": [], "metadata": {}, "error": None}
        ]
        
        result = list_events_logic("Work")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["data"] == []
        assert result["message"] == "No events found in calendar ID: Work"
        assert result["metadata"]["count"] == 0
    
    def test_list_events_applescript_error(self, mock_applescript, mock_calendar_data):
        """Test handling of AppleScript errors during event retrieval."""
        mock_applescript.side_effect = [
            {"success": True, "data": mock_calendar_data, "metadata": {}, "error": None},
            {"success": False, "data": None, "metadata": {}, "error": "Failed to access events"}
        ]
        
        result = list_events_logic("Work")
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["message"] == "Failed to retrieve events from calendar ID: Work"
        assert result["error"] == "Failed to access events"
    
    def test_list_events_calendar_access_error(self, mock_applescript):
        """Test handling of errors when accessing calendars."""
        mock_applescript.return_value = {
            "success": False,
            "data": None,
            "metadata": {},
            "error": "Calendar app not accessible"
        }
        
        result = list_events_logic("Work")
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["error"] == "Failed to access calendars: Calendar app not accessible"
    
    def test_list_events_sorting_failure(self, mock_applescript, mock_calendar_data):
        """Test graceful handling of sorting failures."""
        # Create event data that will cause sorting to fail
        bad_event_data = [{"summary": None, "start_date": "2024-01-15T10:00:00"}]
        mock_applescript.side_effect = [
            {"success": True, "data": mock_calendar_data, "metadata": {}, "error": None},
            {"success": True, "data": bad_event_data, "metadata": {}, "error": None}
        ]
        
        with patch('builtins.print') as mock_print:
            result = list_events_logic("Work", sort_by="summary")
        
        # Should still succeed but with unsorted data
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["data"]) == 1
        # Check that warning was printed
        mock_print.assert_called_once()
        assert "Warning: Failed to sort events" in str(mock_print.call_args)


class TestRegisterToMCP:
    """Test cases for MCP registration."""
    
    def test_register_to_mcp(self):
        """Test that the function registers correctly to MCP."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        
        register_to_mcp(mock_mcp)
        
        # Verify that mcp.tool() was called
        mock_mcp.tool.assert_called_once()
    
    def test_registered_function_calls_logic(self, mock_applescript, mock_calendar_data, mock_event_data):
        """Test that the registered function calls the logic function."""
        mock_mcp = Mock()
        registered_func = None
        
        def capture_registration():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func
            return decorator
        
        mock_mcp.tool = capture_registration
        
        # Configure mock
        mock_applescript.side_effect = [
            {"success": True, "data": mock_calendar_data, "metadata": {}, "error": None},
            {"success": True, "data": mock_event_data, "metadata": {}, "error": None}
        ]
        
        # Register the function
        register_to_mcp(mock_mcp)
        
        # Call the registered function
        assert registered_func is not None
        result = registered_func(
            calendar_id="Work",
            start_date="2024-01-15",
            end_date="2024-01-16",
            limit=10,
            sort_by="end_date"
        )
        
        # Verify it returns the expected result
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["metadata"]["calendar_id"] == "Work"
        assert result["metadata"]["start_date"] == "2024-01-15"
        assert result["metadata"]["end_date"] == "2024-01-16"
        assert result["metadata"]["limit"] == 10
        assert result["metadata"]["sort_by"] == "end_date"