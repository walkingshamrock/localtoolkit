"""
Security utilities for the filesystem module.

This module provides functions for validating file access permissions
and logging security events for the filesystem module.
"""

import os
import json
import time
import getpass
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

# Setup logging
logger = logging.getLogger("localtoolkit.filesystem.security")

# Module-level settings with default values
_settings = {
    "allowed_dirs": [],
    "security_log_dir": None,
    "initialized": False
}

def initialize(settings: Dict[str, Any]) -> None:
    """
    Initialize security settings for the filesystem module.
    
    Args:
        settings: Dictionary containing security settings
    """
    global _settings
    
    # Mark as initialized even if empty settings
    _settings["initialized"] = True
    
    # Log the initialization
    logger.info(f"Initializing filesystem security with settings: {settings}")
    
    # Update settings with provided values
    if settings:
        if "allowed_dirs" in settings and settings["allowed_dirs"]:
            # Normalize paths in allowed_dirs
            allowed_dirs = []
            for dir_config in settings["allowed_dirs"]:
                path = dir_config.get("path", "")
                if not path:
                    continue
                    
                # Handle home directory expansion
                if path.startswith("~"):
                    path = os.path.expanduser(path)
                
                # Verify the path exists
                if not os.path.exists(path):
                    logger.warning(f"Allowed directory does not exist: {path}")
                    # Create the directory if its a subdirectory of home
                    if path.startswith(os.path.expanduser("~")):
                        try:
                            os.makedirs(path, exist_ok=True)
                            logger.info(f"Created missing directory: {path}")
                        except Exception as e:
                            logger.error(f"Failed to create directory {path}: {e}")
                            continue
                    else:
                        continue
                
                # Only add the directory if it exists or was created
                if os.path.exists(path):
                    permissions = dir_config.get("permissions", ["read"])
                    allowed_dirs.append({
                        "path": os.path.abspath(path),
                        "permissions": permissions
                    })
                    logger.info(f"Added allowed directory: {path} with permissions {permissions}")
            
            _settings["allowed_dirs"] = allowed_dirs
            
        if "security_log_dir" in settings and settings["security_log_dir"]:
            log_dir = settings["security_log_dir"]
            
            # Handle home directory expansion
            if log_dir.startswith("~"):
                log_dir = os.path.expanduser(log_dir)
                
            # Ensure the log directory exists
            try:
                os.makedirs(log_dir, exist_ok=True)
                _settings["security_log_dir"] = log_dir
                logger.info(f"Security log directory set to: {log_dir}")
            except Exception as e:
                logger.error(f"Failed to create log directory {log_dir}: {e}")
    
    # Log the results
    if not _settings["allowed_dirs"]:
        logger.warning("No allowed directories configured - filesystem access will be severely restricted")
    else:
        logger.info(f"Filesystem security initialized with {len(_settings['allowed_dirs'])} allowed directories")

def validate_path_access(path: str, operation: str) -> Tuple[bool, Optional[str], str]:
    """
    Validate if a path is allowed for the specified operation.
    
    Args:
        path: Path to validate
        operation: Operation to perform (read, write, list, etc.)
        
    Returns:
        Tuple containing:
        - Boolean indicating if access is allowed
        - Safe path (absolute, normalized) or None if not allowed
        - Message describing the validation result
    """
    # Handle empty paths
    if not path:
        return False, None, "Path cannot be empty"
    
    # Handle home directory expansion
    if path.startswith("~"):
        path = os.path.expanduser(path)
    
    # Convert to absolute path
    try:
        abs_path = os.path.abspath(path)
    except Exception as e:
        return False, None, f"Invalid path format: {path} - {str(e)}"
    
    # Check if we have any allowed directories
    if not _settings.get("allowed_dirs"):
        # Special case: If module is not initialized, use a fallback directory
        if not _settings.get("initialized", False):
            logger.warning("Security module not initialized - using fallback directory")
            # Allow access to the current working directory as fallback
            cwd = os.getcwd()
            if abs_path == cwd or abs_path.startswith(cwd + os.sep):
                return True, abs_path, "Access allowed (fallback directory)"
        
        return False, None, "No allowed directories configured"
    
    # Check if path is in allowed directories
    for allowed_dir in _settings["allowed_dirs"]:
        allowed_path = allowed_dir["path"]
        permissions = allowed_dir["permissions"]
        
        if abs_path == allowed_path or abs_path.startswith(allowed_path + os.sep):
            if operation in permissions:
                return True, abs_path, "Access allowed"
            else:
                return False, None, f"Operation \"{operation}\" not allowed for path: {path}"
    
    return False, None, f"Path not in allowed directories: {path}"

def log_security_event(operation: str, path: str, success: bool, message: str) -> None:
    """
    Log a security event to the security log.
    
    Args:
        operation: Operation being performed
        path: Path being accessed
        success: Whether the operation was successful
        message: Description or error message
    """
    # Always log to the application logger
    if success:
        logger.info(f"{operation} - {path} - {message}")
    else:
        logger.warning(f"{operation} - {path} - {message}")
    
    # Skip file logging if no log directory configured
    if not _settings.get("security_log_dir"):
        return
    
    try:
        # Create log entry
        timestamp = datetime.now().isoformat()
        username = getpass.getuser()
        
        log_entry = {
            "timestamp": timestamp,
            "operation": operation,
            "path": path,
            "success": success,
            "message": message,
            "user": username
        }
        
        # Write to log file
        log_dir = _settings["security_log_dir"]
        log_file = os.path.join(log_dir, "filesystem_security.log")
        
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        # Note: We intentionally swallow errors in logging to prevent
        # logging failures from affecting the main functionality
        logger.error(f"Failed to write security log: {e}")