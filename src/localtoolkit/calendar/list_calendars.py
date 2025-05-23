"""
Implementation of list_calendars for the Calendar app.

This module provides functionality to list all available calendars 
in the macOS Calendar app.
"""

from typing import Dict, Any
from fastmcp import FastMCP
from localtoolkit.calendar.utils.calendar_utils import get_calendars
import time

def list_calendars_logic(sort_by: str = "name") -> Dict[str, Any]:
    """
    List all available calendars in the macOS Calendar app.
    
    Args:
        sort_by: Field to sort the calendars by (default: "name")
                 Valid options are "name", "id", and "type"
    
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,  # True if operation was successful
            "data": [         # Array of calendar objects
                {
                    "name": str,        # Name of the calendar
                    "id": str,          # Unique ID of the calendar
                    "description": str, # Description of the calendar
                    "color": str,       # Color of the calendar
                    "type": str         # Type of calendar (local, iCloud, etc.)
                },
                ...
            ],
            "message": str,   # Success or error message
            "metadata": {     # Additional metadata
                "count": int,          # Total number of calendars
                "execution_time_ms": int,  # Execution time in milliseconds
                "sort_by": str        # Field used for sorting
            },
            "error": str      # Error details, only present if success is False
        }
    """
    start_time = time.time()
    
    # Validate sorting parameter
    valid_sort_fields = ["name", "id", "type"]
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
    
    # Get all calendars
    result = get_calendars()
    
    # Calculate execution time
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    # If there was an error, return error response
    if not result["success"]:
        return {
            "success": False,
            "data": None,
            "message": "Failed to retrieve calendars",
            "metadata": {
                "execution_time_ms": execution_time_ms
            },
            "error": result.get("error", "Unknown error retrieving calendars")
        }
    
    # Build response with the calendars
    calendars = result["data"]
    
    # Handle empty list case specifically
    if not calendars:
        return {
            "success": True,
            "data": [],
            "message": "No calendars found",
            "metadata": {
                "count": 0,
                "execution_time_ms": execution_time_ms,
                "sort_by": sort_by
            },
            "error": None
        }
    
    try:
        # Properly count the actual number of calendars
        actual_count = len(calendars)
        
        # Sort the calendars according to the sort_by parameter
        # Handle None values by converting to empty string for sorting
        sorted_calendars = sorted(calendars, key=lambda x: str(x.get(sort_by, "") or ""))
    except Exception as e:
        # Fallback to unsorted if sorting fails
        sorted_calendars = calendars
        actual_count = len(calendars)
        print(f"Warning: Failed to sort calendars: {str(e)}")
    
    return {
        "success": True,
        "data": sorted_calendars,
        "message": f"Successfully retrieved {actual_count} calendars",
        "metadata": {
            "count": actual_count,
            "execution_time_ms": execution_time_ms,
            "sort_by": sort_by
        },
        "error": None
    }


def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the list_calendars tool to the FastMCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    @mcp.tool()
    def calendar_list_calendars(sort_by: str = "name") -> Dict[str, Any]:
        """
        List all available calendars in the macOS Calendar app.
        
        This endpoint retrieves all calendars from the macOS Calendar app
        and allows sorting them by different fields.
        
        Args:
            sort_by: Field to sort the calendars by (default: "name")
                     Valid options are "name", "id", and "type"
        
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,  # True if operation was successful
                "data": [         # Array of calendar objects
                    {
                        "name": str,        # Name of the calendar
                        "id": str,          # Unique ID of the calendar
                        "description": str, # Description of the calendar
                        "color": str,       # Color of the calendar
                        "type": str         # Type of calendar (local, iCloud, etc.)
                    },
                    ...
                ],
                "message": str,   # Success or error message
                "metadata": {     # Additional metadata
                    "count": int,          # Total number of calendars
                    "execution_time_ms": int,  # Execution time in milliseconds
                    "sort_by": str         # Field used for sorting
                },
                "error": str      # Error details, only present if success is False
            }
            
        Example:
            ```python
            # Get all calendars sorted by name (default)
            result = calendar_list_calendars()
            
            # Get all calendars sorted by type
            result = calendar_list_calendars(sort_by="type")
            
            # Access individual calendars
            for calendar in result["data"]:
                print(f"Calendar: {calendar['name']}, ID: {calendar['id']}")
            ```
        """
        return list_calendars_logic(sort_by)