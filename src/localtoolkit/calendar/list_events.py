"""
Implementation of list_events for the Calendar app.

This module provides functionality to list all events in a specific calendar
in the macOS Calendar app.
"""

from typing import Dict, Any, Optional
from fastmcp import FastMCP
from localtoolkit.calendar.utils.calendar_utils import get_events
import time

def list_events_logic(calendar_id: str, start_date: Optional[str] = None, 
                     end_date: Optional[str] = None, limit: int = 50, 
                     sort_by: str = "start_date") -> Dict[str, Any]:
    """
    List all events in a specific calendar in the macOS Calendar app.
    
    Args:
        calendar_id: ID of the calendar to get events from
        start_date: Start date for filtering events (ISO format: YYYY-MM-DD)
        end_date: End date for filtering events (ISO format: YYYY-MM-DD)
        limit: Maximum number of events to return (default: 50)
        sort_by: Field to sort the events by (default: "start_date")
                 Valid options are "start_date", "summary", "end_date"
    
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,  # True if operation was successful
            "data": [         # Array of event objects
                {
                    "id": str,          # Unique ID of the event
                    "summary": str,     # Title of the event
                    "start_date": str,  # Start date and time (ISO format)
                    "end_date": str,    # End date and time (ISO format)
                    "location": str,    # Location of the event
                    "description": str, # Description of the event
                    "all_day": bool,    # Whether this is an all-day event
                    "calendar_id": str  # ID of the calendar this event belongs to
                },
                ...
            ],
            "message": str,   # Success or error message
            "metadata": {     # Additional metadata
                "count": int,          # Total number of events returned
                "execution_time_ms": int,  # Execution time in milliseconds
                "sort_by": str,       # Field used for sorting
                "calendar_id": str,   # ID of the calendar
                "start_date": str,    # Start date filter (if used)
                "end_date": str,      # End date filter (if used)
                "limit": int          # Maximum number of events requested
            },
            "error": str      # Error details, only present if success is False
        }
    """
    start_time = time.time()
    
    # Validate sorting parameter
    valid_sort_fields = ["start_date", "summary", "end_date"]
    if sort_by not in valid_sort_fields:
        return {
            "success": False,
            "data": None,
            "message": f"Invalid sort_by parameter: '{sort_by}'",
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "valid_sort_fields": valid_sort_fields,
                "calendar_id": calendar_id
            },
            "error": f"sort_by must be one of {valid_sort_fields}"
        }
    
    # Get events from the specified calendar
    result = get_events(calendar_id, start_date=start_date, end_date=end_date, limit=limit)
    
    # Calculate execution time
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    # If there was an error, return error response
    if not result["success"]:
        return {
            "success": False,
            "data": None,
            "message": f"Failed to retrieve events from calendar ID: {calendar_id}",
            "metadata": {
                "execution_time_ms": execution_time_ms,
                "calendar_id": calendar_id
            },
            "error": result.get("error", f"Unknown error retrieving events from calendar ID: {calendar_id}")
        }
    
    # Build response with the events
    events = result["data"]
    
    # Handle empty list case specifically
    if not events:
        return {
            "success": True,
            "data": [],
            "message": f"No events found in calendar ID: {calendar_id}",
            "metadata": {
                "count": 0,
                "execution_time_ms": execution_time_ms,
                "sort_by": sort_by,
                "calendar_id": calendar_id,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit
            }
        }
    
    try:
        # Sort the events according to the sort_by parameter
        if sort_by == "start_date" or sort_by == "end_date":
            # Sort by date fields
            sorted_events = sorted(events, key=lambda x: x.get(sort_by, ""))
        else:
            # Sort by text fields
            sorted_events = sorted(events, key=lambda x: x.get(sort_by, "").lower())
        
        # Total event count
        total_count = len(sorted_events)
        
    except Exception as e:
        # Fallback to unsorted if sorting fails
        sorted_events = events
        total_count = len(events)
        print(f"Warning: Failed to sort events: {str(e)}")
    
    return {
        "success": True,
        "data": sorted_events,
        "message": f"Successfully retrieved {total_count} events from calendar ID: {calendar_id}",
        "metadata": {
            "count": total_count,
            "execution_time_ms": execution_time_ms,
            "sort_by": sort_by,
            "calendar_id": calendar_id,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit
        }
    }

def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the list_events tool to the FastMCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    @mcp.tool()
    def calendar_list_events(
        calendar_id: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
        sort_by: str = "start_date"
    ) -> Dict[str, Any]:
        """
        List all events in a specific calendar in the macOS Calendar app.
        
        This endpoint retrieves all events from a specific calendar in the macOS Calendar app
        and allows filtering by date range and sorting them.
        
        Args:
            calendar_id: ID of the calendar to get events from (obtain from calendar_list_calendars)
            start_date: Start date for filtering events (ISO format: YYYY-MM-DD, optional)
            end_date: End date for filtering events (ISO format: YYYY-MM-DD, optional)
            limit: Maximum number of events to return (default: 50)
            sort_by: Field to sort the events by (default: "start_date")
                     Valid options are "start_date", "summary", "end_date"
        
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,  # True if operation was successful
                "data": [         # Array of event objects
                    {
                        "id": str,          # Unique ID of the event
                        "summary": str,     # Title of the event
                        "start_date": str,  # Start date and time (ISO format)
                        "end_date": str,    # End date and time (ISO format)
                        "location": str,    # Location of the event
                        "description": str, # Description of the event
                        "all_day": bool,    # Whether this is an all-day event
                        "calendar_id": str  # ID of the calendar this event belongs to
                    },
                    ...
                ],
                "message": str,   # Success or error message
                "metadata": {    # Additional metadata
                    "count": int,          # Total number of events returned
                    "execution_time_ms": int,  # Execution time in milliseconds
                    "sort_by": str,       # Field used for sorting
                    "calendar_id": str,   # ID of the calendar
                    "start_date": str,    # Start date filter (if used)
                    "end_date": str,      # End date filter (if used)
                    "limit": int          # Maximum number of events requested
                },
                "error": str      # Error details, only present if success is False
            }
            
        Example:
            ```python
            # First get available calendars
            calendars = calendar_list_calendars()
            
            # Choose a calendar ID
            if calendars["success"] and calendars["data"]:
                calendar_id = calendars["data"][0]["id"]
                
                # Get all events in the calendar
                result = calendar_list_events(calendar_id)
                
                # Get events for a specific date range
                today_events = calendar_list_events(
                    calendar_id, 
                    start_date="2024-01-15", 
                    end_date="2024-01-15"
                )
                
                # Get events sorted by title
                sorted_events = calendar_list_events(calendar_id, sort_by="summary")
            ```
        """
        return list_events_logic(calendar_id, start_date, end_date, limit, sort_by)