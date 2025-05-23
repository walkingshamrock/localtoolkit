"""
Tests for the filesystem write_file module.

This module tests the file writing functionality, including
security validation, error handling, and encoding support.
"""

import pytest
import os
from unittest.mock import patch, MagicMock, call, mock_open

from localtoolkit.filesystem.write_file import write_file_logic


class TestWriteFileLogic:
    """Test the write_file_logic function."""
    
    def test_write_file_success(self, temp_test_dir, patch_security_module):
        """Test successful file writing."""
        file_path = os.path.join(temp_test_dir, "new_file.txt")
        content = "This is new content."
        patch_security_module.validate_write.return_value = (True, file_path, "Access allowed")
        
        result = write_file_logic(file_path, content)
        
        assert result["success"] is True
        assert "bytes_written" in result
        assert result["bytes_written"] == len(content.encode('utf-8'))
        assert result["path"] == file_path
        
        # Verify file was actually written
        with open(file_path, 'r') as f:
            assert f.read() == content
        
        # Verify security was called
        patch_security_module.validate_write.assert_called_once_with(file_path, "write")
        patch_security_module.log_write.assert_called_with(
            "write_file", file_path, True, 
            f"File written successfully ({result['bytes_written']} bytes)"
        )
    
    def test_overwrite_existing_file(self, temp_test_dir, test_files, patch_security_module):
        """Test overwriting an existing file."""
        file_path = test_files["text_file"]
        new_content = "Completely new content"
        patch_security_module.validate_write.return_value = (True, file_path, "Access allowed")
        
        # Verify original content
        with open(file_path, 'r') as f:
            original = f.read()
        assert original != new_content
        
        result = write_file_logic(file_path, new_content)
        
        assert result["success"] is True
        assert result["bytes_written"] == len(new_content.encode('utf-8'))
        
        # Verify file was overwritten
        with open(file_path, 'r') as f:
            assert f.read() == new_content
    
    def test_write_file_with_custom_encoding(self, temp_test_dir, patch_security_module):
        """Test writing file with custom encoding."""
        file_path = os.path.join(temp_test_dir, "latin1_out.txt")
        content = "Café, naïve, résumé"
        patch_security_module.validate_write.return_value = (True, file_path, "Access allowed")
        
        result = write_file_logic(file_path, content, encoding="latin-1")
        
        assert result["success"] is True
        
        # Read back with same encoding
        with open(file_path, 'r', encoding='latin-1') as f:
            assert f.read() == content
    
    def test_write_empty_file(self, temp_test_dir, patch_security_module):
        """Test writing an empty file."""
        file_path = os.path.join(temp_test_dir, "empty_out.txt")
        patch_security_module.validate_write.return_value = (True, file_path, "Access allowed")
        
        result = write_file_logic(file_path, "")
        
        assert result["success"] is True
        assert result["bytes_written"] == 0
        
        # Verify file exists and is empty
        assert os.path.exists(file_path)
        with open(file_path, 'r') as f:
            assert f.read() == ""
    
    def test_write_file_access_denied(self, patch_security_module):
        """Test file writing with access denied."""
        patch_security_module.validate_write.side_effect = None
        patch_security_module.validate_write.return_value = (False, None, "Path not in allowed directories")
        
        result = write_file_logic("/restricted/file.txt", "content")
        
        assert result["success"] is False
        assert result["error"] == "Path not in allowed directories"
        assert result["path"] == "/restricted/file.txt"
        assert "bytes_written" not in result
        
        # Verify security log
        patch_security_module.log_write.assert_called_with(
            "write_file", "/restricted/file.txt", False, 
            "Path not in allowed directories"
        )
    
    def test_write_file_parent_directory_missing(self, temp_test_dir, patch_security_module):
        """Test writing file when parent directory doesn't exist."""
        file_path = os.path.join(temp_test_dir, "nonexistent", "file.txt")
        patch_security_module.validate_write.return_value = (True, file_path, "Access allowed")
        
        result = write_file_logic(file_path, "content")
        
        assert result["success"] is False
        assert "Parent directory does not exist" in result["error"]
        assert result["path"] == file_path
    
    def test_write_file_permission_error(self, patch_security_module):
        """Test handling of permission errors."""
        test_path = "/test/file.txt"
        patch_security_module.validate_write.side_effect = None
        patch_security_module.validate_write.return_value = (True, test_path, "Access allowed")
        
        # Mock OS functions to simulate parent directory exists
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isdir', return_value=True), \
             patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = write_file_logic(test_path, "content")
            
            assert result["success"] is False
            assert "Permission denied" in result["error"]
            assert result["path"] == test_path
    
    def test_write_file_general_error(self, patch_security_module):
        """Test handling of general errors."""
        test_path = "/test/file.txt"
        patch_security_module.validate_write.side_effect = None
        patch_security_module.validate_write.return_value = (True, test_path, "Access allowed")
        
        # Mock OS functions to simulate parent directory exists
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isdir', return_value=True), \
             patch('builtins.open', side_effect=Exception("Disk full")):
            result = write_file_logic(test_path, "content")
            
            assert result["success"] is False
            assert "Error writing file" in result["error"]
            assert "Disk full" in result["error"]
    
    def test_write_large_file(self, temp_test_dir, patch_security_module):
        """Test writing a large file."""
        file_path = os.path.join(temp_test_dir, "large_out.txt")
        # Create 1MB of content
        large_content = "x" * 1024 * 1024
        patch_security_module.validate_write.return_value = (True, file_path, "Access allowed")
        
        result = write_file_logic(file_path, large_content)
        
        assert result["success"] is True
        assert result["bytes_written"] == 1024 * 1024
        
        # Verify file size
        assert os.path.getsize(file_path) == 1024 * 1024
    
    def test_write_file_with_special_characters(self, temp_test_dir, patch_security_module):
        """Test writing file with special characters."""
        file_path = os.path.join(temp_test_dir, "special_out.txt")
        special_content = "Special chars: @#$%^&*()_+={[}]|\\:;\"'<,>.?/~`\n\t"
        patch_security_module.validate_write.return_value = (True, file_path, "Access allowed")
        
        result = write_file_logic(file_path, special_content)
        
        assert result["success"] is True
        
        # Verify content
        with open(file_path, 'r') as f:
            assert f.read() == special_content
    
    def test_write_file_with_unicode(self, temp_test_dir, patch_security_module):
        """Test writing file with Unicode characters."""
        file_path = os.path.join(temp_test_dir, "unicode_out.txt")
        unicode_content = "Unicode: 😀 🎉 🐍 中文 日本語 한국어"
        patch_security_module.validate_write.return_value = (True, file_path, "Access allowed")
        
        result = write_file_logic(file_path, unicode_content)
        
        assert result["success"] is True
        
        # Verify content
        with open(file_path, 'r', encoding='utf-8') as f:
            assert f.read() == unicode_content
    
    def test_write_file_preserves_newlines(self, temp_test_dir, patch_security_module):
        """Test that newlines are preserved correctly."""
        file_path = os.path.join(temp_test_dir, "newlines_out.txt")
        content = "Line 1\nLine 2\r\nLine 3\n\nLine 5"
        patch_security_module.validate_write.return_value = (True, file_path, "Access allowed")
        
        result = write_file_logic(file_path, content)
        
        assert result["success"] is True
        
        # Read back and verify - on Unix systems, \r\n is normalized to \n in text mode
        expected_content = "Line 1\nLine 2\nLine 3\n\nLine 5"
        with open(file_path, 'r') as f:
            assert f.read() == expected_content
    
    def test_write_file_creates_in_subdirectory(self, temp_test_dir, test_files, patch_security_module):
        """Test writing file in an existing subdirectory."""
        sub_dir = test_files["sub_dir"]
        file_path = os.path.join(sub_dir, "new_sub_file.txt")
        content = "Content in subdirectory"
        patch_security_module.validate_write.return_value = (True, file_path, "Access allowed")
        
        result = write_file_logic(file_path, content)
        
        assert result["success"] is True
        assert os.path.exists(file_path)
        
        with open(file_path, 'r') as f:
            assert f.read() == content
    
    def test_write_file_bytes_written_calculation(self, temp_test_dir, patch_security_module):
        """Test that bytes_written is calculated correctly for different encodings."""
        # UTF-8 with multi-byte characters
        file_path = os.path.join(temp_test_dir, "bytes_test.txt")
        content = "Hello 世界"  # "Hello " is 6 bytes, "世界" is 6 bytes in UTF-8
        patch_security_module.validate_write.return_value = (True, file_path, "Access allowed")
        
        result = write_file_logic(file_path, content)
        
        assert result["success"] is True
        assert result["bytes_written"] == 12  # 6 + 6 bytes
        
        # Verify actual file size
        assert os.path.getsize(file_path) == 12