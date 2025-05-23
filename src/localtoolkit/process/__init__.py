"""
Process Management Module for LocalToolKit

This module provides tools for starting, monitoring, and stopping macOS processes.
"""

from typing import Dict, Any, Optional, List
from fastmcp import FastMCP

# Import the registration functions from each module
from .list_processes import register_to_mcp as register_list_processes
from .start_process import register_to_mcp as register_start_process
from .terminate_process import register_to_mcp as register_terminate_process
from .get_process_info import register_to_mcp as register_get_process_info
from .monitor_process import register_to_mcp as register_monitor_process

def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register process management tools with the MCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    # Register all process management tools
    register_list_processes(mcp)
    register_start_process(mcp)
    register_terminate_process(mcp)
    register_get_process_info(mcp)
    register_monitor_process(mcp)

__all__ = ["register_to_mcp"]
