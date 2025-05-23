"""
Tests for the Notes app create_note functionality.

This module contains unit tests for creating notes in the macOS Notes app.
"""

import pytest
from unittest.mock import patch, MagicMock
from localtoolkit.notes.create_note import create_note_logic


class TestCreateNoteLogic:
    """Test cases for the create_note_logic function."""

    @patch('localtoolkit.notes.create_note.applescript_execute')
    def test_create_note_success(self, mock_applescript):
        """Test successful note creation."""
        mock_applescript.return_value = {
            "success": True,
            "data": "SUCCESS:note-id-123<<|>>Test Note<<|>>This is test content<<|>>Monday, January 1, 2024 at 12:00:00 PM<<|>>",
            "metadata": {"execution_time_ms": 200}
        }
        
        result = create_note_logic("Test Note", "This is test content")
        
        assert result["success"] is True
        assert result["note"]["id"] == "note-id-123"
        assert result["note"]["name"] == "Test Note"
        assert result["note"]["body"] == "This is test content"
        assert result["message"] == "Note 'Test Note' created successfully"
        assert "execution_time_ms" in result["metadata"]

    @patch('localtoolkit.notes.create_note.applescript_execute')
    def test_create_note_with_folder(self, mock_applescript):
        """Test note creation with folder specification."""
        mock_applescript.return_value = {
            "success": True,
            "data": "SUCCESS:note-id-456<<|>>Work Note<<|>>Work content<<|>>Monday, January 1, 2024 at 12:00:00 PM<<|>>Work",
            "metadata": {"execution_time_ms": 250}
        }
        
        result = create_note_logic("Work Note", "Work content", folder="Work")
        
        assert result["success"] is True
        assert result["note"]["folder"] == "Work"
        assert result["message"] == "Note 'Work Note' created successfully in folder 'Work'"
        assert result["metadata"]["folder"] == "Work"

    def test_create_note_invalid_name(self):
        """Test error handling for invalid note names."""
        # Test empty name
        result = create_note_logic("", "Some content")
        assert result["success"] is False
        assert result["message"] == "Invalid note name"
        assert result["error"] == "Note name contains invalid characters or is empty"

        # Test name with invalid characters
        result = create_note_logic("Note/with/slashes", "Some content")
        assert result["success"] is False
        assert result["message"] == "Invalid note name"

    @patch('localtoolkit.notes.create_note.applescript_execute')
    def test_create_note_applescript_failure(self, mock_applescript):
        """Test handling of AppleScript execution failure."""
        mock_applescript.return_value = {
            "success": False,
            "error": "Permission denied to access Notes app"
        }
        
        result = create_note_logic("Test Note", "Test content")
        
        assert result["success"] is False
        assert result["note"] is None
        assert result["message"] == "Failed to create note"
        assert "Permission denied" in result["error"]

    @patch('localtoolkit.notes.create_note.applescript_execute')
    def test_create_note_applescript_error_response(self, mock_applescript):
        """Test handling of AppleScript error response."""
        mock_applescript.return_value = {
            "success": True,
            "data": "ERROR:Unable to create note in specified folder"
        }
        
        result = create_note_logic("Test Note", "Test content", folder="NonExistent")
        
        assert result["success"] is False
        assert result["note"] is None
        assert result["message"] == "Error creating note"
        assert result["error"] == "Unable to create note in specified folder"

    @patch('localtoolkit.notes.create_note.applescript_execute')
    def test_create_note_malformed_response(self, mock_applescript):
        """Test handling of malformed AppleScript response."""
        mock_applescript.return_value = {
            "success": True,
            "data": "INVALID:malformed_response_data"
        }
        
        result = create_note_logic("Test Note", "Test content")
        
        assert result["success"] is False
        assert result["note"] is None
        assert result["message"] == "Error processing note creation response"
        assert result["error"] == "Unexpected response format"

    @patch('localtoolkit.notes.create_note.applescript_execute')
    def test_create_note_insufficient_response_fields(self, mock_applescript):
        """Test handling of response with insufficient fields."""
        mock_applescript.return_value = {
            "success": True,
            "data": "SUCCESS:note-id<<|>>incomplete-data"
        }
        
        result = create_note_logic("Test Note", "Test content")
        
        assert result["success"] is False
        assert result["note"] is None
        assert result["message"] == "Error processing note creation response"

    @patch('localtoolkit.notes.create_note.applescript_execute')
    def test_create_note_special_characters(self, mock_applescript):
        """Test note creation with special characters in name and body."""
        # Test with special characters that are allowed, and actual newline in body
        mock_applescript.return_value = {
            "success": True,
            "data": "SUCCESS:note-id-789<<|>>Note with 'apostrophes' & symbols!<<|>>Content with\nnewlines<<|>>Monday, January 1, 2024 at 12:00:00 PM<<|>>",
            "metadata": {"execution_time_ms": 180}
        }
        
        result = create_note_logic("Note with 'apostrophes' & symbols!", 'Content with\nnewlines')
        
        assert result["success"] is True
        assert result["note"]["name"] == "Note with 'apostrophes' & symbols!"
        assert result["note"]["body"] == 'Content with\nnewlines'

    @patch('localtoolkit.notes.create_note.applescript_execute')
    def test_create_note_exception_handling(self, mock_applescript):
        """Test handling of unexpected exceptions during processing."""
        mock_applescript.return_value = {
            "success": True,
            "data": None  # This will cause an exception when trying to process
        }
        
        result = create_note_logic("Test Note", "Test content")
        
        assert result["success"] is False
        assert result["note"] is None
        assert result["message"] == "Error processing note creation response"
        assert "error" in result


