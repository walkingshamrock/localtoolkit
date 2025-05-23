"""
Test fixtures for the AppleScript integration tests.

This module contains fixtures specific to the AppleScript tests.
"""

import pytest


@pytest.fixture
def mock_applescript_success_response():
    """
    Provide a mock successful response from applescript execution.
    
    Returns:
        dict: A mock response dictionary
    """
    return {
        "success": True,
        "data": "Script executed successfully",
        "message": "AppleScript execution completed",
        "metadata": {
            "execution_time_ms": 125,
            "parsed": True
        }
    }


@pytest.fixture
def mock_applescript_error_response():
    """
    Provide a mock error response from applescript execution.
    
    Returns:
        dict: A mock error response dictionary
    """
    return {
        "success": False,
        "data": None,
        "message": "AppleScript execution failed",
        "error": "Syntax error: Expected end of line but found identifier.",
        "metadata": {
            "execution_time_ms": 45
        }
    }


@pytest.fixture
def sample_valid_applescript():
    """
    Provide a sample valid AppleScript code.
    
    Returns:
        str: Valid AppleScript code
    """
    return '''
tell application "System Events"
    display dialog "Hello, World!"
end tell
'''


@pytest.fixture
def sample_invalid_applescript():
    """
    Provide a sample invalid AppleScript code.
    
    Returns:
        str: Invalid AppleScript code with syntax error
    """
    return '''
tell application "System Events"
    display dialog
end tell
'''


@pytest.fixture
def sample_dangerous_applescript():
    """
    Provide a sample potentially dangerous AppleScript code.
    
    Returns:
        str: AppleScript code that should be blocked by security validation
    """
    return '''
do shell script "rm -rf /"
'''