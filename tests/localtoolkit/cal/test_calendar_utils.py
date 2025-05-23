"""Tests for the calendar utils module."""

import pytest
from unittest.mock import patch, Mock
import json

from localtoolkit.calendar.utils.calendar_utils import (
    parse_calendar_response, get_calendars, get_events, create_event
)


class TestParseCalendarResponse:
    """Test cases for parse_calendar_response function."""
    
    def test_parse_success_response(self):
        """Test parsing successful response."""
        response = {
            "success": True,
            "data": [{"name": "Work", "id": "Work"}],
            "metadata": {"count": 1},
            "error": None
        }
        
        result = parse_calendar_response(response)
        
        assert result == response
        assert result["success"] is True
        assert result["data"] == [{"name": "Work", "id": "Work"}]
        assert result["metadata"] == {"count": 1}
        assert result["error"] is None
    
    def test_parse_error_response(self):
        """Test parsing error response."""
        response = {
            "success": False,
            "data": None,
            "metadata": {},
            "error": "Calendar not accessible"
        }
        
        result = parse_calendar_response(response)
        
        assert result == response
        assert result["success"] is False
        assert result["data"] is None
        assert result["error"] == "Calendar not accessible"
    
    def test_parse_response_without_metadata(self):
        """Test parsing response without metadata field."""
        response = {
            "success": True,
            "data": [{"name": "Personal"}],
            "error": None
        }
        
        result = parse_calendar_response(response)
        
        assert result["success"] is True
        assert result["data"] == [{"name": "Personal"}]
        assert result["metadata"] == {}
        assert result["error"] is None


class TestGetCalendars:
    """Test cases for get_calendars function."""
    
    def test_get_calendars_success(self, mock_applescript, mock_calendar_data):
        """Test successful calendar retrieval."""
        # Mock AppleScript to return JSON string
        calendar_json = json.dumps(mock_calendar_data)
        mock_applescript.return_value = {
            "success": True,
            "data": calendar_json,
            "metadata": {},
            "error": None
        }
        
        result = get_calendars()
        
        assert result["success"] is True
        assert result["data"] == mock_calendar_data
        assert len(result["data"]) == 3
    
    def test_get_calendars_applescript_error(self, mock_applescript):
        """Test handling of AppleScript execution error."""
        mock_applescript.return_value = {
            "success": False,
            "data": None,
            "metadata": {},
            "error": "AppleScript execution failed"
        }
        
        result = get_calendars()
        
        assert result["success"] is False
        assert result["data"] is None
        assert result["error"] == "AppleScript execution failed"
    
    def test_get_calendars_error_string_response(self, mock_applescript):
        """Test handling of error string in response data."""
        mock_applescript.return_value = {
            "success": True,
            "data": "ERROR: Calendar app not running",
            "metadata": {},
            "error": None
        }
        
        result = get_calendars()
        
        assert result["success"] is False
        assert result["data"] is None
        assert result["error"] == "Calendar app not running"
    
    def test_get_calendars_empty_list(self, mock_applescript):
        """Test handling of empty calendar list."""
        mock_applescript.return_value = {
            "success": True,
            "data": "[]",
            "metadata": {},
            "error": None
        }
        
        result = get_calendars()
        
        assert result["success"] is True
        assert result["data"] == []


class TestGetEvents:
    """Test cases for get_events function."""
    
    def test_get_events_success(self, mock_applescript, mock_calendar_data, mock_event_data):
        """Test successful event retrieval."""
        # Mock first call to get_calendars and second call to get events
        mock_applescript.side_effect = [
            {"success": True, "data": json.dumps(mock_calendar_data), "metadata": {}, "error": None},
            {"success": True, "data": json.dumps(mock_event_data), "metadata": {}, "error": None}
        ]
        
        result = get_events("Work", limit=50)
        
        assert result["success"] is True
        assert result["data"] == mock_event_data
        assert len(result["data"]) == 3
    
    def test_get_events_calendar_not_found(self, mock_applescript, mock_calendar_data):
        """Test event retrieval for non-existent calendar."""
        mock_applescript.return_value = {
            "success": True,
            "data": json.dumps(mock_calendar_data),
            "metadata": {},
            "error": None
        }
        
        result = get_events("NonExistent")
        
        assert result["success"] is False
        assert result["data"] is None
        assert result["error"] == "Calendar with name 'NonExistent' not found"
    
    def test_get_events_calendar_access_error(self, mock_applescript):
        """Test handling of calendar access error."""
        mock_applescript.return_value = {
            "success": False,
            "data": None,
            "metadata": {},
            "error": "Cannot access calendars"
        }
        
        result = get_events("Work")
        
        assert result["success"] is False
        assert result["data"] is None
        assert result["error"] == "Failed to access calendars: Cannot access calendars"
    
    def test_get_events_with_date_filters(self, mock_applescript, mock_calendar_data):
        """Test event retrieval with date filters."""
        mock_applescript.side_effect = [
            {"success": True, "data": json.dumps(mock_calendar_data), "metadata": {}, "error": None},
            {"success": True, "data": "[]", "metadata": {}, "error": None}
        ]
        
        result = get_events("Work", start_date="2024-01-15", end_date="2024-01-16", limit=10)
        
        assert result["success"] is True
        assert result["data"] == []
        
        # Verify AppleScript was called with correct parameters
        calls = mock_applescript.call_args_list
        assert len(calls) == 2
        # Check that the second call's script contains the limit
        assert "10" in calls[1][0][0]  # limit parameter in script
    
    def test_get_events_error_string_response(self, mock_applescript, mock_calendar_data):
        """Test handling of error string in event response."""
        mock_applescript.side_effect = [
            {"success": True, "data": json.dumps(mock_calendar_data), "metadata": {}, "error": None},
            {"success": True, "data": "ERROR: Failed to get events", "metadata": {}, "error": None}
        ]
        
        result = get_events("Work")
        
        assert result["success"] is False
        assert result["data"] is None
        assert result["error"] == "Failed to get events"


