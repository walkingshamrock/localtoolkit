"""
Test fixtures specific to the Messages app.

This module provides fixtures for testing the Messages app functionality.
"""

import pytest
from unittest.mock import MagicMock
from tests.utils.generators import generate_message, generate_conversation
import json


@pytest.fixture
def mock_messages_response():
    """
    Generate a mock response for the messages_get_messages endpoint.
    
    Returns:
        dict: A mock messages response with realistic data
    """
    messages = [
        generate_message(text="Hello there!", is_from_me=False, days_ago=2),
        generate_message(text="Hi! How are you?", is_from_me=True, days_ago=2),
        generate_message(text="I'm good, thanks. Want to meet up tomorrow?", is_from_me=False, days_ago=1),
        generate_message(text="Sure, how about 2pm at the coffee shop?", is_from_me=True, days_ago=1),
        generate_message(text="Sounds great! See you then.", is_from_me=False, days_ago=0)
    ]
    
    conversation = {
        "id": "iMessage;-;+15551234567",
        "display_name": "John Doe",
        "is_group_chat": False,
        "participants": [
            {"name": "John Doe", "id": "person:12345"},
            {"name": "Me", "id": "me"}
        ]
    }
    
    return {
        "success": True,
        "messages": messages,
        "conversation": conversation,
        "message": "Successfully retrieved 5 messages from conversation"
    }


@pytest.fixture
def mock_conversations_response():
    """
    Generate a mock response for the messages_list_conversations endpoint.
    
    Returns:
        dict: A mock conversations response with realistic data
    """
    conversations = [
        generate_conversation(display_name="John Doe", is_group_chat=False, message_count=5),
        generate_conversation(display_name="Family Chat", is_group_chat=True, message_count=10),
        generate_conversation(display_name="Work Team", is_group_chat=True, message_count=8),
        generate_conversation(display_name="Jane Smith", is_group_chat=False, message_count=3)
    ]
    
    return {
        "success": True,
        "conversations": [
            {
                "id": conv["id"],
                "display_name": conv["display_name"],
                "is_group_chat": conv["is_group_chat"],
                "last_message": conv["last_message"],
                "participants": conv["participants"]
            } for conv in conversations
        ],
        "message": "Successfully retrieved 4 conversations"
    }


@pytest.fixture
def mock_send_message_response():
    """
    Generate a mock response for the messages_send_message endpoint.
    
    Returns:
        dict: A mock send message response
    """
    return {
        "success": True,
        "message": "Successfully sent message to conversation iMessage;-;+15551234567"
    }


@pytest.fixture
def mock_applescript_messages_executor(mock_applescript_executor):
    """
    Configure the mock AppleScript executor with Messages-specific responses.
    
    Args:
        mock_applescript_executor: The base mock executor from the fixture
        
    Returns:
        MagicMock: Configured mock executor
    """
    def side_effect(code, params=None, timeout=30, debug=False):
        # Mock for messages_list_conversations
        if "tell application \"Messages\" to get every chat" in code:
            return {
                "success": True,
                "data": json.dumps([
                    {
                        "id": "iMessage;-;+15551234567",
                        "display_name": "John Doe",
                        "is_group_chat": False,
                        "last_message": {
                            "text": "Sounds great! See you then.",
                            "date": "2025-05-17T14:30:00Z"
                        }
                    },
                    {
                        "id": "iMessage;-;chat123456",
                        "display_name": "Family Chat",
                        "is_group_chat": True,
                        "last_message": {
                            "text": "Don't forget the picnic tomorrow!",
                            "date": "2025-05-18T10:15:00Z"
                        }
                    }
                ]),
                "message": "Successfully executed AppleScript",
                "execution_time_ms": 120
            }
        
        # Mock for messages_get_messages
        elif "tell application \"Messages\" to get" in code or "targetChat" in code:
            return {
                "success": True,
                "data": json.dumps({
                    "messages": [
                        {
                            "id": "p:12345",
                            "text": "Hello there!",
                            "date": "2025-05-17T10:00:00Z",
                            "is_from_me": False,
                            "sender": {
                                "name": "John Doe",
                                "id": "person:12345"
                            }
                        },
                        {
                            "id": "p:12346",
                            "text": "Hi! How are you?",
                            "date": "2025-05-17T10:05:00Z",
                            "is_from_me": True,
                            "sender": {
                                "name": "Me",
                                "id": "me"
                            }
                        }
                    ],
                    "conversation": {
                        "id": "iMessage;-;+15551234567",
                        "display_name": "John Doe",
                        "is_group_chat": False
                    }
                }),
                "message": "Successfully executed AppleScript",
                "execution_time_ms": 150
            }
        
        # Mock for messages_send_message
        elif "tell application \"Messages\" to send" in code:
            return {
                "success": True,
                "data": "Message sent",
                "message": "Successfully executed AppleScript",
                "execution_time_ms": 80
            }
        
        # Default response
        return {
            "success": True,
            "data": "mock_data",
            "message": "Mock execution successful",
            "execution_time_ms": 10
        }
    
    mock_applescript_executor.side_effect = side_effect
    return mock_applescript_executor


@pytest.fixture
def mock_messages_data():
    """
    Generate mock messages data for query_messages function.
    
    Returns:
        dict: A mock messages data structure with realistic data
    """
    return {
        "success": True,
        "messages": [
            {
                "id": "p:12345",
                "text": "Hello there!",
                "date": "2025-05-17T10:00:00Z",
                "is_from_me": False,
                "sender": "John Doe"
            },
            {
                "id": "p:12346",
                "text": "Hi! How are you?",
                "date": "2025-05-17T10:05:00Z",
                "is_from_me": True,
                "sender": "Me"
            },
            {
                "id": "p:12347",
                "text": "I'm good, thanks. Want to meet up tomorrow?",
                "date": "2025-05-18T09:30:00Z",
                "is_from_me": False,
                "sender": "John Doe"
            }
        ],
        "conversation_id": "iMessage;-;+15551234567",
        "count": 3,
        "metadata": {
            "execution_time_ms": 156
        }
    }
