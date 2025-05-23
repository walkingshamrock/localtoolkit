"""
Implementation of create_event for the Calendar app.

This module provides functionality to create new events in a specific calendar
in the macOS Calendar app.
"""

from typing import Dict, Any, Optional
from fastmcp import FastMCP
from localtoolkit.calendar.utils.calendar_utils import create_event
import time

def create_event_logic(calendar_id: str, summary: str, start_date: str, end_date: str,
                      location: Optional[str] = None, description: Optional[str] = None,
                      all_day: bool = False) -> Dict[str, Any]:
    """
    Create a new event in a specific calendar in the macOS Calendar app.
    
    Args:
        calendar_id: ID of the calendar to create the event in
        summary: The title/summary of the event
        start_date: Start date and time (ISO format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD for all-day)
        end_date: End date and time (ISO format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD for all-day)
        location: Optional location for the event
        description: Optional description for the event
        all_day: Whether this is an all-day event (default: False)
    
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,  # True if operation was successful
            "data": {         # Created event information
                "event_id": str,    # ID of the created event
                "summary": str,     # Title of the event
                "start_date": str,  # Start date and time
                "end_date": str,    # End date and time
                "location": str,    # Location (if provided)
                "description": str, # Description (if provided)
                "all_day": bool,    # All-day flag
                "calendar_id": str  # Calendar ID
            },
            "message": str,   # Success or error message
            "metadata": {     # Additional metadata
                "execution_time_ms": int,  # Execution time in milliseconds
                "calendar_id": str        # ID of the calendar
            },
            "error": str      # Error details, only present if success is False
        }
    """
    start_time = time.time()
    
    # Validate required parameters
    if not calendar_id:
        return {
            "success": False,
            "data": None,
            "message": "calendar_id is required",
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            },
            "error": "calendar_id parameter cannot be empty"
        }
    
    if not summary:
        return {
            "success": False,
            "data": None,
            "message": "summary is required",
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "calendar_id": calendar_id
            },
            "error": "summary parameter cannot be empty"
        }
    
    if not start_date:
        return {
            "success": False,
            "data": None,
            "message": "start_date is required",
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "calendar_id": calendar_id
            },
            "error": "start_date parameter cannot be empty"
        }
    
    if not end_date:
        return {
            "success": False,
            "data": None,
            "message": "end_date is required",
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "calendar_id": calendar_id
            },
            "error": "end_date parameter cannot be empty"
        }
    
    # Create the event
    result = create_event(
        calendar_id=calendar_id,
        summary=summary,
        start_date=start_date,
        end_date=end_date,
        location=location,
        description=description,
        all_day=all_day
    )
    
    # Calculate execution time
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    # If there was an error, return error response
    if not result["success"]:
        return {
            "success": False,
            "data": None,
            "message": f"Failed to create event in calendar ID: {calendar_id}",
            "metadata": {
                "execution_time_ms": execution_time_ms,
                "calendar_id": calendar_id
            },
            "error": result.get("error", f"Unknown error creating event in calendar ID: {calendar_id}")
        }
    
    # Build successful response
    event_data = {
        "event_id": result["data"].get("event_id", ""),
        "summary": summary,
        "start_date": start_date,
        "end_date": end_date,
        "location": location or "",
        "description": description or "",
        "all_day": all_day,
        "calendar_id": calendar_id
    }
    
    return {
        "success": True,
        "data": event_data,
        "message": f"Successfully created event '{summary}' in calendar ID: {calendar_id}",
        "metadata": {
            "execution_time_ms": execution_time_ms,
            "calendar_id": calendar_id
        }
    }

def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the create_event tool to the FastMCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    @mcp.tool()
    def calendar_create_event(
        calendar_id: str,
        summary: str,
        start_date: str,
        end_date: str,
        location: Optional[str] = None,
        description: Optional[str] = None,
        all_day: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new event in a specific calendar in the macOS Calendar app.
        
        This endpoint creates a new event in the specified calendar with the provided details.
        
        Args:
            calendar_id: ID of the calendar to create the event in (obtain from calendar_list_calendars)
            summary: The title/summary of the event
            start_date: Start date and time (ISO format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD for all-day)
            end_date: End date and time (ISO format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD for all-day)
            location: Optional location for the event
            description: Optional description for the event
            all_day: Whether this is an all-day event (default: False)
        
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,  # True if operation was successful
                "data": {         # Created event information
                    "event_id": str,    # ID of the created event
                    "summary": str,     # Title of the event
                    "start_date": str,  # Start date and time
                    "end_date": str,    # End date and time
                    "location": str,    # Location (if provided)
                    "description": str, # Description (if provided)
                    "all_day": bool,    # All-day flag
                    "calendar_id": str  # Calendar ID
                },
                "message": str,   # Success or error message
                "metadata": {     # Additional metadata
                    "execution_time_ms": int,  # Execution time in milliseconds
                    "calendar_id": str        # ID of the calendar
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
                
                # Create a simple event
                result = calendar_create_event(
                    calendar_id=calendar_id,
                    summary="Team Meeting",
                    start_date="2024-01-15T10:00:00",
                    end_date="2024-01-15T11:00:00"
                )
                
                # Create an all-day event
                all_day_event = calendar_create_event(
                    calendar_id=calendar_id,
                    summary="Vacation Day",
                    start_date="2024-01-20",
                    end_date="2024-01-20",
                    all_day=True
                )
                
                # Create a detailed event
                detailed_event = calendar_create_event(
                    calendar_id=calendar_id,
                    summary="Project Review",
                    start_date="2024-01-16T14:00:00",
                    end_date="2024-01-16T15:30:00",
                    location="Conference Room A",
                    description="Quarterly project review meeting"
                )
            ```
        """
        return create_event_logic(calendar_id, summary, start_date, end_date, location, description, all_day)