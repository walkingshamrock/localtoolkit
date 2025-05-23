"""
Create reminder endpoint for LocalToolKit.

This module provides functionality to create new reminders in the macOS Reminders app.
"""

from typing import Dict, Any, Optional
from fastmcp import FastMCP
from localtoolkit.applescript.utils.applescript_runner import applescript_execute
from localtoolkit.reminders.utils.reminders_utils import convert_iso_to_applescript_date, escape_applescript_string


def create_reminder_logic(
    list_id: str,
    title: str,
    notes: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a new reminder in the specified reminder list.
    
    Args:
        list_id: ID of the reminder list to add the reminder to
        title: Title/name of the reminder
        notes: Optional notes/body text for the reminder
        due_date: Optional due date in ISO format (YYYY-MM-DDTHH:MM:SS)
        priority: Optional priority (0=high, 5=medium, 9=low)
        
    Returns:
        Dictionary with creation result and reminder details
    """
    if not list_id or not title:
        return {
            "success": False,
            "error": "list_id and title are required",
            "message": "Failed to create reminder: missing required parameters"
        }
    
    # Build AppleScript for creating reminder
    script_parts = [
        'tell application "Reminders"',
        '    try',
        f'        set targetListId to "{list_id}"',
        '        set targetList to missing value',
        '        repeat with theList in (every list)',
        '            if (id of theList as string) is equal to targetListId then',
        '                set targetList to theList',
        '                exit repeat',
        '            end if',
        '        end repeat',
        '        ',
        '        if targetList is missing value then',
        '            return "ERROR: Reminder list with ID \'" & targetListId & "\' not found"',
        '        end if',
        '        ',
        f'        set newReminder to make new reminder at end of targetList with properties {{name:"{escape_applescript_string(title)}"}}'
    ]
    
    # Add optional properties
    if notes:
        script_parts.append(f'        set body of newReminder to "{escape_applescript_string(notes)}"')
    
    if due_date:
        # Convert ISO date to AppleScript format
        try:
            applescript_date = convert_iso_to_applescript_date(due_date)
            script_parts.extend([
                f'        set dueDateStr to "{applescript_date}"',
                '        set dateDate to date dueDateStr',
                '        set due date of newReminder to dateDate'
            ])
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid due_date format: {str(e)}",
                "message": "Failed to create reminder: invalid date format"
            }
    
    if priority is not None:
        script_parts.append(f'        set priority of newReminder to {priority}')
    
    # Complete the script
    script_parts.extend([
        '        ',
        '        -- Return reminder details',
        '        set reminderId to id of newReminder as string',
        '        set reminderTitle to name of newReminder',
        '        set isCompleted to "false"',
        '        if completed of newReminder is true then set isCompleted to "true"',
        '        ',
        '        set dueDateStr to "null"',
        '        if due date of newReminder is not missing value then',
        '            set dueDate to due date of newReminder',
        '            set dueDateStr to "\\"" & (year of dueDate) & "-"',
        '            set m to month of dueDate as integer',
        '            if m < 10 then',
        '                set dueDateStr to dueDateStr & "0" & m',
        '            else',
        '                set dueDateStr to dueDateStr & m',
        '            end if',
        '            set dueDateStr to dueDateStr & "-"',
        '            set d to day of dueDate',
        '            if d < 10 then',
        '                set dueDateStr to dueDateStr & "0" & d',
        '            else',
        '                set dueDateStr to dueDateStr & d',
        '            end if',
        '            set dueDateStr to dueDateStr & "T"',
        '            set h to hours of dueDate',
        '            if h < 10 then',
        '                set dueDateStr to dueDateStr & "0" & h',
        '            else',
        '                set dueDateStr to dueDateStr & h',
        '            end if',
        '            set dueDateStr to dueDateStr & ":"',
        '            set min to minutes of dueDate',
        '            if min < 10 then',
        '                set dueDateStr to dueDateStr & "0" & min',
        '            else',
        '                set dueDateStr to dueDateStr & min',
        '            end if',
        '            set dueDateStr to dueDateStr & ":00Z\\""',
        '        end if',
        '        ',
        '        set notesStr to "null"',
        '        if body of newReminder is not missing value and body of newReminder is not "" then',
        '            set noteBody to body of newReminder as string',
        '            set escapedBody to ""',
        '            repeat with char in (characters of noteBody)',
        '                if char is "\\"" then',
        '                    set escapedBody to escapedBody & "\\\\\\""',
        '                else if char is "\\\\" then',
        '                    set escapedBody to escapedBody & "\\\\\\\\"',
        '                else',
        '                    set escapedBody to escapedBody & char',
        '                end if',
        '            end repeat',
        '            set notesStr to "\\"" & escapedBody & "\\""',
        '        end if',
        '        ',
        '        set priorityStr to "null"',
        '        if priority of newReminder is not missing value then',
        '            set priorityStr to priority of newReminder as string',
        '        end if',
        '        ',
        '        set jsonResult to "{{\\"title\\":\\""',
        '        set jsonResult to jsonResult & reminderTitle & "\\",\\"id\\":\\""',
        '        set jsonResult to jsonResult & reminderId & "\\",\\"completed\\":" & isCompleted',
        '        set jsonResult to jsonResult & ",\\"due_date\\":" & dueDateStr',
        '        set jsonResult to jsonResult & ",\\"notes\\":" & notesStr',
        '        set jsonResult to jsonResult & ",\\"priority\\":" & priorityStr',
        '        set jsonResult to jsonResult & ",\\"list_id\\":\\""',
        '        set jsonResult to jsonResult & targetListId & "\\"}}"',
        '        ',
        '        return jsonResult',
        '    on error errMsg',
        '        return "ERROR: " & errMsg',
        '    end try',
        'end tell'
    ])
    
    script = '\n'.join(script_parts)
    
    try:
        response = applescript_execute(script, timeout=15)
        
        # Check for error string in response data
        if response["success"] and isinstance(response["data"], str) and response["data"].startswith("ERROR:"):
            return {
                "success": False,
                "error": response["data"].replace("ERROR: ", "", 1),
                "message": "Failed to create reminder"
            }
        
        if response["success"]:
            return {
                "success": True,
                "data": response["data"],
                "message": f"Successfully created reminder '{title}' in list ID: {list_id}"
            }
        else:
            return {
                "success": False,
                "error": response.get("error", "Unknown error"),
                "message": "Failed to create reminder"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create reminder due to unexpected error"
        }


def reminders_create_reminder(
    list_id: str,
    title: str,
    notes: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a new reminder in the specified reminder list.
    
    Args:
        list_id: ID of the reminder list to add the reminder to
        title: Title/name of the reminder
        notes: Optional notes/body text for the reminder
        due_date: Optional due date in ISO format (YYYY-MM-DDTHH:MM:SS)
        priority: Optional priority (0=high, 5=medium, 9=low)
        
    Returns:
        Dictionary with creation result and reminder details
    """
    return create_reminder_logic(list_id, title, notes, due_date, priority)


def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the create reminder tool to the MCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    @mcp.tool("reminders_create_reminder")
    def create_reminder_tool(
        list_id: str,
        title: str,
        notes: str = None,
        due_date: str = None,
        priority: int = None
    ) -> Dict[str, Any]:
        """
        Create a new reminder in the specified reminder list.
        
        Args:
            list_id: ID of the reminder list to add the reminder to
            title: Title/name of the reminder
            notes: Optional notes/body text for the reminder
            due_date: Optional due date in ISO format (YYYY-MM-DDTHH:MM:SS)
            priority: Optional priority (0=high, 5=medium, 9=low)
            
        Returns:
            Dictionary with creation result and reminder details
        """
        return reminders_create_reminder(list_id, title, notes, due_date, priority)
