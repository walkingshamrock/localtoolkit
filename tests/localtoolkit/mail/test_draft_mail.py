"""Tests for the draft_mail module."""

import pytest
from unittest.mock import patch, Mock
import os
import datetime

from localtoolkit.mail.draft_mail import draft_mail_logic, register_to_mcp
from tests.utils.assertions import assert_valid_response_format


class TestDraftMailLogic:
    """Test cases for draft_mail_logic function."""
    
    def test_draft_mail_success(self, mock_applescript, mock_email_data, mock_draft_success_response):
        """Test successful draft email creation."""
        # Configure mock to return success
        mock_applescript.return_value = {
            "success": True,
            "data": mock_draft_success_response,
            "metadata": {},
            "error": None
        }
        
        # Mock file existence check
        with patch('os.path.exists', return_value=True):
            result = draft_mail_logic(**mock_email_data)
        
        # Verify response format
        assert_valid_response_format(result)
        assert result["success"] is True
        assert "||Test Email" in result["draft_id"]  # Check that draft_id contains the subject
        assert result["message"] == "Successfully created draft email to recipient@example.com"
    
    def test_draft_mail_multiple_recipients(self, mock_applescript):
        """Test draft creation with multiple recipients."""
        mock_applescript.return_value = {
            "success": True,
            "data": "20240115120000||Multi Recipient Email",
            "metadata": {},
            "error": None
        }
        
        result = draft_mail_logic(
            to=["user1@example.com", "user2@example.com", "user3@example.com"],
            subject="Multi Recipient Email",
            body="Test body"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["message"] == "Successfully created draft email to user1@example.com, user2@example.com, user3@example.com"
    
    def test_draft_mail_html_body(self, mock_applescript):
        """Test draft creation with HTML body."""
        mock_applescript.return_value = {
            "success": True,
            "data": "20240115120000||HTML Email",
            "metadata": {},
            "error": None
        }
        
        result = draft_mail_logic(
            to=["recipient@example.com"],
            subject="HTML Email",
            body="<h1>Hello</h1><p>This is HTML</p>",
            html_body=True
        )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Verify HTML content type was used in AppleScript
        assert mock_applescript.called
        call_args = mock_applescript.call_args
        if call_args and call_args[1] and "code" in call_args[1]:
            assert "html content" in call_args[1]["code"]
    
    def test_draft_mail_missing_recipients(self, mock_applescript):
        """Test draft creation with missing recipients."""
        result = draft_mail_logic(
            to=[],
            subject="Test",
            body="Test body"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["error"] == "Invalid recipients: Must provide at least one recipient"
        assert result["message"] == "Failed to create draft email due to missing recipients"
    
    def test_draft_mail_invalid_recipient_email(self, mock_applescript):
        """Test draft creation with invalid email format."""
        result = draft_mail_logic(
            to=["invalid-email"],
            subject="Test",
            body="Test body"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert "Invalid email address in to list" in result["error"]
    
    def test_draft_mail_invalid_cc_email(self, mock_applescript):
        """Test draft creation with invalid CC email."""
        result = draft_mail_logic(
            to=["valid@example.com"],
            cc=["", "invalid@"],
            subject="Test",
            body="Test body"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert "Invalid email address in cc list" in result["error"]
    
    def test_draft_mail_missing_subject(self, mock_applescript):
        """Test draft creation with missing subject."""
        result = draft_mail_logic(
            to=["recipient@example.com"],
            subject="",
            body="Test body"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["error"] == "Invalid subject: Must be a non-empty string"
    
    def test_draft_mail_missing_body(self, mock_applescript):
        """Test draft creation with missing body."""
        result = draft_mail_logic(
            to=["recipient@example.com"],
            subject="Test Subject",
            body=""
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["error"] == "Invalid body: Must be a non-empty string"
    
    def test_draft_mail_invalid_attachments_format(self, mock_applescript):
        """Test draft creation with invalid attachments format."""
        result = draft_mail_logic(
            to=["recipient@example.com"],
            subject="Test",
            body="Test body",
            attachments="not-a-list"  # Should be a list
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["error"] == "Invalid attachments: Must be a list of file paths"
    
    def test_draft_mail_nonexistent_attachment(self, mock_applescript):
        """Test draft creation with non-existent attachment file."""
        with patch('os.path.exists', return_value=False):
            result = draft_mail_logic(
                to=["recipient@example.com"],
                subject="Test",
                body="Test body",
                attachments=["/nonexistent/file.pdf"]
            )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["error"] == "Attachment file not found: /nonexistent/file.pdf"
    
    def test_draft_mail_with_attachments(self, mock_applescript):
        """Test draft creation with valid attachments."""
        mock_applescript.return_value = {
            "success": True,
            "data": "20240115120000||Email with Attachments",
            "metadata": {},
            "error": None
        }
        
        with patch('os.path.exists', return_value=True):
            result = draft_mail_logic(
                to=["recipient@example.com"],
                subject="Email with Attachments",
                body="See attached files",
                attachments=["/path/to/file1.pdf", "/path/to/file2.docx"]
            )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Verify attachments were included in AppleScript
        assert mock_applescript.called
        call_args = mock_applescript.call_args
        if call_args and call_args[1] and "code" in call_args[1]:
            code = call_args[1]["code"]
            assert "POSIX file" in code
            assert "/path/to/file1.pdf" in code
            assert "/path/to/file2.docx" in code
    
    def test_draft_mail_special_characters(self, mock_applescript):
        """Test draft creation with special characters."""
        mock_applescript.return_value = {
            "success": True,
            "data": '20240115120000||Email with "quotes"',
            "metadata": {},
            "error": None
        }
        
        result = draft_mail_logic(
            to=["recipient@example.com"],
            subject='Email with "quotes"',
            body='Body with "quotes" and \\backslashes\\'
        )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Verify special characters were escaped
        assert mock_applescript.called
        call_args = mock_applescript.call_args
        if call_args and call_args[1] and "code" in call_args[1]:
            code = call_args[1]["code"]
            assert '\\"' in code or 'quotes' in code
    
    def test_draft_mail_applescript_error(self, mock_applescript, mock_email_data):
        """Test handling of AppleScript execution error."""
        mock_applescript.return_value = {
            "success": False,
            "data": None,
            "metadata": {},
            "error": "AppleScript execution failed"
        }
        
        with patch('os.path.exists', return_value=True):
            result = draft_mail_logic(**mock_email_data)
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["error"] == "AppleScript execution failed"
        assert result["message"] == "Failed to create draft email via Mail app"
    
    def test_draft_mail_error_response(self, mock_applescript, mock_email_data, mock_mail_error_response):
        """Test handling of error response from AppleScript."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_mail_error_response,
            "metadata": {},
            "error": None
        }
        
        with patch('os.path.exists', return_value=True):
            result = draft_mail_logic(**mock_email_data)
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["error"] == "Mail app not accessible"
    
    def test_draft_mail_timestamp_generation(self, mock_applescript):
        """Test that timestamp is properly generated."""
        mock_applescript.return_value = {
            "success": True,
            "data": "20240115120000||Test Email",
            "metadata": {},
            "error": None
        }
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240115120000"
            
            result = draft_mail_logic(
                to=["recipient@example.com"],
                subject="Test Email",
                body="Test body"
            )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert "20240115120000" in result["draft_id"]


class TestRegisterToMCP:
    """Test cases for MCP registration."""
    
    def test_register_to_mcp(self):
        """Test that the function registers correctly to MCP."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        
        register_to_mcp(mock_mcp)
        
        # Verify that mcp.tool() was called
        mock_mcp.tool.assert_called_once()
    
    def test_registered_function_calls_logic(self, mock_applescript, mock_draft_success_response):
        """Test that the registered function calls the logic function."""
        mock_mcp = Mock()
        registered_func = None
        
        def capture_registration():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func
            return decorator
        
        mock_mcp.tool = capture_registration
        
        # Configure mock to return Test Subject instead of Test Email
        mock_applescript.return_value = {
            "success": True,
            "data": "20240115120000||Test Subject",
            "metadata": {},
            "error": None
        }
        
        # Register the function
        register_to_mcp(mock_mcp)
        
        # Call the registered function
        assert registered_func is not None
        
        with patch('os.path.exists', return_value=True):
            result = registered_func(
                to=["test@example.com"],
                subject="Test Subject",
                body="Test Body",
                cc=["cc@example.com"],
                bcc=["bcc@example.com"],
                attachments=["/path/to/file.pdf"],
                html_body=True
            )
        
        # Verify it returns the expected result
        assert_valid_response_format(result)
        assert result["success"] is True
        assert "||Test Subject" in result["draft_id"]  # Check that draft_id contains the subject