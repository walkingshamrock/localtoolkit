"""
Test fixtures for the Notes app integration tests.

This module contains fixtures specific to the Notes app tests.
"""

import pytest
import datetime


@pytest.fixture
def mock_notes():
    """Provide mock data for notes."""
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    last_week = now - datetime.timedelta(days=7)
    
    return [
        {
            "id": "x-coredata://12345678-1234-1234-1234-123456789012/Note/p1",
            "name": "Meeting Notes",
            "body": "Discussed project timeline and deliverables.\n\nAction items:\n- Review design mockups\n- Schedule follow-up meeting",
            "preview": "Discussed project timeline and deliverables. Action items: - Review design mockups...",
            "modification_date": now.strftime("%A, %B %d, %Y at %I:%M:%S %p"),
            "creation_date": yesterday.strftime("%A, %B %d, %Y at %I:%M:%S %p"),
            "folder": "Work"
        },
        {
            "id": "x-coredata://87654321-4321-4321-4321-210987654321/Note/p2",
            "name": "Shopping List",
            "body": "- Milk\n- Bread\n- Eggs\n- Apples\n- Chicken",
            "preview": "- Milk - Bread - Eggs - Apples - Chicken",
            "modification_date": yesterday.strftime("%A, %B %d, %Y at %I:%M:%S %p"),
            "creation_date": last_week.strftime("%A, %B %d, %Y at %I:%M:%S %p"),
            "folder": "Personal"
        },
        {
            "id": "x-coredata://11111111-2222-3333-4444-555555555555/Note/p3",
            "name": "Recipe Ideas",
            "body": "Pasta carbonara\nIngredients: pasta, eggs, bacon, parmesan cheese\n\nThai curry\nIngredients: coconut milk, curry paste, vegetables",
            "preview": "Pasta carbonara Ingredients: pasta, eggs, bacon, parmesan cheese Thai curry Ingredients: coco...",
            "modification_date": last_week.strftime("%A, %B %d, %Y at %I:%M:%S %p"),
            "creation_date": last_week.strftime("%A, %B %d, %Y at %I:%M:%S %p"),
            "folder": ""
        }
    ]


@pytest.fixture
def mock_list_notes_response(mock_notes):
    """
    Provide a mock successful response from list_notes.
    
    Args:
        mock_notes: The mock notes data
        
    Returns:
        dict: A mock response dictionary
    """
    return {
        "success": True,
        "notes": mock_notes,
        "message": f"Found {len(mock_notes)} note(s)",
        "metadata": {
            "total_matches": len(mock_notes),
            "execution_time_ms": 156,
            "folder_filter": None
        }
    }


@pytest.fixture
def mock_list_notes_error_response():
    """
    Provide a mock error response from list_notes.
    
    Returns:
        dict: A mock error response dictionary
    """
    return {
        "success": False,
        "notes": [],
        "message": "Failed to list notes",
        "error": "Failed to access Notes application. Permission may be required.",
        "metadata": {
            "execution_time_ms": 34
        }
    }


@pytest.fixture
def mock_created_note():
    """Provide mock data for a newly created note."""
    now = datetime.datetime.now()
    return {
        "id": "x-coredata://99999999-8888-7777-6666-555555555555/Note/p4",
        "name": "New Note",
        "body": "This is a new note created for testing.",
        "modification_date": now.strftime("%A, %B %d, %Y at %I:%M:%S %p"),
        "folder": ""
    }


@pytest.fixture
def mock_create_note_response(mock_created_note):
    """
    Provide a mock successful response from create_note.
    
    Args:
        mock_created_note: The mock created note data
        
    Returns:
        dict: A mock response dictionary
    """
    return {
        "success": True,
        "note": mock_created_note,
        "message": f"Note '{mock_created_note['name']}' created successfully",
        "metadata": {
            "execution_time_ms": 215,
            "folder": None
        }
    }


@pytest.fixture
def mock_create_note_error_response():
    """
    Provide a mock error response from create_note.
    
    Returns:
        dict: A mock error response dictionary
    """
    return {
        "success": False,
        "note": None,
        "message": "Failed to create note",
        "error": "Note name contains invalid characters or is empty",
        "metadata": {
            "execution_time_ms": 56
        }
    }


@pytest.fixture
def mock_get_note_response(mock_notes):
    """
    Provide a mock successful response from get_note.
    
    Args:
        mock_notes: The mock notes data
        
    Returns:
        dict: A mock response dictionary
    """
    note = mock_notes[0]  # Use the first note
    return {
        "success": True,
        "note": note,
        "message": f"Retrieved note '{note['name']}'",
        "metadata": {
            "execution_time_ms": 123
        }
    }


@pytest.fixture
def mock_get_note_error_response():
    """
    Provide a mock error response from get_note.
    
    Returns:
        dict: A mock error response dictionary
    """
    return {
        "success": False,
        "note": None,
        "message": "Note with ID 'invalid-id' not found",
        "error": "Note not found",
        "metadata": {
            "execution_time_ms": 67
        }
    }


@pytest.fixture
def mock_update_note_response(mock_notes):
    """
    Provide a mock successful response from update_note.
    
    Args:
        mock_notes: The mock notes data
        
    Returns:
        dict: A mock response dictionary
    """
    updated_note = mock_notes[0].copy()
    updated_note["name"] = "Updated Meeting Notes"
    updated_note["body"] = "Updated content for the meeting notes."
    updated_note["preview"] = "Updated content for the meeting notes."
    
    return {
        "success": True,
        "note": updated_note,
        "message": "Updated name and content for note 'Updated Meeting Notes'",
        "metadata": {
            "execution_time_ms": 189,
            "updated_fields": ["name", "content"]
        }
    }


@pytest.fixture
def mock_update_note_error_response():
    """
    Provide a mock error response from update_note.
    
    Returns:
        dict: A mock error response dictionary
    """
    return {
        "success": False,
        "note": None,
        "message": "Note with ID 'invalid-id' not found",
        "error": "Note not found",
        "metadata": {
            "execution_time_ms": 78
        }
    }
