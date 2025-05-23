"""Tests for the search_by_phone module."""

import pytest
from unittest.mock import patch, Mock
import json

from localtoolkit.contacts.search_by_phone import (
    search_by_phone_logic, normalize_phone, register_to_mcp
)
from tests.utils.assertions import assert_valid_response_format


class TestNormalizePhone:
    """Test cases for normalize_phone function."""
    
    def test_normalize_phone_basic(self):
        """Test basic phone number normalization."""
        assert normalize_phone("(555) 123-4567") == "5551234567"
        assert normalize_phone("+1 555 123 4567") == "15551234567"
        assert normalize_phone("555.123.4567") == "5551234567"
        assert normalize_phone("555-123-4567") == "5551234567"
    
    def test_normalize_phone_international(self):
        """Test international phone number normalization."""
        assert normalize_phone("+44 20 7946 0958") == "442079460958"
        assert normalize_phone("+1-800-FLOWERS") == "1800"  # Letters removed
        assert normalize_phone("+33 (0) 1 42 86 82 82") == "330142868282"
    
    def test_normalize_phone_edge_cases(self):
        """Test edge cases for phone normalization."""
        assert normalize_phone("") == ""
        assert normalize_phone("no numbers here") == ""
        assert normalize_phone("123") == "123"
        assert normalize_phone("Call: 555-1234") == "5551234"


