"""
Tests for the messages_get_messages endpoint.

This module contains tests for the messages_get_messages function, which
retrieves messages from a specific conversation in the Messages app.
"""

import pytest
from unittest.mock import patch, MagicMock
from tests.utils.assertions import assert_valid_response_format


# Create a mock for direct testing
def get_mock_messages():
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
            }
        ],
        "conversation_info": {
            "id": "iMessage;-;+15551234567",
            "display_name": "John Doe",
            "is_group_chat": False
        },
        "message": "Successfully retrieved messages from conversation"
    }


@pytest.mark.unit
def test_get_messages_valid_input():
    """Test messages_get_messages with valid input parameters."""
    # Create a direct patch of the main function
    with patch('localtoolkit.messages.get_messages.get_messages_with_applescript') as mock_get:
        # Set the mock to return our predefined response
        mock_get.return_value = get_mock_messages()
        
        # Import the function after patching
        from localtoolkit.messages.get_messages import get_messages_logic
        
        # Test with minimum required parameters
        result = get_messages_logic(conversation_id="iMessage;-;+15551234567")
        
        # Verify the response format
        assert result["success"] is True
        assert "messages" in result
        assert isinstance(result["messages"], list)
        assert len(result["messages"]) > 0
        
        # Verify message structure
        message = result["messages"][0]
        assert "id" in message
        assert "text" in message
        assert "date" in message
        assert "sender" in message or "is_from_me" in message


@pytest.mark.unit
def test_get_messages_with_limit(mock_messages_data):
    """Test message retrieval with a specific limit."""
    with patch('localtoolkit.messages.get_messages.get_messages_with_applescript') as mock_get:
        # Configure mock to return our fixture data
        mock_get.return_value = mock_messages_data
        
        # Import our function for testing
        from localtoolkit.messages.get_messages import get_messages_logic

        # Test with a limit of 5 messages
        result = get_messages_logic(conversation_id="iMessage;-;+15551234567", limit=5)
        
        assert result["success"] is True
        assert len(result["messages"]) <= 5


@pytest.mark.unit
def test_get_messages_with_before_id():
    """Test messages_get_messages with a before_id parameter."""
    # Create a direct patch of the main function
    with patch('localtoolkit.messages.get_messages.get_messages_with_applescript') as mock_get:
        # Set the mock to return our predefined response
        mock_get.return_value = get_mock_messages()
        
        # Import the function after patching
        from localtoolkit.messages.get_messages import get_messages_logic
        
        # Test with pagination using before_id
        result = get_messages_logic(
            conversation_id="iMessage;-;+15551234567",
            before_id="p:12346"
        )
        
        assert result["success"] is True


@pytest.mark.unit
def test_get_messages_with_attachments():
    """Test messages_get_messages with include_attachments=True."""
    # Create a direct patch of the main function
    with patch('localtoolkit.messages.get_messages.get_messages_with_applescript') as mock_get:
        # Set the mock to return our predefined response
        mock_get.return_value = get_mock_messages()
        
        # Import the function after patching
        from localtoolkit.messages.get_messages import get_messages_logic
        
        # Test with attachments included
        result = get_messages_logic(
            conversation_id="iMessage;-;+15551234567",
            include_attachments=True
        )
        
        assert result["success"] is True


@pytest.mark.unit
def test_get_messages_invalid_conversation_id():
    """Test messages_get_messages with an invalid conversation ID."""
    # Create a direct patch of the main function
    with patch('localtoolkit.messages.get_messages.get_messages_with_applescript') as mock_get:
        # Set mock to return error
        mock_get.return_value = {
            "success": False,
            "error": "Failed to find conversation with ID invalid_id",
            "message": "Failed to execute AppleScript"
        }
        
        # Import the function after patching
        from localtoolkit.messages.get_messages import get_messages_logic
        
        # Test with invalid ID
        result = get_messages_logic(conversation_id="invalid_id")
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert "error" in result


@pytest.mark.unit
def test_get_messages_applescript_error():
    """Test messages_get_messages when AppleScript execution fails."""
    # Create a direct patch of the main function
    with patch('localtoolkit.messages.get_messages.get_messages_with_applescript') as mock_get:
        # Set mock to return error
        mock_get.return_value = {
            "success": False,
            "error": "Application not responding",
            "message": "Failed to execute AppleScript"
        }
        
        # Import the function after patching
        from localtoolkit.messages.get_messages import get_messages_logic
        
        # Test with error
        result = get_messages_logic(conversation_id="iMessage;-;+15551234567")
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert "error" in result


@pytest.mark.unit
def test_get_messages_empty_conversation():
    """Test messages_get_messages with a conversation that has no messages."""
    # Create a direct patch of the main function
    with patch('localtoolkit.messages.get_messages.get_messages_with_applescript') as mock_get:
        # Set mock to return empty messages
        mock_get.return_value = {
            "success": True,
            "messages": [],
            "conversation_info": {
                "id": "iMessage;-;+15559876543",
                "display_name": "New Contact",
                "is_group_chat": False
            },
            "message": "Retrieved 0 messages from conversation"
        }
        
        # Import the function after patching
        from localtoolkit.messages.get_messages import get_messages_logic
        
        # Test with empty conversation
        result = get_messages_logic(conversation_id="iMessage;-;+15559876543")
        
        assert result["success"] is True
        assert "messages" in result
        assert isinstance(result["messages"], list)
        assert len(result["messages"]) == 0
