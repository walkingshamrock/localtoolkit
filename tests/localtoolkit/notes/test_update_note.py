"""
Tests for the update_note module.

This module contains tests for updating existing notes in the Notes app.
"""

import pytest
from unittest.mock import patch
from localtoolkit.notes.update_note import update_note_logic


class TestUpdateNoteLogic:
    """Test cases for update_note_logic function."""

    @patch('localtoolkit.notes.update_note.applescript_execute')
    def test_update_note_name_only(self, mock_applescript, mock_notes):
        """Test updating only the note name."""
        # Setup mock response
        note = mock_notes[0].copy()
        note['name'] = "Updated Meeting Notes"
        mock_response = f"SUCCESS:{note['id']}<<|>>{note['name']}<<|>>{note['body']}<<|>>{note['modification_date']}<<|>>{note['folder']}<<|>>{note['creation_date']}"
        
        mock_applescript.return_value = {
            "success": True,
            "data": mock_response
        }
        
        # Execute
        result = update_note_logic(note['id'], name="Updated Meeting Notes")
        
        # Verify
        assert result["success"] is True
        assert result["note"]["name"] == "Updated Meeting Notes"
        assert result["note"]["id"] == note['id']
        assert "Updated name for note" in result["message"]
        assert result["metadata"]["updated_fields"] == ["name"]
        assert "execution_time_ms" in result["metadata"]

    @patch('localtoolkit.notes.update_note.applescript_execute')
    def test_update_note_body_only(self, mock_applescript, mock_notes):
        """Test updating only the note body."""
        # Setup mock response
        note = mock_notes[0].copy()
        note['body'] = "Updated content for the note."
        mock_response = f"SUCCESS:{note['id']}<<|>>{note['name']}<<|>>{note['body']}<<|>>{note['modification_date']}<<|>>{note['folder']}<<|>>{note['creation_date']}"
        
        mock_applescript.return_value = {
            "success": True,
            "data": mock_response
        }
        
        # Execute
        result = update_note_logic(note['id'], body="Updated content for the note.")
        
        # Verify
        assert result["success"] is True
        assert result["note"]["body"] == "Updated content for the note."
        assert result["note"]["id"] == note['id']
        assert "Updated content for note" in result["message"]
        assert result["metadata"]["updated_fields"] == ["content"]

    @patch('localtoolkit.notes.update_note.applescript_execute')
    def test_update_note_both_name_and_body(self, mock_applescript, mock_notes):
        """Test updating both name and body."""
        # Setup mock response
        note = mock_notes[0].copy()
        note['name'] = "Updated Meeting Notes"
        note['body'] = "Updated content for the meeting."
        mock_response = f"SUCCESS:{note['id']}<<|>>{note['name']}<<|>>{note['body']}<<|>>{note['modification_date']}<<|>>{note['folder']}<<|>>{note['creation_date']}"
        
        mock_applescript.return_value = {
            "success": True,
            "data": mock_response
        }
        
        # Execute
        result = update_note_logic(
            note['id'], 
            name="Updated Meeting Notes",
            body="Updated content for the meeting."
        )
        
        # Verify
        assert result["success"] is True
        assert result["note"]["name"] == "Updated Meeting Notes"
        assert result["note"]["body"] == "Updated content for the meeting."
        assert "Updated name and content for note" in result["message"]
        assert result["metadata"]["updated_fields"] == ["name", "content"]

    @patch('localtoolkit.notes.update_note.applescript_execute')
    def test_update_note_not_found(self, mock_applescript):
        """Test updating a note that doesn't exist."""
        mock_applescript.return_value = {
            "success": True,
            "data": "ERROR:Notes got an error: can't get note id \"invalid-id\""
        }
        
        result = update_note_logic("invalid-id", name="New Name")
        
        assert result["success"] is False
        assert result["note"] is None
        assert "not found" in result["message"]
        assert result["error"] == "Note not found"

    @patch('localtoolkit.notes.update_note.applescript_execute')
    def test_update_note_applescript_error(self, mock_applescript):
        """Test AppleScript execution error."""
        mock_applescript.return_value = {
            "success": False,
            "error": "AppleScript execution failed"
        }
        
        result = update_note_logic("test-id", name="New Name")
        
        assert result["success"] is False
        assert result["note"] is None
        assert "Failed to update note" in result["message"]
        assert "AppleScript execution failed" in result["error"]

    def test_update_note_empty_id(self):
        """Test with empty note ID."""
        result = update_note_logic("", name="New Name")
        
        assert result["success"] is False
        assert result["note"] is None
        assert "Invalid note ID" in result["message"]
        assert "Note ID cannot be empty" in result["error"]

    def test_update_note_whitespace_id(self):
        """Test with whitespace-only note ID."""
        result = update_note_logic("   ", name="New Name")
        
        assert result["success"] is False
        assert result["note"] is None
        assert "Invalid note ID" in result["message"]
        assert "Note ID cannot be empty" in result["error"]

    def test_update_note_no_updates(self):
        """Test with no name or body provided."""
        result = update_note_logic("test-id")
        
        assert result["success"] is False
        assert result["note"] is None
        assert "No updates specified" in result["message"]
        assert "At least one of name or body must be provided" in result["error"]

    def test_update_note_empty_name_and_body(self):
        """Test with empty name and body."""
        result = update_note_logic("test-id", name=None, body=None)
        
        assert result["success"] is False
        assert result["note"] is None
        assert "No updates specified" in result["message"]

    @patch('localtoolkit.notes.update_note.validate_note_name')
    def test_update_note_invalid_name(self, mock_validate):
        """Test with invalid note name."""
        mock_validate.return_value = False
        
        result = update_note_logic("test-id", name="Invalid\x00Name")
        
        assert result["success"] is False
        assert result["note"] is None
        assert "Invalid note name" in result["message"]
        assert "Note name contains invalid characters" in result["error"]

    @patch('localtoolkit.notes.update_note.applescript_execute')
    def test_update_note_general_error(self, mock_applescript):
        """Test general error from AppleScript."""
        mock_applescript.return_value = {
            "success": True,
            "data": "ERROR:Some other error occurred"
        }
        
        result = update_note_logic("test-id", name="New Name")
        
        assert result["success"] is False
        assert result["note"] is None
        assert "Error updating note" in result["message"]
        assert "Some other error occurred" in result["error"]

    @patch('localtoolkit.notes.update_note.applescript_execute')
    def test_update_note_malformed_response(self, mock_applescript):
        """Test handling of malformed AppleScript response."""
        mock_applescript.return_value = {
            "success": True,
            "data": "SUCCESS:incomplete-data"
        }
        
        result = update_note_logic("test-id", name="New Name")
        
        assert result["success"] is False
        assert result["note"] is None
        assert "Error processing note update response" in result["message"]
        assert "Unexpected response format" in result["error"]

    @patch('localtoolkit.notes.update_note.applescript_execute')
    @patch('localtoolkit.notes.update_note.validate_note_name')
    def test_update_note_string_escaping(self, mock_validate, mock_applescript, mock_notes):
        """Test that strings with special characters are properly escaped."""
        # Mock validation to pass
        mock_validate.return_value = True
        
        note = mock_notes[0].copy()
        special_name = 'Note with "quotes" and \\backslashes'
        special_body = 'Content with "quotes", \\backslashes, and \nnewlines'
        
        note['name'] = special_name
        note['body'] = special_body
        mock_response = f"SUCCESS:{note['id']}<<|>>{note['name']}<<|>>{note['body']}<<|>>{note['modification_date']}<<|>>{note['folder']}<<|>>{note['creation_date']}"
        
        mock_applescript.return_value = {
            "success": True,
            "data": mock_response
        }
        
        result = update_note_logic(note['id'], name=special_name, body=special_body)
        
        # Verify that the AppleScript was called with escaped strings
        mock_applescript.assert_called_once()
        applescript_code = mock_applescript.call_args[0][0]
        assert '\\"' in applescript_code  # Escaped quotes
        assert '\\\\' in applescript_code  # Escaped backslashes
        
        assert result["success"] is True
        assert result["note"]["name"] == special_name
        assert result["note"]["body"] == special_body

    @patch('localtoolkit.notes.update_note.applescript_execute')
    def test_update_note_minimal_fields(self, mock_applescript):
        """Test note update with minimal required fields in response."""
        mock_response = "SUCCESS:test-id<<|>>Updated Note<<|>>Updated content<<|>>Monday, January 1, 2024 at 12:00:00 PM"
        
        mock_applescript.return_value = {
            "success": True,
            "data": mock_response
        }
        
        result = update_note_logic("test-id", name="Updated Note")
        
        assert result["success"] is True
        assert result["note"]["id"] == "test-id"
        assert result["note"]["name"] == "Updated Note"
        assert result["note"]["body"] == "Updated content"
        assert result["note"]["folder"] == ""  # Empty when not provided
        assert result["note"]["creation_date"] == ""  # Empty when not provided
        assert "preview" in result["note"]


