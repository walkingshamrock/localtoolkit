"""
Test fixtures for the MCP server integration tests.

This module contains fixtures specific to the MCP server tests.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_fastmcp():
    """
    Mock FastMCP server instance.
    
    Returns:
        MagicMock: Mock FastMCP server
    """
    mock_server = MagicMock()
    
    # Make tool() return a decorator that returns the original function
    def tool_decorator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    mock_server.tool = MagicMock(side_effect=tool_decorator)
    mock_server.run = MagicMock()
    return mock_server


@pytest.fixture
def mock_tool_registry():
    """
    Mock tool registry for tracking registered tools.
    
    Returns:
        dict: Dictionary to track registered tools
    """
    return {}


@pytest.fixture
def sample_tool_function():
    """
    Sample tool function for testing registration.
    
    Returns:
        function: A sample tool function
    """
    def sample_tool(param1: str, param2: int = 10) -> dict:
        """Sample tool for testing."""
        return {
            "success": True,
            "param1": param1,
            "param2": param2,
            "message": "Sample tool executed"
        }
    
    return sample_tool