"""
Reminders Management Module for LocalToolKit

This module provides tools for accessing the macOS Reminders app to list and manage reminders.
"""

from typing import Dict, Any
from fastmcp import FastMCP

# Import the registration functions from each module
from .list_reminder_lists import register_to_mcp as register_list_reminder_lists
from .list_reminders import register_to_mcp as register_list_reminders
from .create_reminder import register_to_mcp as register_create_reminder
from .update_reminder import register_to_mcp as register_update_reminder
from .complete_reminder import register_to_mcp as register_complete_reminder
from .delete_reminder import register_to_mcp as register_delete_reminder
from .create_reminder_list import register_to_mcp as register_create_reminder_list

def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register reminders management tools with the MCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    # Register all reminders management tools
    register_list_reminder_lists(mcp)
    register_list_reminders(mcp)
    register_create_reminder(mcp)
    register_update_reminder(mcp)
    register_complete_reminder(mcp)
    register_delete_reminder(mcp)
    register_create_reminder_list(mcp)

__all__ = ["register_to_mcp"]