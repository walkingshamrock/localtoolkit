"""Tests for the list_processes module."""

import pytest
from unittest.mock import patch, Mock, MagicMock
import subprocess

from localtoolkit.process.list_processes import list_processes_logic, register_to_mcp
from tests.utils.assertions import assert_valid_response_format


class TestListProcessesLogic:
    """Test cases for list_processes_logic function."""
    
    def test_list_processes_success(self, mock_applescript, mock_process_list_data):
        """Test successful process listing."""
        # Configure mock to return process data
        mock_applescript.return_value = {
            "success": True,
            "data": mock_process_list_data,
            "metadata": {},
            "error": None
        }
        
        # Mock subprocess for ps command
        mock_ps_result = Mock()
        mock_ps_result.returncode = 0
        mock_ps_result.stdout = " 5.2  2.3 user\n"
        
        with patch('subprocess.run', return_value=mock_ps_result):
            result = list_processes_logic()
        
        # Verify response format
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["processes"]) <= 20  # Default limit
        assert result["count"] == len(result["processes"])
        assert "Successfully retrieved" in result["message"]
        assert result["metadata"]["include_background"] is False
        assert result["metadata"]["filter_applied"] is False
        assert result["metadata"]["limit_applied"] == 20
        assert "timestamp" in result["metadata"]
        
        # Verify process data structure
        if result["processes"]:
            process = result["processes"][0]
            assert "pid" in process
            assert "name" in process
            assert "cpu_percent" in process
            assert "memory_percent" in process
            assert "user" in process
    
    def test_list_processes_with_filter(self, mock_applescript, mock_process_list_data):
        """Test process listing with name filter."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_process_list_data,
            "metadata": {},
            "error": None
        }
        
        mock_ps_result = Mock()
        mock_ps_result.returncode = 0
        mock_ps_result.stdout = " 5.2  2.3 user\n"
        
        with patch('subprocess.run', return_value=mock_ps_result):
            result = list_processes_logic(filter_name="Safari")
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["metadata"]["filter_applied"] is True
        assert "matching 'Safari'" in result["message"]
        
        # Should only include Safari process
        assert all("safari" in p["name"].lower() for p in result["processes"])
    
    def test_list_processes_with_limit(self, mock_applescript, mock_process_list_data):
        """Test process listing with custom limit."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_process_list_data,
            "metadata": {},
            "error": None
        }
        
        mock_ps_result = Mock()
        mock_ps_result.returncode = 0
        mock_ps_result.stdout = " 5.2  2.3 user\n"
        
        with patch('subprocess.run', return_value=mock_ps_result):
            result = list_processes_logic(limit=2)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["processes"]) <= 2
        assert result["metadata"]["limit_applied"] == 2
    
    def test_list_processes_ps_command_failure(self, mock_applescript, mock_process_list_data):
        """Test handling of ps command failures."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_process_list_data,
            "metadata": {},
            "error": None
        }
        
        # Mock ps command failure
        mock_ps_result = Mock()
        mock_ps_result.returncode = 1
        mock_ps_result.stdout = ""
        
        with patch('subprocess.run', return_value=mock_ps_result):
            result = list_processes_logic()
        
        assert_valid_response_format(result)
        assert result["success"] is True
        # Processes should still be included but with default values
        if result["processes"]:
            process = result["processes"][0]
            assert process["cpu_percent"] == 0.0
            assert process["memory_percent"] == 0.0
            assert process["user"] == ""
    
    def test_list_processes_malformed_ps_output(self, mock_applescript, mock_process_list_data):
        """Test handling of malformed ps output."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_process_list_data,
            "metadata": {},
            "error": None
        }
        
        # Mock malformed ps output
        mock_ps_result = Mock()
        mock_ps_result.returncode = 0
        mock_ps_result.stdout = "invalid output"
        
        with patch('subprocess.run', return_value=mock_ps_result):
            result = list_processes_logic()
        
        assert_valid_response_format(result)
        assert result["success"] is True
        # Should use default values when parsing fails
        if result["processes"]:
            process = result["processes"][0]
            assert process["cpu_percent"] == 0.0
            assert process["memory_percent"] == 0.0
    
    def test_list_processes_applescript_error(self, mock_applescript):
        """Test handling of AppleScript execution error."""
        mock_applescript.return_value = {
            "success": False,
            "data": None,
            "metadata": {},
            "error": "System Events not accessible"
        }
        
        result = list_processes_logic()
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["error"] == "System Events not accessible"
        assert result["message"] == "Failed to get processes from System Events"
    
    def test_list_processes_empty_result(self, mock_applescript):
        """Test handling of empty process list."""
        mock_applescript.return_value = {
            "success": True,
            "data": [],
            "metadata": {},
            "error": None
        }
        
        result = list_processes_logic()
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["processes"] == []
        assert result["count"] == 0
    
    def test_list_processes_invalid_data_format(self, mock_applescript):
        """Test handling of invalid data format from AppleScript."""
        mock_applescript.return_value = {
            "success": True,
            "data": "not a list",
            "metadata": {},
            "error": None
        }
        
        result = list_processes_logic()
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["processes"] == []
    
    def test_list_processes_parsing_errors(self, mock_applescript):
        """Test handling of parsing errors in process data."""
        # Data with invalid format
        mock_applescript.return_value = {
            "success": True,
            "data": ["Invalid:::format:::extra", "ValidProcess:::1234"],
            "metadata": {},
            "error": None
        }
        
        mock_ps_result = Mock()
        mock_ps_result.returncode = 0
        mock_ps_result.stdout = " 5.2  2.3 user\n"
        
        with patch('subprocess.run', return_value=mock_ps_result):
            result = list_processes_logic()
        
        assert_valid_response_format(result)
        assert result["success"] is True
        # Should only include the valid process
        assert len(result["processes"]) == 1
        assert result["processes"][0]["pid"] == 1234
    
    def test_list_processes_sorting_by_cpu(self, mock_applescript):
        """Test that processes are sorted by CPU usage."""
        mock_applescript.return_value = {
            "success": True,
            "data": ["Process1:::1001", "Process2:::1002", "Process3:::1003"],
            "metadata": {},
            "error": None
        }
        
        # Mock different CPU values for each process
        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "1001" in cmd:
                result = Mock()
                result.returncode = 0
                result.stdout = " %CPU %MEM USER\n 10.0  2.0 user\n"
                return result
            elif "1002" in cmd:
                result = Mock()
                result.returncode = 0
                result.stdout = " %CPU %MEM USER\n  5.0  2.0 user\n"
                return result
            elif "1003" in cmd:
                result = Mock()
                result.returncode = 0
                result.stdout = " %CPU %MEM USER\n 15.0  2.0 user\n"
                return result
            return Mock(returncode=1, stdout="")
        
        with patch('subprocess.run', side_effect=mock_run_side_effect):
            result = list_processes_logic()
        
        assert_valid_response_format(result)
        assert result["success"] is True
        # Should be sorted by CPU usage (highest first)
        assert result["processes"][0]["cpu_percent"] == 15.0
        assert result["processes"][1]["cpu_percent"] == 10.0
        assert result["processes"][2]["cpu_percent"] == 5.0
    
    def test_list_processes_exception_handling(self, mock_applescript):
        """Test handling of unexpected exceptions."""
        mock_applescript.side_effect = Exception("Unexpected error")
        
        result = list_processes_logic()
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert "Failed to list processes" in result["error"]
        assert result["message"] == "Error while retrieving process list"


class TestRegisterToMCP:
    """Test cases for MCP registration."""
    
    def test_register_to_mcp(self):
        """Test that the function registers correctly to MCP."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        
        register_to_mcp(mock_mcp)
        
        # Verify that mcp.tool() was called
        mock_mcp.tool.assert_called_once()
    
    def test_registered_function_calls_logic(self, mock_applescript, mock_process_list_data):
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
            "data": mock_process_list_data,
            "metadata": {},
            "error": None
        }
        
        # Register the function
        register_to_mcp(mock_mcp)
        
        # Call the registered function
        assert registered_func is not None
        
        with patch('subprocess.run', return_value=Mock(returncode=0, stdout=" 5.2  2.3 user\n")):
            result = registered_func(
                filter_name="Chrome",
                include_background=True,
                limit=10
            )
        
        # Verify it returns the expected result
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["metadata"]["limit_applied"] == 10
        assert result["metadata"]["include_background"] is True