"""
Implementation of send_message for the Messages app.

This module provides functionality to send a message to a specific conversation 
in the macOS Messages app using AppleScript.
"""

from fastmcp import FastMCP
from typing import Dict, Any, List, Optional
import os
import json
from localtoolkit.applescript.utils.applescript_runner import applescript_execute

def send_message_logic(
    conversation_id: str,
    text: str,
    attachments: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Send a message to a specific conversation in the Messages app.
    
    Args:
        conversation_id: The ID of the conversation to send the message to
                         (obtained from messages_list_conversations)
        text: The text content of the message to send
        attachments: Optional list of file paths to attach to the message
    
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,     # True if operation was successful
            "message_id": str,   # ID of the sent message (if available)
            "message": str,      # Context message about the results
            "error": str         # Only present if success is False
        }
    """
    # Input validation
    if not conversation_id or not isinstance(conversation_id, str):
        return {
            "success": False,
            "error": "Invalid conversation_id: Must be a non-empty string",
            "message": "Failed to send message due to invalid conversation ID"
        }
    
    # If both text and attachments are empty, return an error
    if (not text or not isinstance(text, str) or text.strip() == "") and not attachments:
        return {
            "success": False,
            "error": "Invalid message: Must provide either text content or attachments",
            "message": "Failed to send message due to missing content"
        }
    
    # Validate attachments if provided
    if attachments:
        if not isinstance(attachments, list):
            return {
                "success": False,
                "error": "Invalid attachments: Must be a list of file paths",
                "message": "Failed to send message due to invalid attachment format"
            }
        
        # Verify attachments exist and are accessible
        for attachment in attachments:
            if not isinstance(attachment, str) or not attachment:
                return {
                    "success": False,
                    "error": f"Invalid attachment path: {attachment}",
                    "message": "Failed to send message due to invalid attachment path"
                }
            
            if not os.path.exists(attachment):
                return {
                    "success": False,
                    "error": f"Attachment file not found: {attachment}",
                    "message": "Failed to send message due to missing attachment file"
                }
    
    # Build AppleScript for sending the message
    applescript_code = """
    on run argv
        try
            tell application "Messages"
                -- Get the conversation
                set targetChat to a reference to chat id "%s"
                
                -- Send the message
    """ % conversation_id
    
    # Add text message if provided
    if text and text.strip():
        # Escape the text for AppleScript
        escaped_text = text.replace('"', '\\"')
        applescript_code += """
                set sentMessage to send "%s" to targetChat
        """ % escaped_text
    
    # Add attachment handling if needed
    if attachments and len(attachments) > 0:
        applescript_code += """
                -- Send attachments
                set attachmentFiles to {}
        """
        
        for attachment in attachments:
            # Use POSIX path to handle spaces and special characters
            applescript_code += """
                set end of attachmentFiles to POSIX file "%s"
            """ % attachment.replace('"', '\\"')
        
        applescript_code += """
                -- Send each attachment
                repeat with attachmentFile in attachmentFiles
                    send attachmentFile to targetChat
                end repeat
        """
    
    # Finish the script
    applescript_code += """
                -- Return success
                return "Message sent successfully"
            end tell
        on error errMsg
            return "ERROR:" & errMsg
        end try
    end run
    """
    
    # Execute the AppleScript
    result = applescript_execute(code=applescript_code, timeout=30)
    
    if not result.get("success", False):
        return {
            "success": False,
            "error": result.get("error", "Unknown error when sending message"),
            "message": "Failed to send message via Messages app"
        }
    
    # Check if the data contains an error message
    data = result.get("data", "")
    if isinstance(data, str) and data.startswith("ERROR:"):
        return {
            "success": False,
            "error": data[6:],  # Remove the "ERROR:" prefix
            "message": "Failed to send message via Messages app"
        }
    
    # Process successful result
    return {
        "success": True,
        "message": f"Successfully sent message to conversation {conversation_id}"
    }

def register_to_mcp(mcp: FastMCP) -> None:
    """Register the send_message tool with the MCP server."""
    @mcp.tool()
    def messages_send_message(
        conversation_id: str,
        text: str,
        attachments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send a message to a specific conversation in the macOS Messages app.
        
        Args:
            conversation_id: The ID of the conversation to send the message to
                             (obtained from messages_list_conversations)
            text: The text content of the message to send
            attachments: Optional list of file paths to attach to the message
        
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,     # True if operation was successful
                "message": str,      # Context message about the results
                "error": str         # Only present if success is False
            }
            
        Error Handling:
            - Invalid conversation_id: Returns error about invalid ID
            - Messages app access denied: Returns error about permissions
            - File not found: Returns error if attachment file doesn't exist
            - AppleScript execution failure: Returns detailed error message
        
        Performance:
            - Typical response time: 1-3 seconds for text messages
            - Attachment sending may take longer depending on file sizes
            
        Usage with other endpoints:
            This endpoint is typically used after calling messages_list_conversations:
            1. Call messages_list_conversations to get available conversations
            2. Select a conversation_id from the results
            3. Call this endpoint with the chosen conversation_id and message content
            
        Examples:
            ```python
            # Send a text message
            result = messages_send_message(
                conversation_id="iMessage;-;+1234567890",
                text="Hello, this is a test message from mac-mcp!"
            )
            # Returns: {"success": True, "message": "Successfully sent message to conversation iMessage;-;+1234567890"}
            
            # Send a message with attachment
            result = messages_send_message(
                conversation_id="iMessage;-;+1234567890",
                text="Check out this image!",
                attachments=["/path/to/image.jpg"]
            )
            ```
        """
        return send_message_logic(
            conversation_id=conversation_id,
            text=text,
            attachments=attachments,
        )