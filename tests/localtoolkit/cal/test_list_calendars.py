"""Tests for the list_calendars module."""

import pytest
from unittest.mock import patch, Mock
import json

from localtoolkit.calendar.list_calendars import list_calendars_logic, register_to_mcp
from tests.utils.assertions import assert_valid_response_format


class TestListCalendarsLogic:
    """Test cases for list_calendars_logic function."""
    
    def test_list_calendars_success(self, mock_applescript, mock_calendar_data):
        """Test successful calendar listing."""
        # Configure mock to return calendar data
        mock_applescript.return_value = {
            "success": True,
            "data": mock_calendar_data,
            "metadata": {},
            "error": None
        }
        
        result = list_calendars_logic()
        
        # Verify response format
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["data"]) == 3
        assert result["message"] == "Successfully retrieved 3 calendars"
        assert result["metadata"]["count"] == 3
        assert result["metadata"]["sort_by"] == "name"
        assert "execution_time_ms" in result["metadata"]
        
        # Verify calendar data
        calendars = result["data"]
        assert calendars[0]["name"] == "Family"  # Sorted by name
        assert calendars[1]["name"] == "Personal"
        assert calendars[2]["name"] == "Work"
    
    def test_list_calendars_with_sort_by_type(self, mock_applescript, mock_calendar_data):
        """Test calendar listing with different sort order."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_calendar_data,
            "metadata": {},
            "error": None
        }
        
        result = list_calendars_logic(sort_by="type")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["metadata"]["sort_by"] == "type"
    
    def test_list_calendars_invalid_sort_field(self, mock_applescript):
        """Test calendar listing with invalid sort field."""
        result = list_calendars_logic(sort_by="invalid_field")
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert "Invalid sort_by parameter" in result["message"]
        assert result["error"] == "sort_by must be one of ['name', 'id', 'type']"
        assert result["metadata"]["valid_sort_fields"] == ["name", "id", "type"]
    
    def test_list_calendars_empty_result(self, mock_applescript):
        """Test handling of empty calendar list."""
        mock_applescript.return_value = {
            "success": True,
            "data": [],
            "metadata": {},
            "error": None
        }
        
        result = list_calendars_logic()
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["data"] == []
        assert result["message"] == "No calendars found"
        assert result["metadata"]["count"] == 0
        assert result["error"] is None
    
    def test_list_calendars_applescript_error(self, mock_applescript):
        """Test handling of AppleScript errors."""
        mock_applescript.return_value = {
            "success": False,
            "data": None,
            "metadata": {},
            "error": "Calendar app not accessible"
        }
        
        result = list_calendars_logic()
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["data"] is None
        assert result["message"] == "Failed to retrieve calendars"
        assert result["error"] == "Calendar app not accessible"
    
    def test_list_calendars_sorting_failure(self, mock_applescript, mock_calendar_data):
        """Test graceful handling of sorting failures."""
        # Create data that will cause sorting to fail by making the lambda raise an exception
        class BadDict(dict):
            def get(self, key, default=None):
                raise RuntimeError("Simulated sorting error")
        
        bad_data = [BadDict({"name": "Test", "id": "test", "type": "calendar"})]
        mock_applescript.return_value = {
            "success": True,
            "data": bad_data,
            "metadata": {},
            "error": None
        }
        
        with patch('builtins.print') as mock_print:
            result = list_calendars_logic()
        
        # Should still succeed but with unsorted data
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["data"]) == 1
        # Check that warning was printed
        mock_print.assert_called_once()
        assert "Warning: Failed to sort calendars" in str(mock_print.call_args)


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
        mock_applescript.return_value = {
            "success": True,
            "data": mock_calendar_data,
            "metadata": {},
            "error": None
        }
        
        # Register the function
        register_to_mcp(mock_mcp)
        
        # Call the registered function
        assert registered_func is not None
        result = registered_func(sort_by="id")
        
        # Verify it returns the expected result
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["metadata"]["sort_by"] == "id"