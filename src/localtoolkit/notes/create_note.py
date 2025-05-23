"""
Implementation of create_note for the Notes app.

This module provides functionality to create new notes in the macOS Notes app using AppleScript.
"""

from fastmcp import FastMCP
from typing import Dict, Any, Optional
import time
from localtoolkit.applescript.utils.applescript_runner import applescript_execute
from localtoolkit.notes.utils.notes_utils import validate_note_name, escape_applescript_string


def create_note_logic(name: str, body: str, folder: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new note in the Notes app using AppleScript.
    
    Args:
        name: The title/name of the note
        body: The content of the note
        folder: Specific folder to create the note in (optional)
    
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,      # True if operation was successful
            "note": Dict,         # Created note object
            "message": str,       # Optional context message
            "metadata": dict,     # Additional metadata
            "error": str          # Only present if success is False
        }
    """
    start_time = time.time()
    
    # Validate inputs
    if not validate_note_name(name):
        return {
            "success": False,
            "note": None,
            "message": "Invalid note name",
            "error": "Note name contains invalid characters or is empty",
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }
    
    # Escape strings for AppleScript
    escaped_name = escape_applescript_string(name)
    escaped_body = escape_applescript_string(body)
    
    # Build folder creation condition
    folder_command = ""
    if folder:
        escaped_folder = escape_applescript_string(folder)
        folder_command = f"""
                -- Create or get the folder
                try
                    set targetFolder to folder "{escaped_folder}"
                on error
                    set targetFolder to make new folder with properties {{name:"{escaped_folder}"}}
                end try"""
    
    # Build creation command based on folder
    if folder:
        folder_setup = folder_command
        creation_command = f'set newNote to make new note in targetFolder with properties {{name:"{escaped_name}", body:"{escaped_body}"}}'
    else:
        folder_setup = ""
        creation_command = f'set newNote to make new note with properties {{name:"{escaped_name}", body:"{escaped_body}"}}'
    
    # Create AppleScript to create note
    applescript_code = f"""
    on run argv
        try
            tell application "Notes"
                {folder_setup}
                
                -- Create the note
                {creation_command}
                
                -- Get note properties
                set noteID to id of newNote as string
                set noteName to name of newNote
                set noteBody to body of newNote
                set modDate to modification date of newNote as string
                
                -- Get folder name
                set folderName to ""
                try
                    set noteContainer to container of newNote
                    if noteContainer is not missing value then
                        set folderName to name of noteContainer
                    end if
                end try
                
                -- Return structured data
                set fieldDelim to "<<|>>"
                return "SUCCESS:" & noteID & fieldDelim & noteName & fieldDelim & noteBody & fieldDelim & modDate & fieldDelim & folderName
                
            end tell
        on error errorMessage
            -- Return error
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
            "message": "Failed to create note",
            "error": result.get("error", "Unknown error during note creation"),
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }
    
    # Parse the output
    output = result["data"]
    
    # Check for error
    if isinstance(output, str) and output.startswith("ERROR:"):
        return {
            "success": False,
            "note": None,
            "message": "Error creating note",
            "error": output[6:],  # Remove ERROR: prefix
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
                    "folder": fields[4].strip() if len(fields) > 4 else ""
                }
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                return {
                    "success": True,
                    "note": note,
                    "message": f"Note '{name}' created successfully" + (f" in folder '{folder}'" if folder else ""),
                    "metadata": {
                        "execution_time_ms": execution_time_ms,
                        "folder": folder
                    }
                }
        
        # If we get here, something went wrong with parsing
        return {
            "success": False,
            "note": None,
            "message": "Error processing note creation response",
            "error": "Unexpected response format",
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "note": None,
            "message": "Error processing note creation data",
            "error": str(e),
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }


def register_to_mcp(mcp: FastMCP) -> None:
    """Register the notes_create_note tool with the MCP server."""
    @mcp.tool()
    def notes_create_note(
        name: str,
        body: str,
        folder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new note in the macOS Notes app.
        
        This endpoint provides a way to create new notes in the Notes app,
        with optional folder placement.
        
        Args:
            name: The title/name of the note (required)
            body: The content of the note (required)
            folder: Name of folder to create the note in (optional, creates folder if it doesn't exist)
        
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,        # True if creation was successful
                "note": dict,           # Created note object
                "message": str,         # Context message
                "metadata": {           # Additional metadata
                    "execution_time_ms": int,   # Execution time in milliseconds
                    "folder": str               # Target folder (if specified)
                },
                "error": str            # Only present if success is False
            }
            
            The note object contains:
            {
                "id": str,              # Unique Note ID
                "name": str,            # Note title/name
                "body": str,            # Full note content
                "modification_date": str, # Creation/modification date
                "folder": str           # Folder/container name
            }
        
        Error Handling:
            - Invalid name: Returns error for names with invalid characters
            - Permission issues: Returns error if Notes access is restricted
            - App not running: Attempts to launch Notes app automatically
            
        Performance:
            - Typical response time: 1-3 seconds
            - Creating folders adds minimal overhead
            
        Examples:
            # Create a simple note
            result = notes_create_note(
                name="Meeting Notes",
                body="Discussed project timeline and deliverables."
            )
            
            # Create note in specific folder
            result = notes_create_note(
                name="Shopping List",
                body="- Milk\\n- Bread\\n- Eggs",
                folder="Personal"
            )
        """
        return create_note_logic(name, body, folder)
