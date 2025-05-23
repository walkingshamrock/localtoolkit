"""Tests for the start_process module."""

import pytest
from unittest.mock import patch, Mock, MagicMock
import subprocess
import os

from localtoolkit.process.start_process import start_process_logic, register_to_mcp
from tests.utils.assertions import assert_valid_response_format


class TestStartProcessLogic:
    """Test cases for start_process_logic function."""
    
    def test_start_process_background_success(self):
        """Test successful background process start."""
        mock_process = Mock()
        mock_process.pid = 12345
        
        with patch('subprocess.Popen', return_value=mock_process) as mock_popen:
            result = start_process_logic("/usr/bin/python3", args=["-m", "http.server"])
        
        # Verify response format
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["pid"] == 12345
        assert result["command"] == "/usr/bin/python3"
        assert result["full_command"] == "/usr/bin/python3 -m http.server"
        assert result["message"] == "Process started with PID 12345"
        
        # Verify Popen was called correctly
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert call_args[0][0] == ["/usr/bin/python3", "-m", "http.server"]
        assert call_args[1]["start_new_session"] is True
    
    def test_start_process_foreground_success(self):
        """Test successful foreground process with wait."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Hello, World!"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            result = start_process_logic(
                "/bin/echo",
                args=["Hello, World!"],
                wait_for_completion=True
            )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["command"] == "/bin/echo"
        assert result["exit_code"] == 0
        assert result["stdout"] == "Hello, World!"
        assert result["stderr"] == ""
        assert result["message"] == "Process completed with exit code 0"
        
        # Verify subprocess.run was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["/bin/echo", "Hello, World!"]
        assert call_args[1]["capture_output"] is True
    
    def test_start_process_app_bundle(self):
        """Test starting a macOS application bundle."""
        mock_process = Mock()
        mock_process.pid = 54321
        
        with patch('subprocess.Popen', return_value=mock_process) as mock_popen:
            result = start_process_logic("/Applications/Safari.app", args=["https://example.com"])
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["pid"] == 54321
        
        # Should use 'open' command for .app bundles
        call_args = mock_popen.call_args
        assert call_args[0][0] == ["open", "/Applications/Safari.app", "https://example.com"]
    
    def test_start_process_with_environment(self):
        """Test starting process with custom environment variables."""
        mock_process = Mock()
        mock_process.pid = 67890
        
        custom_env = {"CUSTOM_VAR": "custom_value", "PATH": "/custom/path"}
        
        with patch('subprocess.Popen', return_value=mock_process) as mock_popen, \
             patch.dict('os.environ', {"EXISTING": "value"}):
            result = start_process_logic("/usr/bin/env", env=custom_env)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Verify environment was merged
        call_args = mock_popen.call_args
        env_used = call_args[1]["env"]
        assert env_used["CUSTOM_VAR"] == "custom_value"
        assert env_used["PATH"] == "/custom/path"
        assert env_used["EXISTING"] == "value"  # Original env preserved
    
    def test_start_process_with_shell_syntax(self):
        """Test starting process with shell command syntax."""
        mock_process = Mock()
        mock_process.pid = 11111
        
        with patch('subprocess.Popen', return_value=mock_process) as mock_popen:
            result = start_process_logic('ls -la "/tmp/test dir"')
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Should properly parse shell syntax
        call_args = mock_popen.call_args
        assert call_args[0][0] == ["ls", "-la", "/tmp/test dir"]
    
    def test_start_process_foreground_failure(self):
        """Test handling of foreground process failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Command not found"
        
        with patch('subprocess.run', return_value=mock_result):
            result = start_process_logic(
                "/nonexistent/command",
                wait_for_completion=True
            )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["exit_code"] == 1
        assert result["stderr"] == "Command not found"
        assert "Process failed with exit code 1" in result["error"]
    
    def test_start_process_popen_exception(self):
        """Test handling of Popen exceptions."""
        with patch('subprocess.Popen', side_effect=OSError("No such file or directory")):
            result = start_process_logic("/nonexistent/program")
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["command"] == "/nonexistent/program"
        assert "Failed to start process" in result["error"]
        assert result["message"] == "Error while starting process"
    
    def test_start_process_run_exception(self):
        """Test handling of subprocess.run exceptions."""
        with patch('subprocess.run', side_effect=Exception("Unexpected error")):
            result = start_process_logic(
                "/bin/echo",
                args=["test"],
                wait_for_completion=True
            )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert "Failed to start process" in result["error"]
    
    def test_start_process_background_false(self):
        """Test starting process with background=False."""
        mock_process = Mock()
        mock_process.pid = 22222
        
        with patch('subprocess.Popen', return_value=mock_process) as mock_popen:
            result = start_process_logic("/usr/bin/python3", background=False)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Should redirect output when not in background
        call_args = mock_popen.call_args
        assert call_args[1]["stdout"] == subprocess.PIPE
        assert call_args[1]["stderr"] == subprocess.PIPE
        assert call_args[1]["start_new_session"] is False
    
    def test_start_process_empty_args(self):
        """Test starting process with no arguments."""
        mock_process = Mock()
        mock_process.pid = 33333
        
        with patch('subprocess.Popen', return_value=mock_process) as mock_popen:
            result = start_process_logic("/usr/bin/top")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Should handle empty args properly
        call_args = mock_popen.call_args
        assert call_args[0][0] == ["/usr/bin/top"]
    
    def test_start_process_complex_command(self):
        """Test starting process with complex command line."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            result = start_process_logic(
                "/bin/sh",
                args=["-c", "echo 'Hello' | grep 'Hello'"],
                wait_for_completion=True
            )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["full_command"] == "/bin/sh -c echo 'Hello' | grep 'Hello'"


class TestRegisterToMCP:
    """Test cases for MCP registration."""
    
    def test_register_to_mcp(self):
        """Test that the function registers correctly to MCP."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        
        register_to_mcp(mock_mcp)
        
        # Verify that mcp.tool() was called
        mock_mcp.tool.assert_called_once()
    
    def test_registered_function_calls_logic(self):
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
        
        # Register the function
        register_to_mcp(mock_mcp)
        
        # Call the registered function
        assert registered_func is not None
        
        mock_process = Mock()
        mock_process.pid = 44444
        
        with patch('subprocess.Popen', return_value=mock_process):
            result = registered_func(
                command="/usr/bin/python3",
                args=["-m", "http.server", "8080"],
                env={"PORT": "8080"},
                background=True,
                wait_for_completion=False
            )
        
        # Verify it returns the expected result
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["pid"] == 44444
        assert result["command"] == "/usr/bin/python3"