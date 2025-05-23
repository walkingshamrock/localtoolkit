"""
Utilities for the Reminders app integration.

This module provides utility functions for interacting with the macOS Reminders app.
"""

from typing import Dict, Any, Optional, List
from localtoolkit.applescript.utils.applescript_runner import applescript_execute
import json
from datetime import datetime

def parse_reminders_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse the response from an AppleScript execution for Reminders operations.
    
    Args:
        response: The response from applescript_execute
        
    Returns:
        A standardized response dictionary
    """
    if not response["success"]:
        return response
    
    # Handle case where JSON wasn't parsed by applescript_execute
    data = response["data"]
    if isinstance(data, str) and not data.startswith("ERROR:"):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            # If we can't parse it, return an error
            return {
                "success": False,
                "data": None,
                "error": f"Failed to parse reminder data: {data[:100]}...",
                "metadata": response.get("metadata", {})
            }
    
    return {
        "success": response["success"],
        "data": data,
        "metadata": response.get("metadata", {}),
        "error": response.get("error")
    }

def get_reminder_lists() -> Dict[str, Any]:
    """
    Get all reminder lists from the Reminders app.
    
    Returns:
        Dictionary with list of reminder lists or error information
    """
    script = """
    tell application "Reminders"
        try
            set listResults to {}
            set allLists to every list
            repeat with i from 1 to count of allLists
                set currentList to item i of allLists
                set listName to name of currentList
                set listId to id of currentList
                set theJSON to "{\\"name\\":\\""
                set theJSON to theJSON & listName & "\\", \\"id\\":\\""
                set theJSON to theJSON & listId & "\\"}"
                set end of listResults to theJSON
                
                if i < count of allLists then
                    set end of listResults to ","
                end if
            end repeat
            return "[" & (items of listResults as string) & "]"
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
    
    return parse_reminders_response(response)


def convert_iso_to_applescript_date(iso_date_str: str) -> str:
    """
    Convert ISO 8601 date format to AppleScript-compatible date format.
    
    Args:
        iso_date_str: Date in ISO format (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD)
        
    Returns:
        Date string in AppleScript format (MM/DD/YYYY HH:MM:SS AM/PM)
        
    Raises:
        ValueError: If the date format is invalid
    """
    if not iso_date_str:
        raise ValueError("Date string cannot be empty")
    
    try:
        # Handle date-only format (YYYY-MM-DD)
        if 'T' not in iso_date_str:
            dt = datetime.strptime(iso_date_str, "%Y-%m-%d")
            # For date-only, set time to midnight
            return dt.strftime("%m/%d/%Y 12:00:00 AM")
        
        # Handle datetime format (YYYY-MM-DDTHH:MM:SS)
        # Remove timezone info if present (Z or +/-offset)
        if iso_date_str.endswith('Z'):
            iso_date_str = iso_date_str[:-1]
        elif '+' in iso_date_str or iso_date_str.count('-') > 2:
            # Remove timezone offset like +05:00 or -08:00
            if '+' in iso_date_str:
                iso_date_str = iso_date_str.split('+')[0]
            else:
                # Handle negative timezone
                parts = iso_date_str.split('-')
                if len(parts) > 3:
                    iso_date_str = '-'.join(parts[:3])
        
        dt = datetime.strptime(iso_date_str, "%Y-%m-%dT%H:%M:%S")
        
        # Convert to AppleScript format: MM/DD/YYYY HH:MM:SS AM/PM
        return dt.strftime("%m/%d/%Y %I:%M:%S %p")
        
    except ValueError as e:
        raise ValueError(f"Invalid date format '{iso_date_str}'. Expected ISO 8601 format (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD). Error: {e}")


def build_applescript_date_assignment(variable_name: str, iso_date: str) -> List[str]:
    """
    Generate AppleScript lines to parse and assign a date from ISO format.
    
    Args:
        variable_name: Name of the AppleScript variable to assign
        iso_date: ISO date string to convert
        
    Returns:
        List of AppleScript lines for date parsing
    """
    try:
        applescript_date = convert_iso_to_applescript_date(iso_date)
        return [
            f'        set {variable_name} to date "{applescript_date}"'
        ]
    except ValueError as e:
        # Return error-generating AppleScript if conversion fails
        return [
            f'        error "Invalid date format: {str(e)}"'
        ]


