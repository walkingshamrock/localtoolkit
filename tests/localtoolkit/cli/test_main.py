"""Tests for the CLI main module."""

import pytest
from unittest.mock import patch, Mock, MagicMock, mock_open
import json
import os
import sys
import logging

from localtoolkit.cli.main import (
    setup_logger, load_filesystem_settings, main
)


class TestSetupLogger:
    """Test cases for setup_logger function."""
    
    def test_setup_logger(self):
        """Test logger setup."""
        with patch('logging.basicConfig') as mock_config:
            logger = setup_logger()
            
            assert logger.name == "localtoolkit"
            mock_config.assert_called_once()
            call_kwargs = mock_config.call_args[1]
            assert call_kwargs["level"] == logging.INFO
            assert "%(asctime)s" in call_kwargs["format"]


class TestLoadFilesystemSettings:
    """Test cases for load_filesystem_settings function."""
    
    def test_load_from_filesystem_config_path(self, temp_filesystem_config_file, mock_filesystem_config):
        """Test loading from filesystem_config_path parameter."""
        settings, logger = load_filesystem_settings(
            filesystem_config_path=temp_filesystem_config_file
        )
        
        assert settings == mock_filesystem_config
        assert settings["allowed_dirs"][0]["path"] == "/tmp/test"
    
    def test_load_from_config_path(self, temp_config_file, mock_filesystem_config):
        """Test loading from config_path parameter."""
        settings, logger = load_filesystem_settings(
            config_path=temp_config_file
        )
        
        assert settings == mock_filesystem_config
    
    def test_load_from_environment_variable(self, mock_filesystem_config):
        """Test loading from LOCALTOOLKIT_FILESYSTEM_CONFIG env var."""
        with patch.dict(os.environ, {"LOCALTOOLKIT_FILESYSTEM_CONFIG": json.dumps(mock_filesystem_config)}):
            settings, logger = load_filesystem_settings()
        
        assert settings == mock_filesystem_config
    
    def test_load_from_general_config_env(self, temp_config_file, mock_filesystem_config):
        """Test loading from LOCALTOOLKIT_CONFIG env var."""
        with patch.dict(os.environ, {"LOCALTOOLKIT_CONFIG": temp_config_file}):
            settings, logger = load_filesystem_settings()
        
        assert settings == mock_filesystem_config
    
    def test_load_from_command_line_args(self, temp_filesystem_config_file, mock_filesystem_config):
        """Test loading from command line arguments."""
        with patch.object(sys, 'argv', ['localtoolkit', f'--filesystem-config={temp_filesystem_config_file}']):
            settings, logger = load_filesystem_settings()
        
        assert settings == mock_filesystem_config
    
    def test_load_from_claude_desktop_config(self, mock_claude_desktop_config, mock_filesystem_config):
        """Test loading from Claude Desktop config file."""
        # Mock the file existence and reading
        claude_config_path = os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
        
        with patch('os.path.exists') as mock_exists, \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_claude_desktop_config))):
            
            # Only the Claude config path exists
            def exists_side_effect(path):
                return path == claude_config_path
            
            mock_exists.side_effect = exists_side_effect
            
            settings, logger = load_filesystem_settings()
        
        assert settings == mock_filesystem_config
    
    def test_default_fallback_settings(self):
        """Test default settings when no config is found."""
        with patch('os.path.exists', return_value=False):
            settings, logger = load_filesystem_settings()
        
        assert "allowed_dirs" in settings
        assert len(settings["allowed_dirs"]) > 0
        assert settings["allowed_dirs"][0]["permissions"] == ["read", "write", "list"]
        # Should use project directory as default
        assert "localtoolkit" in settings["allowed_dirs"][0]["path"]
    
    def test_error_handling_in_config_loading(self):
        """Test error handling when config loading fails."""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=IOError("File read error")), \
             patch('logging.getLogger') as mock_get_logger:
            
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            settings, logger = load_filesystem_settings(config_path="/fake/path")
        
        # Should fall back to defaults
        assert "allowed_dirs" in settings
        # Check that warning was logged
        mock_logger.warning.assert_called()
    
    def test_invalid_json_in_env_var(self):
        """Test handling of invalid JSON in environment variable."""
        with patch.dict(os.environ, {"LOCALTOOLKIT_FILESYSTEM_CONFIG": "invalid json"}):
            settings, logger = load_filesystem_settings()
        
        # Should fall back to defaults
        assert "allowed_dirs" in settings
    
    def test_priority_order(self, temp_filesystem_config_file, temp_config_file):
        """Test that filesystem_config_path has priority over config_path."""
        # Create different configs
        with open(temp_filesystem_config_file, 'w') as f:
            json.dump({"allowed_dirs": [{"path": "/priority", "permissions": ["read"]}]}, f)
        
        settings, logger = load_filesystem_settings(
            config_path=temp_config_file,
            filesystem_config_path=temp_filesystem_config_file
        )
        
        # Should use filesystem_config_path
        assert settings["allowed_dirs"][0]["path"] == "/priority"
    
    def test_security_log_dir_creation(self):
        """Test that security log directory is created if not specified."""
        with patch('os.path.exists', return_value=False), \
             patch('os.makedirs') as mock_makedirs:
            
            settings, logger = load_filesystem_settings()
        
        assert "security_log_dir" in settings
        mock_makedirs.assert_called()


