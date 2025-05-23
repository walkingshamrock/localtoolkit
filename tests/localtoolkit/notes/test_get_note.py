"""
Tests for the get_note module.

This module contains tests for getting specific notes from the Notes app.
"""

import pytest
from unittest.mock import patch
from localtoolkit.notes.get_note import get_note_logic


class TestGetNoteLogic:
    """Test cases for get_note_logic function."""

    @patch('localtoolkit.notes.get_note.applescript_execute')
    def test_get_note_success(self, mock_applescript, mock_notes):
        """Test successful note retrieval."""
        # Setup mock response
        note = mock_notes[0]
        mock_response = f"SUCCESS:{note['id']}<<|>>{note['name']}<<|>>{note['body']}<<|>>{note['modification_date']}<<|>>{note['folder']}<<|>>{note['creation_date']}"
        
        mock_applescript.return_value = {
            "success": True,
            "data": mock_response
        }
        
        # Execute
        result = get_note_logic(note['id'])
        
        # Verify
        assert result["success"] is True
        assert result["note"]["id"] == note['id']
        assert result["note"]["name"] == note['name']
        assert result["note"]["body"] == note['body']
        assert result["note"]["folder"] == note['folder']
        assert "preview" in result["note"]
        assert "Retrieved note" in result["message"]
        assert "execution_time_ms" in result["metadata"]

    @patch('localtoolkit.notes.get_note.applescript_execute')
    def test_get_note_not_found(self, mock_applescript):
        """Test note not found scenario."""
        mock_applescript.return_value = {
            "success": True,
            "data": "ERROR:Notes got an error: can't get note id \"invalid-id\""
        }
        
        result = get_note_logic("invalid-id")
        
        assert result["success"] is False
        assert result["note"] is None
        assert "not found" in result["message"]
        assert result["error"] == "Note not found"

    @patch('localtoolkit.notes.get_note.applescript_execute')
    def test_get_note_applescript_error(self, mock_applescript):
        """Test AppleScript execution error."""
        mock_applescript.return_value = {
            "success": False,
            "error": "AppleScript execution failed"
        }
        
        result = get_note_logic("test-id")
        
        assert result["success"] is False
        assert result["note"] is None
        assert "Failed to retrieve note" in result["message"]
        assert "AppleScript execution failed" in result["error"]

    def test_get_note_empty_id(self):
        """Test with empty note ID."""
        result = get_note_logic("")
        
        assert result["success"] is False
        assert result["note"] is None
        assert "Invalid note ID" in result["message"]
        assert "Note ID cannot be empty" in result["error"]

    def test_get_note_whitespace_id(self):
        """Test with whitespace-only note ID."""
        result = get_note_logic("   ")
        
        assert result["success"] is False
        assert result["note"] is None
        assert "Invalid note ID" in result["message"]
        assert "Note ID cannot be empty" in result["error"]

    @patch('localtoolkit.notes.get_note.applescript_execute')
    def test_get_note_general_error(self, mock_applescript):
        """Test general error from AppleScript."""
        mock_applescript.return_value = {
            "success": True,
            "data": "ERROR:Some other error occurred"
        }
        
        result = get_note_logic("test-id")
        
        assert result["success"] is False
        assert result["note"] is None
        assert "Error retrieving note" in result["message"]
        assert "Some other error occurred" in result["error"]

    @patch('localtoolkit.notes.get_note.applescript_execute')
    def test_get_note_malformed_response(self, mock_applescript):
        """Test handling of malformed AppleScript response."""
        mock_applescript.return_value = {
            "success": True,
            "data": "SUCCESS:incomplete-data"
        }
        
        result = get_note_logic("test-id")
        
        assert result["success"] is False
        assert result["note"] is None
        assert "Error processing note retrieval response" in result["message"]
        assert "Unexpected response format" in result["error"]

    @patch('localtoolkit.notes.get_note.applescript_execute')
    def test_get_note_minimal_fields(self, mock_applescript):
        """Test note retrieval with minimal required fields."""
        mock_response = "SUCCESS:test-id<<|>>Test Note<<|>>Test content<<|>>Monday, January 1, 2024 at 12:00:00 PM"
        
        mock_applescript.return_value = {
            "success": True,
            "data": mock_response
        }
        
        result = get_note_logic("test-id")
        
        assert result["success"] is True
        assert result["note"]["id"] == "test-id"
        assert result["note"]["name"] == "Test Note"
        assert result["note"]["body"] == "Test content"
        assert result["note"]["folder"] == ""  # Empty when not provided
        assert result["note"]["creation_date"] == ""  # Empty when not provided

    @patch('localtoolkit.notes.get_note.applescript_execute')
    def test_get_note_id_escaping(self, mock_applescript):
        """Test that note IDs with quotes are properly escaped."""
        note_id_with_quotes = 'test-"id"-with-quotes'
        
        mock_applescript.return_value = {
            "success": True,
            "data": f"SUCCESS:{note_id_with_quotes}<<|>>Test Note<<|>>Test content<<|>>Monday, January 1, 2024 at 12:00:00 PM<<|>>Test Folder<<|>>Sunday, December 31, 2023 at 11:59:59 PM"
        }
        
        result = get_note_logic(note_id_with_quotes)
        
        # Verify that the AppleScript was called with escaped quotes
        mock_applescript.assert_called_once()
        applescript_code = mock_applescript.call_args[0][0]
        assert 'test-\\"id\\"-with-quotes' in applescript_code
        
        assert result["success"] is True
        assert result["note"]["id"] == note_id_with_quotes


class TestGetNoteMCPIntegration:
    """Test cases for MCP integration."""

    def test_register_to_mcp(self):
        """Test that the tool registers correctly with MCP."""
        from unittest.mock import MagicMock
        from localtoolkit.notes.get_note import register_to_mcp
        
        mock_mcp = MagicMock()
        register_to_mcp(mock_mcp)
        
        # Verify that the tool decorator was called
        mock_mcp.tool.assert_called_once()

    @patch('localtoolkit.notes.get_note.get_note_logic')
    def test_mcp_tool_function(self, mock_get_note_logic, mock_get_note_response):
        """Test the MCP tool function calls the logic function correctly."""
        from localtoolkit.notes.get_note import register_to_mcp
        from unittest.mock import MagicMock
        
        mock_get_note_logic.return_value = mock_get_note_response
        
        # Create a mock MCP instance
        mock_mcp = MagicMock()
        
        # Capture the decorated function
        decorated_functions = []
        def capture_tool(*args, **kwargs):
            def decorator(func):
                decorated_functions.append(func)
                return func
            return decorator
        
        mock_mcp.tool = capture_tool
        
        # Register the tool
        register_to_mcp(mock_mcp)
        
        # Get the registered function
        assert len(decorated_functions) == 1
        notes_get_note = decorated_functions[0]
        
        # Test the function
        test_note_id = "x-coredata://12345678-1234-1234-1234-123456789012/Note/p1"
        result = notes_get_note(test_note_id)
        
        # Verify
        mock_get_note_logic.assert_called_once_with(test_note_id)
        assert result == mock_get_note_response