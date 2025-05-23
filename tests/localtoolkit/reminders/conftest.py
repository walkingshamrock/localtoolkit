"""
Test fixtures for the Reminders app integration tests.

This module contains fixtures specific to the Reminders app tests.
"""

import pytest
import datetime


@pytest.fixture
def mock_reminder_lists():
    """Provide mock data for reminder lists."""
    return [
        {
            "name": "Reminders",
            "id": "x-apple-reminder://F0A0F342-FC00-1234-B630-CFBE2EB928A1"
        },
        {
            "name": "Work",
            "id": "x-apple-reminder://B1D2C234-AA00-4567-9012-ABCDE1234567"
        },
        {
            "name": "Shopping",
            "id": "x-apple-reminder://C8B4A123-DD22-4567-5678-FEDCBA987654"
        }
    ]


@pytest.fixture
def mock_reminder_lists_response(mock_reminder_lists):
    """
    Provide a mock successful response from get_reminder_lists.
    
    Args:
        mock_reminder_lists: The mock reminder lists data
        
    Returns:
        dict: A mock response dictionary
    """
    return {
        "success": True,
        "data": mock_reminder_lists,
        "metadata": {
            "execution_time_ms": 156
        },
        "error": None
    }


@pytest.fixture
def mock_reminder_lists_error_response():
    """
    Provide a mock error response from get_reminder_lists.
    
    Returns:
        dict: A mock error response dictionary
    """
    return {
        "success": False,
        "data": None,
        "metadata": {
            "execution_time_ms": 34
        },
        "error": "Failed to access Reminders application. Permission may be required."
    }


@pytest.fixture
def mock_reminders():
    """Provide mock data for reminder items."""
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    next_week = datetime.datetime.now() + datetime.timedelta(days=7)
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    
    return [
        {
            "title": "Buy groceries",
            "id": "x-apple-reminder://TASK-12345-ABCD-1234-EFGH-12345678",
            "completed": False,
            "due_date": tomorrow.isoformat(),
            "notes": "Need milk, eggs, bread",
            "priority": 1,  # Medium priority
            "list_id": "x-apple-reminder://F0A0F342-FC00-1234-B630-CFBE2EB928A1"  # Reminders list
        },
        {
            "title": "Prepare presentation",
            "id": "x-apple-reminder://TASK-67890-WXYZ-5678-IJKL-87654321",
            "completed": False,
            "due_date": next_week.isoformat(),
            "notes": "Client meeting presentation",
            "priority": 0,  # High priority
            "list_id": "x-apple-reminder://B1D2C234-AA00-4567-9012-ABCDE1234567"  # Work list
        },
        {
            "title": "Call mom",
            "id": "x-apple-reminder://TASK-13579-PQRS-9876-MNOP-24680135",
            "completed": True,
            "due_date": yesterday.isoformat(),
            "notes": "Birthday wishes",
            "priority": 2,  # Low priority
            "list_id": "x-apple-reminder://F0A0F342-FC00-1234-B630-CFBE2EB928A1"  # Reminders list
        }
    ]


@pytest.fixture
def mock_get_reminders_response(mock_reminders):
    """
    Provide a mock successful response for get_reminders.
    
    Args:
        mock_reminders: The mock reminders data
        
    Returns:
        dict: A mock response dictionary
    """
    return {
        "success": True,
        "data": mock_reminders,
        "metadata": {
            "execution_time_ms": 178,
            "count": len(mock_reminders)
        },
        "error": None
    }


@pytest.fixture
def mock_get_reminders_error_response():
    """
    Provide a mock error response for get_reminders.
    
    Returns:
        dict: A mock error response dictionary
    """
    return {
        "success": False,
        "data": None,
        "metadata": {
            "execution_time_ms": 45
        },
        "error": "Failed to retrieve reminders. Permission may be required."
    }


@pytest.fixture
def mock_create_reminder_response():
    """
    Provide a mock successful response for create_reminder.
    
    Returns:
        dict: A mock response dictionary with the created reminder ID
    """
    return {
        "success": True,
        "data": {
            "id": "x-apple-reminder://TASK-NEW12-ABCD-1234-EFGH-98765432"
        },
        "metadata": {
            "execution_time_ms": 215
        },
        "error": None
    }


@pytest.fixture
def mock_create_reminder_error_response():
    """
    Provide a mock error response for create_reminder.
    
    Returns:
        dict: A mock error response dictionary
    """
    return {
        "success": False,
        "data": None,
        "metadata": {
            "execution_time_ms": 56
        },
        "error": "Failed to create reminder. Invalid list ID or permission issue."
    }