class TestMain:
    """Test cases for main function."""
    
    def test_main_stdio_transport(self, mock_fastmcp):
        """Test main function with stdio transport."""
        with patch('localtoolkit.cli.main.FastMCP', return_value=mock_fastmcp), \
             patch('localtoolkit.cli.main.load_filesystem_settings') as mock_load, \
             patch('localtoolkit.cli.main.register_messages') as mock_register_messages, \
             patch('localtoolkit.cli.main.register_contacts') as mock_register_contacts, \
             patch('localtoolkit.cli.main.register_mail') as mock_register_mail, \
             patch('localtoolkit.cli.main.register_applescript') as mock_register_applescript, \
             patch('localtoolkit.cli.main.register_process') as mock_register_process, \
             patch('localtoolkit.cli.main.register_reminders') as mock_register_reminders, \
             patch('localtoolkit.cli.main.register_filesystem') as mock_register_filesystem:
            
            mock_load.return_value = ({"allowed_dirs": []}, Mock())
            
            main(transport="stdio")
            
            # Verify FastMCP was created
            assert mock_fastmcp.run.called
            mock_fastmcp.run.assert_called_with()
            
            # Verify all modules were registered
            mock_register_messages.assert_called_once_with(mock_fastmcp)
            mock_register_contacts.assert_called_once_with(mock_fastmcp)
            mock_register_mail.assert_called_once_with(mock_fastmcp)
            mock_register_applescript.assert_called_once_with(mock_fastmcp)
            mock_register_process.assert_called_once_with(mock_fastmcp)
            mock_register_reminders.assert_called_once_with(mock_fastmcp)
            mock_register_filesystem.assert_called_once()
    
    def test_main_http_transport(self, mock_fastmcp):
        """Test main function with HTTP transport."""
        with patch('localtoolkit.cli.main.FastMCP', return_value=mock_fastmcp), \
             patch('localtoolkit.cli.main.load_filesystem_settings') as mock_load, \
             patch('localtoolkit.cli.main.register_messages'), \
             patch('localtoolkit.cli.main.register_contacts'), \
             patch('localtoolkit.cli.main.register_mail'), \
             patch('localtoolkit.cli.main.register_applescript'), \
             patch('localtoolkit.cli.main.register_process'), \
             patch('localtoolkit.cli.main.register_reminders'), \
             patch('localtoolkit.cli.main.register_filesystem'):
            
            mock_load.return_value = ({"allowed_dirs": []}, Mock())
            
            main(transport="http", host="0.0.0.0", port=9000)
            
            # Verify HTTP settings
            assert mock_fastmcp.settings.host == "0.0.0.0"
            assert mock_fastmcp.settings.port == 9000
            mock_fastmcp.run.assert_called_with(transport="streamable-http")
    
    def test_main_with_config_paths(self, mock_fastmcp, temp_config_file, temp_filesystem_config_file):
        """Test main function with config paths."""
        with patch('localtoolkit.cli.main.FastMCP', return_value=mock_fastmcp), \
             patch('localtoolkit.cli.main.register_messages'), \
             patch('localtoolkit.cli.main.register_contacts'), \
             patch('localtoolkit.cli.main.register_mail'), \
             patch('localtoolkit.cli.main.register_applescript'), \
             patch('localtoolkit.cli.main.register_process'), \
             patch('localtoolkit.cli.main.register_reminders'), \
             patch('localtoolkit.cli.main.register_filesystem'):
            
            main(
                config_path=temp_config_file,
                filesystem_config_path=temp_filesystem_config_file
            )
            
            # Should run without errors
            mock_fastmcp.run.assert_called_once()
    
    def test_main_verbose_logging(self, mock_fastmcp):
        """Test main function with verbose logging."""
        with patch('localtoolkit.cli.main.FastMCP', return_value=mock_fastmcp), \
             patch('localtoolkit.cli.main.load_filesystem_settings') as mock_load, \
             patch('logging.basicConfig') as mock_logging_config, \
             patch('localtoolkit.cli.main.register_messages'), \
             patch('localtoolkit.cli.main.register_contacts'), \
             patch('localtoolkit.cli.main.register_mail'), \
             patch('localtoolkit.cli.main.register_applescript'), \
             patch('localtoolkit.cli.main.register_process'), \
             patch('localtoolkit.cli.main.register_reminders'), \
             patch('localtoolkit.cli.main.register_filesystem'):
            
            mock_load.return_value = ({"allowed_dirs": []}, Mock())
            
            main(verbose=True)
            
            # Should set DEBUG level
            mock_logging_config.assert_called_with(level=logging.DEBUG)
    
    def test_main_entry_point(self, mock_fastmcp):
        """Test __main__ entry point."""
        with patch('localtoolkit.cli.main.FastMCP', return_value=mock_fastmcp), \
             patch('localtoolkit.cli.main.load_filesystem_settings') as mock_load, \
             patch('localtoolkit.cli.main.register_messages'), \
             patch('localtoolkit.cli.main.register_contacts'), \
             patch('localtoolkit.cli.main.register_mail'), \
             patch('localtoolkit.cli.main.register_applescript'), \
             patch('localtoolkit.cli.main.register_process'), \
             patch('localtoolkit.cli.main.register_reminders'), \
             patch('localtoolkit.cli.main.register_filesystem'):
            
            mock_load.return_value = ({"allowed_dirs": []}, Mock())
            
            # Import and run the module
            import localtoolkit.cli.main
            if hasattr(localtoolkit.cli.main, '__name__'):
                # This won't actually run the if __name__ == "__main__" block in tests
                # but we can test the main function was defined
                assert callable(localtoolkit.cli.main.main)