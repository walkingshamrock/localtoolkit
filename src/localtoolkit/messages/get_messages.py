"""
Implementation of get_messages for the Messages app.

This module provides functionality to retrieve messages from a specific conversation
using either direct database access (SQLite) or AppleScript.
"""

from typing import Dict, Any, List, Optional
import os
import sqlite3
import subprocess
import time
import re
import tempfile
import base64
import json
from datetime import datetime
from localtoolkit.applescript.utils.applescript_runner import applescript_execute
from fastmcp import FastMCP


def extract_url_from_payload(payload_data):
    """
    Extracts a URL from the payload_data binary blob associated with link previews

    Args:
        payload_data: Binary data from messages table payload_data column

    Returns:
        Extracted URL if found, None otherwise
    """
    if not payload_data:
        return None

    try:
        # Method 1: Direct string search in binary data
        # Convert binary data to string for pattern matching, tolerating encoding errors
        payload_str = payload_data.decode("utf-8", errors="ignore")

        # Look for URL patterns in the payload
        url_match = re.search(r'https?://[^\s"\'\}\{\]\[><]+', payload_str)
        if url_match:
            # Clean up extracted URL to remove trailing binary data
            raw_url = url_match.group(0)
            # Clean URL by removing trailing binary data markers
            clean_url = re.sub(r"[zZ]\$classname.*$", "", raw_url)
            # Remove any other trailing non-URL characters
            clean_url = re.sub(r"[;,]$", "", clean_url)
            return clean_url

        return None
    except Exception:
        return None


def query_messages(
    conversation_id: str,
    limit: int = 50,
    before_id: Optional[str] = None,
    include_attachments: bool = True
) -> Dict[str, Any]:
    """
    Query messages from a specific conversation using the most appropriate method.
    
    Args:
        conversation_id: The ID of the conversation to query
        limit: Maximum number of messages to return
        before_id: Only return messages before this message ID (for pagination)
        include_attachments: Whether to include attachment information
        
    Returns:
        A dictionary containing the messages and metadata
    """
    # Call the AppleScript implementation by default
    return get_messages_with_applescript(
        conversation_id=conversation_id,
        limit=limit,
        before_id=before_id,
        include_attachments=include_attachments
    )


def get_messages_with_applescript(
    conversation_id: str,
    limit: int = 50,
    before_id: Optional[str] = None,
    include_attachments: bool = True
) -> Dict[str, Any]:
    """
    Get messages from a specific conversation using AppleScript.
    
    Args:
        conversation_id: The ID of the conversation to get messages from
        limit: Maximum number of messages to return
        before_id: Only return messages before this message ID (for pagination)
        include_attachments: Whether to include attachment information
        
    Returns:
        A dictionary containing the messages and conversation details
    """
    start_time = time.time()
    
    # Build the AppleScript command
    script = f"""
    tell application "Messages"
        set targetChat to chat id "{conversation_id}"
        set msgCount to count of messages in targetChat
        set msgLimit to {limit}
        
        set messageList to {{}}
        set startIdx to msgCount
        
        -- Retrieve messages (most recent first)
        repeat with i from startIdx to 1 by -1
            set currentMsg to message i of targetChat
            
            -- Basic message properties
            set msgData to {{
                "text": (content of currentMsg as string),
                "date": (date sent of currentMsg as string),
                "sender": (sender of currentMsg as string),
                "id": "msg:" & (id of currentMsg as string)
            }}
            
            -- Add message to our list
            set end of messageList to msgData
            
            -- Check if we've reached our limit
            if (count of messageList) >= msgLimit then
                exit repeat
            end if
        end repeat
        
        -- Get conversation info
        set convoName to name of targetChat
        set isGroup to (count of participants of targetChat) > 1
        
        -- Build final result
        return {{
            "success": true,
            "messages": messageList,
            "conversation": {{
                "id": id of targetChat,
                "display_name": convoName,
                "is_group_chat": isGroup
            }}
        }}
    end tell
    """
    
    # Execute the AppleScript and parse the result
    result = applescript_execute(script)
    
    # Add execution time and standardize the response
    execution_time = int((time.time() - start_time) * 1000)
    
    if not result["success"]:
        return {
            "success": False,
            "messages": [],
            "conversation": None,
            "error": result["error"] if "error" in result else "Unknown error",
            "message": result["message"] if "message" in result else "Failed to retrieve messages",
            "metadata": {
                "execution_time_ms": execution_time
            }
        }
    
    # Process and standardize the response
    return {
        "success": True,
        "messages": result["data"]["messages"] if "data" in result and "messages" in result["data"] else [],
        "conversation": result["data"]["conversation"] if "data" in result and "conversation" in result["data"] else None,
        "message": f"Successfully retrieved {len(result['data']['messages']) if 'data' in result and 'messages' in result['data'] else 0} messages from conversation",
        "metadata": {
            "execution_time_ms": execution_time
        }
    }


def get_messages_logic(
    conversation_id: str,
    limit: int = 50,
    before_id: Optional[str] = None,
    skip_attachments: bool = False,
    include_attachments: bool = True,
    include_service_messages: bool = False
) -> Dict[str, Any]:
    """
    Get messages from a specific conversation.
    
    Args:
        conversation_id: The ID of the conversation to get messages from
        limit: Maximum number of messages to return
        before_id: Only return messages before this message ID (for pagination)
        skip_attachments: Whether to skip attachment processing
        include_attachments: Whether to include attachment information
        include_service_messages: Whether to include service messages
        
    Returns:
        A dictionary containing the messages and metadata
    """
    # Call the AppleScript implementation
    result = get_messages_with_applescript(
        conversation_id=conversation_id,
        limit=limit,
        before_id=before_id,
        include_attachments=not skip_attachments and include_attachments
    )
    
    return result


def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the messages_get_messages tool to the FastMCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    @mcp.tool()
    def messages_get_messages(
        conversation_id: str,
        limit: int = 50,
        skip_attachments: bool = False,
        include_service_messages: bool = False
    ) -> Dict[str, Any]:
        """
        Get messages from a specific conversation.
        
        Retrieves messages from a specified conversation in the Messages app,
        with options to control the number of messages and whether to include
        attachments and service messages.
        
        Args:
            conversation_id: The ID of the conversation to get messages from
            limit: Maximum number of messages to return
            skip_attachments: Whether to skip attachment processing
            include_service_messages: Whether to include service messages
            
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,
                "messages": List[Dict],
                "conversation_id": str,
                "count": int,
                "limit": int,
                "error": str  # Only present if success is False
            }
        """
        return get_messages_logic(
            conversation_id=conversation_id,
            limit=limit,
            skip_attachments=skip_attachments,
            include_service_messages=include_service_messages
        )