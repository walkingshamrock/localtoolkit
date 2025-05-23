"""
Complete reminder endpoint for LocalToolKit.

This module provides functionality to mark reminders as complete or incomplete in the macOS Reminders app.
"""

from typing import Dict, Any
from fastmcp import FastMCP
from localtoolkit.applescript.utils.applescript_runner import applescript_execute


def complete_reminder_logic(
    reminder_id: str,
    completed: bool = True
) -> Dict[str, Any]:
    """
    Mark a reminder as complete or incomplete.
    
    Args:
        reminder_id: ID of the reminder to update
        completed: True to mark as complete, False to mark as incomplete
        
    Returns:
        Dictionary with completion result and reminder details
    """
    if not reminder_id:
        return {
            "success": False,
            "error": "reminder_id is required",
            "message": "Failed to update reminder: missing required parameter"
        }
    
    completed_value = "true" if completed else "false"
    
    # Build AppleScript for updating reminder completion status
    script = f"""
    tell application "Reminders"
        try
            set targetReminderId to "{reminder_id}"
            set targetReminder to missing value
            
            -- Find the reminder by ID using whose filter
            try
                set targetReminder to first reminder whose id is targetReminderId
            on error
                set targetReminder to missing value
            end try
            
            if targetReminder is missing value then
                return "ERROR: Reminder with ID '" & targetReminderId & "' not found"
            end if
            
            -- Update completion status
            set completed of targetReminder to {completed_value}
            
            -- Return updated reminder details
            set reminderId to id of targetReminder as string
            set reminderTitle to name of targetReminder
            set isCompleted to "false"
            if completed of targetReminder is true then set isCompleted to "true"
            
            set dueDateStr to "null"
            if due date of targetReminder is not missing value then
                set dueDate to due date of targetReminder
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
            
            set notesStr to "null"
            if body of targetReminder is not missing value and body of targetReminder is not "" then
                set noteBody to body of targetReminder as string
                set escapedBody to ""
                repeat with char in (characters of noteBody)
                    if char is "\\"" then
                        set escapedBody to escapedBody & "\\\\\\""
                    else if char is "\\\\" then
                        set escapedBody to escapedBody & "\\\\\\\\"
                    else
                        set escapedBody to escapedBody & char
                    end if
                end repeat
                set notesStr to "\\"" & escapedBody & "\\""
            end if
            
            set priorityStr to "null"
            if priority of targetReminder is not missing value then
                set priorityStr to priority of targetReminder as string
            end if
            
            -- Get list ID efficiently using container property
            set listId to "unknown"
            try
                set containerList to container of targetReminder
                set listId to id of containerList as string
            on error
                -- Fallback if container property fails
                set listId to "unknown"
            end try
            
            set jsonResult to "{{\\"title\\":\\""
            set jsonResult to jsonResult & reminderTitle & "\\",\\"id\\":\\""
            set jsonResult to jsonResult & reminderId & "\\",\\"completed\\":" & isCompleted
            set jsonResult to jsonResult & ",\\"due_date\\":" & dueDateStr
            set jsonResult to jsonResult & ",\\"notes\\":" & notesStr
            set jsonResult to jsonResult & ",\\"priority\\":" & priorityStr
            set jsonResult to jsonResult & ",\\"list_id\\":\\""
            set jsonResult to jsonResult & listId & "\\"}}"
            
            return jsonResult
        on error errMsg
            return "ERROR: " & errMsg
        end try
    end tell
    """
    
    try:
        response = applescript_execute(script, timeout=60)
        
        # Check for error string in response data
        if response["success"] and isinstance(response["data"], str) and response["data"].startswith("ERROR:"):
            return {
                "success": False,
                "error": response["data"].replace("ERROR: ", "", 1),
                "message": "Failed to update reminder completion status"
            }
        
        if response["success"]:
            status_text = "completed" if completed else "incomplete"
            return {
                "success": True,
                "data": response["data"],
                "message": f"Successfully marked reminder ID: {reminder_id} as {status_text}"
            }
        else:
            return {
                "success": False,
                "error": response.get("error", "Unknown error"),
                "message": "Failed to update reminder completion status"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to update reminder completion status due to unexpected error"
        }


def reminders_complete_reminder(
    reminder_id: str,
    completed: bool = True
) -> Dict[str, Any]:
    """
    Mark a reminder as complete or incomplete.
    
    Args:
        reminder_id: ID of the reminder to update
        completed: True to mark as complete, False to mark as incomplete
        
    Returns:
        Dictionary with completion result and reminder details
    """
    return complete_reminder_logic(reminder_id, completed)


def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the complete reminder tool to the MCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    @mcp.tool("reminders_complete_reminder")
    def complete_reminder_tool(
        reminder_id: str,
        completed: bool = True
    ) -> Dict[str, Any]:
        """
        Mark a reminder as complete or incomplete.
        
        Args:
            reminder_id: ID of the reminder to update
            completed: True to mark as complete, False to mark as incomplete
            
        Returns:
            Dictionary with completion result and reminder details
        """
        return reminders_complete_reminder(reminder_id, completed)
