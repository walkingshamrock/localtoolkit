"""Tests for the monitor_process module."""

import pytest
from unittest.mock import patch, Mock, MagicMock
import time
import statistics

from localtoolkit.process.monitor_process import monitor_process_logic, register_to_mcp
from tests.utils.assertions import assert_valid_response_format


class TestMonitorProcessLogic:
    """Test cases for monitor_process_logic function."""
    
    def test_monitor_process_success(self, mock_monitor_metrics):
        """Test successful process monitoring."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run, \
             patch('time.time') as mock_time, \
             patch('time.sleep'):  # Speed up test
            
            # Process exists
            mock_kill.return_value = None
            
            # Mock time progression
            # We need: start_time, then for each loop: while check + current_time, 
            # then final while check that exits, then summary calculations
            mock_time.side_effect = [
                1705315200.0,  # start_time
                1705315200.0,  # first while check (< end_time)
                1705315200.0,  # first current_time
                1705315201.0,  # second while check (< end_time)
                1705315201.0,  # second current_time
                1705315202.0,  # third while check (< end_time)
                1705315202.0,  # third current_time
                1705315203.0,  # fourth while check (>= end_time, exit loop)
                1705315203.0,  # monitoring_end
                1705315203.0   # monitoring_duration_seconds
            ]
            
            # Mock ps command results
            ps_results = []
            
            # Initial process info
            info_result = Mock()
            info_result.returncode = 0
            info_result.stdout = "/usr/bin/python3 script.py"
            ps_results.append(info_result)
            
            # Monitoring samples
            for metric in mock_monitor_metrics:
                sample_result = Mock()
                sample_result.returncode = 0
                sample_result.stdout = f"pid %cpu %mem   rss   vsz\n1234 {metric['cpu_percent']} {metric['memory_percent']} {metric['rss_kb']} {metric['vsz_kb']}"
                ps_results.append(sample_result)
            
            mock_run.side_effect = ps_results
            
            result = monitor_process_logic(
                pid=1234,
                interval=1.0,
                duration=3.0,
                include_cpu=True,
                include_memory=True
            )
        
        # Verify response format
        assert_valid_response_format(result)
        if not result["success"]:
            print(f"Result: {result}")
        assert result["success"] is True
        assert result["pid"] == 1234
        assert result["process_name"] == "python3"
        assert len(result["metrics"]) == 3
        assert "Successfully monitored process 1234" in result["message"]
        
        # Verify metadata
        assert result["metadata"]["include_cpu"] is True
        assert result["metadata"]["include_memory"] is True
        assert result["metadata"]["include_io"] is False
        assert result["metadata"]["interval"] == 1.0
        assert result["metadata"]["requested_duration"] == 3.0
        
        # Verify summary statistics
        summary = result["summary"]
        assert summary["pid"] == 1234
        assert summary["process_name"] == "python3"
        assert summary["samples_collected"] == 3
        assert "cpu_percent" in summary
        assert "memory_percent" in summary
        assert "rss_kb" in summary
        
        # Check CPU statistics
        cpu_stats = summary["cpu_percent"]
        assert cpu_stats["min"] == 4.8
        assert cpu_stats["max"] == 5.5
        assert cpu_stats["avg"] == pytest.approx(5.1, 0.1)
        assert cpu_stats["first"] == 5.0
        assert cpu_stats["last"] == 4.8
        assert "change" in cpu_stats
        assert "change_percent" in cpu_stats
    
    def test_monitor_process_nonexistent(self):
        """Test monitoring non-existent process."""
        with patch('os.kill', side_effect=OSError("No such process")):
            result = monitor_process_logic(99999, duration=1.0)
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["pid"] == 99999
        assert "does not exist" in result["error"]
        assert result["message"] == "No such process: 99999"
    
    def test_monitor_process_with_io(self, mock_lsof_output):
        """Test monitoring with I/O statistics."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run, \
             patch('time.time') as mock_time, \
             patch('time.sleep'):
            
            mock_kill.return_value = None
            
            # Mock time progression
            mock_time.side_effect = [
                1705315200.0,  # start_time
                1705315200.0,  # first while check (< end_time)
                1705315200.0,  # first current_time
                1705315201.0,  # second while check (>= end_time, exit)
                1705315201.0,  # monitoring_end
                1705315201.0   # monitoring_duration_seconds
            ]
            
            # Mock subprocess results
            results = []
            
            # Process info
            info_result = Mock()
            info_result.returncode = 0
            info_result.stdout = "test_process"
            results.append(info_result)
            
            # Initial lsof
            lsof_result = Mock()
            lsof_result.returncode = 0
            lsof_result.stdout = mock_lsof_output
            results.append(lsof_result)
            
            # Monitoring sample
            ps_result = Mock()
            ps_result.returncode = 0
            ps_result.stdout = "pid %cpu %mem rss vsz\n1234 5.0 2.0 1000 2000"
            results.append(ps_result)
            
            # Sample lsof
            lsof_result2 = Mock()
            lsof_result2.returncode = 0
            lsof_result2.stdout = mock_lsof_output + "\nSafari  1234 user    3u   REG    1,4      1024 87654321 /tmp/newfile"
            results.append(lsof_result2)
            
            mock_run.side_effect = results
            
            result = monitor_process_logic(
                pid=1234,
                interval=1.0,
                duration=1.0,
                include_io=True
            )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["metadata"]["include_io"] is True
        
        # Check that I/O metrics were collected
        assert len(result["metrics"]) > 0
        metric = result["metrics"][0]
        assert "open_files_count" in metric
    
    def test_monitor_process_terminated_during_monitoring(self):
        """Test handling of process termination during monitoring."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run, \
             patch('time.time') as mock_time, \
             patch('time.sleep'):
            
            mock_kill.return_value = None
            
            mock_time.side_effect = [
                1705315200.0,  # start_time
                1705315200.0,  # first while check (< end_time)
                1705315200.0,  # first current_time
                1705315201.0,  # second while check (< end_time)
                1705315201.0,  # second current_time (process gone)
                1705315201.0,  # monitoring_end
                1705315201.0   # monitoring_duration_seconds
            ]
            
            # Process info succeeds
            info_result = Mock()
            info_result.returncode = 0
            info_result.stdout = "dying_process"
            
            # First sample succeeds
            sample1_result = Mock()
            sample1_result.returncode = 0
            sample1_result.stdout = "pid %cpu\n1234 5.0"
            
            # Second sample fails (process terminated)
            sample2_result = Mock()
            sample2_result.returncode = 1
            sample2_result.stdout = ""
            
            mock_run.side_effect = [info_result, sample1_result, sample2_result]
            
            result = monitor_process_logic(pid=1234, duration=5.0)
        
        assert_valid_response_format(result)
        assert result["success"] is True  # Partial success
        assert len(result["metrics"]) == 2
        assert result["metrics"][1]["error"] == "Process terminated during monitoring"
    
    def test_monitor_process_ps_parsing_error(self):
        """Test handling of ps output parsing errors."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run, \
             patch('time.time') as mock_time, \
             patch('time.sleep'):
            
            mock_kill.return_value = None
            
            mock_time.side_effect = [
                1705315200.0,  # start_time
                1705315200.0,  # first while check (< end_time)
                1705315200.0,  # first current_time
                1705315201.0,  # second while check (>= end_time, exit)
                1705315201.0,  # monitoring_end
                1705315201.0   # monitoring_duration_seconds
            ]
            
            # Process info
            info_result = Mock()
            info_result.returncode = 0
            info_result.stdout = "test_process"
            
            # Malformed ps output
            sample_result = Mock()
            sample_result.returncode = 0
            sample_result.stdout = "HEADER\n"  # No data line
            
            mock_run.side_effect = [info_result, sample_result]
            
            result = monitor_process_logic(pid=1234, duration=1.0)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["metrics"]) == 1
        assert "error" in result["metrics"][0]
        assert "Process not found in ps output" in result["metrics"][0]["error"]
    
    def test_monitor_process_minimal_metrics(self):
        """Test monitoring with minimal metrics (CPU only)."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run, \
             patch('time.time') as mock_time, \
             patch('time.sleep'):
            
            mock_kill.return_value = None
            
            mock_time.side_effect = [
                1705315200.0,  # start_time
                1705315200.0,  # first while check (< end_time)
                1705315200.0,  # first current_time
                1705315201.0,  # second while check (>= end_time, exit)
                1705315201.0,  # monitoring_end
                1705315201.0   # monitoring_duration_seconds
            ]
            
            info_result = Mock()
            info_result.returncode = 0
            info_result.stdout = "test_process"
            
            sample_result = Mock()
            sample_result.returncode = 0
            sample_result.stdout = "pid %cpu\n1234 8.5"
            
            mock_run.side_effect = [info_result, sample_result]
            
            result = monitor_process_logic(
                pid=1234,
                duration=1.0,
                include_cpu=True,
                include_memory=False,
                include_io=False
            )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Should only have CPU metrics
        metric = result["metrics"][0]
        assert "cpu_percent" in metric
        assert "memory_percent" not in metric
        assert "rss_kb" not in metric
    
    def test_monitor_process_io_error_handling(self):
        """Test handling of I/O monitoring errors."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run, \
             patch('time.time') as mock_time, \
             patch('time.sleep'):
            
            mock_kill.return_value = None
            
            mock_time.side_effect = [
                1705315200.0,  # start_time
                1705315200.0,  # first while check (< end_time)
                1705315200.0,  # first current_time
                1705315201.0,  # second while check (>= end_time, exit)
                1705315201.0,  # monitoring_end
                1705315201.0   # monitoring_duration_seconds
            ]
            
            info_result = Mock()
            info_result.returncode = 0
            info_result.stdout = "test_process"
            
            # lsof fails
            lsof_result = Mock()
            lsof_result.returncode = 1
            
            sample_result = Mock()
            sample_result.returncode = 0
            sample_result.stdout = "pid\n1234"
            
            mock_run.side_effect = [info_result, lsof_result, sample_result]
            
            result = monitor_process_logic(pid=1234, duration=1.0, include_io=True)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        # I/O monitoring was requested but failed
        assert result["metadata"]["include_io"] is True
        # Check that no IO metrics were collected
        for metric in result["metrics"]:
            assert "open_files_count" not in metric
    
    def test_monitor_process_exception_handling(self):
        """Test handling of unexpected exceptions."""
        with patch('os.kill', side_effect=Exception("Unexpected error")):
            result = monitor_process_logic(1234, duration=1.0)
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert "Failed to monitor process" in result["error"]
        assert result["message"] == "Error while monitoring process"
    
    def test_monitor_process_single_sample(self):
        """Test monitoring with single sample (edge case for statistics)."""
        with patch('os.kill') as mock_kill, \
             patch('subprocess.run') as mock_run, \
             patch('time.time') as mock_time, \
             patch('time.sleep'):
            
            mock_kill.return_value = None
            
            # Very short duration - only one sample
            mock_time.side_effect = [
                1705315200.0,  # start_time
                1705315200.0,  # first while check (< end_time)
                1705315200.0,  # first current_time
                1705315200.1,  # second while check (>= end_time, exit)
                1705315200.1,  # monitoring_end
                1705315200.1   # monitoring_duration_seconds
            ]
            
            info_result = Mock()
            info_result.returncode = 0
            info_result.stdout = "test_process"
            
            sample_result = Mock()
            sample_result.returncode = 0
            sample_result.stdout = "pid %cpu\n1234 5.0"
            
            mock_run.side_effect = [info_result, sample_result]
            
            result = monitor_process_logic(pid=1234, interval=1.0, duration=0.1)
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert len(result["metrics"]) == 1
        
        # Statistics should handle single sample gracefully
        cpu_stats = result["summary"]["cpu_percent"]
        assert cpu_stats["min"] == 5.0
        assert cpu_stats["max"] == 5.0
        assert cpu_stats["avg"] == 5.0
        assert cpu_stats["median"] == 5.0
        assert "std_dev" not in cpu_stats  # Not calculated for single sample


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
             patch('time.time') as mock_time, \
             patch('time.sleep'):
            
            mock_kill.return_value = None
            
            mock_time.side_effect = [
                1705315200.0,  # start_time
                1705315200.0,  # first while check (< end_time)
                1705315200.0,  # first current_time
                1705315201.0,  # second while check (>= end_time, exit)
                1705315201.0,  # monitoring_end
                1705315201.0   # monitoring_duration_seconds
            ]
            
            info_result = Mock()
            info_result.returncode = 0
            info_result.stdout = "test_process"
            
            sample_result = Mock()
            sample_result.returncode = 0
            sample_result.stdout = "pid %cpu %mem rss vsz\n1234 5.0 2.0 1000 2000"
            
            # Initial lsof for IO monitoring
            lsof_result = Mock()
            lsof_result.returncode = 0
            lsof_result.stdout = "COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME\npython 1234 user 1u REG 1,4 12345 /tmp/test.txt\n"
            
            # Sample lsof
            lsof_result2 = Mock()
            lsof_result2.returncode = 0
            lsof_result2.stdout = "COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME\npython 1234 user 1u REG 1,4 12345 /tmp/test.txt\npython 1234 user 2u REG 1,4 67890 /tmp/test2.txt\n"
            
            mock_run.side_effect = [info_result, lsof_result, sample_result, lsof_result2]
            
            result = registered_func(
                pid=1234,
                interval=0.5,
                duration=1.0,
                include_cpu=True,
                include_memory=True,
                include_io=True
            )
        
        # Verify it returns the expected result
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["metadata"]["interval"] == 0.5
        assert result["metadata"]["requested_duration"] == 1.0