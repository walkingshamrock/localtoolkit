"""
AppleScript module for LocalToolkit.

This module provides the applescript_run_code endpoint for executing
AppleScript code in a safe, standardized way.
"""
from fastmcp import FastMCP
from typing import Optional, Any, List, Dict, Union, Literal

from localtoolkit.applescript.run_code import register_to_mcp as register_applescript_run_code

def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register AppleScript tools with the MCP server.
    
    Args:
        mcp_server: The MCP server instance to register tools with
    """
    register_applescript_run_code(mcp)

        
__all__ = [
    "register_to_mcp",
]