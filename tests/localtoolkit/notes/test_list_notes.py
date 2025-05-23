"""
Tests for the Notes app list_notes functionality.

This module contains unit tests for listing notes from the macOS Notes app.
"""

import pytest
from unittest.mock import patch, MagicMock
from localtoolkit.notes.list_notes import list_notes_logic


class TestListNotesLogic:
    """Test cases for the list_notes_logic function."""

    @patch('localtoolkit.notes.list_notes.applescript_execute')
    def test_list_notes_success(self, mock_applescript, mock_notes):
        """Test successful note listing."""
        # Mock AppleScript output with proper delimiters
        output_data = "3<<||>>" + "<<||>>".join([
            f"{note['id']}<<|>>{note['name']}<<|>>{note['body']}<<|>>{note['modification_date']}<<|>>{note['folder']}"
            for note in mock_notes
        ])
        
        mock_applescript.return_value = {
            "success": True,
            "data": output_data,
            "metadata": {"execution_time_ms": 100}
        }
        
        result = list_notes_logic(limit=20)
        
        assert result["success"] is True
        assert len(result["notes"]) == 3
        assert result["message"] == "Found 3 note(s)"
        assert result["metadata"]["total_matches"] == 3
        assert "execution_time_ms" in result["metadata"]
        
        # Check first note structure
        first_note = result["notes"][0]
        assert "id" in first_note
        assert "name" in first_note
        assert "body" in first_note
        assert "preview" in first_note
        assert "modification_date" in first_note
        assert "folder" in first_note

    @patch('localtoolkit.notes.list_notes.applescript_execute')
    def test_list_notes_with_folder_filter(self, mock_applescript, mock_notes):
        """Test note listing with folder filter."""
        # Mock AppleScript output for Work folder
        work_notes = [note for note in mock_notes if note['folder'] == 'Work']
        output_data = f"{len(work_notes)}<<||>>" + "<<||>>".join([
            f"{note['id']}<<|>>{note['name']}<<|>>{note['body']}<<|>>{note['modification_date']}<<|>>{note['folder']}"
            for note in work_notes
        ])
        
        mock_applescript.return_value = {
            "success": True,
            "data": output_data,
            "metadata": {"execution_time_ms": 100}
        }
        
        result = list_notes_logic(limit=20, folder="Work")
        
        assert result["success"] is True
        assert len(result["notes"]) == 1
        assert result["message"] == "Found 1 note(s) in folder 'Work'"
        assert result["metadata"]["folder_filter"] == "Work"

    @patch('localtoolkit.notes.list_notes.applescript_execute')
    def test_list_notes_applescript_failure(self, mock_applescript):
        """Test handling of AppleScript execution failure."""
        mock_applescript.return_value = {
            "success": False,
            "error": "Permission denied to access Notes app"
        }
        
        result = list_notes_logic()
        
        assert result["success"] is False
        assert result["notes"] == []
        assert result["message"] == "Failed to list notes"
        assert "Permission denied" in result["error"]

    @patch('localtoolkit.notes.list_notes.applescript_execute')
    def test_list_notes_applescript_error_response(self, mock_applescript):
        """Test handling of AppleScript error response."""
        mock_applescript.return_value = {
            "success": True,
            "data": "ERROR:Notes app is not accessible"
        }
        
        result = list_notes_logic()
        
        assert result["success"] is False
        assert result["notes"] == []
        assert result["message"] == "Error listing notes"
        assert result["error"] == "Notes app is not accessible"

    @patch('localtoolkit.notes.list_notes.applescript_execute')
    def test_list_notes_empty_result(self, mock_applescript):
        """Test handling of empty notes list."""
        mock_applescript.return_value = {
            "success": True,
            "data": "0<<||>>"
        }
        
        result = list_notes_logic()
        
        assert result["success"] is True
        assert result["notes"] == []
        assert result["message"] == "Found 0 note(s)"
        assert result["metadata"]["total_matches"] == 0

    @patch('localtoolkit.notes.list_notes.applescript_execute')
    def test_list_notes_limit_parameter(self, mock_applescript):
        """Test that limit parameter is applied correctly."""
        # Mock AppleScript output with 5 notes but limit to 2
        mock_applescript.return_value = {
            "success": True,
            "data": "5<<||>>note1<<|>>name1<<|>>body1<<|>>date1<<|>>folder1<<||>>note2<<|>>name2<<|>>body2<<|>>date2<<|>>folder2"
        }
        
        result = list_notes_logic(limit=2)
        
        assert result["success"] is True
        assert len(result["notes"]) == 2
        assert result["metadata"]["total_matches"] == 5
        
        # Verify the script was called with the correct limit
        mock_applescript.assert_called_once()
        call_args = mock_applescript.call_args[0][0]
        assert "set maxResults to 2" in call_args

    @patch('localtoolkit.notes.list_notes.applescript_execute')
    def test_list_notes_malformed_data(self, mock_applescript):
        """Test handling of malformed AppleScript output."""
        mock_applescript.return_value = {
            "success": True,
            "data": "invalid_format_data"
        }
        
        result = list_notes_logic()
        
        assert result["success"] is False
        assert result["notes"] == []
        assert result["message"] == "Error processing notes data"
        assert "error" in result

    @patch('localtoolkit.notes.list_notes.applescript_execute')
    def test_list_notes_parse_exception(self, mock_applescript):
        """Test handling of parsing exceptions."""
        mock_applescript.return_value = {
            "success": True,
            "data": "not_a_number<<||>>invalid_data"
        }
        
        result = list_notes_logic()
        
        assert result["success"] is False
        assert result["notes"] == []
        assert result["message"] == "Error processing notes data"
        assert "error" in result


class TestNotesListNotesIntegration:
    """Integration tests for the complete notes listing workflow."""

    def test_applescript_generation_with_folder(self):
        """Test that AppleScript is generated correctly with folder filtering."""
        with patch('localtoolkit.notes.list_notes.applescript_execute') as mock_applescript:
            mock_applescript.return_value = {
                "success": True,
                "data": "0<<||>>"
            }
            
            list_notes_logic(folder="Work")
            
            # Check that the AppleScript contains the folder filter
            call_args = mock_applescript.call_args[0][0]
            assert 'whose container is folder "Work"' in call_args

    def test_applescript_generation_without_folder(self):
        """Test that AppleScript is generated correctly without folder filtering."""
        with patch('localtoolkit.notes.list_notes.applescript_execute') as mock_applescript:
            mock_applescript.return_value = {
                "success": True,
                "data": "0<<||>>"
            }
            
            list_notes_logic()
            
            # Check that the AppleScript doesn't contain folder filter
            call_args = mock_applescript.call_args[0][0]
            assert 'whose container is folder' not in call_args
            assert 'set allNotes to (every note)' in call_args
