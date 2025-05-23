"""
Filesystem module for LocalToolKit.

This module provides secure access to the filesystem with appropriate
permissions controls and security logging.
"""

import os
import logging
from typing import Dict, Any, Optional
from fastmcp import FastMCP

from .read_file import register_to_mcp as register_filesystem_read_file
from .write_file import register_to_mcp as register_filesystem_write_file
from .list_directory import register_to_mcp as register_filesystem_list_directory
from .utils import initialize as initialize_security

# Setup logging
logger = logging.getLogger("localtoolkit.filesystem")

# Module-level settings storage
_settings = {}

def register_to_mcp(mcp: FastMCP, settings: Optional[Dict[str, Any]] = None) -> None:
    """
    Register the filesystem tools to the FastMCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
        settings (Dict[str, Any], optional): Configuration settings for the filesystem module.
    """
    global _settings
    
    # Log registration
    logger.info("Registering filesystem module")
    
    # Store settings
    if settings:
        _settings.update(settings)
        logger.info(f"Using provided settings with {len(settings.get('allowed_dirs', []))} allowed directories")
    else:
        logger.warning("No settings provided for filesystem module")
    
    # Initialize security with settings
    initialize_security(_settings)
    
    # Register filesystem tools
    register_filesystem_read_file(mcp)
    register_filesystem_write_file(mcp)
    register_filesystem_list_directory(mcp)
    
    logger.info("Filesystem module registered successfully")

__all__ = [
    "register_to_mcp",
]