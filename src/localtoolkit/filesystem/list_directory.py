"""
Implementation of list_directory for the filesystem module.

This module provides functionality to list the contents of a directory
with proper security validation and error handling.
"""

import os
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP

from localtoolkit.filesystem.utils.security import validate_path_access, log_security_event

def list_directory_logic(path: str) -> Dict[str, Any]:
    """
    Get a detailed listing of all files and directories in a specified path.
    
    Results clearly distinguish between files and directories.
    Only works within allowed directories.
    
    Args:
        path: Path to the directory to list
        
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,     # True if operation was successful
            "entries": List[Dict], # List of directory entries (only present if success is True)
            "error": str,        # Error message (only present if success is False)
            "path": str,         # Original path requested
        }
        
        Each entry in the entries list has:
        {
            "name": str,         # Name of the file or directory
            "type": str,         # Type: "file" or "directory"
            "size": int,         # Size in bytes (files only)
            "modified": str      # Last modified timestamp (ISO format)
        }
    """
    try:
        # Validate path
        is_allowed, safe_path, message = validate_path_access(path, "list")
        if not is_allowed or safe_path is None:
            log_security_event("list_directory", path, False, message)
            return {
                "success": False,
                "error": message,
                "path": path
            }
        
        # Check if directory exists
        if not os.path.exists(safe_path):
            error = f"Directory not found: {path}"
            log_security_event("list_directory", path, False, error)
            return {
                "success": False,
                "error": error,
                "path": path
            }
        
        # Check if its a directory, not a file
        if not os.path.isdir(safe_path):
            error = f"Not a directory: {path}"
            log_security_event("list_directory", path, False, error)
            return {
                "success": False,
                "error": error,
                "path": path
            }
        
        # List directory contents
        entries = []
        for item in os.listdir(safe_path):
            item_path = os.path.join(safe_path, item)
            
            # Get item info
            stat_info = os.stat(item_path)
            
            entry = {
                "name": item,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": stat_info.st_size if os.path.isfile(item_path) else 0,
                "modified": os.path.getmtime(item_path)  # Unix timestamp
            }
            
            entries.append(entry)
        
        # Sort entries by name (directories first, then files)
        entries.sort(key=lambda e: (0 if e["type"] == "directory" else 1, e["name"]))
        
        # Log success
        log_security_event("list_directory", path, True, f"Directory listed successfully with {len(entries)} entries")
        
        return {
            "success": True,
            "entries": entries,
            "path": path,
            "count": len(entries)
        }
    except PermissionError:
        error = f"Permission denied when listing directory: {path}"
        log_security_event("list_directory", path, False, error)
        return {
            "success": False,
            "error": error,
            "path": path
        }
    except Exception as e:
        error = f"Error listing directory: {str(e)}"
        log_security_event("list_directory", path, False, error)
        return {
            "success": False,
            "error": error,
            "path": path
        }

def register_to_mcp(mcp: FastMCP) -> None:
    @mcp.tool()
    def filesystem_list_directory(path: str) -> Dict[str, Any]:
        """
        Get a detailed listing of all files and directories in a specified path.
        
        Results clearly distinguish between files and directories with detailed metadata.
        This tool is essential for understanding directory structure and finding specific
        files within a directory. Only works within allowed directories.
        
        Args:
            path: Path to the directory to list
            
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,     # True if operation was successful
                "entries": List[Dict], # List of directory entries (only present if success is True)
                "error": str,        # Error message (only present if success is False)
                "path": str,         # Original path requested
                "count": int         # Number of entries found
            }
            
            Each entry in the entries list has:
            {
                "name": str,         # Name of the file or directory
                "type": str,         # Type: "file" or "directory"
                "size": int,         # Size in bytes (files only)
                "modified": float    # Last modified timestamp (Unix time)
            }
            
        Error Handling:
            - Path not in allowed directories: Returns error about invalid path
            - Directory not found: Returns detailed error message
            - Permission denied: Returns error about insufficient permissions
            
        Performance:
            - Typical response time: 0.1-1 second depending on directory size
            
        Usage with other endpoints:
            This endpoint is often used before reading files:
            1. Call filesystem_list_directory to discover available files
            2. Call filesystem_read_file with a specific file path
            
        Examples:
            ```python
            # List files in a directory
            result = filesystem_list_directory("/path/to/directory")
            if result["success"]:
                files = [entry for entry in result["entries"] if entry["type"] == "file"]
                print(f"Found {len(files)} files:")
                for file in files:
                    print(f"  - {file[\"name\"]} ({file[\"size\"]} bytes)")
            else:
                print(f"Error: {result[\"error\"]}")
            ```
        """
        return list_directory_logic(path)