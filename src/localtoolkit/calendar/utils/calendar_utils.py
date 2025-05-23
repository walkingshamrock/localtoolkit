"""
Utilities for the Calendar app integration.

This module provides utility functions for interacting with the macOS Calendar app.
"""

import json
from typing import Dict, Any, Optional, List
from localtoolkit.applescript.utils.applescript_runner import applescript_execute

def parse_calendar_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse the response from an AppleScript execution for Calendar operations.
    
    Args:
        response: The response from applescript_execute
        
    Returns:
        A standardized response dictionary
    """
    if not response["success"]:
        return response
    
    return {
        "success": response["success"],
        "data": response["data"],
        "metadata": response.get("metadata", {}),
        "error": response.get("error")
    }

def get_calendars() -> Dict[str, Any]:
    """
    Get all calendars from the Calendar app.
    
    Returns:
        Dictionary with list of calendars or error information
    """
    # Working script that uses calendar names as IDs (since accessing 'id' property fails)
    script = """
    tell application "Calendar"
        try
            set calendarResults to {}
            set allCalendars to calendars
            repeat with i from 1 to count of allCalendars
                set cal to item i of allCalendars
                set calendarName to name of cal
                
                -- Escape quotes in the name for JSON
                set safeName to calendarName
                if safeName contains "\\"" then
                    set AppleScript's text item delimiters to "\\"" 
                    set nameItems to every text item of safeName
                    set AppleScript's text item delimiters to "\\\\\\""
                    set safeName to nameItems as string
                    set AppleScript's text item delimiters to ""
                end if
                
                -- Use name as ID since calendar.id property causes errors
                set theJSON to "{\\"name\\":\\"" & safeName & "\\", \\"id\\":\\"" & safeName
                set theJSON to theJSON & "\\", \\"description\\":\\"\\", \\"color\\":\\"default\\", \\"type\\":\\"calendar\\"}"
                set end of calendarResults to theJSON
                
                -- Add comma if not the last item
                if i < count of allCalendars then
                    set end of calendarResults to ","
                end if
            end repeat
            return "[" & (calendarResults as string) & "]"
        on error errMsg
            return "ERROR: " & errMsg
        end try
    end tell
    """
    
    response = applescript_execute(script)
    
    # Check for error string in response data
    if response["success"] and isinstance(response["data"], str) and response["data"].startswith("ERROR:"):
        response["success"] = False
        response["error"] = response["data"].replace("ERROR: ", "", 1)
        response["data"] = None
    
    # Parse JSON string if needed (for mocked tests)
    if response["success"] and isinstance(response["data"], str):
        try:
            response["data"] = json.loads(response["data"])
        except (json.JSONDecodeError, ValueError):
            # If it's not valid JSON, keep it as string
            pass
    
    return parse_calendar_response(response)

def get_events(calendar_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """
    Get events from a specific calendar in the Calendar app.
    
    Args:
        calendar_id: The name/ID of the calendar to get events from
        start_date: Start date for filtering events (ISO format: YYYY-MM-DD)
        end_date: End date for filtering events (ISO format: YYYY-MM-DD)
        limit: Maximum number of events to return (default: 50)
        
    Returns:
        Dictionary with list of events or error information
    """
    # First check if the calendar exists (calendar_id is actually the calendar name)
    calendars_response = get_calendars()
    if not calendars_response["success"]:
        return {
            "success": False,
            "data": None,
            "error": f"Failed to access calendars: {calendars_response.get('error', 'Unknown error')}"
        }
    
    # Verify the calendar exists
    calendar_exists = False
    calendar_name = calendar_id  # Since we use names as IDs
    for calendar in calendars_response["data"]:
        if calendar["name"] == calendar_id:
            calendar_exists = True
            break
    
    if not calendar_exists:
        return {
            "success": False,
            "data": None,
            "error": f"Calendar with name '{calendar_id}' not found"
        }
    
    # Simplified script that gets basic event information
    calendar_json_part = f'\\"{calendar_name}\\"'
    script = f"""
    tell application "Calendar"
        try
            set theCalendar to calendar "{calendar_name}"
            set eventResults to {{}}
            set allEvents to events of theCalendar
            set counter to 0
            
            -- Limit the number of events processed
            repeat with e in allEvents
                set counter to counter + 1
                if counter > {limit} then exit repeat
                
                -- Get basic event properties
                set eventSummary to summary of e
                set eventStartDate to start date of e
                set eventEndDate to end date of e
                
                -- Simple date formatting (just the date part for now)
                set startYear to year of eventStartDate as string
                set startMonth to month of eventStartDate as integer
                set startDay to day of eventStartDate as string
                
                set endYear to year of eventEndDate as string
                set endMonth to month of eventEndDate as integer  
                set endDay to day of eventEndDate as string
                
                -- Pad single digits
                if startMonth < 10 then set startMonth to "0" & startMonth
                if length of startDay = 1 then set startDay to "0" & startDay
                if endMonth < 10 then set endMonth to "0" & endMonth
                if length of endDay = 1 then set endDay to "0" & endDay
                
                set startDateFormatted to startYear & "-" & startMonth & "-" & startDay & "T00:00:00"
                set endDateFormatted to endYear & "-" & endMonth & "-" & endDay & "T23:59:59"
                
                -- Escape quotes in summary
                set safeSummary to eventSummary
                if safeSummary contains "\\"" then
                    set AppleScript's text item delimiters to "\\"" 
                    set summaryItems to every text item of safeSummary
                    set AppleScript's text item delimiters to "\\\\\\""
                    set safeSummary to summaryItems as string
                    set AppleScript's text item delimiters to ""
                end if
                
                -- Build simplified JSON
                set eventJSON to "{{\\"id\\":\\"" & safeSummary & "-" & counter & "\\""
                set eventJSON to eventJSON & ", \\"summary\\":\\"" & safeSummary & "\\""
                set eventJSON to eventJSON & ", \\"start_date\\":\\"" & startDateFormatted & "\\""
                set eventJSON to eventJSON & ", \\"end_date\\":\\"" & endDateFormatted & "\\""
                set eventJSON to eventJSON & ", \\"location\\":\\"\\""
                set eventJSON to eventJSON & ", \\"description\\":\\"\\""
                set eventJSON to eventJSON & ", \\"all_day\\":false"
                set eventJSON to eventJSON & ", \\"calendar_id\\":" & "{calendar_json_part}" & "}}"
                
                set end of eventResults to eventJSON
                
                -- Add comma if not the last item we'll process
                if counter < {limit} and counter < (count of allEvents) then
                    set end of eventResults to ","
                end if
            end repeat
            
            return "[" & (eventResults as string) & "]"
        on error errMsg
            return "ERROR: " & errMsg
        end try
    end tell
    """
    
    # Use a longer timeout for large event lists
    response = applescript_execute(script, timeout=60)
    
    # Check for error string in response data
    if response["success"] and isinstance(response["data"], str) and response["data"].startswith("ERROR:"):
        response["success"] = False
        response["error"] = response["data"].replace("ERROR: ", "", 1)
        response["data"] = None
    
    # Parse JSON string if needed (for mocked tests)
    if response["success"] and isinstance(response["data"], str):
        try:
            response["data"] = json.loads(response["data"])
        except (json.JSONDecodeError, ValueError):
            # If it's not valid JSON, keep it as string
            pass
    
    return parse_calendar_response(response)

def create_event(calendar_id: str, summary: str, start_date: str, end_date: str, 
                 location: Optional[str] = None, description: Optional[str] = None,
                 all_day: bool = False) -> Dict[str, Any]:
    """
    Create a new event in a specific calendar.
    
    Args:
        calendar_id: The ID of the calendar to create the event in
        summary: The title/summary of the event
        start_date: Start date and time (ISO format: YYYY-MM-DDTHH:MM:SS)
        end_date: End date and time (ISO format: YYYY-MM-DDTHH:MM:SS)
        location: Optional location for the event
        description: Optional description for the event
        all_day: Whether this is an all-day event (default: False)
        
    Returns:
        Dictionary with created event information or error information
    """
    # First check if the calendar ID exists
    calendars_response = get_calendars()
    if not calendars_response["success"]:
        return {
            "success": False,
            "data": None,
            "error": f"Failed to access calendars: {calendars_response.get('error', 'Unknown error')}"
        }
    
    # Verify the calendar exists
    calendar_exists = False
    calendar_name = ""
    for calendar in calendars_response["data"]:
        if calendar["id"] == calendar_id:
            calendar_exists = True
            calendar_name = calendar["name"]
            break
    
    if not calendar_exists:
        return {
            "success": False,
            "data": None,
            "error": f"Calendar with name '{calendar_id}' not found"
        }
    
    # Escape strings for AppleScript
    safe_summary = summary.replace('"', '\\"').replace('\\', '\\\\')
    safe_location = (location or "").replace('"', '\\"').replace('\\', '\\\\')
    safe_description = (description or "").replace('"', '\\"').replace('\\', '\\\\')
    
    script = f'''
    tell application "Calendar"
        set calendarName to "{calendar_name}"
        
        try
            set theCalendar to calendar calendarName
            
            -- Parse dates (simplified for now, assuming ISO format)
            set startDate to date "{start_date}"
            set endDate to date "{end_date}"
            
            -- Create the event
            set newEvent to make new event at end of events of theCalendar
            set summary of newEvent to "{safe_summary}"
            set start date of newEvent to startDate
            set end date of newEvent to endDate
            set allday event of newEvent to {str(all_day).lower()}
            
            if "{safe_location}" is not "" then
                set location of newEvent to "{safe_location}"
            end if
            
            if "{safe_description}" is not "" then
                set description of newEvent to "{safe_description}"
            end if
            
            -- Return the created event info
            set eventId to id of newEvent as string
            return "{{\\"success\\": true, \\"event_id\\": \\"" & eventId & "\\", \\"message\\": \\"Event created successfully\\"}}"
        on error errMsg
            return "ERROR: " & errMsg
        end try
    end tell
    '''
    
    response = applescript_execute(script)
    
    # Check for error string in response data
    if response["success"] and isinstance(response["data"], str) and response["data"].startswith("ERROR:"):
        response["success"] = False
        response["error"] = response["data"].replace("ERROR: ", "", 1)
        response["data"] = None
    
    # Parse JSON string if needed (for mocked tests)
    if response["success"] and isinstance(response["data"], str):
        try:
            response["data"] = json.loads(response["data"])
        except (json.JSONDecodeError, ValueError):
            # If it's not valid JSON, keep it as string
            pass
    
    return parse_calendar_response(response)