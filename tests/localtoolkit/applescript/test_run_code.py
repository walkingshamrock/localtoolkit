"""
Tests for the AppleScript run_code module.

This module tests the AppleScript execution functionality, including
parameter injection, error handling, and different return formats.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from localtoolkit.applescript.run_code import run_code_logic


class TestRunCodeLogic:
    """Test the run_code_logic function."""
    
    def test_simple_script_execution(self, mock_applescript_success_response):
        """Test execution of a simple AppleScript without parameters."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = mock_applescript_success_response
            
            result = run_code_logic('display dialog "Hello"')
            
            assert result["success"] is True
            assert result["status"] == 1
            assert result["runtime_seconds"] == 0.125
            assert "error" not in result
            mock_execute.assert_called_once()
    
    def test_script_with_string_parameter(self):
        """Test parameter injection with string values."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": "Hello, John!",
                "metadata": {"execution_time_ms": 100}
            }
            
            code = 'display dialog "Hello, $name!"'
            params = {"name": "John"}
            
            result = run_code_logic(code, params)
            
            # Check that the parameter was injected
            expected_code = 'display dialog "Hello, "John"!"'
            mock_execute.assert_called_with(expected_code, params=None, timeout=30)
            assert result["success"] is True
    
    def test_script_with_escaped_quotes(self):
        """Test parameter injection with strings containing quotes."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": "Success",
                "metadata": {"execution_time_ms": 100}
            }
            
            code = 'set myText to $message'
            params = {"message": 'He said "Hello"'}
            
            result = run_code_logic(code, params)
            
            # Check that quotes were properly escaped
            expected_code = 'set myText to "He said \\"Hello\\""'
            mock_execute.assert_called_with(expected_code, params=None, timeout=30)
    
    def test_script_with_numeric_parameters(self):
        """Test parameter injection with numeric values."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": "15",
                "metadata": {"execution_time_ms": 100}
            }
            
            code = 'set result to $num1 + $num2'
            params = {"num1": 10, "num2": 5.5}
            
            result = run_code_logic(code, params)
            
            expected_code = 'set result to 10 + 5.5'
            mock_execute.assert_called_with(expected_code, params=None, timeout=30)
    
    def test_script_with_boolean_parameters(self):
        """Test parameter injection with boolean values."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": "Done",
                "metadata": {"execution_time_ms": 100}
            }
            
            code = 'set isEnabled to $enabled'
            params = {"enabled": True}
            
            result = run_code_logic(code, params)
            
            expected_code = 'set isEnabled to true'
            mock_execute.assert_called_with(expected_code, params=None, timeout=30)
    
    def test_script_with_list_parameters(self):
        """Test parameter injection with list values."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": "Done",
                "metadata": {"execution_time_ms": 100}
            }
            
            code = 'set myList to $items'
            params = {"items": ["apple", "banana", True, 42]}
            
            result = run_code_logic(code, params)
            
            expected_code = 'set myList to {"apple", "banana", true, 42}'
            mock_execute.assert_called_with(expected_code, params=None, timeout=30)
    
    def test_script_with_none_parameter(self):
        """Test parameter injection with None values."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": "Done",
                "metadata": {"execution_time_ms": 100}
            }
            
            code = 'set myValue to $value'
            params = {"value": None}
            
            result = run_code_logic(code, params)
            
            expected_code = 'set myValue to missing value'
            mock_execute.assert_called_with(expected_code, params=None, timeout=30)
    
    def test_script_with_complex_object_parameter(self):
        """Test parameter injection with complex objects (converted to JSON)."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": "Done",
                "metadata": {"execution_time_ms": 100}
            }
            
            code = 'set jsonData to $data'
            params = {"data": {"name": "John", "age": 30, "active": True}}
            
            result = run_code_logic(code, params)
            
            # Complex objects should be JSON-encoded
            expected_json = json.dumps({"name": "John", "age": 30, "active": True})
            escaped_json = expected_json.replace('"', '\\"')
            expected_code = f'set jsonData to "{escaped_json}"'
            mock_execute.assert_called_with(expected_code, params=None, timeout=30)
    
    def test_json_return_format_with_parsed_data(self):
        """Test JSON return format with pre-parsed data."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": {"message": "Hello", "count": 42},
                "metadata": {"execution_time_ms": 100, "parsed": True}
            }
            
            result = run_code_logic('some script', return_format="json")
            
            assert result["success"] is True
            assert result["result"] == {"message": "Hello", "count": 42}
            assert "warning" not in result
    
    def test_json_return_format_with_unparsed_data(self):
        """Test JSON return format with unparsed string data."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": '{"message": "Hello"}',
                "metadata": {"execution_time_ms": 100, "parsed": False}
            }
            
            result = run_code_logic('some script', return_format="json")
            
            assert result["success"] is True
            assert result["result"] == {"message": "Hello"}
            assert "warning" not in result
    
    def test_json_return_format_with_invalid_json(self):
        """Test JSON return format with unparseable data."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": "Not valid JSON",
                "metadata": {"execution_time_ms": 100, "parsed": False}
            }
            
            result = run_code_logic('some script', return_format="json")
            
            assert result["success"] is True
            assert result["result"] == "Not valid JSON"
            assert result["warning"] == "Output could not be parsed as JSON"
    
    def test_text_return_format(self):
        """Test text return format."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": "Hello, World!",
                "metadata": {"execution_time_ms": 100}
            }
            
            result = run_code_logic('some script', return_format="text")
            
            assert result["success"] is True
            assert result["result"] == "Hello, World!"
            assert "raw_output" not in result
    
    def test_raw_return_format(self):
        """Test raw return format."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": "Raw output data",
                "metadata": {"execution_time_ms": 100}
            }
            
            result = run_code_logic('some script', return_format="raw")
            
            assert result["success"] is True
            assert result["raw_output"] == "Raw output data"
            assert "result" not in result
    
    def test_script_execution_error(self, mock_applescript_error_response):
        """Test handling of script execution errors."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = mock_applescript_error_response
            
            result = run_code_logic('invalid script')
            
            assert result["success"] is False
            assert result["status"] == 0
            assert result["error"] == "Syntax error: Expected end of line but found identifier."
            assert "result" not in result
    
    def test_custom_timeout(self):
        """Test script execution with custom timeout."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": "Done",
                "metadata": {"execution_time_ms": 100}
            }
            
            result = run_code_logic('some script', timeout=60)
            
            mock_execute.assert_called_with('some script', params=None, timeout=60)
            assert result["success"] is True
    
    def test_multiple_parameter_replacement(self):
        """Test replacing multiple parameters in a single script."""
        with patch('localtoolkit.applescript.run_code.applescript_execute') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": "Done",
                "metadata": {"execution_time_ms": 100}
            }
            
            code = '''
            tell application $app
                display dialog $message with title $title
            end tell
            '''
            params = {
                "app": "Finder",
                "message": "Hello, World!",
                "title": "Greeting"
            }
            
            result = run_code_logic(code, params)
            
            expected_code = '''
            tell application "Finder"
                display dialog "Hello, World!" with title "Greeting"
            end tell
            '''
            mock_execute.assert_called_with(expected_code, params=None, timeout=30)
            assert result["success"] is True