class TestUpdateNoteMCPIntegration:
    """Test cases for MCP integration."""

    def test_register_to_mcp(self):
        """Test that the tool registers correctly with MCP."""
        from unittest.mock import MagicMock
        from localtoolkit.notes.update_note import register_to_mcp
        
        mock_mcp = MagicMock()
        register_to_mcp(mock_mcp)
        
        # Verify that the tool decorator was called
        mock_mcp.tool.assert_called_once()

    @patch('localtoolkit.notes.update_note.update_note_logic')
    def test_mcp_tool_function(self, mock_update_note_logic, mock_update_note_response):
        """Test the MCP tool function calls the logic function correctly."""
        from localtoolkit.notes.update_note import register_to_mcp
        from unittest.mock import MagicMock
        
        mock_update_note_logic.return_value = mock_update_note_response
        
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
        notes_update_note = decorated_functions[0]
        
        # Test the function
        test_note_id = "x-coredata://12345678-1234-1234-1234-123456789012/Note/p1"
        test_name = "Updated Note Name"
        test_body = "Updated note content"
        result = notes_update_note(test_note_id, name=test_name, body=test_body)
        
        # Verify
        mock_update_note_logic.assert_called_once_with(test_note_id, test_name, test_body)
        assert result == mock_update_note_response

    @patch('localtoolkit.notes.update_note.update_note_logic')
    def test_mcp_tool_function_optional_params(self, mock_update_note_logic, mock_update_note_response):
        """Test the MCP tool function with optional parameters."""
        from localtoolkit.notes.update_note import register_to_mcp
        from unittest.mock import MagicMock
        
        mock_update_note_logic.return_value = mock_update_note_response
        
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
        notes_update_note = decorated_functions[0]
        
        # Test the function with only name parameter
        test_note_id = "x-coredata://12345678-1234-1234-1234-123456789012/Note/p1"
        test_name = "Updated Note Name"
        result = notes_update_note(test_note_id, name=test_name)
        
        # Verify
        mock_update_note_logic.assert_called_once_with(test_note_id, test_name, None)
        assert result == mock_update_note_response