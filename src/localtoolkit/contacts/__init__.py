"""
Contacts app endpoints for LocalToolKit.

This module provides access to the macOS Contacts app, allowing searching and
retrieving contact information.
"""

from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from localtoolkit.contacts.search_by_name import register_to_mcp as register_contacts_search_by_name
from localtoolkit.contacts.search_by_phone import register_to_mcp as register_contacts_search_by_phone


def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register all contacts app tools to the MCP server.
    
    Args:
        mcp: The FastMCP instance to register tools with
    """
    register_contacts_search_by_name(mcp)
    register_contacts_search_by_phone(mcp)


__all__ = ["register_to_mcp"]