def validate_reminder_data(reminder_data: Dict[str, Any]) -> bool:
    """
    Validate reminder data structure.
    
    Args:
        reminder_data: Dictionary containing reminder data
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["title", "id", "completed", "list_id"]
    return all(field in reminder_data for field in required_fields)


def format_reminder_response(reminder_json: str) -> Dict[str, Any]:
    """
    Format a JSON string response from AppleScript into a structured reminder object.
    
    Args:
        reminder_json: JSON string from AppleScript
        
    Returns:
        Formatted reminder dictionary
    """
    try:
        reminder_data = json.loads(reminder_json)
        return reminder_data
    except json.JSONDecodeError:
        return {
            "title": "Unknown",
            "id": "unknown",
            "completed": False,
            "due_date": None,
            "notes": None,
            "priority": None,
            "list_id": "unknown"
        }


def escape_applescript_string(text: str) -> str:
    """
    Escape special characters for AppleScript string literals.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text safe for AppleScript
    """
    if not text:
        return ""
    
    # Replace backslashes first, then quotes
    escaped = text.replace('\\', '\\\\').replace('"', '\\"')
    return escaped

def get_reminders_simple(list_id: str, limit: int = 50, show_completed: bool = True) -> Dict[str, Any]:
    """
    Simplified version that returns basic reminder info without complex escaping.
    """
    # For large lists with filtering, we need more items to ensure we get enough after filtering
    fetch_limit = limit * 3 if not show_completed else limit
    
    script = """
    tell application "Reminders"
        set targetListId to "{0}"
        set limitCount to {1}
        set showCompleted to {2}
        set output to ""
        set counter to 0
        set actualCount to 0
        
        try
            -- Find the list by ID
            set targetList to missing value
            repeat with theList in (every list)
                if (id of theList as string) is equal to targetListId then
                    set targetList to theList
                    exit repeat
                end if
            end repeat
            
            if targetList is missing value then
                return "ERROR: Reminder list with ID '" & targetListId & "' not found"
            end if
            
            -- Get reminders with simple delimiter format
            repeat with r in (every reminder in targetList)
                -- Filter check
                if showCompleted is false and completed of r is true then
                    -- Skip completed items
                else
                    set actualCount to actualCount + 1
                    
                    -- Build simple delimited format
                    set reminderLine to (id of r as string) & "||"
                    
                    -- Get title safely
                    try
                        set titleText to name of r as string
                        -- Just use first 100 chars to avoid issues
                        if length of titleText > 100 then
                            set titleText to text 1 thru 100 of titleText & "..."
                        end if
                        set reminderLine to reminderLine & titleText & "||"
                    on error
                        set reminderLine to reminderLine & "(No Title)||"
                    end try
                    
                    set reminderLine to reminderLine & (completed of r as string) & "||"
                    
                    -- Due date formatting
                    if due date of r is not missing value then
                        set dueDate to due date of r
                        set dateStr to (year of dueDate) & "-"
                        set m to month of dueDate as integer
                        if m < 10 then set dateStr to dateStr & "0"
                        set dateStr to dateStr & m & "-"
                        set d to day of dueDate
                        if d < 10 then set dateStr to dateStr & "0"
                        set dateStr to dateStr & d & "T"
                        set h to hours of dueDate
                        if h < 10 then set dateStr to dateStr & "0"
                        set dateStr to dateStr & h & ":"
                        set min to minutes of dueDate
                        if min < 10 then set dateStr to dateStr & "0"
                        set dateStr to dateStr & min & ":00Z"
                        set reminderLine to reminderLine & dateStr & "||"
                    else
                        set reminderLine to reminderLine & "null||"
                    end if
                    
                    -- Priority
                    if priority of r is not missing value then
                        set reminderLine to reminderLine & (priority of r as string)
                    else
                        set reminderLine to reminderLine & "null"
                    end if
                    
                    -- Add to output with special delimiter
                    set output to output & reminderLine & "|||NEWLINE|||"
                    
                    if actualCount >= limitCount then exit repeat
                end if
                
                set counter to counter + 1
                -- Safety limit to prevent infinite loops
                if counter > 1000 then exit repeat
            end repeat
            
            return output
            
        on error errMsg
            return "ERROR: " & errMsg
        end try
    end tell
    """
    
    show_completed_str = "true" if show_completed else "false"
    formatted_script = script.format(list_id, fetch_limit, show_completed_str)
    response = applescript_execute(formatted_script, timeout=60)  # Increased timeout
    
    if not response["success"]:
        return response
        
    data = response["data"]
    if isinstance(data, str) and data.startswith("ERROR:"):
        return {
            "success": False,
            "data": None,
            "error": data.replace("ERROR: ", "", 1)
        }
    
    # Parse the delimited format
    reminders = []
    if data and data.strip():
        # Split by our special delimiter
        lines = data.strip().split("|||NEWLINE|||")
        for line in lines:
            if not line.strip():
                continue
            parts = line.split("||")
            if len(parts) >= 5:
                try:
                    reminder = {
                        "id": parts[0].strip(),
                        "title": parts[1].strip(),
                        "completed": parts[2].strip().lower() == "true",
                        "due_date": parts[3].strip() if parts[3].strip() != "null" else None,
                        "priority": int(parts[4].strip()) if parts[4].strip() != "null" else None,
                        "notes": None,
                        "list_id": list_id
                    }
                    reminders.append(reminder)
                except (ValueError, IndexError) as e:
                    # Skip malformed lines
                    print(f"Warning: Skipping malformed reminder line: {line[:100]}... Error: {e}")
                    continue
    
    return {
        "success": True,
        "data": reminders
    }


def get_reminders(list_id: str, limit: int = 50, show_completed: bool = True) -> Dict[str, Any]:
    """
    Get reminders from a specific list in the Reminders app.
    Uses simplified delimiter-based format to avoid JSON escaping issues.
    """
    # Use the simplified version to avoid JSON escaping issues
    return get_reminders_simple(list_id, limit, show_completed)
    # DEPRECATED - kept for reference only
    return get_reminders_simple(list_id, limit, show_completed)
    
    script = """
    tell application "Reminders"
        set targetListId to "{0}"
        set limitCount to {1}
        set jsonResults to {{}}
        set counter to 0
        
        try
            -- Find the list by ID directly (more efficient than name lookup)
            set targetList to missing value
            repeat with theList in (every list)
                if (id of theList as string) is equal to targetListId then
                    set targetList to theList
                    exit repeat
                end if
            end repeat
            
            -- Check if list was found
            if targetList is missing value then
                return "ERROR: Reminder list with ID '" & targetListId & "' not found"
            end if
            
            -- Process reminders with early exit for limit
            repeat with r in (every reminder in targetList)
                set counter to counter + 1
                
                -- Extract data efficiently
                set reminderId to id of r as string
                set reminderTitle to name of r
                if reminderTitle is missing value then set reminderTitle to "(No Title)"
                
                -- Escape title for JSON
                set escapedTitle to ""
                repeat with char in (characters of reminderTitle)
                    if char is "\"" then
                        set escapedTitle to escapedTitle & "\\\""
                    else if char is "\\" then
                        set escapedTitle to escapedTitle & "\\\\"
                    else
                        set escapedTitle to escapedTitle & char
                    end if
                end repeat
                
                set isCompleted to "false"
                if completed of r is true then set isCompleted to "true"
                
                -- Simplified date handling
                set dueDateStr to "null"
                if due date of r is not missing value then
                    set dueDate to due date of r
                    set dueDateStr to "\\"" & (year of dueDate) & "-"
                    
                    set m to month of dueDate as integer
                    if m < 10 then
                        set dueDateStr to dueDateStr & "0" & m
                    else
                        set dueDateStr to dueDateStr & m
                    end if
                    
                    set dueDateStr to dueDateStr & "-"
                    set d to day of dueDate
                    if d < 10 then
                        set dueDateStr to dueDateStr & "0" & d
                    else
                        set dueDateStr to dueDateStr & d
                    end if
                    
                    set dueDateStr to dueDateStr & "T"
                    set h to hours of dueDate
                    if h < 10 then
                        set dueDateStr to dueDateStr & "0" & h
                    else
                        set dueDateStr to dueDateStr & h
                    end if
                    
                    set dueDateStr to dueDateStr & ":"
                    set min to minutes of dueDate
                    if min < 10 then
                        set dueDateStr to dueDateStr & "0" & min
                    else
                        set dueDateStr to dueDateStr & min
                    end if
                    
                    set dueDateStr to dueDateStr & ":00Z\\""
                end if
                
                -- Skip notes for performance (escaping is too slow for large lists)
                set notesStr to "null"
                
                -- Priority handling
                set priorityStr to "null"
                if priority of r is not missing value then
                    set priorityStr to priority of r as string
                end if
                
                -- Build JSON more efficiently
                set jsonItem to "{{\\"title\\":\\""
                set jsonItem to jsonItem & escapedTitle & "\\",\\"id\\":\\""
                set jsonItem to jsonItem & reminderId & "\\",\\"completed\\":" & isCompleted
                set jsonItem to jsonItem & ",\\"due_date\\":" & dueDateStr
                set jsonItem to jsonItem & ",\\"notes\\":" & notesStr
                set jsonItem to jsonItem & ",\\"priority\\":" & priorityStr
                set jsonItem to jsonItem & ",\\"list_id\\":\\""
                set jsonItem to jsonItem & targetListId & "\\"}}"
                
                set end of jsonResults to jsonItem
                
                -- Exit early if we've reached the limit
                if counter is equal to limitCount then exit repeat
                
                -- Add comma separator (except for last item when at limit)
                if counter < limitCount then
                    set end of jsonResults to ","
                end if
            end repeat
            
            -- Return results
            if counter is 0 then
                return "[]"
            else
                return "[" & (items of jsonResults as string) & "]"
            end if
            
        on error errMsg
            return "ERROR: " & errMsg
        end try
    end tell
    """
    
    # Format script with list ID and limit
    formatted_script = script.format(list_id, limit)
    
    # Use longer timeout for large lists (up to 60 seconds)
    response = applescript_execute(formatted_script, timeout=60)
    
    # Check for error string in response data
    if response["success"] and isinstance(response["data"], str) and response["data"].startswith("ERROR:"):
        response["success"] = False
        response["error"] = response["data"].replace("ERROR: ", "", 1)
        response["data"] = None
    
    return parse_reminders_response(response)


def convert_iso_to_applescript_date(iso_date_str: str) -> str:
    """
    Convert ISO 8601 date format to AppleScript-compatible date format.
    
    Args:
        iso_date_str: Date in ISO format (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD)
        
    Returns:
        Date string in AppleScript format (MM/DD/YYYY HH:MM:SS AM/PM)
        
    Raises:
        ValueError: If the date format is invalid
    """
    if not iso_date_str:
        raise ValueError("Date string cannot be empty")
    
    try:
        # Handle date-only format (YYYY-MM-DD)
        if 'T' not in iso_date_str:
            dt = datetime.strptime(iso_date_str, "%Y-%m-%d")
            # For date-only, set time to midnight
            return dt.strftime("%m/%d/%Y 12:00:00 AM")
        
        # Handle datetime format (YYYY-MM-DDTHH:MM:SS)
        # Remove timezone info if present (Z or +/-offset)
        if iso_date_str.endswith('Z'):
            iso_date_str = iso_date_str[:-1]
        elif '+' in iso_date_str or iso_date_str.count('-') > 2:
            # Remove timezone offset like +05:00 or -08:00
            if '+' in iso_date_str:
                iso_date_str = iso_date_str.split('+')[0]
            else:
                # Handle negative timezone
                parts = iso_date_str.split('-')
                if len(parts) > 3:
                    iso_date_str = '-'.join(parts[:3])
        
        dt = datetime.strptime(iso_date_str, "%Y-%m-%dT%H:%M:%S")
        
        # Convert to AppleScript format: MM/DD/YYYY HH:MM:SS AM/PM
        return dt.strftime("%m/%d/%Y %I:%M:%S %p")
        
    except ValueError as e:
        raise ValueError(f"Invalid date format '{iso_date_str}'. Expected ISO 8601 format (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD). Error: {e}")


def build_applescript_date_assignment(variable_name: str, iso_date: str) -> List[str]:
    """
    Generate AppleScript lines to parse and assign a date from ISO format.
    
    Args:
        variable_name: Name of the AppleScript variable to assign
        iso_date: ISO date string to convert
        
    Returns:
        List of AppleScript lines for date parsing
    """
    try:
        applescript_date = convert_iso_to_applescript_date(iso_date)
        return [
            f'        set {variable_name} to date "{applescript_date}"'
        ]
    except ValueError as e:
        # Return error-generating AppleScript if conversion fails
        return [
            f'        error "Invalid date format: {str(e)}"'
        ]


def validate_reminder_data(reminder_data: Dict[str, Any]) -> bool:
    """
    Validate reminder data structure.
    
    Args:
        reminder_data: Dictionary containing reminder data
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["title", "id", "completed", "list_id"]
    return all(field in reminder_data for field in required_fields)


def format_reminder_response(reminder_json: str) -> Dict[str, Any]:
    """
    Format a JSON string response from AppleScript into a structured reminder object.
    
    Args:
        reminder_json: JSON string from AppleScript
        
    Returns:
        Formatted reminder dictionary
    """
    try:
        reminder_data = json.loads(reminder_json)
        return reminder_data
    except json.JSONDecodeError:
        return {
            "title": "Unknown",
            "id": "unknown",
            "completed": False,
            "due_date": None,
            "notes": None,
            "priority": None,
            "list_id": "unknown"
        }


def escape_applescript_string(text: str) -> str:
    """
    Escape special characters for AppleScript string literals.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text safe for AppleScript
    """
    if not text:
        return ""
    
    # Replace backslashes first, then quotes
    escaped = text.replace('\\', '\\\\').replace('"', '\\"')
    return escaped