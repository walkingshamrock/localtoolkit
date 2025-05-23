"""
Tests for the filesystem list_directory module.

This module tests the directory listing functionality, including
security validation, error handling, and proper file/directory metadata.
"""

import pytest
import os
import time
from unittest.mock import patch, MagicMock, call

from localtoolkit.filesystem.list_directory import list_directory_logic


class TestListDirectoryLogic:
    """Test the list_directory_logic function."""
    
    def test_list_directory_success(self, temp_test_dir, test_files, patch_security_module):
        """Test successful directory listing."""
        # Configure security to allow access
        patch_security_module.validate_list.return_value = (True, temp_test_dir, "Access allowed")
        
        result = list_directory_logic(temp_test_dir)
        
        assert result["success"] is True
        assert "entries" in result
        assert result["path"] == temp_test_dir
        assert result["count"] == len(os.listdir(temp_test_dir))
        
        # Verify security was called
        patch_security_module.validate_list.assert_called_once_with(temp_test_dir, "list")
        patch_security_module.log_list.assert_called_with(
            "list_directory", temp_test_dir, True, 
            f"Directory listed successfully with {result['count']} entries"
        )
    
    def test_list_directory_entry_structure(self, temp_test_dir, test_files, patch_security_module):
        """Test that directory entries have correct structure."""
        patch_security_module.validate_list.return_value = (True, temp_test_dir, "Access allowed")
        
        result = list_directory_logic(temp_test_dir)
        
        assert result["success"] is True
        
        # Check each entry
        for entry in result["entries"]:
            assert "name" in entry
            assert "type" in entry
            assert "size" in entry
            assert "modified" in entry
            assert entry["type"] in ["file", "directory"]
            assert isinstance(entry["size"], int)
            assert isinstance(entry["modified"], float)
            
            # Directories should have size 0
            if entry["type"] == "directory":
                assert entry["size"] == 0
    
    def test_list_directory_sorting(self, temp_test_dir, test_files, patch_security_module):
        """Test that entries are sorted correctly (directories first, then files)."""
        patch_security_module.validate_list.return_value = (True, temp_test_dir, "Access allowed")
        
        result = list_directory_logic(temp_test_dir)
        
        assert result["success"] is True
        
        # Separate directories and files
        directories = [e for e in result["entries"] if e["type"] == "directory"]
        files = [e for e in result["entries"] if e["type"] == "file"]
        
        # Check that all directories come before files
        if directories and files:
            last_dir_index = result["entries"].index(directories[-1])
            first_file_index = result["entries"].index(files[0])
            assert last_dir_index < first_file_index
        
        # Check alphabetical sorting within each type
        dir_names = [d["name"] for d in directories]
        assert dir_names == sorted(dir_names)
        
        file_names = [f["name"] for f in files]
        assert file_names == sorted(file_names)
    
    def test_list_directory_with_subdirectory(self, temp_test_dir, test_files, patch_security_module):
        """Test listing a subdirectory."""
        sub_dir = test_files["sub_dir"]
        patch_security_module.validate_list.return_value = (True, sub_dir, "Access allowed")
        
        result = list_directory_logic(sub_dir)
        
        assert result["success"] is True
        assert result["count"] == 1  # Should contain nested.txt
        assert result["entries"][0]["name"] == "nested.txt"
        assert result["entries"][0]["type"] == "file"
    
    def test_list_directory_access_denied(self, patch_security_module):
        """Test directory listing with access denied."""
        # Clear the side_effect and set return_value
        patch_security_module.validate_list.side_effect = None
        patch_security_module.validate_list.return_value = (False, None, "Path not in allowed directories")
        
        result = list_directory_logic("/restricted/path")
        
        assert result["success"] is False
        assert result["error"] == "Path not in allowed directories"
        assert result["path"] == "/restricted/path"
        assert "entries" not in result
        
        # Verify security log
        patch_security_module.log_list.assert_called_with(
            "list_directory", "/restricted/path", False, 
            "Path not in allowed directories"
        )
    
    def test_list_directory_not_found(self, patch_security_module):
        """Test listing a non-existent directory."""
        nonexistent = "/tmp/nonexistent_dir_12345"
        patch_security_module.validate_list.return_value = (True, nonexistent, "Access allowed")
        
        result = list_directory_logic(nonexistent)
        
        assert result["success"] is False
        assert "not found" in result["error"]
        assert result["path"] == nonexistent
    
    def test_list_file_instead_of_directory(self, temp_test_dir, test_files, patch_security_module):
        """Test listing a file path instead of directory."""
        file_path = test_files["text_file"]
        patch_security_module.validate_list.return_value = (True, file_path, "Access allowed")
        
        result = list_directory_logic(file_path)
        
        assert result["success"] is False
        assert "Not a directory" in result["error"]
        assert result["path"] == file_path
    
    def test_list_directory_permission_error(self, patch_security_module):
        """Test handling of permission errors."""
        restricted_dir = "/root"  # Typically restricted on Unix systems
        patch_security_module.validate_list.side_effect = None
        patch_security_module.validate_list.return_value = (True, restricted_dir, "Access allowed")
        
        # Mock os functions to simulate the directory exists but can't be listed
        with patch('os.listdir') as mock_listdir, \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isdir', return_value=True):
            mock_listdir.side_effect = PermissionError("Access denied")
            
            result = list_directory_logic(restricted_dir)
            
            assert result["success"] is False
            assert "Permission denied" in result["error"]
            assert result["path"] == restricted_dir
    
    def test_list_directory_general_error(self, patch_security_module):
        """Test handling of general errors."""
        test_path = "/test/path"
        patch_security_module.validate_list.side_effect = None
        patch_security_module.validate_list.return_value = (True, test_path, "Access allowed")
        
        # Mock os functions to simulate the directory exists but throws an error
        with patch('os.listdir') as mock_listdir, \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isdir', return_value=True):
            mock_listdir.side_effect = Exception("Unexpected error")
            
            result = list_directory_logic(test_path)
            
            assert result["success"] is False
            assert "Error listing directory" in result["error"]
            assert "Unexpected error" in result["error"]
    
    def test_list_empty_directory(self, temp_test_dir, patch_security_module):
        """Test listing an empty directory."""
        # Create an empty directory
        empty_dir = os.path.join(temp_test_dir, "empty")
        os.makedirs(empty_dir)
        
        patch_security_module.validate_list.return_value = (True, empty_dir, "Access allowed")
        
        result = list_directory_logic(empty_dir)
        
        assert result["success"] is True
        assert result["entries"] == []
        assert result["count"] == 0
    
    def test_list_directory_with_hidden_files(self, temp_test_dir, patch_security_module):
        """Test that hidden files (starting with .) are included."""
        # Create a hidden file
        hidden_file = os.path.join(temp_test_dir, ".hidden")
        with open(hidden_file, "w") as f:
            f.write("hidden content")
        
        patch_security_module.validate_list.return_value = (True, temp_test_dir, "Access allowed")
        
        result = list_directory_logic(temp_test_dir)
        
        assert result["success"] is True
        hidden_entries = [e for e in result["entries"] if e["name"].startswith(".")]
        assert len(hidden_entries) > 0
        assert any(e["name"] == ".hidden" for e in hidden_entries)
    
    def test_list_directory_file_metadata(self, temp_test_dir, test_files, patch_security_module):
        """Test that file metadata is accurate."""
        patch_security_module.validate_list.return_value = (True, temp_test_dir, "Access allowed")
        
        # Get actual file info
        text_file = test_files["text_file"]
        actual_stat = os.stat(text_file)
        
        result = list_directory_logic(temp_test_dir)
        
        # Find the test.txt entry
        text_entry = next(e for e in result["entries"] if e["name"] == "test.txt")
        
        assert text_entry["type"] == "file"
        assert text_entry["size"] == actual_stat.st_size
        assert abs(text_entry["modified"] - actual_stat.st_mtime) < 1  # Within 1 second
    
    def test_list_directory_with_special_characters(self, temp_test_dir, patch_security_module):
        """Test listing directory with files having special characters."""
        # Create files with special characters
        special_names = ["file with spaces.txt", "file@#$.txt", "file'quote.txt"]
        for name in special_names:
            path = os.path.join(temp_test_dir, name)
            with open(path, "w") as f:
                f.write("content")
        
        patch_security_module.validate_list.return_value = (True, temp_test_dir, "Access allowed")
        
        result = list_directory_logic(temp_test_dir)
        
        assert result["success"] is True
        entry_names = [e["name"] for e in result["entries"]]
        for special_name in special_names:
            assert special_name in entry_names