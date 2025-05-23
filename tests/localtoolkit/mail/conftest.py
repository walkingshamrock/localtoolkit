"""Mail-specific test fixtures and configurations."""

import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def mock_email_data():
    """Return sample email data for testing."""
    return {
        "to": ["recipient@example.com"],
        "subject": "Test Email",
        "body": "This is a test email body.",
        "cc": ["cc@example.com"],
        "bcc": ["bcc@example.com"],
        "attachments": ["/path/to/file.pdf"],
        "html_body": False
    }


@pytest.fixture
def mock_email_html_data():
    """Return sample HTML email data for testing."""
    return {
        "to": ["recipient@example.com", "another@example.com"],
        "subject": "HTML Test Email",
        "body": "<h1>Hello</h1><p>This is an HTML email.</p>",
        "cc": [],
        "bcc": [],
        "attachments": [],
        "html_body": True
    }


@pytest.fixture
def mock_draft_success_response():
    """Return mock successful draft creation response."""
    return "20240115120000||Test Email"


@pytest.fixture
def mock_send_success_response():
    """Return mock successful send response."""
    return "SUCCESS: Email sent successfully"


@pytest.fixture
def mock_mail_error_response():
    """Return mock error response."""
    return "ERROR: Mail app not accessible"


@pytest.fixture
def mock_applescript():
    """Mock AppleScript executor for mail tests."""
    with patch('localtoolkit.mail.draft_mail.applescript_execute') as mock_draft, \
         patch('localtoolkit.mail.send_mail.applescript_execute') as mock_send:
        # Set the same return value for both
        return_value = {
            "success": True,
            "data": "Mail sent successfully",
            "metadata": {},
            "error": None
        }
        mock_draft.return_value = return_value
        mock_send.return_value = return_value
        
        # Create a wrapper that updates both mocks
        class MockWrapper:
            def __init__(self, draft_mock, send_mock):
                self._draft = draft_mock
                self._send = send_mock
                
            @property
            def return_value(self):
                return self._draft.return_value
                
            @return_value.setter
            def return_value(self, value):
                self._draft.return_value = value
                self._send.return_value = value
                
            @property
            def called(self):
                return self._draft.called or self._send.called
                
            @property
            def call_count(self):
                return self._draft.call_count + self._send.call_count
                
            @property
            def call_args(self):
                # Return whichever was actually called
                if self._send.called:
                    return self._send.call_args
                return self._draft.call_args
        
        yield MockWrapper(mock_draft, mock_send)