"""
Tests for reminders date conversion functionality.
"""

import pytest
from localtoolkit.reminders.utils.reminders_utils import convert_iso_to_applescript_date, build_applescript_date_assignment


class TestDateConversion:
    """Test cases for ISO to AppleScript date conversion."""
    
    def test_convert_datetime_format(self):
        """Test conversion of full datetime format."""
        iso_date = "2025-05-23T09:00:00"
        result = convert_iso_to_applescript_date(iso_date)
        expected = "05/23/2025 09:00:00 AM"
        assert result == expected
    
    def test_convert_date_only_format(self):
        """Test conversion of date-only format."""
        iso_date = "2025-05-23"
        result = convert_iso_to_applescript_date(iso_date)
        expected = "05/23/2025 12:00:00 AM"
        assert result == expected
    
    def test_convert_with_timezone_z(self):
        """Test conversion with UTC timezone (Z suffix)."""
        iso_date = "2025-05-23T14:30:00Z"
        result = convert_iso_to_applescript_date(iso_date)
        expected = "05/23/2025 02:30:00 PM"
        assert result == expected
    
    def test_convert_with_timezone_offset(self):
        """Test conversion with timezone offset."""
        iso_date = "2025-05-23T14:30:00+05:00"
        result = convert_iso_to_applescript_date(iso_date)
        # Should strip timezone and use local time
        expected = "05/23/2025 02:30:00 PM"
        assert result == expected
    
    def test_convert_pm_time(self):
        """Test conversion for PM time."""
        iso_date = "2025-12-31T23:59:00"
        result = convert_iso_to_applescript_date(iso_date)
        expected = "12/31/2025 11:59:00 PM"
        assert result == expected
    
    def test_convert_midnight(self):
        """Test conversion for midnight."""
        iso_date = "2025-01-01T00:00:00"
        result = convert_iso_to_applescript_date(iso_date)
        expected = "01/01/2025 12:00:00 AM"
        assert result == expected
    
    def test_convert_noon(self):
        """Test conversion for noon."""
        iso_date = "2025-06-15T12:00:00"
        result = convert_iso_to_applescript_date(iso_date)
        expected = "06/15/2025 12:00:00 PM"
        assert result == expected
    
    def test_invalid_date_format(self):
        """Test error handling for invalid date format."""
        with pytest.raises(ValueError) as exc_info:
            convert_iso_to_applescript_date("not-a-date")
        
        assert "Invalid date format" in str(exc_info.value)
        assert "YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD" in str(exc_info.value)
    
    def test_empty_date_string(self):
        """Test error handling for empty date string."""
        with pytest.raises(ValueError) as exc_info:
            convert_iso_to_applescript_date("")
        
        assert "Date string cannot be empty" in str(exc_info.value)
    
    def test_build_applescript_date_assignment_success(self):
        """Test building AppleScript date assignment for valid date."""
        iso_date = "2025-05-23T09:00:00"
        result = build_applescript_date_assignment("myDate", iso_date)
        
        expected = ['        set myDate to date "05/23/2025 09:00:00 AM"']
        assert result == expected
    
    def test_build_applescript_date_assignment_error(self):
        """Test building AppleScript date assignment for invalid date."""
        result = build_applescript_date_assignment("myDate", "invalid-date")
        
        assert len(result) == 1
        assert result[0].startswith('        error "Invalid date format:')
    
    def test_edge_case_single_digit_components(self):
        """Test dates with single digit day/month."""
        iso_date = "2025-01-05T07:09:01"
        result = convert_iso_to_applescript_date(iso_date)
        expected = "01/05/2025 07:09:01 AM"
        assert result == expected
    
    def test_february_29_leap_year(self):
        """Test leap year date handling."""
        iso_date = "2024-02-29T12:00:00"
        result = convert_iso_to_applescript_date(iso_date)
        expected = "02/29/2024 12:00:00 PM"
        assert result == expected


class TestDateFormatSupport:
    """Test various real-world date format scenarios."""
    
    def test_user_reported_formats(self):
        """Test the specific formats that failed for the user."""
        # Full datetime format that failed
        iso_date1 = "2025-05-23T09:00:00"
        result1 = convert_iso_to_applescript_date(iso_date1)
        assert result1 == "05/23/2025 09:00:00 AM"
        
        # Date-only format that failed
        iso_date2 = "2025-05-23"
        result2 = convert_iso_to_applescript_date(iso_date2)
        assert result2 == "05/23/2025 12:00:00 AM"
    
    def test_common_iso_variants(self):
        """Test common ISO 8601 format variations."""
        test_cases = [
            ("2025-05-23T09:00:00", "05/23/2025 09:00:00 AM"),
            ("2025-05-23T09:00:00Z", "05/23/2025 09:00:00 AM"),
            ("2025-05-23T21:30:45", "05/23/2025 09:30:45 PM"),
            ("2025-12-01", "12/01/2025 12:00:00 AM"),
            ("2025-01-01T00:01:00", "01/01/2025 12:01:00 AM"),
        ]
        
        for iso_input, expected_output in test_cases:
            result = convert_iso_to_applescript_date(iso_input)
            assert result == expected_output, f"Failed for {iso_input}: got {result}, expected {expected_output}"