"""
Notes app endpoints for LocalToolKit.

This module provides access to the macOS Notes app, allowing creation,
reading, updating, and listing of notes.
"""

from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from localtoolkit.notes.list_notes import register_to_mcp as register_notes_list_notes
from localtoolkit.notes.create_note import register_to_mcp as register_notes_create_note
from localtoolkit.notes.get_note import register_to_mcp as register_notes_get_note
from localtoolkit.notes.update_note import register_to_mcp as register_notes_update_note


def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register all notes app tools to the MCP server.
    
    Args:
        mcp: The FastMCP instance to register tools with
    """
    register_notes_list_notes(mcp)
    register_notes_create_note(mcp)
    register_notes_get_note(mcp)
    register_notes_update_note(mcp)


__all__ = ["register_to_mcp"]
