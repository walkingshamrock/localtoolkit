"""
Notes utilities for LocalToolKit.

Helper functions for Notes app integration including date formatting,
text processing, and validation.
"""

import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime


def format_note_date(date_str: str) -> str:
    """
    Format a Notes app date string into a standardized ISO 8601 format.
    
    Args:
        date_str: Raw date string from Notes app (e.g., "Monday, January 1, 2024 at 12:00:00 PM")
        
    Returns:
        Formatted date string in ISO 8601 format, or original stripped string if parsing fails
    """
    if not date_str:
        return ""
    try:
        # This format handles dates like "Monday, January 1, 2024 at 12:00:00 PM"
        # Adjust strptime format if AppleScript output varies or for locale considerations
        dt_obj = datetime.strptime(date_str.strip(), "%A, %B %d, %Y at %I:%M:%S %p")
        return dt_obj.isoformat()
    except ValueError:
        # Fallback to returning the stripped original string if parsing fails
        return date_str.strip()


def extract_note_preview(body: str, max_length: int = 100) -> str:
    """
    Extract a preview from note body text.
    
    Args:
        body: Full note body text
        max_length: Maximum length of preview
        
    Returns:
        Preview text
    """
    if not body:
        return ""
    
    # Remove extra whitespace and newlines
    cleaned = re.sub(r'\s+', ' ', body.strip())
    
    if len(cleaned) <= max_length:
        return cleaned
    
    # Truncate and add ellipsis
    return cleaned[:max_length].rstrip() + "..."


def validate_note_name(name: str) -> bool:
    """
    Validate a note name/title.
    
    Args:
        name: The note name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not name or not name.strip():
        return False
    
    # Notes app has some restrictions on note names
    # Check for common problematic characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    return not any(char in name for char in invalid_chars)


def escape_applescript_string(text: str) -> str:
    """
    Escape a string for safe use in AppleScript.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text safe for AppleScript
    """
    if not text:
        return ""
    
    # Escape quotes and backslashes
    escaped = text.replace('\\', '\\\\').replace('"', '\\"')
    return escaped


def parse_notes_list_output(output: str) -> List[Dict[str, Any]]:
    """
    Parse structured output from Notes list AppleScript.
    
    Args:
        output: Raw output from AppleScript
        
    Returns:
        List of note dictionaries
    """
    notes = []
    
    if not output or output.startswith("ERROR:"):
        return notes
    
    try:
        # Split by note delimiter
        note_entries = output.split("<<||>>")
        
        for i, entry in enumerate(note_entries):
            if not entry.strip():
                continue
                
            try:
                fields = entry.split("<<|>>")
                if len(fields) >= 4:
                    note = {
                        "id": fields[0].strip(),
                        "name": fields[1].strip(),
                        "body": fields[2].strip(),
                        "modification_date": format_note_date(fields[3].strip()),
                        "folder": fields[4].strip() if len(fields) > 4 else ""
                    }
                    
                    # Add preview
                    note["preview"] = extract_note_preview(note["body"])
                    notes.append(note)
                else:
                    logging.warning(f"Skipping malformed note entry {i}: insufficient fields ({len(fields)} < 4)")
            except Exception as e:
                logging.warning(f"Failed to parse note entry {i}: {e}")
                continue
                
    except Exception as e:
        logging.error(f"Failed to parse notes list output: {e}")
        return []
    
    return notes
