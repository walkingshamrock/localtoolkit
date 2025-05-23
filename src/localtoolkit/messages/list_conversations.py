"""
Implementation of list_conversations for the Messages app.

This module provides functionality to retrieve a list of conversations
from the macOS Messages app using AppleScript.
"""

from fastmcp import FastMCP
from typing import Dict, Any, List
import json
from localtoolkit.applescript.utils.applescript_runner import applescript_execute

def list_conversations_logic() -> Dict[str, Any]:
    """
    Retrieve a list of conversations from the Messages app.
    
    Returns the conversation list with information about:
    - Conversation IDs
    - Display names
    - Group chat status
    - Last message preview
    
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,           # True if operation was successful
            "conversations": List[Dict], # List of conversation objects
            "message": str,            # Optional context message
            "error": str               # Only present if success is False
        }
    """
    applescript_code = """
    on run argv
        try
            tell application "Messages"
                set allChats to every chat
                
                -- Create a delimiter that's unlikely to appear in names/content
                set delim to "<<|>>"
                set lineDelim to "<<||>>"
                
                set outputLines to {}
                
                repeat with currentChat in allChats
                    set chatID to the id of currentChat
                    
                    -- Get chat name
                    set chatName to "Unknown"
                    try
                        set chatName to the name of currentChat
                    on error
                        -- If no name, use the first participant
                        try
                            set participantList to participants of currentChat
                            if (count of participantList) > 0 then
                                set firstPerson to item 1 of participantList
                                set chatName to the name of firstPerson
                            end if
                        end try
                    end try
                    
                    -- Count participants
                    set participantCount to 0
                    try
                        set participantList to participants of currentChat
                        set participantCount to count of participantList
                    end try
                    
                    -- Is it a group chat?
                    set isGroupChat to (participantCount > 1)
                    
                    -- Get last message preview
                    set lastMessagePreview to ""
                    try
                        if (count of (messages of currentChat)) > 0 then
                            set lastMsg to item 1 of (messages of currentChat)
                            set lastMessagePreview to the content of lastMsg
                        end if
                    end try
                    
                    -- Build the output line with delimiters between fields
                    set chatLine to chatID & delim & chatName & delim & (isGroupChat as string) & delim & lastMessagePreview
                    set end of outputLines to chatLine
                end repeat
                
                -- Join all lines with line delimiter
                set astid to AppleScript's text item delimiters
                set AppleScript's text item delimiters to lineDelim
                set outputText to outputLines as string
                set AppleScript's text item delimiters to astid
                
                return outputText
            end tell
        on error errMsg
            return "ERROR:" & errMsg
        end try
    end run
    """
    
    # Run the AppleScript
    result = applescript_execute(code=applescript_code, timeout=30)
    
    # Handle the result
    if not result.get("success", False):
        return {
            "success": False,
            "error": result.get("error", "Unknown error occurred"),
            "message": "Failed to get conversations from Messages app"
        }
    
    # Process the data
    try:
        data = result["data"]
        
        # Parse the delimited data
        conversations = []
        
        if isinstance(data, str):
            # Constants for parsing
            DELIM = "<<|>>"
            LINE_DELIM = "<<||>>"
            
            # Split into lines
            lines = data.split(LINE_DELIM)
            
            for line in lines:
                parts = line.split(DELIM)
                
                if len(parts) >= 4:
                    # Extract the fields
                    chat_id = parts[0]
                    display_name = parts[1]
                    is_group_chat = parts[2].lower() == "true"
                    last_message_text = parts[3]
                    
                    # Create conversation object
                    conversation = {
                        "id": chat_id,
                        "display_name": display_name,
                        "is_group_chat": is_group_chat,
                        "last_message": {
                            "text": last_message_text,
                            "date": "",  # We're not including date in this basic version
                            "sender": ""  # We're not including sender in this basic version
                        },
                        "participants": [],  # We're not including full participant list in this basic version
                        "unread_count": 0  # We're not including unread count in this basic version
                    }
                    
                    conversations.append(conversation)
        
        return {
            "success": True,
            "conversations": conversations,
            "message": "Successfully retrieved conversations from Messages app"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error processing conversations data"
        }

def register_to_mcp(mcp: FastMCP) -> None:
    @mcp.tool()
    def messages_list_conversations() -> Dict[str, Any]:
        """
        Retrieve a list of conversations from the macOS Messages app.
        
        Lists all available conversations (iMessage and SMS) from the Messages app,
        providing conversation IDs, display names, group chat status, and a preview
        of the last message in each conversation.
        
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,           # True if operation was successful
                "conversations": List[Dict], # List of conversation objects
                "message": str,            # Context message about the results
                "error": str               # Only present if success is False
            }
            
            Each conversation object contains:
            - "id": Conversation identifier string
            - "display_name": Name of the conversation/contact
            - "is_group_chat": Boolean indicating if this is a group conversation
            - "last_message": Object with text preview of the last message
            - "participants": List of participant information (in basic version)
            - "unread_count": Number of unread messages (in enhanced version)
        
        Error Handling:
            - Messages app access denied: Returns error with appropriate message
            - Messages database locked: Returns error about database access
            - AppleScript execution failure: Returns detailed error information
        
        Performance:
            - Typical response time: 1-3 seconds depending on number of conversations
            
        Usage with other endpoints:
            This endpoint is typically used before calling messages_get_messages:
            1. Call messages_list_conversations to get conversation IDs
            2. Call messages_get_messages with a specific conversation_id
            
        Examples:
            ```python
            result = messages_list_conversations()
            # Returns: {"success": True, "conversations": [...], "message": "Successfully retrieved conversations"}
            
            # Access the first conversation
            if result["success"] and result["conversations"]:
                first_conversation = result["conversations"][0]
                print(f"Conversation: {first_conversation['display_name']}")
                print(f"Last message: {first_conversation['last_message']['text']}")
            ```
        """
        return list_conversations_logic()