class TestCreateNoteIntegration:
    """Integration tests for the complete note creation workflow."""

    def test_applescript_generation_no_folder(self):
        """Test that AppleScript is generated correctly without folder."""
        with patch('localtoolkit.notes.create_note.applescript_execute') as mock_applescript:
            mock_applescript.return_value = {
                "success": True,
                "data": "SUCCESS:note-id<<|>>Test<<|>>Content<<|>>Date<<|>>"
            }
            
            create_note_logic("Test", "Content")
            
            # Check that the AppleScript doesn't include folder creation
            call_args = mock_applescript.call_args[0][0]
            assert "targetFolder" not in call_args
            assert 'make new note with properties' in call_args

    def test_applescript_generation_with_folder(self):
        """Test that AppleScript is generated correctly with folder."""
        with patch('localtoolkit.notes.create_note.applescript_execute') as mock_applescript:
            mock_applescript.return_value = {
                "success": True,
                "data": "SUCCESS:note-id<<|>>Test<<|>>Content<<|>>Date<<|>>Work"
            }
            
            create_note_logic("Test", "Content", folder="Work")
            
            # Check that the AppleScript includes folder creation
            call_args = mock_applescript.call_args[0][0]
            assert "targetFolder" in call_args
            assert 'folder "Work"' in call_args
            assert 'make new note in targetFolder' in call_args

    def test_string_escaping(self):
        """Test that strings are properly escaped for AppleScript."""
        with patch('localtoolkit.notes.create_note.applescript_execute') as mock_applescript:
            mock_applescript.return_value = {
                "success": True,
                "data": "SUCCESS:note-id<<|>>Test Note<<|>>Body with quotes and backslash<<|>>Date<<|>>"
            }
            
            # Create note with special characters in body that need escaping
            # Note: name can't have quotes or backslashes as they're invalid
            create_note_logic('Test Note', 'Body with "quotes" and \\ backslash')
            
            # Check that the AppleScript properly escapes special characters in body
            call_args = mock_applescript.call_args[0][0]
            assert '\\\\' in call_args  # Escaped backslashes should be present
            assert '\\"' in call_args  # Escaped quotes in body should be present
