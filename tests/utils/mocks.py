"""
Common mock implementations for mac-mcp tests.

This module provides mock implementations of external dependencies like
AppleScript execution, system calls, etc. to allow for deterministic testing.
"""

import json
from unittest.mock import MagicMock


class MockAppleScriptExecutor:
    """
    Advanced mock for AppleScript execution with script-specific responses.
    
    This class provides a more advanced mock for AppleScript execution than the
    simple mock_applescript_executor fixture. It allows for configuring different
    responses for different scripts and tracking call history.
    """
    
    def __init__(self, responses=None):
        """
        Initialize the mock with optional predefined responses.
        
        Args:
            responses (dict, optional): A mapping of script hashes to responses.
                                       Default is an empty dictionary.
        """
        self.responses = responses or {}
        self.executed_scripts = []
    
    def execute(self, code, params=None, timeout=30, debug=False):
        """
        Mock AppleScript execution with tracking and predefined responses.
        
        Args:
            code (str): The AppleScript code to execute
            params (dict, optional): Parameters to inject into the script
            timeout (int, optional): Execution timeout in seconds
            debug (bool, optional): Enable debug logging
            
        Returns:
            dict: A predefined response or a default success response
        """
        # Record the execution
        execution = {
            "code": code,
            "params": params,
            "timeout": timeout,
            "debug": debug
        }
        self.executed_scripts.append(execution)
        
        # Find a matching response or return default
        # We use simple string matching here, but this could be made more sophisticated
        for script_pattern, response in self.responses.items():
            if script_pattern in code:
                return response
        
        # Default response
        return {
            "success": True,
            "data": "mock_data",
            "message": "Mock execution successful",
            "metadata": {
                "execution_time_ms": 10,
                "parsed": False
            }
        }

    def add_response(self, script_pattern, response):
        """
        Add a predefined response for a script pattern.
        
        Args:
            script_pattern (str): A substring that identifies the script
            response (dict): The response to return for matching scripts
        """
        self.responses[script_pattern] = response


class MockFileSystem:
    """
    Mock for file system operations.
    
    This class provides mocks for file operations like reading, writing, and listing
    directories to allow for testing without actual file system access.
    """
    
    def __init__(self, files=None, directories=None):
        """
        Initialize the mock file system with optional predefined files and directories.
        
        Args:
            files (dict, optional): A mapping of file paths to file contents.
            directories (dict, optional): A mapping of directory paths to lists of entries.
        """
        self.files = files or {}
        self.directories = directories or {}
        self.operations = []
    
    def read_file(self, path, encoding="utf-8"):
        """
        Mock file reading operation.
        
        Args:
            path (str): Path to the file
            encoding (str, optional): Text encoding to use
            
        Returns:
            dict: A response with the file content or an error
        """
        self.operations.append(("read", path, encoding))
        
        if path in self.files:
            return {
                "success": True,
                "content": self.files[path],
                "path": path,
                "encoding": encoding
            }
        else:
            return {
                "success": False,
                "error": f"File not found: {path}",
                "path": path,
                "encoding": encoding
            }
    
    def write_file(self, path, content, encoding="utf-8"):
        """
        Mock file writing operation.
        
        Args:
            path (str): Path to the file
            content (str): Content to write
            encoding (str, optional): Text encoding to use
            
        Returns:
            dict: A response indicating success or failure
        """
        self.operations.append(("write", path, content, encoding))
        self.files[path] = content
        
        return {
            "success": True,
            "bytes_written": len(content),
            "path": path
        }
    
    def list_directory(self, path):
        """
        Mock directory listing operation.
        
        Args:
            path (str): Path to the directory
            
        Returns:
            dict: A response with directory entries or an error
        """
        self.operations.append(("list", path))
        
        if path in self.directories:
            return {
                "success": True,
                "entries": self.directories[path],
                "path": path,
                "count": len(self.directories[path])
            }
        else:
            return {
                "success": False,
                "error": f"Directory not found: {path}",
                "path": path
            }
