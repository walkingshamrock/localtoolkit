"""
Project-level test fixtures and configuration for mac-mcp tests.

This file contains fixtures that are available to all tests in the project,
providing common mocking and testing utilities.
"""

import pytest
import json
import sys
from unittest.mock import MagicMock, patch

# Fix FastMCP import issue in tests
# This is a workaround for a pytest module loading issue
try:
    import mcp.server.auth
except ImportError:
    # Mock the problematic imports if they fail to load in pytest
    mock_mcp = MagicMock()
    sys.modules['mcp.server.auth'] = mock_mcp
    sys.modules['mcp.server.auth.provider'] = mock_mcp
    sys.modules['mcp.server.lowlevel'] = mock_mcp
    sys.modules['mcp.server.lowlevel.helper_types'] = mock_mcp
    sys.modules['mcp.server.lowlevel.server'] = mock_mcp
    sys.modules['mcp.server.stdio'] = mock_mcp
    sys.modules['mcp.types'] = mock_mcp


@pytest.fixture
def mock_applescript_executor():
    """
    Mock for the AppleScript executor that returns predefined responses.
    
    This fixture can be used by any test that needs to mock AppleScript execution.
    The mock can be configured to return different responses for different scripts.
    
    Returns:
        MagicMock: A mock object that can be used to simulate AppleScript execution.
    
    Example:
        def test_something(mock_applescript_executor):
            mock_applescript_executor.return_value = {
                "success": True,
                "data": "mock data",
                "message": "Mock execution successful"
            }
            # Test your function that uses AppleScript
    """
    mock = MagicMock()
    # Default successful response
    mock.return_value = {
        "success": True,
        "data": "",
        "message": "Mock execution successful",
        "metadata": {
            "execution_time_ms": 10,
            "parsed": False
        }
    }
    return mock


@pytest.fixture
def patch_applescript_run_code(mock_applescript_executor):
    """
    Patch the applescript_run_code function with a mock.
    
    This fixture patches the applescript_run_code function in the apps.applescript module
    with the mock_applescript_executor fixture.
    
    Args:
        mock_applescript_executor: The mock executor from the fixture above
        
    Yields:
        MagicMock: The mock object for use in tests
    """
    with patch('localtoolkit.applescript.run_code.applescript_run_code', mock_applescript_executor):
        yield mock_applescript_executor


@pytest.fixture
def standard_response_keys():
    """
    List of keys that should be present in all successful responses.
    
    Returns:
        list: List of required keys for API responses
    """
    return ["success", "message"]


@pytest.fixture
def error_response_keys():
    """
    List of keys that should be present in all error responses.
    
    Returns:
        list: List of required keys for API error responses
    """
    return ["success", "error", "message"]
