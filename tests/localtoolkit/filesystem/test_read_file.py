"""
Tests for the filesystem read_file module.

This module tests the file reading functionality, including
security validation, error handling, and encoding support.
"""

import pytest
import os
from unittest.mock import patch, MagicMock, call, mock_open

from localtoolkit.filesystem.read_file import read_file_logic


class TestReadFileLogic:
    """Test the read_file_logic function."""
    
    def test_read_file_success(self, temp_test_dir, test_files, patch_security_module):
        """Test successful file reading."""
        file_path = test_files["text_file"]
        # The mock already has a side_effect that returns (True, path, "Access allowed")
        # So we don't need to set return_value
        
        result = read_file_logic(file_path)
        
        assert result["success"] is True
        assert "content" in result
        assert result["content"] == "This is a test file.\nIt has multiple lines.\n"
        assert result["path"] == file_path
        assert result["encoding"] == "utf-8"
        
        # Verify security was called
        patch_security_module.validate_read.assert_called_once_with(file_path, "read")
        patch_security_module.log_read.assert_called_with(
            "read_file", file_path, True, "File read successfully"
        )
    
    def test_read_file_with_custom_encoding(self, temp_test_dir, patch_security_module):
        """Test reading file with custom encoding."""
        # Create a file with latin-1 encoding
        file_path = os.path.join(temp_test_dir, "latin1.txt")
        with open(file_path, "w", encoding="latin-1") as f:
            f.write("Café, naïve, résumé")
        
        patch_security_module.validate_read.return_value = (True, file_path, "Access allowed")
        
        result = read_file_logic(file_path, encoding="latin-1")
        
        assert result["success"] is True
        assert result["content"] == "Café, naïve, résumé"
        assert result["encoding"] == "latin-1"
    
    def test_read_json_file(self, test_files, patch_security_module):
        """Test reading a JSON file."""
        json_path = test_files["json_file"]
        patch_security_module.validate_read.return_value = (True, json_path, "Access allowed")
        
        result = read_file_logic(json_path)
        
        assert result["success"] is True
        assert result["content"] == '{"name": "test", "value": 42}'
    
    def test_read_empty_file(self, test_files, patch_security_module):
        """Test reading an empty file."""
        empty_path = test_files["empty_file"]
        patch_security_module.validate_read.return_value = (True, empty_path, "Access allowed")
        
        result = read_file_logic(empty_path)
        
        assert result["success"] is True
        assert result["content"] == ""
    
    def test_read_file_access_denied(self, patch_security_module):
        """Test file reading with access denied."""
        patch_security_module.validate_read.side_effect = None
        patch_security_module.validate_read.return_value = (False, None, "Path not in allowed directories")
        
        result = read_file_logic("/restricted/file.txt")
        
        assert result["success"] is False
        assert result["error"] == "Path not in allowed directories"
        assert result["path"] == "/restricted/file.txt"
        assert "content" not in result
        
        # Verify security log
        patch_security_module.log_read.assert_called_with(
            "read_file", "/restricted/file.txt", False, 
            "Path not in allowed directories"
        )
    
    def test_read_file_not_found(self, patch_security_module):
        """Test reading a non-existent file."""
        nonexistent = "/tmp/nonexistent_file_12345.txt"
        patch_security_module.validate_read.return_value = (True, nonexistent, "Access allowed")
        
        result = read_file_logic(nonexistent)
        
        assert result["success"] is False
        assert "not found" in result["error"]
        assert result["path"] == nonexistent
    
    def test_read_directory_instead_of_file(self, temp_test_dir, test_files, patch_security_module):
        """Test reading a directory path instead of file."""
        dir_path = test_files["sub_dir"]
        patch_security_module.validate_read.return_value = (True, dir_path, "Access allowed")
        
        result = read_file_logic(dir_path)
        
        assert result["success"] is False
        assert "Not a file" in result["error"]
        assert result["path"] == dir_path
    
    def test_read_file_encoding_error(self, temp_test_dir, patch_security_module):
        """Test handling of encoding errors."""
        # Create a file with problematic encoding
        file_path = os.path.join(temp_test_dir, "binary.dat")
        with open(file_path, "wb") as f:
            f.write(b'\x80\x81\x82\x83')  # Invalid UTF-8 bytes
        
        patch_security_module.validate_read.return_value = (True, file_path, "Access allowed")
        
        result = read_file_logic(file_path, encoding="utf-8")
        
        assert result["success"] is False
        assert "Encoding error" in result["error"]
        assert "Try a different encoding" in result["error"]
    
    def test_read_file_permission_error(self, patch_security_module):
        """Test handling of permission errors."""
        test_path = "/test/file.txt"
        patch_security_module.validate_read.side_effect = None
        patch_security_module.validate_read.return_value = (True, test_path, "Access allowed")
        
        # Mock file exists and is a file, then open raises PermissionError
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = read_file_logic(test_path)
            
            assert result["success"] is False
            assert "Permission denied" in result["error"]
            assert result["path"] == test_path
    
    def test_read_file_general_error(self, patch_security_module):
        """Test handling of general errors."""
        test_path = "/test/file.txt"
        patch_security_module.validate_read.side_effect = None
        patch_security_module.validate_read.return_value = (True, test_path, "Access allowed")
        
        # Mock file exists and is a file, then open raises generic exception
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('builtins.open', side_effect=Exception("Disk error")):
            result = read_file_logic(test_path)
            
            assert result["success"] is False
            assert "Error reading file" in result["error"]
            assert "Disk error" in result["error"]
    
    def test_read_large_file(self, temp_test_dir, patch_security_module):
        """Test reading a large file."""
        # Create a large file (1MB)
        large_file = os.path.join(temp_test_dir, "large.txt")
        content = "x" * 1024 * 1024  # 1MB of 'x'
        with open(large_file, "w") as f:
            f.write(content)
        
        patch_security_module.validate_read.return_value = (True, large_file, "Access allowed")
        
        result = read_file_logic(large_file)
        
        assert result["success"] is True
        assert len(result["content"]) == 1024 * 1024
        assert result["content"][:10] == "xxxxxxxxxx"
    
    def test_read_file_with_special_characters(self, temp_test_dir, patch_security_module):
        """Test reading file with special characters."""
        file_path = os.path.join(temp_test_dir, "special.txt")
        special_content = "Special chars: @#$%^&*()_+={[}]|\\:;\"'<,>.?/~`"
        with open(file_path, "w") as f:
            f.write(special_content)
        
        patch_security_module.validate_read.return_value = (True, file_path, "Access allowed")
        
        result = read_file_logic(file_path)
        
        assert result["success"] is True
        assert result["content"] == special_content
    
    def test_read_file_with_newlines(self, temp_test_dir, patch_security_module):
        """Test reading file with different newline types."""
        file_path = os.path.join(temp_test_dir, "newlines.txt")
        # Mix of Unix (\n) and Windows (\r\n) newlines
        content = "Line 1\nLine 2\r\nLine 3\n"
        with open(file_path, "w") as f:
            f.write(content)
        
        patch_security_module.validate_read.return_value = (True, file_path, "Access allowed")
        
        result = read_file_logic(file_path)
        
        assert result["success"] is True
        # Python's text mode converts \r\n to \n on Unix systems
        # So we should expect the normalized content
        expected_content = "Line 1\nLine 2\nLine 3\n"
        assert result["content"] == expected_content
    
    def test_read_file_preserves_exact_content(self, temp_test_dir, patch_security_module):
        """Test that file content is preserved exactly."""
        file_path = os.path.join(temp_test_dir, "exact.txt")
        # Content with trailing spaces, tabs, and empty lines
        content = "Line 1  \n\tLine 2\n\n\nLine 3"
        with open(file_path, "w") as f:
            f.write(content)
        
        patch_security_module.validate_read.return_value = (True, file_path, "Access allowed")
        
        result = read_file_logic(file_path)
        
        assert result["success"] is True
        assert result["content"] == content