class TestCreateEvent:
    """Test cases for create_event function."""
    
    def test_create_event_success(self, mock_applescript, mock_calendar_data):
        """Test successful event creation."""
        mock_applescript.side_effect = [
            {"success": True, "data": json.dumps(mock_calendar_data), "metadata": {}, "error": None},
            {"success": True, "data": '{"success": true, "event_id": "new-123", "message": "Event created successfully"}', 
             "metadata": {}, "error": None}
        ]
        
        result = create_event(
            calendar_id="Work",
            summary="Team Meeting",
            start_date="2024-01-20T10:00:00",
            end_date="2024-01-20T11:00:00"
        )
        
        assert result["success"] is True
        assert result["data"]["event_id"] == "new-123"
    
    def test_create_event_with_all_fields(self, mock_applescript, mock_calendar_data):
        """Test event creation with all optional fields."""
        mock_applescript.side_effect = [
            {"success": True, "data": json.dumps(mock_calendar_data), "metadata": {}, "error": None},
            {"success": True, "data": '{"success": true, "event_id": "new-456", "message": "Event created successfully"}',
             "metadata": {}, "error": None}
        ]
        
        result = create_event(
            calendar_id="Personal",
            summary="Doctor Visit",
            start_date="2024-01-25T14:00:00",
            end_date="2024-01-25T15:00:00",
            location="Medical Center",
            description="Annual checkup",
            all_day=False
        )
        
        assert result["success"] is True
        assert result["data"]["event_id"] == "new-456"
        
        # Verify the script contains the location and description
        calls = mock_applescript.call_args_list
        script = calls[1][0][0]
        assert "Medical Center" in script
        assert "Annual checkup" in script
    
    def test_create_event_calendar_not_found(self, mock_applescript, mock_calendar_data):
        """Test event creation for non-existent calendar."""
        mock_applescript.return_value = {
            "success": True,
            "data": json.dumps(mock_calendar_data),
            "metadata": {},
            "error": None
        }
        
        result = create_event(
            calendar_id="NonExistent",
            summary="Test Event",
            start_date="2024-01-20T10:00:00",
            end_date="2024-01-20T11:00:00"
        )
        
        assert result["success"] is False
        assert result["data"] is None
        assert result["error"] == "Calendar with name 'NonExistent' not found"
    
    def test_create_event_special_characters(self, mock_applescript, mock_calendar_data):
        """Test event creation with special characters."""
        mock_applescript.side_effect = [
            {"success": True, "data": json.dumps(mock_calendar_data), "metadata": {}, "error": None},
            {"success": True, "data": '{"success": true, "event_id": "new-789", "message": "Event created successfully"}',
             "metadata": {}, "error": None}
        ]
        
        result = create_event(
            calendar_id="Work",
            summary='Meeting with "Team"',
            start_date="2024-01-20T10:00:00",
            end_date="2024-01-20T11:00:00",
            location="Room A & B",
            description='Discuss "roadmap"'
        )
        
        assert result["success"] is True
        
        # Verify special characters are escaped in the script
        calls = mock_applescript.call_args_list
        script = calls[1][0][0]
        assert '\\\\"Team\\\\"' in script or 'Meeting with \\\\"Team\\\\"' in script
    
    def test_create_event_error_response(self, mock_applescript, mock_calendar_data):
        """Test handling of error during event creation."""
        mock_applescript.side_effect = [
            {"success": True, "data": json.dumps(mock_calendar_data), "metadata": {}, "error": None},
            {"success": True, "data": "ERROR: Failed to create event", "metadata": {}, "error": None}
        ]
        
        result = create_event(
            calendar_id="Work",
            summary="Test Event",
            start_date="2024-01-20T10:00:00",
            end_date="2024-01-20T11:00:00"
        )
        
        assert result["success"] is False
        assert result["data"] is None
        assert result["error"] == "Failed to create event"