"""Tests for the CLI run module."""

import pytest
from unittest.mock import patch, Mock
import argparse

from localtoolkit.cli.run import run_command


class TestRunCommand:
    """Test cases for run_command function."""
    
    def test_run_command_default_args(self):
        """Test run_command with default arguments."""
        with patch('localtoolkit.cli.run.main') as mock_main:
            run_command([])
            
            mock_main.assert_called_once_with(
                transport="stdio",
                host="127.0.0.1",
                port=8000,
                config_path=None,
                filesystem_config_path=None,
                verbose=False
            )
    
    def test_run_command_http_transport(self):
        """Test run_command with HTTP transport."""
        with patch('localtoolkit.cli.run.main') as mock_main:
            run_command(["--transport", "http"])
            
            mock_main.assert_called_once_with(
                transport="http",
                host="127.0.0.1",
                port=8000,
                config_path=None,
                filesystem_config_path=None,
                verbose=False
            )
    
    def test_run_command_custom_host_port(self):
        """Test run_command with custom host and port."""
        with patch('localtoolkit.cli.run.main') as mock_main:
            run_command(["--transport", "http", "--host", "0.0.0.0", "--port", "9000"])
            
            mock_main.assert_called_once_with(
                transport="http",
                host="0.0.0.0",
                port=9000,
                config_path=None,
                filesystem_config_path=None,
                verbose=False
            )
    
    def test_run_command_with_config(self):
        """Test run_command with config file."""
        with patch('localtoolkit.cli.run.main') as mock_main:
            run_command(["--config", "/path/to/config.json"])
            
            mock_main.assert_called_once_with(
                transport="stdio",
                host="127.0.0.1",
                port=8000,
                config_path="/path/to/config.json",
                filesystem_config_path=None,
                verbose=False
            )
    
    def test_run_command_with_filesystem_config(self):
        """Test run_command with filesystem config file."""
        with patch('localtoolkit.cli.run.main') as mock_main:
            run_command(["--filesystem-config", "/path/to/fs-config.json"])
            
            mock_main.assert_called_once_with(
                transport="stdio",
                host="127.0.0.1",
                port=8000,
                config_path=None,
                filesystem_config_path="/path/to/fs-config.json",
                verbose=False
            )
    
    def test_run_command_verbose(self):
        """Test run_command with verbose flag."""
        with patch('localtoolkit.cli.run.main') as mock_main:
            run_command(["--verbose"])
            
            mock_main.assert_called_once_with(
                transport="stdio",
                host="127.0.0.1",
                port=8000,
                config_path=None,
                filesystem_config_path=None,
                verbose=True
            )
    
    def test_run_command_short_verbose_flag(self):
        """Test run_command with short verbose flag."""
        with patch('localtoolkit.cli.run.main') as mock_main:
            run_command(["-v"])
            
            mock_main.assert_called_once_with(
                transport="stdio",
                host="127.0.0.1",
                port=8000,
                config_path=None,
                filesystem_config_path=None,
                verbose=True
            )
    
    def test_run_command_all_args(self):
        """Test run_command with all arguments."""
        with patch('localtoolkit.cli.run.main') as mock_main:
            run_command([
                "--transport", "http",
                "--host", "192.168.1.100",
                "--port", "8080",
                "--config", "/config.json",
                "--filesystem-config", "/fs-config.json",
                "--verbose"
            ])
            
            mock_main.assert_called_once_with(
                transport="http",
                host="192.168.1.100",
                port=8080,
                config_path="/config.json",
                filesystem_config_path="/fs-config.json",
                verbose=True
            )
    
    def test_run_command_invalid_transport(self):
        """Test run_command with invalid transport."""
        with patch('localtoolkit.cli.run.main'):
            with pytest.raises(SystemExit):
                # argparse will exit on invalid choice
                run_command(["--transport", "invalid"])
    
    def test_run_command_invalid_port(self):
        """Test run_command with invalid port."""
        with patch('localtoolkit.cli.run.main'):
            with pytest.raises(SystemExit):
                # argparse will exit on invalid type
                run_command(["--port", "not-a-number"])
    
    def test_run_command_help(self):
        """Test run_command with help flag."""
        with patch('sys.stdout'), pytest.raises(SystemExit) as exc_info:
            run_command(["--help"])
        
        # Help should exit with code 0
        assert exc_info.value.code == 0
    
    def test_run_command_no_args_uses_sys_argv(self):
        """Test run_command with None args uses sys.argv."""
        with patch('localtoolkit.cli.run.main') as mock_main, \
             patch('sys.argv', ['localtoolkit', '--verbose']):
            
            run_command(None)
            
            mock_main.assert_called_once()
            call_kwargs = mock_main.call_args[1]
            assert call_kwargs["verbose"] is True
    
    def test_run_command_entry_point(self):
        """Test __main__ entry point."""
        with patch('localtoolkit.cli.run.run_command') as mock_run_command:
            # Import and check the module
            import localtoolkit.cli.run
            
            # Simulate running as main
            with patch.object(localtoolkit.cli.run, '__name__', '__main__'):
                # This would normally trigger the if __name__ == "__main__" block
                # In practice, we just verify the function exists
                assert callable(localtoolkit.cli.run.run_command)