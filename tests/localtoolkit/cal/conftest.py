"""Calendar-specific test fixtures and configurations."""

import pytest
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_calendar_data():
    """Return sample calendar data for testing."""
    return [
        {
            "name": "Personal",
            "id": "Personal",
            "description": "",
            "color": "default",
            "type": "calendar"
        },
        {
            "name": "Work",
            "id": "Work", 
            "description": "",
            "color": "default",
            "type": "calendar"
        },
        {
            "name": "Family",
            "id": "Family",
            "description": "",
            "color": "default",
            "type": "calendar"
        }
    ]


@pytest.fixture
def mock_event_data():
    """Return sample event data for testing."""
    return [
        {
            "id": "Team Meeting-1",
            "summary": "Team Meeting",
            "start_date": "2024-01-15T10:00:00",
            "end_date": "2024-01-15T11:00:00",
            "location": "",
            "description": "",
            "all_day": False,
            "calendar_id": "Work"
        },
        {
            "id": "Lunch Break-2",
            "summary": "Lunch Break",
            "start_date": "2024-01-15T12:00:00",
            "end_date": "2024-01-15T13:00:00",
            "location": "",
            "description": "",
            "all_day": False,
            "calendar_id": "Personal"
        },
        {
            "id": "Birthday Party-3",
            "summary": "Birthday Party",
            "start_date": "2024-01-16T18:00:00",
            "end_date": "2024-01-16T21:00:00",
            "location": "",
            "description": "",
            "all_day": False,
            "calendar_id": "Family"
        }
    ]


@pytest.fixture
def mock_created_event_data():
    """Return sample created event data for testing."""
    return {
        "event_id": "new-event-123",
        "summary": "New Meeting",
        "start_date": "2024-01-20T14:00:00",
        "end_date": "2024-01-20T15:00:00",
        "location": "Conference Room A",
        "description": "Quarterly review",
        "all_day": False,
        "calendar_id": "Work"
    }


@pytest.fixture
def mock_applescript():
    """Mock AppleScript executor for calendar tests."""
    with patch('localtoolkit.calendar.utils.calendar_utils.applescript_execute') as mock:
        mock.return_value = {
            "success": True,
            "data": "[]",
            "metadata": {},
            "error": None
        }
        yield mock