"""
Implementation of update_note for the Notes app.

This module provides functionality to update existing notes in the macOS Notes app using AppleScript.
"""

from fastmcp import FastMCP
from typing import Dict, Any, Optional
import time
from localtoolkit.applescript.utils.applescript_runner import applescript_execute
from localtoolkit.notes.utils.notes_utils import validate_note_name, escape_applescript_string, extract_note_preview


def update_note_logic(note_id: str, name: Optional[str] = None, body: Optional[str] = None) -> Dict[str, Any]:
    """
    Update an existing note in the Notes app using AppleScript.
    
    Args:
        note_id: The unique identifier of the note to update
        name: New name/title for the note (optional)
        body: New content for the note (optional)
    
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,      # True if operation was successful
            "note": Dict,         # Updated note object
            "message": str,       # Optional context message
            "metadata": dict,     # Additional metadata
            "error": str          # Only present if success is False
        }
    """
    start_time = time.time()
    
    # Validate inputs
    if not note_id or not note_id.strip():
        return {
            "success": False,
            "note": None,
            "message": "Invalid note ID",
            "error": "Note ID cannot be empty",
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }
    
    if not name and not body:
        return {
            "success": False,
            "note": None,
            "message": "No updates specified",
            "error": "At least one of name or body must be provided",
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }
    
    # Validate name if provided
    if name and not validate_note_name(name):
        return {
            "success": False,
            "note": None,
            "message": "Invalid note name",
            "error": "Note name contains invalid characters",
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }
    
    # Escape strings for AppleScript
    escaped_note_id = note_id.replace('"', '\\"')
    
    # Build update commands
    update_commands = []
    if name:
        escaped_name = escape_applescript_string(name)
        update_commands.append(f'set name of targetNote to "{escaped_name}"')
    
    if body:
        escaped_body = escape_applescript_string(body)
        update_commands.append(f'set body of targetNote to "{escaped_body}"')
    
    update_block = "\n                ".join(update_commands)
    
    # Create AppleScript to update note
    applescript_code = f"""
    on run argv
        set targetNoteID to "{escaped_note_id}"
        
        try
            tell application "Notes"
                -- Find the note by ID
                set targetNote to note id targetNoteID
                
                -- Apply updates
                {update_block}
                
                -- Get updated note properties
                set noteID to id of targetNote as string
                set noteName to name of targetNote
                set noteBody to body of targetNote
                set modDate to modification date of targetNote as string
                set creationDate to creation date of targetNote as string
                
                -- Get folder name
                set folderName to ""
                try
                    set noteContainer to container of targetNote
                    if noteContainer is not missing value then
                        set folderName to name of noteContainer
                    end if
                end try
                
                -- Return structured data
                set fieldDelim to "<<|>>"
                return "SUCCESS:" & noteID & fieldDelim & noteName & fieldDelim & noteBody & fieldDelim & modDate & fieldDelim & folderName & fieldDelim & creationDate
                
            end tell
        on error errorMessage
            -- Return error (note not found or other issue)
            return "ERROR:" & errorMessage
        end try
    end run
    """
    
    # Execute the AppleScript
    result = applescript_execute(applescript_code)
    
    # Process the result
    if not result["success"]:
        return {
            "success": False,
            "note": None,
            "message": "Failed to update note",
            "error": result.get("error", "Unknown error during note update"),
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }
    
    # Parse the output
    output = result["data"]
    
    # Check for error
    if isinstance(output, str) and output.startswith("ERROR:"):
        error_msg = output[6:]  # Remove ERROR: prefix
        
        # Check if it's a "not found" error
        if "can't get note id" in error_msg.lower() or "doesn't understand" in error_msg.lower():
            return {
                "success": False,
                "note": None,
                "message": f"Note with ID '{note_id}' not found",
                "error": "Note not found",
                "metadata": {
                    "execution_time_ms": int((time.time() - start_time) * 1000)
                }
            }
        else:
            return {
                "success": False,
                "note": None,
                "message": "Error updating note",
                "error": error_msg,
                "metadata": {
                    "execution_time_ms": int((time.time() - start_time) * 1000)
                }
            }
    
    # Process valid output
    try:
        if isinstance(output, str) and output.startswith("SUCCESS:"):
            data = output[8:]  # Remove SUCCESS: prefix
            fields = data.split("<<|>>")
            
            if len(fields) >= 4:
                note = {
                    "id": fields[0].strip(),
                    "name": fields[1].strip(),
                    "body": fields[2].strip(),
                    "modification_date": fields[3].strip(),
                    "folder": fields[4].strip() if len(fields) > 4 else "",
                    "creation_date": fields[5].strip() if len(fields) > 5 else ""
                }
                
                # Add preview
                note["preview"] = extract_note_preview(note["body"])
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Create update summary
                updates = []
                if name:
                    updates.append("name")
                if body:
                    updates.append("content")
                update_summary = " and ".join(updates)
                
                return {
                    "success": True,
                    "note": note,
                    "message": f"Updated {update_summary} for note '{note['name']}'",
                    "metadata": {
                        "execution_time_ms": execution_time_ms,
                        "updated_fields": updates
                    }
                }
        
        # If we get here, something went wrong with parsing
        return {
            "success": False,
            "note": None,
            "message": "Error processing note update response",
            "error": "Unexpected response format",
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "note": None,
            "message": "Error processing note update data",
            "error": str(e),
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }


