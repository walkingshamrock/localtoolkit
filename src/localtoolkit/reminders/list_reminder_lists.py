"""
Implementation of list_reminder_lists for the Reminders app.

This module provides functionality to list all available reminder lists 
in the macOS Reminders app with accurate counts.
"""

from typing import Dict, Any
from fastmcp import FastMCP
from localtoolkit.reminders.utils.reminders_utils import get_reminder_lists
import time

def list_reminder_lists_logic(sort_by: str = "name") -> Dict[str, Any]:
    """
    List all available reminder lists in the macOS Reminders app.
    
    Args:
        sort_by: Field to sort the reminder lists by (default: "name")
                 Valid options are "name" and "id"
    
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,  # True if operation was successful
            "data": [         # Array of reminder list objects
                {
                    "name": str,  # Name of the reminder list
                    "id": str     # Unique ID of the reminder list
                },
                ...
            ],
            "message": str,   # Success or error message
            "metadata": {     # Additional metadata
                "count": int,          # Total number of reminder lists
                "execution_time_ms": int,  # Execution time in milliseconds
                "sort_by": str        # Field used for sorting
            },
            "error": str      # Error details, only present if success is False
        }
    """
    start_time = time.time()
    
    # Validate sorting parameter
    valid_sort_fields = ["name", "id"]
    if sort_by not in valid_sort_fields:
        return {
            "success": False,
            "data": None,
            "message": f"Invalid sort_by parameter: '{sort_by}'",
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "valid_sort_fields": valid_sort_fields
            },
            "error": f"sort_by must be one of {valid_sort_fields}"
        }
    
    # Get all reminder lists
    result = get_reminder_lists()
    
    # Calculate execution time
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    # If there was an error, return error response
    if not result["success"]:
        return {
            "success": False,
            "data": None,
            "message": "Failed to retrieve reminder lists",
            "metadata": {
                "execution_time_ms": execution_time_ms
            },
            "error": result.get("error", "Unknown error retrieving reminder lists")
        }
    
    # Build response with the lists
    reminder_lists = result["data"]
    
    # Handle empty list case specifically
    if not reminder_lists:
        return {
            "success": True,
            "data": [],
            "message": "No reminder lists found",
            "metadata": {
                "count": 0,
                "execution_time_ms": execution_time_ms,
                "sort_by": sort_by
            },
            "error": None
        }
    
    try:
        # Properly count the actual number of lists
        actual_count = len(reminder_lists)
        
        # Sort the lists according to the sort_by parameter
        sorted_lists = sorted(reminder_lists, key=lambda x: x.get(sort_by, ""))
    except Exception as e:
        # Fallback to unsorted if sorting fails
        sorted_lists = reminder_lists
        actual_count = len(reminder_lists)
        print(f"Warning: Failed to sort reminder lists: {str(e)}")
    
    return {
        "success": True,
        "data": sorted_lists,
        "message": f"Successfully retrieved {actual_count} reminder lists",
        "metadata": {
            "count": actual_count,
            "execution_time_ms": execution_time_ms,
            "sort_by": sort_by
        },
        "error": None
    }


def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the list_reminder_lists tool to the FastMCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    @mcp.tool()
    def reminders_list_reminder_lists(sort_by: str = "name") -> Dict[str, Any]:
        """
        List all available reminder lists in the macOS Reminders app.
        
        This endpoint retrieves all reminder lists from the macOS Reminders app
        and allows sorting them by different fields.
        
        Args:
            sort_by: Field to sort the reminder lists by (default: "name")
                     Valid options are "name" and "id"
        
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,  # True if operation was successful
                "data": [         # Array of reminder list objects
                    {
                        "name": str,  # Name of the reminder list
                        "id": str     # Unique ID of the reminder list
                    },
                    ...
                ],
                "message": str,   # Success or error message
                "metadata": {     # Additional metadata
                    "count": int,          # Total number of reminder lists
                    "execution_time_ms": int,  # Execution time in milliseconds
                    "sort_by": str         # Field used for sorting
                },
                "error": str      # Error details, only present if success is False
            }
            
        Example:
            ```python
            # Get all reminder lists sorted by name (default)
            result = reminders_list_reminder_lists()
            
            # Get all reminder lists sorted by ID
            result = reminders_list_reminder_lists(sort_by="id")
            
            # Access individual lists
            for reminder_list in result["data"]:
                print(f"List: {reminder_list['name']}, ID: {reminder_list['id']}")
            ```
        """
        return list_reminder_lists_logic(sort_by)