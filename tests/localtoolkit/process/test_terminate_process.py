"""Tests for the terminate_process module."""

import pytest
from unittest.mock import patch, Mock, call
import os
import signal
import time
import subprocess

from localtoolkit.process.terminate_process import terminate_process_logic, register_to_mcp
from tests.utils.assertions import assert_valid_response_format


class TestTerminateProcessLogic:
    """Test cases for terminate_process_logic function."""
    
    def test_terminate_process_success(self):
        """Test successful process termination."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run:
            
            # First call checks existence, second sends signal
            mock_kill.side_effect = [None, None]
            
            # Mock ps command to get process name
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = "/usr/bin/python3 script.py"
            mock_run.return_value = ps_result
            
            result = terminate_process_logic(1234)
        
        # Verify response format
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["pid"] == 1234
        assert result["signal"] == signal.SIGTERM
        assert result["forced_kill"] is False
        assert "Successfully sent signal 15" in result["message"]
        assert "python3 script.py" in result["message"]
        
        # Verify os.kill was called correctly
        assert mock_kill.call_count == 2
        mock_kill.assert_any_call(1234, 0)  # Check existence
        mock_kill.assert_any_call(1234, signal.SIGTERM)  # Send signal
    
    def test_terminate_process_nonexistent(self):
        """Test terminating non-existent process."""
        with patch('os.kill', side_effect=OSError("No such process")):
            result = terminate_process_logic(99999)
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["pid"] == 99999
        assert "does not exist" in result["error"]
        assert result["message"] == "No such process: 99999"
    
    def test_terminate_process_with_force(self):
        """Test forced termination with SIGKILL."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run, \
             patch('time.sleep'):  # Speed up test
            
            # Track calls to determine behavior
            calls = []
            
            def kill_side_effect(pid, sig):
                calls.append((pid, sig))
                if sig == 0:
                    # Check if process exists
                    if len(calls) == 1:
                        # Initial check - process exists
                        return None
                    elif len(calls) == 3:
                        # Check after SIGTERM - process still exists
                        return None
                    else:
                        # Final check after SIGKILL - process gone
                        raise OSError("No such process")
                elif sig == signal.SIGTERM:
                    # SIGTERM succeeds but process doesn't die
                    return None
                elif sig == signal.SIGKILL:
                    # SIGKILL succeeds
                    return None
                return None
            
            mock_kill.side_effect = kill_side_effect
            
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = "stubborn_process"
            mock_run.return_value = ps_result
            
            result = terminate_process_logic(1234, force=True)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["forced_kill"] is True
        assert "Successfully terminated" in result["message"]
        assert "with SIGKILL after SIGTERM" in result["message"]
    
    def test_terminate_process_force_not_needed(self):
        """Test force option when process terminates with SIGTERM."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run, \
             patch('time.sleep'):
            
            # Process terminates after SIGTERM
            def kill_side_effect(pid, sig):
                if sig == 0 and mock_kill.call_count == 1:
                    # Initial check - process exists
                    return None
                elif sig == signal.SIGTERM:
                    # SIGTERM sent
                    return None
                elif sig == 0:
                    # Check after SIGTERM - process gone
                    raise OSError("No such process")
                return None
            
            mock_kill.side_effect = kill_side_effect
            
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = "nice_process"
            mock_run.return_value = ps_result
            
            result = terminate_process_logic(1234, force=True)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["forced_kill"] is False
        assert "Successfully terminated" in result["message"]
    
    def test_terminate_process_custom_signal(self):
        """Test termination with custom signal."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run:
            
            mock_kill.side_effect = [None, None]
            
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = "test_process"
            mock_run.return_value = ps_result
            
            result = terminate_process_logic(1234, signal_num=signal.SIGHUP)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["signal"] == signal.SIGHUP
        assert f"signal {signal.SIGHUP}" in result["message"]
    
    def test_terminate_process_force_fails(self):
        """Test when even SIGKILL fails to terminate."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run, \
             patch('time.sleep'):
            
            # Process refuses to die even with SIGKILL
            def kill_side_effect(pid, sig):
                if sig == 0:
                    # Process always exists
                    return None
                return None
            
            mock_kill.side_effect = kill_side_effect
            
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = "zombie_process"
            mock_run.return_value = ps_result
            
            result = terminate_process_logic(1234, force=True)
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["forced_kill"] is True
        assert "Failed to terminate" in result["error"]
        assert "even with SIGKILL" in result["error"]
    
    def test_terminate_process_no_name_lookup(self):
        """Test termination when process name lookup fails."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run:
            
            mock_kill.side_effect = [None, None]
            
            # ps command fails
            ps_result = Mock()
            ps_result.returncode = 1
            mock_run.return_value = ps_result
            
            result = terminate_process_logic(1234)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        # Should still work but without process name
        assert "PID 1234" in result["message"]
        assert "(" not in result["message"]  # No process name in parentheses
    
    def test_terminate_process_exception_during_termination(self):
        """Test handling of exceptions during termination."""
        with patch('os.kill') as mock_kill:
            # First check succeeds, then exception on SIGTERM
            mock_kill.side_effect = [None, Exception("Unexpected error")]
            
            result = terminate_process_logic(1234)
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert "Failed to terminate process" in result["error"]
        assert result["message"] == "Error while terminating process"
    
    def test_terminate_process_permission_denied(self):
        """Test handling of permission denied error."""
        with patch('os.kill', side_effect=OSError("Operation not permitted")):
            result = terminate_process_logic(1)  # PID 1 typically requires root
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert "permission denied" in result["error"]
    
    def test_terminate_process_with_subprocess_exception(self):
        """Test handling of subprocess exceptions during name lookup."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run', side_effect=Exception("Subprocess error")):
            
            mock_kill.side_effect = [None, None]
            
            # Should still work despite subprocess error
            result = terminate_process_logic(1234)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["pid"] == 1234


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
        
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run, \
             patch('time.sleep'):  # Speed up test
            
            # Mock: initial check, send SIGKILL, check (still there), send SIGKILL again, final check (gone)
            def kill_side_effect(pid, sig):
                if sig == 0:
                    # First and second checks - process exists
                    if mock_kill.call_count <= 3:
                        return None
                    else:
                        # Final check - process gone
                        raise OSError("No such process")
                else:
                    # SIGKILL always succeeds
                    return None
            
            mock_kill.side_effect = kill_side_effect
            
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = "test_process"
            mock_run.return_value = ps_result
            
            result = registered_func(
                pid=1234,
                signal_num=9,  # SIGKILL
                force=True
            )
        
        # Verify it returns the expected result
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["pid"] == 1234
        assert result["signal"] == 9