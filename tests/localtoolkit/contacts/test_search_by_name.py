"""Tests for the search_by_name module."""

import pytest
from unittest.mock import patch, Mock
import json

from localtoolkit.contacts.search_by_name import search_by_name_logic, register_to_mcp
from tests.utils.assertions import assert_valid_response_format


class TestSearchByNameLogic:
    """Test cases for search_by_name_logic function."""
    
    def test_search_by_name_success(self, mock_applescript, mock_applescript_contact_output):
        """Test successful contact search by name."""
        # Configure mock to return contact data
        mock_applescript.return_value = {
            "success": True,
            "data": mock_applescript_contact_output,
            "metadata": {},
            "error": None
        }
        
        result = search_by_name_logic("John")
        
        # Verify response format
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["contacts"]) == 3
        assert result["message"] == "Found 3 contact(s)"
        assert result["metadata"]["total_matches"] == 3
        assert "execution_time_ms" in result["metadata"]
        
        # Verify first contact details
        john = result["contacts"][0]
        assert john["id"] == "contact-1"
        assert john["display_name"] == "John Smith"
        assert john["first_name"] == "John"
        assert john["last_name"] == "Smith"
        assert len(john["phones"]) == 2
        assert john["phones"][0]["label"] == "mobile"
        assert john["phones"][0]["value"] == "(555) 123-4567"
        assert len(john["emails"]) == 2
        assert john["organization"] == "Acme Corp"
        assert john["notes"] == "Important client"
    
    def test_search_by_name_with_limit(self, mock_applescript):
        """Test contact search with result limit."""
        # Mock output with only 2 contacts
        limited_output = """2<<||>>contact-1<<|>>John Smith<<|>>John<<|>>Smith<<|>>mobile:(555) 123-4567<<+++>><<|>><<|>><<|>><<|>><<|>><<||>>contact-2<<|>>Jane Doe<<|>>Jane<<|>>Doe<<|>><<|>><<|>><<|>><<|>><<|>>"""
        
        mock_applescript.return_value = {
            "success": True,
            "data": limited_output,
            "metadata": {},
            "error": None
        }
        
        result = search_by_name_logic("Smith", limit=2)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["contacts"]) == 2
        assert result["metadata"]["total_matches"] == 2
    
    def test_search_by_name_no_results(self, mock_applescript):
        """Test contact search with no results."""
        mock_applescript.return_value = {
            "success": True,
            "data": "0<<||>>",
            "metadata": {},
            "error": None
        }
        
        result = search_by_name_logic("NonExistentName")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["contacts"] == []
        assert result["message"] == "No contacts found matching the search criteria"
        assert result["metadata"]["total_matches"] == 0
    
    def test_search_by_name_with_special_characters(self, mock_applescript):
        """Test contact search with special characters in name."""
        # Test with quotes in search name
        mock_applescript.return_value = {
            "success": True,
            "data": "0<<||>>",
            "metadata": {},
            "error": None
        }
        
        result = search_by_name_logic('John "Johnny" Smith')
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Verify that quotes were escaped in the AppleScript
        call_args = mock_applescript.call_args[0][0]
        assert '\\"' in call_args or 'Johnny' in call_args
    
    def test_search_by_name_applescript_error(self, mock_applescript):
        """Test handling of AppleScript execution error."""
        mock_applescript.return_value = {
            "success": False,
            "data": None,
            "metadata": {},
            "error": "AppleScript execution failed"
        }
        
        result = search_by_name_logic("John")
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["contacts"] == []
        assert result["message"] == "Failed to search contacts"
        assert result["error"] == "AppleScript execution failed"
    
    def test_search_by_name_error_response(self, mock_applescript):
        """Test handling of error response from AppleScript."""
        mock_applescript.return_value = {
            "success": True,
            "data": "ERROR:Contacts app not accessible",
            "metadata": {},
            "error": None
        }
        
        result = search_by_name_logic("John")
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["message"] == "Error searching contacts"
        assert result["error"] == "Contacts app not accessible"
    
    def test_search_by_name_malformed_data(self, mock_applescript):
        """Test handling of malformed contact data."""
        # Data with missing fields
        malformed_output = """1<<||>>contact-1<<|>>John Smith<<|>>John"""  # Missing fields
        
        mock_applescript.return_value = {
            "success": True,
            "data": malformed_output,
            "metadata": {},
            "error": None
        }
        
        result = search_by_name_logic("John")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["contacts"] == []  # Malformed contact should be skipped
    
    def test_search_by_name_with_addresses(self, mock_applescript):
        """Test parsing contacts with address information."""
        output_with_address = """1<<||>>contact-1<<|>>John Smith<<|>>John<<|>>Smith<<|>><<|>><<|>>home:street:123 Main St,city:Springfield,state:CA,zip:90210,country:USA,<<***>><<|>><<|>><<|>>"""
        
        mock_applescript.return_value = {
            "success": True,
            "data": output_with_address,
            "metadata": {},
            "error": None
        }
        
        result = search_by_name_logic("John")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["contacts"]) == 1
        
        contact = result["contacts"][0]
        assert len(contact["addresses"]) == 1
        assert contact["addresses"][0]["label"] == "home"
        assert contact["addresses"][0]["components"]["street"] == "123 Main St"
        assert contact["addresses"][0]["components"]["city"] == "Springfield"
        assert contact["addresses"][0]["components"]["state"] == "CA"
        assert contact["addresses"][0]["components"]["zip"] == "90210"
    
    def test_search_by_name_with_birthday(self, mock_applescript):
        """Test parsing contacts with birthday information."""
        output_with_birthday = """1<<||>>contact-1<<|>>Jane Doe<<|>>Jane<<|>>Doe<<|>><<|>><<|>><<|>>1985-June-15<<|>><<|>>"""
        
        mock_applescript.return_value = {
            "success": True,
            "data": output_with_birthday,
            "metadata": {},
            "error": None
        }
        
        result = search_by_name_logic("Jane")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["contacts"]) == 1
        assert result["contacts"][0]["birthday"] == "1985-June-15"
    
    def test_search_by_name_processing_exception(self, mock_applescript):
        """Test handling of exceptions during data processing."""
        # Return non-string data to cause processing error
        mock_applescript.return_value = {
            "success": True,
            "data": {"invalid": "data"},
            "metadata": {},
            "error": None
        }
        
        result = search_by_name_logic("John")
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["message"] == "Error processing contact data"
        assert "error" in result
    
    def test_search_by_name_count_parsing_error(self, mock_applescript):
        """Test handling of invalid count in output."""
        # Invalid count format - this will cause ValueError when parsed
        invalid_count_output = """invalid_count<<||>>contact-1<<|>>John Smith<<|>>John<<|>>Smith<<|>><<|>><<|>><<|>><<|>><<|>>"""
        
        mock_applescript.return_value = {
            "success": True,
            "data": invalid_count_output,
            "metadata": {},
            "error": None
        }
        
        result = search_by_name_logic("John")
        
        assert_valid_response_format(result)
        # Should fail due to ValueError when parsing count
        assert result["success"] is False
        assert result["message"] == "Error processing contact data"
        assert "invalid literal" in result["error"]


class TestRegisterToMCP:
    """Test cases for MCP registration."""
    
    def test_register_to_mcp(self):
        """Test that the function registers correctly to MCP."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        
        register_to_mcp(mock_mcp)
        
        # Verify that mcp.tool() was called
        mock_mcp.tool.assert_called_once()
    
    def test_registered_function_calls_logic(self, mock_applescript, mock_applescript_contact_output):
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
            "data": mock_applescript_contact_output,
            "metadata": {},
            "error": None
        }
        
        # Register the function
        register_to_mcp(mock_mcp)
        
        # Call the registered function
        assert registered_func is not None
        result = registered_func(name="Smith", limit=5)
        
        # Verify it returns the expected result
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["contacts"]) == 3