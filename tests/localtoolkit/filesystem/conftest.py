"""
Test fixtures for the Filesystem integration tests.

This module contains fixtures specific to the Filesystem tests.
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock


@pytest.fixture
def temp_test_dir():
    """
    Create a temporary directory for testing.
    
    Yields:
        str: Path to the temporary directory
    """
    temp_dir = tempfile.mkdtemp(prefix="ltk_test_")
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_files(temp_test_dir):
    """
    Create test files in the temporary directory.
    
    Args:
        temp_test_dir: The temporary directory fixture
        
    Returns:
        dict: Dictionary with paths to created test files
    """
    files = {}
    
    # Create a simple text file
    text_file = os.path.join(temp_test_dir, "test.txt")
    with open(text_file, "w") as f:
        f.write("This is a test file.\nIt has multiple lines.\n")
    files["text_file"] = text_file
    
    # Create a JSON file
    json_file = os.path.join(temp_test_dir, "data.json")
    with open(json_file, "w") as f:
        f.write('{"name": "test", "value": 42}')
    files["json_file"] = json_file
    
    # Create a subdirectory with files
    sub_dir = os.path.join(temp_test_dir, "subdir")
    os.makedirs(sub_dir)
    files["sub_dir"] = sub_dir
    
    sub_file = os.path.join(sub_dir, "nested.txt")
    with open(sub_file, "w") as f:
        f.write("Nested file content")
    files["sub_file"] = sub_file
    
    # Create an empty file
    empty_file = os.path.join(temp_test_dir, "empty.txt")
    open(empty_file, "w").close()
    files["empty_file"] = empty_file
    
    return files


@pytest.fixture
def mock_security_settings(temp_test_dir):
    """
    Mock security settings for testing.
    
    Args:
        temp_test_dir: The temporary directory fixture
        
    Returns:
        dict: Security settings dictionary
    """
    return {
        "allowed_dirs": [
            {
                "path": temp_test_dir,
                "permissions": ["read", "write", "list"]
            }
        ],
        "security_log_dir": os.path.join(temp_test_dir, "logs")
    }


@pytest.fixture
def restricted_security_settings(temp_test_dir):
    """
    Mock security settings with restricted permissions.
    
    Args:
        temp_test_dir: The temporary directory fixture
        
    Returns:
        dict: Security settings with read-only permission
    """
    return {
        "allowed_dirs": [
            {
                "path": temp_test_dir,
                "permissions": ["read", "list"]  # No write permission
            }
        ],
        "security_log_dir": None
    }


@pytest.fixture
def mock_read_file_response():
    """
    Mock successful response from read_file.
    
    Returns:
        dict: A mock response dictionary
    """
    return {
        "success": True,
        "content": "This is the file content.",
        "message": "File read successfully",
        "metadata": {
            "size_bytes": 24,
            "mime_type": "text/plain",
            "encoding": "utf-8"
        }
    }


@pytest.fixture
def mock_write_file_response():
    """
    Mock successful response from write_file.
    
    Returns:
        dict: A mock response dictionary
    """
    return {
        "success": True,
        "path": "/path/to/file.txt",
        "message": "File written successfully",
        "metadata": {
            "size_bytes": 100,
            "mode": "overwrite"
        }
    }


@pytest.fixture
def mock_list_directory_response():
    """
    Mock successful response from list_directory.
    
    Returns:
        dict: A mock response dictionary
    """
    return {
        "success": True,
        "entries": [
            {
                "name": "file1.txt",
                "type": "file",
                "size": 1024,
                "modified": "2024-01-15T10:30:00"
            },
            {
                "name": "subdir",
                "type": "directory",
                "size": 0,
                "modified": "2024-01-10T08:00:00"
            }
        ],
        "message": "Directory listed successfully",
        "metadata": {
            "total_entries": 2,
            "path": "/test/path"
        }
    }


@pytest.fixture
def mock_error_response():
    """
    Mock error response for filesystem operations.
    
    Returns:
        dict: A mock error response dictionary
    """
    return {
        "success": False,
        "error": "Permission denied",
        "message": "Failed to access path",
        "metadata": {
            "path": "/restricted/path"
        }
    }


@pytest.fixture
def patch_security_module():
    """
    Patch the security module for testing.
    
    Yields:
        dict: Dictionary with mocked security functions
    """
    # Patch at the usage locations, not the definition location
    with patch('localtoolkit.filesystem.list_directory.validate_path_access') as mock_validate_list, \
         patch('localtoolkit.filesystem.list_directory.log_security_event') as mock_log_list, \
         patch('localtoolkit.filesystem.read_file.validate_path_access') as mock_validate_read, \
         patch('localtoolkit.filesystem.read_file.log_security_event') as mock_log_read, \
         patch('localtoolkit.filesystem.write_file.validate_path_access') as mock_validate_write, \
         patch('localtoolkit.filesystem.write_file.log_security_event') as mock_log_write, \
         patch('localtoolkit.filesystem.utils.security.initialize') as mock_init:
        
        # Default behavior - allow all access and return the requested path
        def mock_validate_side_effect(path, operation):
            """Return the same path that was requested."""
            return (True, path, "Access allowed")
        
        mock_validate_list.side_effect = mock_validate_side_effect
        mock_validate_read.side_effect = mock_validate_side_effect
        mock_validate_write.side_effect = mock_validate_side_effect
        
        # Create a wrapper that manages all mocks
        class MockWrapper:
            def __init__(self):
                self.validate_list = mock_validate_list
                self.validate_read = mock_validate_read
                self.validate_write = mock_validate_write
                self.log_list = mock_log_list
                self.log_read = mock_log_read
                self.log_write = mock_log_write
                self.initialize = mock_init
                
            # For backward compatibility, make the wrapper act like a dict
            def __getitem__(self, key):
                if key == "validate":
                    # Return a mock that tracks all validate calls
                    return self.validate_read  # Default to read for tests
                elif key == "log":
                    return self.log_read
                elif key == "initialize":
                    return self.initialize
                    
        yield MockWrapper()


@pytest.fixture
def sample_file_content():
    """
    Sample file content for testing.
    
    Returns:
        str: Multi-line text content
    """
    return """Line 1: This is a test file
Line 2: It contains multiple lines
Line 3: For testing purposes
Line 4: With some special characters: @#$%
Line 5: And a final line"""