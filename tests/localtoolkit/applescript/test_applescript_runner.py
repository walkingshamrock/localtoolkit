"""
Tests for the AppleScript runner utility module.

This module tests the secure AppleScript execution functionality,
including security validation, parameter handling, and error cases.
"""

import pytest
import json
import subprocess
from unittest.mock import patch, MagicMock

from localtoolkit.applescript.utils.applescript_runner import (
    applescript_execute, 
    check_security
)


class TestCheckSecurity:
    """Test the security checking functionality."""
    
    def test_safe_script(self):
        """Test that safe scripts pass security checks."""
        safe_scripts = [
            'tell application "Finder" to activate',
            'display dialog "Hello, World!"',
            'set myList to {1, 2, 3}',
            'tell application "Safari" to get URL of current tab'
        ]
        
        for script in safe_scripts:
            assert check_security(script) is None
    
    def test_dangerous_shell_commands(self):
        """Test detection of dangerous shell commands."""
        dangerous_scripts = [
            'do shell script "rm -rf /"',
            'do shell script "sudo rm /etc/passwd"',
            'do shell script "mkfs.ext4 /dev/sda1"',
            'do shell script "dd if=/dev/zero of=/dev/sda"'
        ]
        
        for script in dangerous_scripts:
            result = check_security(script)
            assert result is not None
            assert result["success"] is False
            assert "dangerous pattern detected" in result["error"]
    
    def test_dangerous_applescript_patterns(self):
        """Test detection of dangerous AppleScript patterns."""
        dangerous_scripts = [
            'do shell script "ls" with administrator privileges',
            'do shell script "echo test" with administrator privileges',
            'tell application "System Events" to delete file "/important/file"',
            'set x to system attribute "HOME"'
        ]
        
        for script in dangerous_scripts:
            result = check_security(script)
            assert result is not None
            assert result["success"] is False
            assert "dangerous pattern detected" in result["error"]
    
    def test_case_insensitive_detection(self):
        """Test that security checks are case-insensitive."""
        dangerous_scripts = [
            'do shell script "RM -RF /"',
            'do shell script "SUDO rm /etc/passwd"',
            'WITH ADMINISTRATOR PRIVILEGES'
        ]
        
        for script in dangerous_scripts:
            result = check_security(script)
            assert result is not None
            assert result["success"] is False


