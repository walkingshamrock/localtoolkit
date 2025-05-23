"""
Create reminder list endpoint for LocalToolKit.

This module provides functionality to create new reminder lists in the macOS Reminders app.
"""

from typing import Dict, Any
from fastmcp import FastMCP
from localtoolkit.applescript.utils.applescript_runner import applescript_execute


def create_reminder_list_logic(name: str) -> Dict[str, Any]:
    """
    Create a new reminder list in the Reminders app.
    
    Args:
        name: Name of the reminder list to create
        
    Returns:
        Dictionary with creation result and list details
    """
    if not name:
        return {
            "success": False,
            "error": "name is required",
            "message": "Failed to create reminder list: missing required parameter"
        }
    
    # Escape quotes in the name
    escaped_name = name.replace('"', '\\"').replace('\\', '\\\\')
    
    # Build AppleScript for creating reminder list
    script = f"""
    tell application "Reminders"
        try
            -- Create the new list
            set newList to make new list with properties {{name:"{escaped_name}"}}
            
            -- Get the details of the newly created list
            set listId to id of newList as string
            set listName to name of newList
            
            -- Build JSON response
            set jsonResult to "{{\\"name\\":\\""
            set jsonResult to jsonResult & listName & "\\",\\"id\\":\\""
            set jsonResult to jsonResult & listId & "\\"}}"
            
            return jsonResult
            
        on error errMsg
            return "ERROR: " & errMsg
        end try
    end tell
    """
    
    try:
        response = applescript_execute(script, timeout=15)
        
        # Check for error string in response data
        if response["success"] and isinstance(response["data"], str) and response["data"].startswith("ERROR:"):
            return {
                "success": False,
                "error": response["data"].replace("ERROR: ", "", 1),
                "message": "Failed to create reminder list"
            }
        
        if response["success"]:
            return {
                "success": True,
                "data": response["data"],
                "message": f"Successfully created reminder list '{name}'"
            }
        else:
            return {
                "success": False,
                "error": response.get("error", "Unknown error"),
                "message": "Failed to create reminder list"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create reminder list due to unexpected error"
        }


def reminders_create_reminder_list(name: str) -> Dict[str, Any]:
    """
    Create a new reminder list in the Reminders app.
    
    Args:
        name: Name of the reminder list to create
        
    Returns:
        Dictionary with creation result and list details
    """
    return create_reminder_list_logic(name)


def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the create reminder list tool to the MCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    @mcp.tool("reminders_create_reminder_list")
    def create_reminder_list_tool(name: str) -> Dict[str, Any]:
        """
        Create a new reminder list in the Reminders app.
        
        Args:
            name: Name of the reminder list to create
            
        Returns:
            Dictionary with creation result and list details
        """
        return reminders_create_reminder_list(name)
