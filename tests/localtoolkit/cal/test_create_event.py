"""Tests for the create_event module."""

import pytest
from unittest.mock import patch, Mock
import json

from localtoolkit.calendar.create_event import create_event_logic, register_to_mcp
from tests.utils.assertions import assert_valid_response_format


class TestCreateEventLogic:
    """Test cases for create_event_logic function."""
    
    def test_create_event_success(self, mock_applescript, mock_calendar_data):
        """Test successful event creation."""
        # Configure mock to return calendar data first, then event creation result
        mock_applescript.side_effect = [
            # First call for get_calendars to verify calendar exists
            {
                "success": True,
                "data": mock_calendar_data,
                "metadata": {},
                "error": None
            },
            # Second call for create_event
            {
                "success": True,
                "data": {"event_id": "new-event-123"},
                "metadata": {},
                "error": None
            }
        ]
        
        result = create_event_logic(
            calendar_id="Work",
            summary="Team Standup",
            start_date="2024-01-20T09:00:00",
            end_date="2024-01-20T09:30:00"
        )
        
        # Verify response format
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["data"]["event_id"] == "new-event-123"
        assert result["data"]["summary"] == "Team Standup"
        assert result["data"]["start_date"] == "2024-01-20T09:00:00"
        assert result["data"]["end_date"] == "2024-01-20T09:30:00"
        assert result["data"]["location"] == ""
        assert result["data"]["description"] == ""
        assert result["data"]["all_day"] is False
        assert result["data"]["calendar_id"] == "Work"
        assert result["message"] == "Successfully created event 'Team Standup' in calendar ID: Work"
        assert result["metadata"]["calendar_id"] == "Work"
        assert "execution_time_ms" in result["metadata"]
    
    def test_create_event_with_all_fields(self, mock_applescript, mock_calendar_data):
        """Test event creation with all optional fields."""
        mock_applescript.side_effect = [
            {"success": True, "data": mock_calendar_data, "metadata": {}, "error": None},
            {"success": True, "data": {"event_id": "new-event-456"}, "metadata": {}, "error": None}
        ]
        
        result = create_event_logic(
            calendar_id="Personal",
            summary="Doctor Appointment",
            start_date="2024-01-25T14:00:00",
            end_date="2024-01-25T15:00:00",
            location="Medical Center",
            description="Annual checkup",
            all_day=False
        )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["data"]["location"] == "Medical Center"
        assert result["data"]["description"] == "Annual checkup"
        assert result["data"]["all_day"] is False
    
    def test_create_all_day_event(self, mock_applescript, mock_calendar_data):
        """Test creation of all-day event."""
        mock_applescript.side_effect = [
            {"success": True, "data": mock_calendar_data, "metadata": {}, "error": None},
            {"success": True, "data": {"event_id": "all-day-event-789"}, "metadata": {}, "error": None}
        ]
        
        result = create_event_logic(
            calendar_id="Family",
            summary="Birthday",
            start_date="2024-02-01",
            end_date="2024-02-01",
            all_day=True
        )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["data"]["all_day"] is True
        assert result["data"]["start_date"] == "2024-02-01"
        assert result["data"]["end_date"] == "2024-02-01"
    
    def test_create_event_missing_calendar_id(self, mock_applescript):
        """Test event creation with missing calendar_id."""
        result = create_event_logic(
            calendar_id="",
            summary="Test Event",
            start_date="2024-01-20T10:00:00",
            end_date="2024-01-20T11:00:00"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["message"] == "calendar_id is required"
        assert result["error"] == "calendar_id parameter cannot be empty"
    
    def test_create_event_missing_summary(self, mock_applescript):
        """Test event creation with missing summary."""
        result = create_event_logic(
            calendar_id="Work",
            summary="",
            start_date="2024-01-20T10:00:00",
            end_date="2024-01-20T11:00:00"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["message"] == "summary is required"
        assert result["error"] == "summary parameter cannot be empty"
        assert result["metadata"]["calendar_id"] == "Work"
    
    def test_create_event_missing_start_date(self, mock_applescript):
        """Test event creation with missing start_date."""
        result = create_event_logic(
            calendar_id="Work",
            summary="Test Event",
            start_date="",
            end_date="2024-01-20T11:00:00"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["message"] == "start_date is required"
        assert result["error"] == "start_date parameter cannot be empty"
    
    def test_create_event_missing_end_date(self, mock_applescript):
        """Test event creation with missing end_date."""
        result = create_event_logic(
            calendar_id="Work",
            summary="Test Event",
            start_date="2024-01-20T10:00:00",
            end_date=""
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["message"] == "end_date is required"
        assert result["error"] == "end_date parameter cannot be empty"
    
    def test_create_event_calendar_not_found(self, mock_applescript, mock_calendar_data):
        """Test event creation for non-existent calendar."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_calendar_data,
            "metadata": {},
            "error": None
        }
        
        result = create_event_logic(
            calendar_id="NonExistentCalendar",
            summary="Test Event",
            start_date="2024-01-20T10:00:00",
            end_date="2024-01-20T11:00:00"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["message"] == "Failed to create event in calendar ID: NonExistentCalendar"
        assert "Calendar with name 'NonExistentCalendar' not found" in result["error"]
    
    def test_create_event_applescript_error(self, mock_applescript, mock_calendar_data):
        """Test handling of AppleScript errors during event creation."""
        mock_applescript.side_effect = [
            {"success": True, "data": mock_calendar_data, "metadata": {}, "error": None},
            {"success": False, "data": None, "metadata": {}, "error": "Failed to create event"}
        ]
        
        result = create_event_logic(
            calendar_id="Work",
            summary="Test Event",
            start_date="2024-01-20T10:00:00",
            end_date="2024-01-20T11:00:00"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["message"] == "Failed to create event in calendar ID: Work"
        assert result["error"] == "Failed to create event"
    
    def test_create_event_calendar_access_error(self, mock_applescript):
        """Test handling of errors when accessing calendars."""
        mock_applescript.return_value = {
            "success": False,
            "data": None,
            "metadata": {},
            "error": "Calendar app not accessible"
        }
        
        result = create_event_logic(
            calendar_id="Work",
            summary="Test Event",
            start_date="2024-01-20T10:00:00",
            end_date="2024-01-20T11:00:00"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["error"] == "Failed to access calendars: Calendar app not accessible"
    
    def test_create_event_with_special_characters(self, mock_applescript, mock_calendar_data):
        """Test event creation with special characters in fields."""
        mock_applescript.side_effect = [
            {"success": True, "data": mock_calendar_data, "metadata": {}, "error": None},
            {"success": True, "data": {"event_id": "special-event-101"}, "metadata": {}, "error": None}
        ]
        
        result = create_event_logic(
            calendar_id="Work",
            summary='Meeting with "Team Lead"',
            start_date="2024-01-20T10:00:00",
            end_date="2024-01-20T11:00:00",
            location="Conference Room A & B",
            description="Discuss Q1 goals\nand deliverables"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["data"]["summary"] == 'Meeting with "Team Lead"'
        assert result["data"]["location"] == "Conference Room A & B"
        assert result["data"]["description"] == "Discuss Q1 goals\nand deliverables"


class TestRegisterToMCP:
    """Test cases for MCP registration."""
    
    def test_register_to_mcp(self):
        """Test that the function registers correctly to MCP."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        
        register_to_mcp(mock_mcp)
        
        # Verify that mcp.tool() was called
        mock_mcp.tool.assert_called_once()
    
    def test_registered_function_calls_logic(self, mock_applescript, mock_calendar_data):
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
            {"success": True, "data": {"event_id": "registered-event-999"}, "metadata": {}, "error": None}
        ]
        
        # Register the function
        register_to_mcp(mock_mcp)
        
        # Call the registered function
        assert registered_func is not None
        result = registered_func(
            calendar_id="Personal",
            summary="Lunch Meeting",
            start_date="2024-01-22T12:00:00",
            end_date="2024-01-22T13:00:00",
            location="Downtown Cafe",
            description="Catch up with client",
            all_day=False
        )
        
        # Verify it returns the expected result
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["data"]["event_id"] == "registered-event-999"
        assert result["data"]["summary"] == "Lunch Meeting"
        assert result["data"]["location"] == "Downtown Cafe"