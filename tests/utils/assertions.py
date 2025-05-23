"""
Custom test assertions for mac-mcp tests.

This module provides custom assertions that can be used across
tests to validate common patterns like response formats.
"""


def assert_valid_response_format(response, expected_keys=None):
    """
    Assert that a response has the correct basic format.
    
    Args:
        response (dict): The response to validate
        expected_keys (list, optional): Additional keys expected in the response
        
    Raises:
        AssertionError: If the response does not have the correct format
    """
    # All responses must have a success key
    assert "success" in response, "Response missing 'success' key"
    assert isinstance(response["success"], bool), "'success' must be a boolean"
    
    # Successful responses must have a message
    if response["success"]:
        assert "message" in response, "Successful response missing 'message' key"
    
    # Error responses must have error and message
    if not response["success"]:
        assert "error" in response, "Error response missing 'error' key"
        assert "message" in response, "Error response missing 'message' key"
    
    # Check for additional expected keys
    if expected_keys:
        for key in expected_keys:
            assert key in response, f"Response missing expected key: '{key}'"


def assert_valid_messages_response(response):
    """
    Assert that a Messages app response has the correct format.
    
    Args:
        response (dict): The response to validate
        
    Raises:
        AssertionError: If the response does not have the correct format
    """
    assert_valid_response_format(response)
    
    if response["success"]:
        assert "messages" in response, "Messages response missing 'messages' key"
        assert isinstance(response["messages"], list), "'messages' must be a list"
        
        # If there are messages, check their structure
        if response["messages"]:
            message = response["messages"][0]
            assert "id" in message, "Message missing 'id' key"
            assert "text" in message, "Message missing 'text' key"
            assert "date" in message, "Message missing 'date' key"
            assert "sender" in message, "Message missing 'sender' key"
            assert "is_from_me" in message, "Message missing 'is_from_me' key"


def assert_valid_contacts_response(response):
    """
    Assert that a Contacts app response has the correct format.
    
    Args:
        response (dict): The response to validate
        
    Raises:
        AssertionError: If the response does not have the correct format
    """
    assert_valid_response_format(response)
    
    if response["success"]:
        assert "contacts" in response, "Contacts response missing 'contacts' key"
        assert isinstance(response["contacts"], list), "'contacts' must be a list"
        
        # If there are contacts, check their structure
        if response["contacts"]:
            contact = response["contacts"][0]
            assert "id" in contact, "Contact missing 'id' key"
            assert "display_name" in contact, "Contact missing 'display_name' key"


def assert_valid_applescript_response(response):
    """
    Assert that an AppleScript response has the correct format.
    
    Args:
        response (dict): The response to validate
        
    Raises:
        AssertionError: If the response does not have the correct format
    """
    assert_valid_response_format(response)
    
    if response["success"]:
        assert "data" in response, "AppleScript response missing 'data' key"
        assert "metadata" in response, "AppleScript response missing 'metadata' key"
        assert "execution_time_ms" in response["metadata"], "Metadata missing 'execution_time_ms'"


def assert_valid_reminders_response(response):
    """
    Assert that a Reminders app response has the correct format.
    
    Args:
        response (dict): The response to validate
        
    Raises:
        AssertionError: If the response does not have the correct format
    """
    assert_valid_response_format(response)
    
    if response["success"]:
        assert "data" in response, "Reminders response missing 'data' key"
        assert "metadata" in response, "Reminders response missing 'metadata' key"