"""
Implementation of read_file for the filesystem module.

This module provides functionality to read files from the filesystem
with proper security validation and error handling.
"""

import os
from typing import Dict, Any, Optional
from fastmcp import FastMCP

from localtoolkit.filesystem.utils.security import validate_path_access, log_security_event

def read_file_logic(path: str, encoding: Optional[str] = "utf-8") -> Dict[str, Any]:
    """
    Read the complete contents of a file from the file system.
    
    Handles various text encodings and provides detailed error messages
    if the file cannot be read. Only works within allowed directories.
    
    Args:
        path: Path to the file to read
        encoding: Text encoding to use when reading the file (default: utf-8)
        
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,     # True if operation was successful
            "content": str,      # File content (only present if success is True)
            "error": str,        # Error message (only present if success is False)
            "path": str,         # Original path requested
            "encoding": str      # Encoding used for reading
        }
    """
    try:
        # Validate path
        is_allowed, safe_path, message = validate_path_access(path, "read")
        if not is_allowed or safe_path is None:
            log_security_event("read_file", path, False, message)
            return {
                "success": False,
                "error": message,
                "path": path
            }
        
        # Check if file exists
        if not os.path.exists(safe_path):
            error = f"File not found: {path}"
            log_security_event("read_file", path, False, error)
            return {
                "success": False,
                "error": error,
                "path": path
            }
        
        # Check if it's a file, not a directory
        if not os.path.isfile(safe_path):
            error = f"Not a file: {path}"
            log_security_event("read_file", path, False, error)
            return {
                "success": False,
                "error": error,
                "path": path
            }
        
        # Read the file
        with open(safe_path, 'r', encoding=encoding) as f:
            content = f.read()
        
        # Log success
        log_security_event("read_file", path, True, "File read successfully")
        
        return {
            "success": True,
            "content": content,
            "path": path,
            "encoding": encoding
        }
    except UnicodeDecodeError as e:
        error = f"Encoding error: {str(e)}. Try a different encoding."
        log_security_event("read_file", path, False, error)
        return {
            "success": False,
            "error": error,
            "path": path
        }
    except PermissionError:
        error = f"Permission denied when reading file: {path}"
        log_security_event("read_file", path, False, error)
        return {
            "success": False,
            "error": error,
            "path": path
        }
    except Exception as e:
        error = f"Error reading file: {str(e)}"
        log_security_event("read_file", path, False, error)
        return {
            "success": False,
            "error": error,
            "path": path
        }

def register_to_mcp(mcp: FastMCP) -> None:
    @mcp.tool()
    def filesystem_read_file(path: str, encoding: Optional[str] = "utf-8") -> Dict[str, Any]:
        """
        Read the complete contents of a file from the file system.
        
        Handles various text encodings and provides detailed error messages
        if the file cannot be read. Only works within allowed directories.
        
        Args:
            path: Path to the file to read
            encoding: Text encoding to use when reading the file (default: utf-8)
            
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,     # True if operation was successful
                "content": str,      # File content (only present if success is True)
                "error": str,        # Error message (only present if success is False)
                "path": str,         # Original path requested
                "encoding": str      # Encoding used for reading
            }
            
        Error Handling:
            - Path not in allowed directories: Returns error about invalid path
            - File not found: Returns detailed error message
            - Permission denied: Returns error about insufficient permissions
            - Encoding issues: Suggests trying a different encoding
            
        Performance:
            - Typical response time: 0.1-1 second depending on file size
            
        Usage with other endpoints:
            This endpoint is often used after listing directories to read specific files:
            1. Call filesystem_list_directory to find files
            2. Call filesystem_read_file with a specific file path
            
        Examples:
            ```python
            # Read a configuration file
            result = filesystem_read_file("/path/to/config.json")
            if result["success"]:
                config_content = result["content"]
                print(f"Configuration loaded, length: {len(config_content)}")
            else:
                print(f"Error: {result['error']}")
                
            # Read a file with specific encoding
            result = filesystem_read_file("/path/to/file.txt", encoding="latin-1")
            ```
        """
        return read_file_logic(path, encoding)