class TestSearchByPhoneLogic:
    """Test cases for search_by_phone_logic function."""
    
    def test_search_by_phone_partial_match_success(self, mock_applescript, mock_applescript_phone_output):
        """Test successful partial phone number search."""
        # Configure mock to return contact data
        mock_applescript.return_value = {
            "success": True,
            "data": mock_applescript_phone_output,
            "metadata": {},
            "error": None
        }
        
        result = search_by_phone_logic("555-123")
        
        # Verify response format
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["contacts"]) == 1
        assert result["message"] == "Found 1 contacts with phone numbers partially matching '555-123'"
        assert result["total_found"] == 1
        
        # Verify contact details
        contact = result["contacts"][0]
        assert contact["id"] == "contact-1"
        assert contact["display_name"] == "John Smith"
        assert contact["first_name"] == "John"
        assert contact["last_name"] == "Smith"
        assert len(contact["phones"]) == 2
        assert contact["phones"][0]["label"] == "mobile"
        assert contact["phones"][0]["value"] == "(555) 123-4567"
    
    def test_search_by_phone_exact_match_success(self, mock_applescript, mock_applescript_phone_output):
        """Test successful exact phone number search."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_applescript_phone_output,
            "metadata": {},
            "error": None
        }
        
        result = search_by_phone_logic("(555) 123-4567", exact_match=True)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["message"] == "Found 1 contacts with phone numbers exactly matching '(555) 123-4567'"
        
        # Verify the AppleScript was called with exact match mode
        call_args = mock_applescript.call_args
        assert call_args is not None
        # Check that the code contains 'exact' mode
        if 'code' in call_args.kwargs:
            assert 'exact' in call_args.kwargs['code']
    
    def test_search_by_phone_no_results(self, mock_applescript):
        """Test phone search with no results."""
        mock_applescript.return_value = {
            "success": True,
            "data": "0<<||>>",
            "metadata": {},
            "error": None
        }
        
        result = search_by_phone_logic("999-999-9999")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["contacts"] == []
        assert result["total_found"] == 0
        assert "Found 0 contacts" in result["message"]
    
    def test_search_by_phone_multiple_results(self, mock_applescript):
        """Test phone search with multiple results."""
        multiple_output = """2<<||>>contact-1<<|>>John Smith<<|>>John<<|>>Smith<<|>>mobile:(555) 123-4567<<+++>><<|>>work:john@example.com<<===>>><<||>>contact-2<<|>>Jane Doe<<|>>Jane<<|>>Doe<<|>>home:(555) 123-9999<<+++>><<|>><<"""
        
        mock_applescript.return_value = {
            "success": True,
            "data": multiple_output,
            "metadata": {},
            "error": None
        }
        
        result = search_by_phone_logic("555-123")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["contacts"]) == 2
        assert result["total_found"] == 2
    
    def test_search_by_phone_applescript_error(self, mock_applescript):
        """Test handling of AppleScript execution error."""
        mock_applescript.return_value = {
            "success": False,
            "data": None,
            "metadata": {},
            "error": "AppleScript execution failed"
        }
        
        result = search_by_phone_logic("555-1234")
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["error"] == "AppleScript execution failed"
        assert result["message"] == "Failed to search contacts for phone number: 555-1234"
    
    def test_search_by_phone_error_response(self, mock_applescript):
        """Test handling of error response from AppleScript."""
        mock_applescript.return_value = {
            "success": True,
            "data": "ERROR:Permission denied to access Contacts",
            "metadata": {},
            "error": None
        }
        
        result = search_by_phone_logic("555-1234")
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["error"] == "Permission denied to access Contacts"
        assert result["message"] == "Error searching for contacts with phone: 555-1234"
    
    def test_search_by_phone_malformed_data(self, mock_applescript):
        """Test handling of malformed contact data."""
        # Data with missing fields
        malformed_output = """1<<||>>contact-1<<|>>John Smith"""  # Missing fields
        
        mock_applescript.return_value = {
            "success": True,
            "data": malformed_output,
            "metadata": {},
            "error": None
        }
        
        result = search_by_phone_logic("555-1234")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["contacts"] == []  # Malformed contact should be skipped
    
    def test_search_by_phone_invalid_count(self, mock_applescript):
        """Test handling of invalid count in output."""
        invalid_count_output = """invalid<<||>>contact-1<<|>>John Smith<<|>>John<<|>>Smith<<|>>mobile:555-1234<<+++>><<|>><<"""
        
        mock_applescript.return_value = {
            "success": True,
            "data": invalid_count_output,
            "metadata": {},
            "error": None
        }
        
        result = search_by_phone_logic("555-1234")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["total_found"] == 0  # Should default to 0 on parse error
    
    def test_search_by_phone_empty_phone(self, mock_applescript):
        """Test searching with empty phone number."""
        mock_applescript.return_value = {
            "success": True,
            "data": "0<<||>>",
            "metadata": {},
            "error": None
        }
        
        result = search_by_phone_logic("")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["contacts"] == []
    
    def test_search_by_phone_special_characters(self, mock_applescript):
        """Test phone search with special characters."""
        mock_applescript.return_value = {
            "success": True,
            "data": "0<<||>>",
            "metadata": {},
            "error": None
        }
        
        result = search_by_phone_logic("+1 (555) 123-4567 ext. 123")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Verify normalization happened
        call_args = mock_applescript.call_args
        assert call_args is not None
        # Check that the code contains normalized phone number
        if 'code' in call_args.kwargs:
            assert "15551234567123" in call_args.kwargs['code']  # Normalized version
    
    def test_search_by_phone_processing_exception(self, mock_applescript):
        """Test handling of exceptions during data processing."""
        # Return non-string data to cause processing error
        mock_applescript.return_value = {
            "success": True,
            "data": {"invalid": "data"},
            "metadata": {},
            "error": None
        }
        
        result = search_by_phone_logic("555-1234")
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["message"] == "Error processing contacts data for phone: 555-1234"
        assert "error" in result
    
    def test_search_by_phone_with_emails(self, mock_applescript):
        """Test parsing contacts with email information."""
        output_with_emails = """1<<||>>contact-1<<|>>John Smith<<|>>John<<|>>Smith<<|>>mobile:555-1234<<+++>><<|>>work:john@work.com<<===>>>home:john@home.com<<===>>>"""
        
        mock_applescript.return_value = {
            "success": True,
            "data": output_with_emails,
            "metadata": {},
            "error": None
        }
        
        result = search_by_phone_logic("555-1234")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        contact = result["contacts"][0]
        assert len(contact["emails"]) == 2
        assert contact["emails"][0]["label"] == "work"
        assert contact["emails"][0]["value"] == "john@work.com"


class TestRegisterToMCP:
    """Test cases for MCP registration."""
    
    def test_register_to_mcp(self):
        """Test that the function registers correctly to MCP."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        
        register_to_mcp(mock_mcp)
        
        # Verify that mcp.tool() was called
        mock_mcp.tool.assert_called_once()
    
    def test_registered_function_calls_logic(self, mock_applescript, mock_applescript_phone_output):
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
            "data": mock_applescript_phone_output,
            "metadata": {},
            "error": None
        }
        
        # Register the function
        register_to_mcp(mock_mcp)
        
        # Call the registered function
        assert registered_func is not None
        result = registered_func(phone="(555) 123-4567", exact_match=True)
        
        # Verify it returns the expected result
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["total_found"] == 1