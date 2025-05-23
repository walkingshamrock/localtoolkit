"""
Implementation of write_file for the filesystem module.

This module provides functionality to write content to files
with proper security validation and error handling.
"""

import os
from typing import Dict, Any, Optional
from fastmcp import FastMCP

from localtoolkit.filesystem.utils.security import validate_path_access, log_security_event

def write_file_logic(path: str, content: str, encoding: Optional[str] = "utf-8") -> Dict[str, Any]:
    """
    Create a new file or completely overwrite an existing file with new content.
    
    Handles text content with proper encoding. Only works within allowed directories.
    
    Args:
        path: Path to the file to write
        content: Text content to write to the file
        encoding: Text encoding to use when writing the file (default: utf-8)
        
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,     # True if operation was successful
            "bytes_written": int, # Number of bytes written (only present if success is True)
            "error": str,        # Error message (only present if success is False)
            "path": str,         # Original path requested
        }
    """
    try:
        # Validate path
        is_allowed, safe_path, message = validate_path_access(path, "write")
        if not is_allowed or safe_path is None:
            log_security_event("write_file", path, False, message)
            return {
                "success": False,
                "error": message,
                "path": path
            }
        
        # Ensure the parent directory exists
        parent_dir = os.path.dirname(safe_path)
        if parent_dir and not os.path.exists(parent_dir):
            error = f"Parent directory does not exist: {os.path.dirname(path)}"
            log_security_event("write_file", path, False, error)
            return {
                "success": False,
                "error": error,
                "path": path
            }
        
        # Write the file
        with open(safe_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        # Get bytes written
        bytes_written = os.path.getsize(safe_path)
        
        # Log success
        log_security_event("write_file", path, True, f"File written successfully ({bytes_written} bytes)")
        
        return {
            "success": True,
            "bytes_written": bytes_written,
            "path": path
        }
    except PermissionError:
        error = f"Permission denied when writing file: {path}"
        log_security_event("write_file", path, False, error)
        return {
            "success": False,
            "error": error,
            "path": path
        }
    except Exception as e:
        error = f"Error writing file: {str(e)}"
        log_security_event("write_file", path, False, error)
        return {
            "success": False,
            "error": error,
            "path": path
        }

def register_to_mcp(mcp: FastMCP) -> None:
    @mcp.tool()
    def filesystem_write_file(path: str, content: str, encoding: Optional[str] = "utf-8") -> Dict[str, Any]:
        """
        Create a new file or completely overwrite an existing file with new content.
        
        Use with caution as it will overwrite existing files without warning.
        Handles text content with proper encoding. Only works within allowed directories.
        
        Args:
            path: Path to the file to write
            content: Text content to write to the file
            encoding: Text encoding to use when writing the file (default: utf-8)
            
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,     # True if operation was successful
                "bytes_written": int, # Number of bytes written (only present if success is True)
                "error": str,        # Error message (only present if success is False)
                "path": str,         # Original path requested
            }
            
        Error Handling:
            - Path not in allowed directories: Returns error about invalid path
            - Parent directory not found: Returns error about missing directory
            - Permission denied: Returns error about insufficient permissions
            
        Performance:
            - Typical response time: 0.1-1 second depending on content size
            
        Usage with other endpoints:
            This endpoint is often used with read_file for reading and modifying content:
            1. Call filesystem_read_file to get current content
            2. Modify the content
            3. Call filesystem_write_file to save changes
            
        Examples:
            ```python
            # Create a new file
            result = filesystem_write_file("/path/to/file.txt", "Hello, world!")
            if result["success"]:
                print(f"File created successfully, {result['bytes_written']} bytes written")
            else:
                print(f"Error: {result['error']}")
            ```
        """
        return write_file_logic(path, content, encoding)