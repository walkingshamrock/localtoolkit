"""Tests for the send_mail module."""

import pytest
from unittest.mock import patch, Mock
import os

from localtoolkit.mail.send_mail import send_mail_logic, register_to_mcp
from tests.utils.assertions import assert_valid_response_format


class TestSendMailLogic:
    """Test cases for send_mail_logic function."""
    
    def test_send_mail_success(self, mock_applescript, mock_send_success_response):
        """Test successful email sending."""
        # Configure mock to return success
        mock_applescript.return_value = {
            "success": True,
            "data": mock_send_success_response,
            "metadata": {},
            "error": None
        }
        
        result = send_mail_logic(
            to=["recipient@example.com"],
            subject="Test Email",
            body="This is a test email."
        )
        
        # Verify response format
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["message"] == "Email sent successfully"
    
    def test_send_mail_with_cc_bcc(self, mock_applescript, mock_send_success_response):
        """Test sending email with CC and BCC recipients."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_send_success_response,
            "metadata": {},
            "error": None
        }
        
        result = send_mail_logic(
            to=["recipient@example.com"],
            subject="Test Email",
            body="Test body",
            cc=["cc1@example.com", "cc2@example.com"],
            bcc=["bcc@example.com"]
        )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Verify CC and BCC were included in AppleScript
        assert mock_applescript.called
        call_args = mock_applescript.call_args
        if call_args and call_args[1] and "code" in call_args[1]:
            code = call_args[1]["code"]
            assert "cc1@example.com" in code
            assert "cc2@example.com" in code
            assert "bcc@example.com" in code
    
    def test_send_mail_html_content(self, mock_applescript, mock_send_success_response):
        """Test sending HTML email."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_send_success_response,
            "metadata": {},
            "error": None
        }
        
        result = send_mail_logic(
            to=["recipient@example.com"],
            subject="HTML Email",
            body="<h1>Hello</h1><p>This is HTML</p>",
            html=True
        )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Verify HTML content type was set
        assert mock_applescript.called
        call_args = mock_applescript.call_args
        if call_args and call_args[1] and "code" in call_args[1]:
            code = call_args[1]["code"]
            assert 'set content type to "html"' in code
    
    def test_send_mail_with_attachments(self, mock_applescript, mock_send_success_response):
        """Test sending email with attachments."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_send_success_response,
            "metadata": {},
            "error": None
        }
        
        # Mock file existence
        with patch('os.path.exists') as mock_exists, \
             patch('os.path.isfile') as mock_isfile, \
             patch('os.path.abspath') as mock_abspath:
            
            mock_exists.return_value = True
            mock_isfile.return_value = True
            mock_abspath.side_effect = lambda x: f"/absolute{x}"
            
            result = send_mail_logic(
                to=["recipient@example.com"],
                subject="Email with Attachments",
                body="See attached files",
                attachments=["/path/to/file1.pdf", "/path/to/file2.docx"]
            )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Verify attachments were included
        assert mock_applescript.called
        call_args = mock_applescript.call_args
        if call_args and call_args[1] and "code" in call_args[1]:
            code = call_args[1]["code"]
            assert "POSIX file" in code
            assert "/absolute/path/to/file1.pdf" in code
            assert "/absolute/path/to/file2.docx" in code
    
    def test_send_mail_nonexistent_attachments(self, mock_applescript, mock_send_success_response):
        """Test sending email with non-existent attachments (should skip them)."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_send_success_response,
            "metadata": {},
            "error": None
        }
        
        # Mock file existence - only first file exists
        with patch('os.path.exists') as mock_exists, \
             patch('os.path.isfile') as mock_isfile, \
             patch('os.path.abspath') as mock_abspath:
            
            def exists_side_effect(path):
                return "/file1.pdf" in path
            
            def isfile_side_effect(path):
                return "/file1.pdf" in path
            
            mock_exists.side_effect = exists_side_effect
            mock_isfile.side_effect = isfile_side_effect
            mock_abspath.side_effect = lambda x: f"/absolute{x}"
            
            result = send_mail_logic(
                to=["recipient@example.com"],
                subject="Test",
                body="Test body",
                attachments=["/file1.pdf", "/nonexistent.pdf"]
            )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Verify only valid attachment was included
        assert mock_applescript.called
        call_args = mock_applescript.call_args
        if call_args and call_args[1] and "code" in call_args[1]:
            code = call_args[1]["code"]
            assert "/absolute/file1.pdf" in code
            assert "nonexistent.pdf" not in code
    
    def test_send_mail_special_characters(self, mock_applescript, mock_send_success_response):
        """Test sending email with special characters."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_send_success_response,
            "metadata": {},
            "error": None
        }
        
        result = send_mail_logic(
            to=["recipient@example.com"],
            subject='Subject with "quotes"',
            body='Body with "quotes"\nand newlines'
        )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Verify special characters were escaped
        assert mock_applescript.called
        call_args = mock_applescript.call_args
        if call_args and call_args[1] and "code" in call_args[1]:
            code = call_args[1]["code"]
            assert '\\"' in code
            assert '\\n' in code
    
    def test_send_mail_empty_recipients(self, mock_applescript, mock_send_success_response):
        """Test sending email with empty recipient list."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_send_success_response,
            "metadata": {},
            "error": None
        }
        
        result = send_mail_logic(
            to=[],
            subject="Test",
            body="Test body"
        )
        
        assert_valid_response_format(result)
        # Should still attempt to send (validation is done in AppleScript)
        assert result["success"] is True
    
    def test_send_mail_applescript_error(self, mock_applescript):
        """Test handling of AppleScript execution error."""
        mock_applescript.return_value = {
            "success": False,
            "data": None,
            "metadata": {},
            "error": "AppleScript execution failed"
        }
        
        result = send_mail_logic(
            to=["recipient@example.com"],
            subject="Test",
            body="Test body"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["message"] == "Failed to execute mail sending script"
        assert result["error"] == "AppleScript execution failed"
    
    def test_send_mail_error_response(self, mock_applescript, mock_mail_error_response):
        """Test handling of error response from AppleScript."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_mail_error_response,
            "metadata": {},
            "error": None
        }
        
        result = send_mail_logic(
            to=["recipient@example.com"],
            subject="Test",
            body="Test body"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["message"] == "Failed to send email"
        assert result["error"] == "Mail app not accessible"
    
    def test_send_mail_attachment_error_response(self, mock_applescript):
        """Test handling of attachment error from AppleScript."""
        mock_applescript.return_value = {
            "success": True,
            "data": "ERROR: Failed to attach file: File not found",
            "metadata": {},
            "error": None
        }
        
        result = send_mail_logic(
            to=["recipient@example.com"],
            subject="Test",
            body="Test body"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is False
        assert result["error"] == "Failed to attach file: File not found"
    
    def test_send_mail_unknown_response(self, mock_applescript):
        """Test handling of unknown response format."""
        mock_applescript.return_value = {
            "success": True,
            "data": "Unknown response format",
            "metadata": {},
            "error": None
        }
        
        result = send_mail_logic(
            to=["recipient@example.com"],
            subject="Test",
            body="Test body"
        )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["message"] == "Email sent successfully"
    
    def test_send_mail_whitespace_in_emails(self, mock_applescript, mock_send_success_response):
        """Test handling of whitespace in email addresses."""
        mock_applescript.return_value = {
            "success": True,
            "data": mock_send_success_response,
            "metadata": {},
            "error": None
        }
        
        result = send_mail_logic(
            to=[" recipient@example.com ", "  another@example.com"],
            subject="Test",
            body="Test body",
            cc=["  cc@example.com  "]
        )
        
        assert_valid_response_format(result)
        assert result["success"] is True
        
        # Verify emails were trimmed in AppleScript
        assert mock_applescript.called
        call_args = mock_applescript.call_args
        if call_args and call_args[1] and "code" in call_args[1]:
            code = call_args[1]["code"]
            assert '"recipient@example.com"' in code
            assert '"another@example.com"' in code
            assert '"cc@example.com"' in code


class TestRegisterToMCP:
    """Test cases for MCP registration."""
    
    def test_register_to_mcp(self):
        """Test that the function registers correctly to MCP."""
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda f: f)
        
        register_to_mcp(mock_mcp)
        
        # Verify that mcp.tool() was called
        mock_mcp.tool.assert_called_once()
    
    def test_registered_function_calls_logic(self, mock_applescript, mock_send_success_response):
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
        
        # Configure mock
        mock_applescript.return_value = {
            "success": True,
            "data": mock_send_success_response,
            "metadata": {},
            "error": None
        }
        
        # Register the function
        register_to_mcp(mock_mcp)
        
        # Call the registered function
        assert registered_func is not None
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('os.path.abspath', side_effect=lambda x: f"/absolute{x}"):
            
            result = registered_func(
                to=["test@example.com"],
                subject="Test Subject",
                body="Test Body",
                cc=["cc@example.com"],
                bcc=["bcc@example.com"],
                attachments=["/file.pdf"],
                html=True
            )
        
        # Verify it returns the expected result
        assert_valid_response_format(result)
        assert result["success"] is True
        assert result["message"] == "Email sent successfully"