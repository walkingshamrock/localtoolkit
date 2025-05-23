"""
Implementation of get_note for the Notes app.

This module provides functionality to retrieve a specific note from the macOS Notes app using AppleScript.
"""

from fastmcp import FastMCP
from typing import Dict, Any, Optional
import time
from localtoolkit.applescript.utils.applescript_runner import applescript_execute
from localtoolkit.notes.utils.notes_utils import extract_note_preview


def get_note_logic(note_id: str) -> Dict[str, Any]:
    """
    Get a specific note from the Notes app using AppleScript.
    
    Args:
        note_id: The unique identifier of the note to retrieve
    
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,      # True if operation was successful
            "note": Dict,         # Note object (None if not found)
            "message": str,       # Optional context message
            "metadata": dict,     # Additional metadata
            "error": str          # Only present if success is False
        }
    """
    start_time = time.time()
    
    # Validate input
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
    
    # Escape note ID for AppleScript
    escaped_note_id = note_id.replace('"', '\\"')
    
    # Create AppleScript to get note
    applescript_code = f"""
    on run argv
        set targetNoteID to "{escaped_note_id}"
        
        try
            tell application "Notes"
                -- Find the note by ID
                set targetNote to note id targetNoteID
                
                -- Get note properties
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
            "message": "Failed to retrieve note",
            "error": result.get("error", "Unknown error during note retrieval"),
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
                "message": "Error retrieving note",
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
                
                return {
                    "success": True,
                    "note": note,
                    "message": f"Retrieved note '{note['name']}'",
                    "metadata": {
                        "execution_time_ms": execution_time_ms
                    }
                }
        
        # If we get here, something went wrong with parsing
        return {
            "success": False,
            "note": None,
            "message": "Error processing note retrieval response",
            "error": "Unexpected response format",
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "note": None,
            "message": "Error processing note retrieval data",
            "error": str(e),
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }


def register_to_mcp(mcp: FastMCP) -> None:
    """Register the notes_get_note tool with the MCP server."""
    @mcp.tool()
    def notes_get_note(note_id: str) -> Dict[str, Any]:
        """
        Get a specific note from the macOS Notes app by ID.
        
        This endpoint provides a way to retrieve a specific note from the Notes app
        using its unique identifier.
        
        Args:
            note_id: The unique identifier of the note to retrieve (required)
        
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,        # True if retrieval was successful
                "note": dict,           # Note object (None if not found)
                "message": str,         # Context message
                "metadata": {           # Additional metadata
                    "execution_time_ms": int,   # Execution time in milliseconds
                },
                "error": str            # Only present if success is False
            }
            
            The note object contains:
            {
                "id": str,              # Unique Note ID
                "name": str,            # Note title/name
                "body": str,            # Full note content
                "preview": str,         # Preview of note content
                "modification_date": str, # Last modification date
                "creation_date": str,   # Creation date
                "folder": str           # Folder/container name
            }
        
        Error Handling:
            - Invalid ID: Returns error for empty or malformed IDs
            - Note not found: Returns specific error if note doesn't exist
            - Permission issues: Returns error if Notes access is restricted
            - App not running: Attempts to launch Notes app automatically
            
        Performance:
            - Typical response time: 0.5-2 seconds
            - Response time is independent of total number of notes
            
        Examples:
            # Get a specific note
            result = notes_get_note("x-coredata://12345678-1234-1234-1234-123456789012/Note/p1")
            if result["success"]:
                note = result["note"]
                print(f"Note: {note['name']}")
                print(f"Content: {note['body']}")
            else:
                print(f"Error: {result['error']}")
        """
        return get_note_logic(note_id)
