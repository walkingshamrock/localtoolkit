"""
Tests for the Notes app utility functions.

This module contains unit tests for Notes utility functions.
"""

import pytest
from localtoolkit.notes.utils.notes_utils import (
    format_note_date, extract_note_preview, validate_note_name,
    escape_applescript_string, parse_notes_list_output
)


class TestNotesUtils:
    """Test cases for Notes utility functions."""

    def test_format_note_date(self):
        """Test date formatting function."""
        # Test normal date string - should convert to ISO format
        date_str = "Monday, January 1, 2024 at 12:00:00 PM"
        result = format_note_date(date_str)
        assert result == "2024-01-01T12:00:00"
        
        # Test date with whitespace - should convert to ISO format
        date_str = "  Tuesday, February 2, 2024 at 1:30:45 PM  "
        result = format_note_date(date_str)
        assert result == "2024-02-02T13:30:45"
        
        # Test invalid format - should return original stripped string
        date_str = "Invalid date format"
        result = format_note_date(date_str)
        assert result == "Invalid date format"
        
        # Test empty string
        result = format_note_date("")
        assert result == ""

    def test_extract_note_preview(self):
        """Test note preview extraction."""
        # Test normal text
        body = "This is a test note with some content that should be previewed."
        result = extract_note_preview(body, max_length=30)
        # The result will be max_length chars + "..." (3 chars)
        assert len(result) <= 33  # 30 + 3 for "..."
        assert result.endswith("...")
        assert result.startswith("This is a test note")
        
        # Test short text
        body = "Short note"
        result = extract_note_preview(body, max_length=100)
        assert result == "Short note"
        assert not result.endswith("...")
        
        # Test text with newlines and extra spaces
        body = "Line 1\n\n  Line 2  \n   Line 3   "
        result = extract_note_preview(body, max_length=100)
        assert result == "Line 1 Line 2 Line 3"
        
        # Test empty body
        result = extract_note_preview("", max_length=100)
        assert result == ""
        
        # Test None body
        result = extract_note_preview(None, max_length=100)
        assert result == ""

    def test_validate_note_name(self):
        """Test note name validation."""
        # Test valid names
        assert validate_note_name("Valid Note Name") is True
        assert validate_note_name("Meeting Notes 2024") is True
        assert validate_note_name("note-with-dashes") is True
        assert validate_note_name("note_with_underscores") is True
        
        # Test invalid names
        assert validate_note_name("") is False
        assert validate_note_name("   ") is False
        assert validate_note_name("name/with/slashes") is False
        assert validate_note_name("name\\with\\backslashes") is False
        assert validate_note_name("name:with:colons") is False
        assert validate_note_name("name*with*asterisks") is False
        assert validate_note_name("name?with?questions") is False
        assert validate_note_name('name"with"quotes') is False
        assert validate_note_name("name<with>brackets") is False
        assert validate_note_name("name|with|pipes") is False
        
        # Test None
        assert validate_note_name(None) is False

    def test_escape_applescript_string(self):
        """Test AppleScript string escaping."""
        # Test normal string
        result = escape_applescript_string("Normal string")
        assert result == "Normal string"
        
        # Test string with quotes
        result = escape_applescript_string('String with "quotes"')
        assert result == 'String with \\"quotes\\"'
        
        # Test string with backslashes
        result = escape_applescript_string("String with \\backslashes")
        assert result == "String with \\\\backslashes"
        
        # Test string with both quotes and backslashes
        result = escape_applescript_string('String with "quotes" and \\backslashes')
        assert result == 'String with \\"quotes\\" and \\\\backslashes'
        
        # Test empty string
        result = escape_applescript_string("")
        assert result == ""
        
        # Test None
        result = escape_applescript_string(None)
        assert result == ""

    def test_parse_notes_list_output(self):
        """Test parsing of AppleScript notes list output."""
        # Test valid output with multiple notes
        output = (
            "note1<<|>>Note 1<<|>>Content 1<<|>>Date 1<<|>>Folder 1<<||>>"
            "note2<<|>>Note 2<<|>>Content 2<<|>>Date 2<<|>>Folder 2<<||>>"
            "note3<<|>>Note 3<<|>>Content 3<<|>>Date 3<<|>>"
        )
        
        result = parse_notes_list_output(output)
        
        assert len(result) == 3
        
        # Check first note
        assert result[0]["id"] == "note1"
        assert result[0]["name"] == "Note 1"
        assert result[0]["body"] == "Content 1"
        assert result[0]["modification_date"] == "Date 1"
        assert result[0]["folder"] == "Folder 1"
        assert "preview" in result[0]
        
        # Check note with missing folder
        assert result[2]["folder"] == ""
        
        # Test empty output
        result = parse_notes_list_output("")
        assert result == []
        
        # Test error output
        result = parse_notes_list_output("ERROR:Something went wrong")
        assert result == []
        
        # Test malformed output
        result = parse_notes_list_output("invalid<<|>>data")
        assert result == []
        
        # Test single note
        output = "note1<<|>>Note 1<<|>>Content 1<<|>>Date 1<<|>>Folder 1"
        result = parse_notes_list_output(output)
        assert len(result) == 1
        assert result[0]["id"] == "note1"

    def test_parse_notes_list_output_edge_cases(self):
        """Test edge cases for notes list output parsing."""
        # Test note with empty fields
        output = "note1<<|>><<|>><<|>>Date 1<<|>>"
        result = parse_notes_list_output(output)
        assert len(result) == 1
        assert result[0]["name"] == ""
        assert result[0]["body"] == ""
        assert result[0]["folder"] == ""
        
        # Test output with insufficient fields
        output = "note1<<|>>Note 1"
        result = parse_notes_list_output(output)
        assert result == []  # Should skip notes with insufficient fields
        
        # Test output with extra delimiters
        output = "note1<<|>>Note 1<<|>>Content 1<<|>>Date 1<<|>>Folder 1<<|>>Extra Field"
        result = parse_notes_list_output(output)
        assert len(result) == 1
        assert result[0]["folder"] == "Folder 1"  # Extra field should be ignored
        
        # Test None input
        result = parse_notes_list_output(None)
        assert result == []
