"""
Implementation of list_notes for the Notes app.

This module provides functionality to list notes from the macOS Notes app using AppleScript.
"""

from fastmcp import FastMCP
from typing import Dict, Any, List, Optional
import time
from localtoolkit.applescript.utils.applescript_runner import applescript_execute
from localtoolkit.notes.utils.notes_utils import parse_notes_list_output


def list_notes_logic(limit: int = 20, folder: Optional[str] = None) -> Dict[str, Any]:
    """
    List notes from the Notes app using AppleScript.
    
    Args:
        limit: Maximum number of notes to return (default: 20)
        folder: Specific folder to list notes from (optional)
    
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,      # True if operation was successful
            "notes": List[Dict],  # List of note objects
            "message": str,       # Optional context message
            "metadata": dict,     # Additional metadata
            "error": str          # Only present if success is False
        }
    """
    start_time = time.time()
    
    # Build folder filter condition
    folder_condition = ""
    if folder:
        escaped_folder = folder.replace('"', '\\"')
        folder_condition = f'whose container is folder "{escaped_folder}"'
    
    # Create AppleScript to list notes
    applescript_code = f"""
    on run argv
        set maxResults to {limit}
        
        try
            tell application "Notes"
                -- Prepare result containers
                set foundNotes to {{}}
                
                -- Create delimiters for structured output
                set fieldDelim to "<<|>>"
                set itemDelim to "<<||>>"
                
                -- Get notes (with optional folder filter)
                {"set allNotes to (every note " + folder_condition + ")" if folder_condition else "set allNotes to (every note)"}
                
                -- Get total found and limit results
                set totalFound to count of allNotes
                
                if totalFound > maxResults then
                    set notesToProcess to maxResults
                else
                    set notesToProcess to totalFound
                end if
                
                -- Process each note
                repeat with i from 1 to notesToProcess
                    set currentNote to item i of allNotes
                    
                    -- Get note properties
                    set noteID to id of currentNote as string
                    set noteName to name of currentNote
                    set noteBody to body of currentNote
                    set modDate to modification date of currentNote as string
                    
                    -- Get folder name (container)
                    set folderName to ""
                    try
                        set noteContainer to container of currentNote
                        if noteContainer is not missing value then
                            set folderName to name of noteContainer
                        end if
                    end try
                    
                    -- Format note data with delimiters
                    set noteData to noteID & fieldDelim & noteName & fieldDelim & noteBody & fieldDelim & modDate & fieldDelim & folderName
                    
                    -- Add to results list
                    set end of foundNotes to noteData
                end repeat
                
                -- Format final result with delimiter
                set resultText to ""
                if (count of foundNotes) > 0 then
                    repeat with i from 1 to (count of foundNotes)
                        set resultText to resultText & (item i of foundNotes)
                        if i < (count of foundNotes) then
                            set resultText to resultText & itemDelim
                        end if
                    end repeat
                end if
                
                -- Return with counts (always include delimiter even if no notes)
                return (totalFound as string) & itemDelim & resultText
                
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
            "notes": [],
            "message": "Failed to list notes",
            "error": result.get("error", "Unknown error during notes listing"),
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
            "notes": [],
            "message": "Error listing notes",
            "error": output[6:],  # Remove ERROR: prefix
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        }
    
    # Process valid output
    try:
        # Split by the item delimiter to get the total count and note data
        parts = output.split("<<||>>", 1)
        
        # Clean up the count string by removing any trailing commas or whitespace
        count_str = parts[0].strip().rstrip(',').strip()
        total_count = int(count_str)
        
        notes = []
        
        if len(parts) > 1 and parts[1]:
            notes = parse_notes_list_output(parts[1])
        
        # Return final result
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "success": True,
            "notes": notes,
            "message": f"Found {len(notes)} note(s)" + (f" in folder '{folder}'" if folder else ""),
            "metadata": {
                "total_matches": total_count,
                "execution_time_ms": execution_time_ms,
                "folder_filter": folder
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "notes": [],
            "message": "Error processing notes data",
            "error": str(e),
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "raw_output": output[:200] if isinstance(output, str) else str(output)[:200]  # First 200 chars for debugging
            }
        }


def register_to_mcp(mcp: FastMCP) -> None:
    """Register the notes_list_notes tool with the MCP server."""
    @mcp.tool()
    def notes_list_notes(
        limit: int = 20,
        folder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List notes from the macOS Notes app.
        
        This endpoint provides a way to retrieve notes from the Notes app,
        with optional filtering by folder and result limiting.
        
        Args:
            limit: Maximum number of notes to return (default: 20)
            folder: Name of specific folder to list notes from (optional)
        
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,        # True if listing was successful
                "notes": list,          # List of note objects
                "message": str,         # Context message
                "metadata": {           # Additional metadata
                    "total_matches": int,       # Total notes before limiting
                    "execution_time_ms": int,   # Execution time in milliseconds
                    "folder_filter": str        # Applied folder filter (if any)
                },
                "error": str            # Only present if success is False
            }
            
            Each note object contains:
            {
                "id": str,              # Unique Note ID
                "name": str,            # Note title/name
                "body": str,            # Full note content
                "preview": str,         # Preview of note content
                "modification_date": str, # Last modification date
                "folder": str           # Folder/container name
            }
        
        Error Handling:
            - Permission issues: Returns error if Notes access is restricted
            - Invalid folder: Returns error if specified folder doesn't exist
            - App not running: Attempts to launch Notes app automatically
            
        Performance:
            - Response time increases with the number of notes
            - Using folder filtering improves performance
            - Limiting results reduces processing time
            
        Examples:
            # List all notes (up to 20)
            result = notes_list_notes()
            
            # List notes from specific folder
            result = notes_list_notes(folder="Work")
            
            # List more notes
            result = notes_list_notes(limit=50)
        """
        return list_notes_logic(limit, folder)
