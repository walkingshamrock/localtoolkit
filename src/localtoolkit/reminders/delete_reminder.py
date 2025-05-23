"""
Delete reminder endpoint for LocalToolKit.

This module provides functionality to delete reminders from the macOS Reminders app.
"""

from typing import Dict, Any
from fastmcp import FastMCP
from localtoolkit.applescript.utils.applescript_runner import applescript_execute


def delete_reminder_logic(reminder_id: str) -> Dict[str, Any]:
    """
    Delete a reminder from the Reminders app.
    
    Args:
        reminder_id: ID of the reminder to delete
        
    Returns:
        Dictionary with deletion result
    """
    if not reminder_id:
        return {
            "success": False,
            "error": "reminder_id is required",
            "message": "Failed to delete reminder: missing required parameter"
        }
    
    # Build AppleScript for deleting reminder
    script = f"""
    tell application "Reminders"
        try
            set targetReminderId to "{reminder_id}"
            set targetReminder to missing value
            set reminderDetails to missing value
            
            -- Find the reminder by ID using whose filter
            try
                set targetReminder to first reminder whose id is targetReminderId
            on error
                set targetReminder to missing value
            end try
            
            if targetReminder is not missing value then
                        
                        -- Capture reminder details before deletion
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
                        
                        -- Get list ID by finding which list contains this reminder
                        set listId to "unknown"
                        repeat with theList in (every list)
                            repeat with theReminder in (every reminder in theList)
                                if (id of theReminder as string) is equal to targetReminderId then
                                    set listId to id of theList as string
                                    exit repeat
                                end if
                            end repeat
                            if listId is not "unknown" then exit repeat
                        end repeat
                        
                        set reminderDetails to "{{\\"title\\":\\""
                        set reminderDetails to reminderDetails & reminderTitle & "\\",\\"id\\":\\""
                        set reminderDetails to reminderDetails & reminderId & "\\",\\"completed\\":" & isCompleted
                        set reminderDetails to reminderDetails & ",\\"due_date\\":" & dueDateStr
                        set reminderDetails to reminderDetails & ",\\"notes\\":" & notesStr
                        set reminderDetails to reminderDetails & ",\\"priority\\":" & priorityStr
                        set reminderDetails to reminderDetails & ",\\"list_id\\":\\""
                        set reminderDetails to reminderDetails & listId & "\\"}}"
            end if
            
            if targetReminder is missing value then
                return "ERROR: Reminder with ID '" & targetReminderId & "' not found"
            end if
            
            -- Delete the reminder
            delete targetReminder
            
            -- Return the details of the deleted reminder
            return reminderDetails
            
        on error errMsg
            return "ERROR: " & errMsg
        end try
    end tell
    """
    
    try:
        response = applescript_execute(script, timeout=15)
        
        # Check for error string in response data
        if response["success"] and isinstance(response["data"], str) and response["data"].startswith("ERROR:"):
            return {
                "success": False,
                "error": response["data"].replace("ERROR: ", "", 1),
                "message": "Failed to delete reminder"
            }
        
        if response["success"]:
            return {
                "success": True,
                "data": response["data"],
                "message": f"Successfully deleted reminder ID: {reminder_id}"
            }
        else:
            return {
                "success": False,
                "error": response.get("error", "Unknown error"),
                "message": "Failed to delete reminder"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to delete reminder due to unexpected error"
        }


def reminders_delete_reminder(reminder_id: str) -> Dict[str, Any]:
    """
    Delete a reminder from the Reminders app.
    
    Args:
        reminder_id: ID of the reminder to delete
        
    Returns:
        Dictionary with deletion result
    """
    return delete_reminder_logic(reminder_id)


def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the delete reminder tool to the MCP server.
    
    Args:
        mcp: The FastMCP server instance
    """
    @mcp.tool("reminders_delete_reminder")
    def delete_reminder_tool(reminder_id: str) -> Dict[str, Any]:
        """
        Delete a reminder from the Reminders app.
        
        Args:
            reminder_id: ID of the reminder to delete
            
        Returns:
            Dictionary with deletion result
        """
        return reminders_delete_reminder(reminder_id)
