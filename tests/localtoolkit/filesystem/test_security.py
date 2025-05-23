"""
Tests for the filesystem security utilities module.

This module tests the security validation, path checking,
and logging functionality for filesystem operations.
"""

import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock, mock_open

from localtoolkit.filesystem.utils.security import (
    initialize, 
    validate_path_access, 
    log_security_event,
    _settings
)


class TestSecurityInitialization:
    """Test the security module initialization."""
    
    def test_initialize_with_empty_settings(self):
        """Test initialization with empty settings."""
        # Reset settings first
        _settings.clear()
        _settings.update({
            "allowed_dirs": [],
            "security_log_dir": None,
            "initialized": False
        })
        
        initialize({})
        
        assert _settings["initialized"] is True
        assert _settings["allowed_dirs"] == []
        assert _settings["security_log_dir"] is None
    
    def test_initialize_with_allowed_dirs(self, temp_test_dir):
        """Test initialization with allowed directories."""
        settings = {
            "allowed_dirs": [
                {"path": temp_test_dir, "permissions": ["read", "write"]},
                {"path": "/tmp", "permissions": ["read"]}
            ]
        }
        
        initialize(settings)
        
        assert len(_settings["allowed_dirs"]) >= 1  # At least temp_test_dir should be added
        
        # Find the temp_test_dir entry
        temp_dir_entry = next(
            (d for d in _settings["allowed_dirs"] if d["path"] == os.path.abspath(temp_test_dir)),
            None
        )
        assert temp_dir_entry is not None
        assert temp_dir_entry["permissions"] == ["read", "write"]
    
    def test_initialize_with_home_expansion(self):
        """Test initialization with home directory expansion."""
        settings = {
            "allowed_dirs": [
                {"path": "~/test_dir", "permissions": ["read"]}
            ]
        }
        
        with patch('os.path.exists', return_value=True):
            initialize(settings)
        
        # Check that ~ was expanded
        assert len(_settings["allowed_dirs"]) == 1
        assert not _settings["allowed_dirs"][0]["path"].startswith("~")
        assert _settings["allowed_dirs"][0]["path"].startswith(os.path.expanduser("~"))
    
    def test_initialize_creates_missing_home_subdirectory(self, temp_test_dir):
        """Test that missing subdirectories of home are created."""
        missing_dir = os.path.join(temp_test_dir, "missing_subdir")
        settings = {
            "allowed_dirs": [
                {"path": missing_dir, "permissions": ["read", "write"]}
            ]
        }
        
        with patch('os.path.expanduser', return_value=temp_test_dir):
            initialize(settings)
        
        # Directory should be created
        assert os.path.exists(missing_dir)
        assert len(_settings["allowed_dirs"]) == 1
    
    def test_initialize_skips_nonexistent_non_home_dirs(self):
        """Test that non-home directories that don't exist are skipped."""
        settings = {
            "allowed_dirs": [
                {"path": "/nonexistent/system/dir", "permissions": ["read"]}
            ]
        }
        
        initialize(settings)
        
        # Directory should be skipped
        assert len(_settings["allowed_dirs"]) == 0
    
    def test_initialize_security_log_dir(self, temp_test_dir):
        """Test initialization of security log directory."""
        log_dir = os.path.join(temp_test_dir, "logs")
        settings = {
            "security_log_dir": log_dir
        }
        
        initialize(settings)
        
        assert _settings["security_log_dir"] == log_dir
        assert os.path.exists(log_dir)
    
    def test_initialize_handles_invalid_path_in_allowed_dirs(self):
        """Test handling of invalid paths in allowed_dirs."""
        settings = {
            "allowed_dirs": [
                {"path": "", "permissions": ["read"]},  # Empty path
                {"permissions": ["read"]},  # Missing path
                {"path": "/valid/path", "permissions": ["read"]}
            ]
        }
        
        with patch('os.path.exists', return_value=True):
            initialize(settings)
        
        # Only valid paths should be added
        assert len(_settings["allowed_dirs"]) == 1
        assert _settings["allowed_dirs"][0]["path"] == os.path.abspath("/valid/path")


