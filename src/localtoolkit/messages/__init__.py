"""
Messages app integration for localtoolkit.

This module provides functionality for interacting with the macOS Messages app.
"""

from typing import Dict, Any, Optional
from fastmcp import FastMCP
from localtoolkit.messages.list_conversations import list_conversations_logic
from localtoolkit.messages.get_messages import register_to_mcp as register_messages_get_messages
from localtoolkit.messages.list_conversations import register_to_mcp as register_messages_list_conversations
from localtoolkit.messages.send_message import register_to_mcp as register_messages_send_message

def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the Messages app tools to the FastMCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    # Define the Messages app tools
    register_messages_get_messages(mcp)
    register_messages_list_conversations(mcp)
    register_messages_send_message(mcp)

__all__ = [
    "register_to_mcp",
]
