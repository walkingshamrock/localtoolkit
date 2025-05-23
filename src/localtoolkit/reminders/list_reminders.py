"""
Implementation of list_reminders for the Reminders app.

This module provides functionality to list all reminders in a specific list
in the macOS Reminders app.
"""

from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from localtoolkit.reminders.utils.reminders_utils import get_reminders
import time

def list_reminders_logic(list_id: str, show_completed: bool = True, sort_by: str = "title", limit: int = 50) -> Dict[str, Any]:
    """
    List all reminders in a specific list in the macOS Reminders app.
    
    Args:
        list_id: ID of the reminder list to get reminders from
        show_completed: Whether to include completed reminders (default: True)
        sort_by: Field to sort the reminders by (default: "title")
                 Valid options are "title", "due_date", "priority", and "completed"
        limit: Maximum number of reminders to return (default: 50)
    
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,  # True if operation was successful
            "data": [         # Array of reminder objects
                {
                    "title": str,     # Title of the reminder
                    "id": str,        # Unique ID of the reminder
                    "completed": bool,  # Whether the reminder is completed
                    "due_date": str,  # Due date of the reminder (ISO 8601 format)
                    "notes": str,     # Notes associated with the reminder
                    "priority": int,  # Priority (0=high, 5=medium, 9=low, null=none)
                    "list_id": str    # ID of the list this reminder belongs to
                },
                ...
            ],
            "message": str,   # Success or error message
            "metadata": {     # Additional metadata                    "count": int,          # Total number of reminders in the list
                    "incomplete_count": int, # Number of incomplete reminders
                    "execution_time_ms": int,  # Execution time in milliseconds
                    "sort_by": str,       # Field used for sorting
                    "list_id": str        # ID of the list
            },
            "error": str      # Error details, only present if success is False
        }
    """
    start_time = time.time()
    
    # Validate sorting parameter
    valid_sort_fields = ["title", "due_date", "priority", "completed"]
    if sort_by not in valid_sort_fields:
        return {
            "success": False,
            "data": None,
            "message": f"Invalid sort_by parameter: '{sort_by}'",
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "valid_sort_fields": valid_sort_fields,
                "list_id": list_id
            },
            "error": f"sort_by must be one of {valid_sort_fields}"
        }
    
    # Get reminders from the specified list
    # Note: We get all reminders and filter in Python for now due to AppleScript complexity
    result = get_reminders(list_id, limit=limit if show_completed else limit * 2)
    
    # Calculate execution time
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    # If there was an error, return error response
    if not result["success"]:
        return {
            "success": False,
            "data": None,
            "message": f"Failed to retrieve reminders from list ID: {list_id}",
            "metadata": {
                "execution_time_ms": execution_time_ms,
                "list_id": list_id
            },
            "error": result.get("error", f"Unknown error retrieving reminders from list ID: {list_id}")
        }
    
    # Build response with the reminders
    reminders = result["data"]
    
    # Ensure reminders is a list
    if not isinstance(reminders, list):
        return {
            "success": False,
            "data": None,
            "message": f"Invalid response format from reminders query",
            "metadata": {
                "execution_time_ms": execution_time_ms,
                "list_id": list_id
            },
            "error": f"Expected list of reminders but got {type(reminders).__name__}"
        }
    
    # Handle empty list case specifically
    if not reminders:
        return {
            "success": True,
            "data": [],
            "message": f"No reminders found in list ID: {list_id}",
            "metadata": {
                "count": 0,
                "incomplete_count": 0,
                "execution_time_ms": execution_time_ms,
                "sort_by": sort_by,
                "list_id": list_id,
                "show_completed": show_completed
            }
        }
    
    # Filter out completed reminders if show_completed is False
    if not show_completed:
        reminders = [r for r in reminders if not r.get("completed", False)]
    
    # Single pass for counting incomplete items
    incomplete_count = 0
    for reminder in reminders:
        if not reminder.get("completed", False):
            incomplete_count += 1
    
    # Efficient sorting with proper null handling
    sort_keys = {
        "title": lambda x: (x.get("title") or "").lower(),
        "due_date": lambda x: x.get("due_date") or "9999-12-31",  # Nulls sort last
        "priority": lambda x: x.get("priority") if x.get("priority") is not None else 999,
        "completed": lambda x: x.get("completed", False)
    }
    
    try:
        sorted_reminders = sorted(reminders, key=sort_keys[sort_by])
    except Exception as e:
        # Fallback to unsorted if sorting fails
        sorted_reminders = reminders
        print(f"Warning: Failed to sort reminders: {str(e)}")
    
    total_count = len(sorted_reminders)
    
    return {
        "success": True,
        "data": sorted_reminders,
        "message": f"Successfully retrieved {total_count} reminders from list ID: {list_id}",
        "metadata": {
            "count": total_count,
            "incomplete_count": incomplete_count,
            "execution_time_ms": execution_time_ms,
            "sort_by": sort_by,
            "list_id": list_id,
            "show_completed": show_completed
        }
    }

def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the list_reminders tool to the FastMCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    @mcp.tool()
    def reminders_list_reminders(
        list_id: str, 
        show_completed: bool = True, 
        sort_by: str = "title",
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List all reminders in a specific list in the macOS Reminders app.
        
        This endpoint retrieves all reminders from a specific list in the macOS Reminders app
        and allows filtering and sorting them.
        
        Args:
            list_id: ID of the reminder list to get reminders from (obtain from list_reminder_lists)
            show_completed: Whether to include completed reminders (default: True)
            sort_by: Field to sort the reminders by (default: "title")
                     Valid options are "title", "due_date", "priority", and "completed"
            limit: Maximum number of reminders to return (default: 50)
        
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,  # True if operation was successful
                "data": [         # Array of reminder objects
                    {
                        "title": str,     # Title of the reminder
                        "id": str,        # Unique ID of the reminder
                        "completed": bool,  # Whether the reminder is completed
                        "list_id": str    # ID of the list this reminder belongs to
                    },
                    ...
                ],
                "message": str,   # Success or error message
                "metadata": {    # Additional metadata
                    "count": int,          # Total number of reminders returned
                    "incomplete_count": int, # Number of incomplete reminders
                    "execution_time_ms": int,  # Execution time in milliseconds
                    "sort_by": str,       # Field used for sorting
                    "list_id": str,       # ID of the list
                    "show_completed": bool # Whether completed items are included
                },
                "error": str      # Error details, only present if success is False
            }
            
        Example:
            ```python
            # First get available lists
            lists = reminders_list_reminder_lists()
            
            # Choose a list ID
            if lists["success"] and lists["data"]:
                list_id = lists["data"][0]["id"]
                
                # Get all reminders in the list
                result = reminders_list_reminders(list_id)
                
                # Get only incomplete reminders
                incomplete = reminders_list_reminders(list_id, show_completed=False)
                
                # Get reminders sorted by completed status
                sorted_by_status = reminders_list_reminders(list_id, sort_by="completed")
            ```
        """
        return list_reminders_logic(list_id, show_completed, sort_by, limit)