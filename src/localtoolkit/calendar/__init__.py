"""
Calendar Management Module for LocalToolKit

This module provides tools for accessing the macOS Calendar app to list calendars,
view events, and create new events.
"""

from typing import Dict, Any
from fastmcp import FastMCP

# Import the registration functions from each module
from .list_calendars import register_to_mcp as register_list_calendars
from .list_events import register_to_mcp as register_list_events
from .create_event import register_to_mcp as register_create_event

def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register calendar management tools with the MCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    # Register all calendar management tools
    register_list_calendars(mcp)
    register_list_events(mcp)
    register_create_event(mcp)

__all__ = ["register_to_mcp"]