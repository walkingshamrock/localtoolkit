"""Tests for the get_process_info module."""

import pytest
from unittest.mock import patch, Mock, call
import os
import subprocess

from localtoolkit.process.get_process_info import get_process_info_logic, register_to_mcp
from tests.utils.assertions import assert_valid_response_format


class TestGetProcessInfoLogic:
    """Test cases for get_process_info_logic function."""
    
    def test_get_process_info_success(self, mock_ps_output):
        """Test successful process info retrieval."""
        # Mock os.kill to indicate process exists
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run:
            
            mock_kill.return_value = None  # Process exists
            
            # Configure subprocess.run mock
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = mock_ps_output
            
            parent_result = Mock()
            parent_result.returncode = 0
            parent_result.stdout = "/sbin/launchd\n"
            
            mock_run.side_effect = [ps_result, parent_result]
            
            result = get_process_info_logic(1234)
        
        # Verify response format
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["message"] == "Successfully retrieved information for process 1234"
        assert "metadata" in result
        assert result["metadata"]["include_memory_details"] is False
        assert result["metadata"]["include_file_handles"] is False
        assert "timestamp" in result["metadata"]
        
        # Verify process info
        process = result["process"]
        assert process["pid"] == 1234
        assert process["ppid"] == 1
        assert process["user"] == "user"
        assert process["cpu_percent"] == 5.2
        assert process["memory_percent"] == 2.3
        assert process["name"] == "Safari"
        assert process["parent_name"] == "launchd"
    
    def test_get_process_info_nonexistent_process(self):
        """Test handling of non-existent process."""
        with patch('os.kill', side_effect=OSError("No such process")):
            result = get_process_info_logic(99999)
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["pid"] == 99999
        assert "does not exist" in result["error"]
        assert result["message"] == "No such process: 99999"
    
    def test_get_process_info_with_memory_details(self, mock_ps_output, mock_vm_stat_output):
        """Test process info retrieval with memory details."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run:
            
            mock_kill.return_value = None
            
            # Configure subprocess.run mock for different commands
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = mock_ps_output
            
            parent_result = Mock()
            parent_result.returncode = 0
            parent_result.stdout = "/sbin/launchd\n"
            
            vm_stat_result = Mock()
            vm_stat_result.returncode = 0
            vm_stat_result.stdout = mock_vm_stat_output
            
            mem_result = Mock()
            mem_result.returncode = 0
            mem_result.stdout = "   RSS      VSZ\n 98304  4194304\n"
            
            mock_run.side_effect = [ps_result, parent_result, vm_stat_result, mem_result]
            
            result = get_process_info_logic(1234, include_memory_details=True)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["metadata"]["include_memory_details"] is True
        
        # Verify memory details
        process = result["process"]
        assert "memory_details" in process
        memory = process["memory_details"]
        assert "system_total_mb" in memory
        assert "system_free_mb" in memory
        assert memory["rss_kb"] == 98304
        assert memory["rss_mb"] == 96
        assert memory["vsz_kb"] == 4194304
        assert memory["vsz_mb"] == 4096
    
    def test_get_process_info_with_file_handles(self, mock_ps_output, mock_lsof_output):
        """Test process info retrieval with file handles."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run:
            
            mock_kill.return_value = None
            
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = mock_ps_output
            
            parent_result = Mock()
            parent_result.returncode = 0
            parent_result.stdout = "/sbin/launchd\n"
            
            lsof_result = Mock()
            lsof_result.returncode = 0
            lsof_result.stdout = mock_lsof_output
            
            mock_run.side_effect = [ps_result, parent_result, lsof_result]
            
            result = get_process_info_logic(1234, include_file_handles=True)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["metadata"]["include_file_handles"] is True
        
        # Verify file handles
        process = result["process"]
        assert "file_handles" in process
        assert "file_handles_count" in process
        assert len(process["file_handles"]) > 0
        
        # Check file handle structure
        handle = process["file_handles"][0]
        assert "fd" in handle
        assert "type" in handle
        assert "name" in handle
    
    def test_get_process_info_ps_command_failure(self):
        """Test handling of ps command failure."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run:
            
            mock_kill.return_value = None
            
            ps_result = Mock()
            ps_result.returncode = 1
            ps_result.stderr = "ps: No such process"
            
            mock_run.return_value = ps_result
            
            result = get_process_info_logic(1234)
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["pid"] == 1234
        assert "Failed to get process info" in result["error"]
    
    def test_get_process_info_empty_ps_output(self):
        """Test handling of empty ps output."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run:
            
            mock_kill.return_value = None
            
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = "HEADER\n"  # Only header, no data
            
            mock_run.return_value = ps_result
            
            result = get_process_info_logic(1234)
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["error"] == "Process not found in ps output"
        assert result["message"] == "No information found for PID 1234"
    
    def test_get_process_info_malformed_ps_output(self):
        """Test handling of malformed ps output."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run:
            
            mock_kill.return_value = None
            
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = "HEADER\nincomplete data"  # Not enough fields
            
            mock_run.return_value = ps_result
            
            result = get_process_info_logic(1234)
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["error"] == "Invalid process information format"
    
    def test_get_process_info_parent_process_error(self, mock_ps_output):
        """Test handling of parent process lookup error."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run:
            
            mock_kill.return_value = None
            
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = mock_ps_output
            
            parent_result = Mock()
            parent_result.returncode = 1  # Parent lookup fails
            
            mock_run.side_effect = [ps_result, parent_result]
            
            result = get_process_info_logic(1234)
        
        assert_valid_response_format(result)
        assert result["success"] is True  # Main operation still succeeds
        # Parent name should not be set or should be "Unknown"
    
    def test_get_process_info_memory_details_error(self, mock_ps_output):
        """Test handling of memory details collection error."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run:
            
            mock_kill.return_value = None
            
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = mock_ps_output
            
            vm_stat_result = Mock()
            vm_stat_result.returncode = 1  # vm_stat fails
            
            mock_run.side_effect = [ps_result, vm_stat_result]
            
            result = get_process_info_logic(1234, include_memory_details=True)
        
        assert_valid_response_format(result)
        assert result["success"] is True  # Main operation still succeeds
        process = result["process"]
        # Memory details might have error or be incomplete
        if "memory_details_error" in process:
            assert isinstance(process["memory_details_error"], str)
    
    def test_get_process_info_file_handles_error(self, mock_ps_output):
        """Test handling of file handles collection error."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run:
            
            mock_kill.return_value = None
            
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = mock_ps_output
            
            lsof_result = Mock()
            lsof_result.returncode = 1  # lsof fails
            
            mock_run.side_effect = [ps_result, lsof_result]
            
            result = get_process_info_logic(1234, include_file_handles=True)
        
        assert_valid_response_format(result)
        assert result["success"] is True  # Main operation still succeeds
        process = result["process"]
        # File handles should not be present or have error
        assert "file_handles" not in process or "file_handles_error" in process
    
    def test_get_process_info_exception_handling(self):
        """Test handling of unexpected exceptions."""
        with patch('os.kill', side_effect=Exception("Unexpected error")):
            result = get_process_info_logic(1234)
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert "Failed to get process info" in result["error"]
        assert result["message"] == "Error while retrieving process information"


class TestRegisterToMCP:
    """Test cases for MCP registration."""
    
    def test_register_to_mcp(self):
        """Test that the function registers correctly to MCP."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        
        register_to_mcp(mock_mcp)
        
        # Verify that mcp.tool() was called
        mock_mcp.tool.assert_called_once()
    
    def test_registered_function_calls_logic(self, mock_ps_output):
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
             patch('subprocess.run') as mock_run:
            
            mock_kill.return_value = None
            
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = mock_ps_output
            
            mock_run.return_value = ps_result
            
            result = registered_func(
                pid=1234,
                include_memory_details=True,
                include_file_handles=True
            )
        
        # Verify it returns the expected result
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["metadata"]["include_memory_details"] is True
        assert result["metadata"]["include_file_handles"] is True