def register_to_mcp(mcp: FastMCP) -> None:
    """Register the notes_update_note tool with the MCP server."""
    @mcp.tool()
    def notes_update_note(
        note_id: str,
        name: Optional[str] = None,
        body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing note in the macOS Notes app.
        
        This endpoint provides a way to update the name and/or content of an existing note
        in the Notes app using its unique identifier.
        
        Args:
            note_id: The unique identifier of the note to update (required)
            name: New name/title for the note (optional)
            body: New content for the note (optional)
        
        Note: At least one of name or body must be provided.
        
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,        # True if update was successful
                "note": dict,           # Updated note object
                "message": str,         # Context message
                "metadata": {           # Additional metadata
                    "execution_time_ms": int,   # Execution time in milliseconds
                    "updated_fields": list      # List of fields that were updated
                },
                "error": str            # Only present if success is False
            }
            
            The note object contains:
            {
                "id": str,              # Unique Note ID
                "name": str,            # Note title/name
                "body": str,            # Full note content
                "preview": str,         # Preview of note content
                "modification_date": str, # Last modification date (updated)
                "creation_date": str,   # Original creation date
                "folder": str           # Folder/container name
            }
        
        Error Handling:
            - Invalid ID: Returns error for empty or malformed IDs
            - Note not found: Returns specific error if note doesn't exist
            - Invalid name: Returns error for names with invalid characters
            - No updates: Returns error if neither name nor body is provided
            - Permission issues: Returns error if Notes access is restricted
            - App not running: Attempts to launch Notes app automatically
            
        Performance:
            - Typical response time: 1-3 seconds
            - Response time is independent of total number of notes
            
        Examples:
            # Update note content only
            result = notes_update_note(
                note_id="x-coredata://12345678-1234-1234-1234-123456789012/Note/p1",
                body="Updated content for this note."
            )
            
            # Update note name only
            result = notes_update_note(
                note_id="x-coredata://12345678-1234-1234-1234-123456789012/Note/p1",
                name="New Note Title"
            )
            
            # Update both name and content
            result = notes_update_note(
                note_id="x-coredata://12345678-1234-1234-1234-123456789012/Note/p1",
                name="Updated Meeting Notes",
                body="Meeting was postponed to next week.\\nNew agenda items to discuss."
            )
        """
        return update_note_logic(note_id, name, body)
