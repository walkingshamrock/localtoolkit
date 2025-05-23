"""
Update reminder endpoint for LocalToolKit.

This module provides functionality to update existing reminders in the macOS Reminders app.
"""

from typing import Dict, Any, Optional
from fastmcp import FastMCP
from localtoolkit.applescript.utils.applescript_runner import applescript_execute
from localtoolkit.reminders.utils.reminders_utils import convert_iso_to_applescript_date, escape_applescript_string


def update_reminder_logic(
    reminder_id: str,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[int] = None,
    completed: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Update an existing reminder with new values.
    
    Args:
        reminder_id: ID of the reminder to update
        title: Optional new title/name for the reminder
        notes: Optional new notes/body text for the reminder
        due_date: Optional new due date in ISO format (YYYY-MM-DDTHH:MM:SS) or None to clear
        priority: Optional new priority (0=high, 5=medium, 9=low) or None to clear
        completed: Optional completion status
        
    Returns:
        Dictionary with update result and reminder details
    """
    if not reminder_id:
        return {
            "success": False,
            "error": "reminder_id is required",
            "message": "Failed to update reminder: missing required parameter"
        }
    
    # Check if any updates are provided
    if all(param is None for param in [title, notes, due_date, priority, completed]):
        return {
            "success": False,
            "error": "No update parameters provided",
            "message": "Failed to update reminder: at least one parameter must be provided"
        }
    
    # Build AppleScript for updating reminder
    script_parts = [
        'tell application "Reminders"',
        '    try',
        f'        set targetReminderId to "{reminder_id}"',
        '        set targetReminder to missing value',
        '        ',
        '        -- Find the reminder by ID using whose filter',
        '        try',
        '            set targetReminder to first reminder whose id is targetReminderId',
        '        on error',
        '            set targetReminder to missing value',
        '        end try',
        '        ',
        '        if targetReminder is missing value then',
        '            return "ERROR: Reminder with ID \'" & targetReminderId & "\' not found"',
        '        end if',
        '        '
    ]
    
    # Add update operations for each provided parameter
    if title is not None:
        script_parts.append(f'        set name of targetReminder to "{escape_applescript_string(title)}"')
    
    if notes is not None:
        if notes == "":
            script_parts.append('        set body of targetReminder to ""')
        else:
            script_parts.append(f'        set body of targetReminder to "{escape_applescript_string(notes)}"')
    
    if due_date is not None:
        if due_date == "":
            script_parts.append('        set due date of targetReminder to missing value')
        else:
            # Convert ISO date to AppleScript format
            try:
                applescript_date = convert_iso_to_applescript_date(due_date)
                script_parts.extend([
                    f'        set dueDateStr to "{applescript_date}"',
                    '        set dateDate to date dueDateStr',
                    '        set due date of targetReminder to dateDate'
                ])
            except ValueError as e:
                return {
                    "success": False,
                    "error": f"Invalid due_date format: {str(e)}",
                    "message": "Failed to update reminder: invalid date format"
                }
    
    if priority is not None:
        script_parts.append(f'        set priority of targetReminder to {priority}')
    
    if completed is not None:
        completed_value = "true" if completed else "false"
        script_parts.append(f'        set completed of targetReminder to {completed_value}')
    
    # Complete the script with return data
    script_parts.extend([
        '        ',
        '        -- Return updated reminder details',
        '        set reminderId to id of targetReminder as string',
        '        set reminderTitle to name of targetReminder',
        '        set isCompleted to "false"',
        '        if completed of targetReminder is true then set isCompleted to "true"',
        '        ',
        '        set dueDateStr to "null"',
        '        if due date of targetReminder is not missing value then',
        '            set dueDate to due date of targetReminder',
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
        '        if body of targetReminder is not missing value and body of targetReminder is not "" then',
        '            set noteBody to body of targetReminder as string',
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
        '        if priority of targetReminder is not missing value then',
        '            set priorityStr to priority of targetReminder as string',
        '        end if',
        '        ',
        '        -- Get list ID',
        '        set listId to "unknown"',
        '        repeat with theList in (every list)',
        '            repeat with theReminder in (every reminder in theList)',
        '                if (id of theReminder as string) is equal to targetReminderId then',
        '                    set listId to id of theList as string',
        '                    exit repeat',
        '                end if',
        '            end repeat',
        '            if listId is not "unknown" then exit repeat',
        '        end repeat',
        '        ',
        '        set jsonResult to "{{\\"title\\":\\""',
        '        set jsonResult to jsonResult & reminderTitle & "\\",\\"id\\":\\""',
        '        set jsonResult to jsonResult & reminderId & "\\",\\"completed\\":" & isCompleted',
        '        set jsonResult to jsonResult & ",\\"due_date\\":" & dueDateStr',
        '        set jsonResult to jsonResult & ",\\"notes\\":" & notesStr',
        '        set jsonResult to jsonResult & ",\\"priority\\":" & priorityStr',
        '        set jsonResult to jsonResult & ",\\"list_id\\":\\""',
        '        set jsonResult to jsonResult & listId & "\\"}}"',
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
                "message": "Failed to update reminder"
            }
        
        if response["success"]:
            return {
                "success": True,
                "data": response["data"],
                "message": f"Successfully updated reminder ID: {reminder_id}"
            }
        else:
            return {
                "success": False,
                "error": response.get("error", "Unknown error"),
                "message": "Failed to update reminder"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to update reminder due to unexpected error"
        }


def reminders_update_reminder(
    reminder_id: str,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[int] = None,
    completed: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Update an existing reminder with new values.
    
    Args:
        reminder_id: ID of the reminder to update
        title: Optional new title/name for the reminder
        notes: Optional new notes/body text for the reminder
        due_date: Optional new due date in ISO format (YYYY-MM-DDTHH:MM:SS) or None to clear
        priority: Optional new priority (0=high, 5=medium, 9=low) or None to clear
        completed: Optional completion status
        
    Returns:
        Dictionary with update result and reminder details
    """
    return update_reminder_logic(reminder_id, title, notes, due_date, priority, completed)


def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the update reminder tool to the MCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    @mcp.tool("reminders_update_reminder")
    def update_reminder_tool(
        reminder_id: str,
        title: str = None,
        notes: str = None,
        due_date: str = None,
        priority: int = None,
        completed: bool = None
    ) -> Dict[str, Any]:
        """
        Update an existing reminder with new values.
        
        Args:
            reminder_id: ID of the reminder to update
            title: Optional new title/name for the reminder
            notes: Optional new notes/body text for the reminder
            due_date: Optional new due date in ISO format (YYYY-MM-DDTHH:MM:SS) or None to clear
            priority: Optional new priority (0=high, 5=medium, 9=low) or None to clear
            completed: Optional completion status
            
        Returns:
            Dictionary with update result and reminder details
        """
        return reminders_update_reminder(reminder_id, title, notes, due_date, priority, completed)