class TestAppleScriptExecute:
    """Test the applescript_execute function."""
    
    def test_successful_execution(self):
        """Test successful script execution."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Success"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = applescript_execute('display dialog "Test"')
            
            assert result["success"] is True
            assert result["data"] == "Success"
            assert result["message"] == "AppleScript execution successful"
            assert "execution_time_ms" in result["metadata"]
            assert result["metadata"]["parsed"] is False
            
            # Verify subprocess was called correctly
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0]
            assert call_args[0] == ["osascript", "-e", 'display dialog "Test"']
    
    def test_execution_with_error(self):
        """Test handling of execution errors."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Syntax error: Expected end of line"
            mock_run.return_value = mock_result
            
            result = applescript_execute('invalid script')
            
            assert result["success"] is False
            assert result["error"] == "Syntax error: Expected end of line"
            assert result["data"] is None
            assert result["message"] == "AppleScript execution failed"
    
    def test_execution_timeout(self):
        """Test handling of execution timeout."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="osascript", timeout=5)
            
            result = applescript_execute('long running script', timeout=5)
            
            assert result["success"] is False
            assert "timed out after 5 seconds" in result["error"]
            assert result["data"] is None
            assert result["message"] == "AppleScript execution timed out"
            assert result["metadata"]["execution_time_ms"] == 5000
    
    def test_execution_exception(self):
        """Test handling of unexpected exceptions."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Unexpected error")
            
            result = applescript_execute('some script')
            
            assert result["success"] is False
            assert result["error"] == "Unexpected error"
            assert result["data"] is None
            assert result["message"] == "AppleScript execution failed with exception"
    
    def test_json_output_parsing(self):
        """Test automatic JSON parsing of output."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"name": "Test", "value": 42}'
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = applescript_execute('some script')
            
            assert result["success"] is True
            assert result["data"] == {"name": "Test", "value": 42}
            assert result["metadata"]["parsed"] is True
    
    def test_json_array_output_parsing(self):
        """Test automatic JSON array parsing of output."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '[1, 2, 3, 4, 5]'
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = applescript_execute('some script')
            
            assert result["success"] is True
            assert result["data"] == [1, 2, 3, 4, 5]
            assert result["metadata"]["parsed"] is True
    
    def test_invalid_json_keeps_string(self):
        """Test that invalid JSON is kept as string."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{invalid json}'
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = applescript_execute('some script')
            
            assert result["success"] is True
            assert result["data"] == '{invalid json}'
            assert result["metadata"]["parsed"] is False
    
    def test_parameter_injection_string(self):
        """Test parameter injection with string values."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Done"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            params = {"name": "John Doe"}
            result = applescript_execute('display dialog name', params=params)
            
            # Check that parameters were injected at the beginning
            expected_script = 'set name to "John Doe"\n\ndisplay dialog name'
            call_args = mock_run.call_args[0]
            assert call_args[0][2] == expected_script
    
    def test_parameter_injection_with_quotes(self):
        """Test parameter injection with strings containing quotes."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Done"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            params = {"message": 'He said "Hello"'}
            result = applescript_execute('display dialog message', params=params)
            
            # Check that quotes were properly escaped
            expected_script = 'set message to "He said \\"Hello\\""\n\ndisplay dialog message'
            call_args = mock_run.call_args[0]
            assert call_args[0][2] == expected_script
    
    def test_parameter_injection_numeric(self):
        """Test parameter injection with numeric values."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "15"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            params = {"count": 42, "ratio": 3.14}
            result = applescript_execute('set x to count * ratio', params=params)
            
            expected_script = 'set count to 42\nset ratio to 3.14\n\nset x to count * ratio'
            call_args = mock_run.call_args[0]
            assert call_args[0][2] == expected_script
    
    def test_parameter_injection_boolean(self):
        """Test parameter injection with boolean values."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Done"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            params = {"isEnabled": True, "isVisible": False}
            result = applescript_execute('if isEnabled then...', params=params)
            
            expected_script = 'set isEnabled to true\nset isVisible to false\n\nif isEnabled then...'
            call_args = mock_run.call_args[0]
            assert call_args[0][2] == expected_script
    
    def test_parameter_injection_none(self):
        """Test parameter injection with None values."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Done"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            params = {"value": None}
            result = applescript_execute('set x to value', params=params)
            
            expected_script = 'set value to missing value\n\nset x to value'
            call_args = mock_run.call_args[0]
            assert call_args[0][2] == expected_script
    
    def test_security_check_blocks_execution(self):
        """Test that dangerous scripts are blocked before execution."""
        result = applescript_execute('do shell script "rm -rf /"')
        
        assert result["success"] is False
        assert "dangerous pattern detected" in result["error"]
        assert result["execution_time_ms"] == 0
        
        # Ensure subprocess.run was never called
        with patch('subprocess.run') as mock_run:
            mock_run.assert_not_called()
    
    def test_custom_timeout(self):
        """Test execution with custom timeout."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Done"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = applescript_execute('some script', timeout=60)
            
            # Verify timeout was passed to subprocess
            mock_run.assert_called_once()
            assert mock_run.call_args[1]['timeout'] == 60
    
    def test_debug_mode(self, capsys):
        """Test debug mode output."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Done"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = applescript_execute('test script', params={"x": 1}, debug=True)
            
            # Check debug output
            captured = capsys.readouterr()
            assert "Executing AppleScript with timeout: 30s" in captured.out
            assert "Script length: 11 characters" in captured.out
            assert "Parameters: {'x': 1}" in captured.out