class TestValidatePathAccess:
    """Test the path validation functionality."""
    
    def test_validate_empty_path(self):
        """Test validation of empty path."""
        is_allowed, safe_path, message = validate_path_access("", "read")
        
        assert is_allowed is False
        assert safe_path is None
        assert message == "Path cannot be empty"
    
    def test_validate_allowed_path(self):
        """Test validation of allowed path."""
        # Setup allowed directory
        _settings["allowed_dirs"] = [
            {"path": "/allowed/dir", "permissions": ["read", "write"]}
        ]
        _settings["initialized"] = True
        
        is_allowed, safe_path, message = validate_path_access("/allowed/dir/file.txt", "read")
        
        assert is_allowed is True
        assert safe_path == "/allowed/dir/file.txt"
        assert message == "Access allowed"
    
    def test_validate_subdirectory_access(self):
        """Test validation of subdirectory access."""
        _settings["allowed_dirs"] = [
            {"path": "/allowed", "permissions": ["read"]}
        ]
        _settings["initialized"] = True
        
        is_allowed, safe_path, message = validate_path_access("/allowed/sub/dir/file.txt", "read")
        
        assert is_allowed is True
        assert safe_path == "/allowed/sub/dir/file.txt"
        assert message == "Access allowed"
    
    def test_validate_operation_not_permitted(self):
        """Test validation when operation is not in permissions."""
        _settings["allowed_dirs"] = [
            {"path": "/allowed", "permissions": ["read"]}  # No write permission
        ]
        _settings["initialized"] = True
        
        is_allowed, safe_path, message = validate_path_access("/allowed/file.txt", "write")
        
        assert is_allowed is False
        assert safe_path is None
        assert '"write" not allowed' in message
    
    def test_validate_path_not_in_allowed_dirs(self):
        """Test validation of path not in allowed directories."""
        _settings["allowed_dirs"] = [
            {"path": "/allowed", "permissions": ["read"]}
        ]
        _settings["initialized"] = True
        
        is_allowed, safe_path, message = validate_path_access("/restricted/file.txt", "read")
        
        assert is_allowed is False
        assert safe_path is None
        assert "not in allowed directories" in message
    
    def test_validate_with_no_allowed_dirs(self):
        """Test validation when no directories are configured."""
        _settings["allowed_dirs"] = []
        _settings["initialized"] = True
        
        is_allowed, safe_path, message = validate_path_access("/any/path", "read")
        
        assert is_allowed is False
        assert safe_path is None
        assert message == "No allowed directories configured"
    
    def test_validate_fallback_when_not_initialized(self):
        """Test fallback behavior when module is not initialized."""
        _settings["allowed_dirs"] = []
        _settings["initialized"] = False
        
        cwd = os.getcwd()
        test_path = os.path.join(cwd, "file.txt")
        
        is_allowed, safe_path, message = validate_path_access(test_path, "read")
        
        assert is_allowed is True
        assert safe_path == test_path
        assert message == "Access allowed (fallback directory)"
    
    def test_validate_home_directory_expansion(self):
        """Test validation with home directory expansion."""
        home_dir = os.path.expanduser("~")
        _settings["allowed_dirs"] = [
            {"path": home_dir, "permissions": ["read"]}
        ]
        _settings["initialized"] = True
        
        is_allowed, safe_path, message = validate_path_access("~/file.txt", "read")
        
        assert is_allowed is True
        assert safe_path == os.path.join(home_dir, "file.txt")
        assert message == "Access allowed"
    
    def test_validate_relative_to_absolute_conversion(self):
        """Test conversion of relative paths to absolute."""
        cwd = os.getcwd()
        _settings["allowed_dirs"] = [
            {"path": cwd, "permissions": ["read"]}
        ]
        _settings["initialized"] = True
        
        is_allowed, safe_path, message = validate_path_access("./file.txt", "read")
        
        assert is_allowed is True
        assert safe_path == os.path.join(cwd, "file.txt")
        assert message == "Access allowed"
    
    def test_validate_invalid_path_format(self):
        """Test handling of invalid path formats."""
        with patch('os.path.abspath', side_effect=Exception("Invalid path")):
            is_allowed, safe_path, message = validate_path_access("\x00invalid", "read")
            
            assert is_allowed is False
            assert safe_path is None
            assert "Invalid path format" in message


class TestLogSecurityEvent:
    """Test the security event logging functionality."""
    
    def test_log_event_without_file_logging(self):
        """Test logging when no log directory is configured."""
        _settings["security_log_dir"] = None
        
        # Should not raise any exceptions
        log_security_event("read", "/test/path", True, "Success")
        log_security_event("write", "/test/path", False, "Access denied")
    
    def test_log_event_with_file_logging(self, temp_test_dir):
        """Test logging to file when log directory is configured."""
        log_dir = os.path.join(temp_test_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        _settings["security_log_dir"] = log_dir
        
        # Log an event
        log_security_event("read", "/test/path", True, "File read successfully")
        
        # Check log file was created
        log_file = os.path.join(log_dir, "filesystem_security.log")
        assert os.path.exists(log_file)
        
        # Read and verify log entry
        with open(log_file, 'r') as f:
            line = f.readline()
            log_entry = json.loads(line)
            
            assert log_entry["operation"] == "read"
            assert log_entry["path"] == "/test/path"
            assert log_entry["success"] is True
            assert log_entry["message"] == "File read successfully"
            assert "timestamp" in log_entry
            assert "user" in log_entry
    
    def test_log_event_appends_to_existing_file(self, temp_test_dir):
        """Test that events are appended to existing log file."""
        log_dir = os.path.join(temp_test_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        _settings["security_log_dir"] = log_dir
        
        # Log multiple events
        log_security_event("read", "/path1", True, "Success 1")
        log_security_event("write", "/path2", False, "Failed 2")
        
        # Check both entries exist
        log_file = os.path.join(log_dir, "filesystem_security.log")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2
            
            entry1 = json.loads(lines[0])
            assert entry1["path"] == "/path1"
            assert entry1["success"] is True
            
            entry2 = json.loads(lines[1])
            assert entry2["path"] == "/path2"
            assert entry2["success"] is False
    
    def test_log_event_handles_file_write_errors(self, temp_test_dir):
        """Test that logging errors don't affect main functionality."""
        _settings["security_log_dir"] = "/invalid/log/dir"
        
        # Should not raise exception even with invalid log dir
        log_security_event("read", "/test/path", True, "Success")
    
    def test_log_event_format(self, temp_test_dir):
        """Test the format of logged events."""
        log_dir = os.path.join(temp_test_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        _settings["security_log_dir"] = log_dir
        
        # Log different types of events
        operations = [
            ("read", "/file.txt", True, "Read successful"),
            ("write", "/new.txt", True, "Write successful"),
            ("list", "/dir", True, "List successful"),
            ("read", "/restricted", False, "Access denied")
        ]
        
        for op, path, success, msg in operations:
            log_security_event(op, path, success, msg)
        
        # Verify all events
        log_file = os.path.join(log_dir, "filesystem_security.log")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == len(operations)
            
            for i, (op, path, success, msg) in enumerate(operations):
                entry = json.loads(lines[i])
                assert entry["operation"] == op
                assert entry["path"] == path
                assert entry["success"] == success
                assert entry["message"] == msg