"""
Implementation of send_mail for the Mail app.

This module provides functionality to send an email message using 
the macOS Mail app via AppleScript.
"""

from fastmcp import FastMCP
from typing import Dict, Any, List, Optional
import os
import json
from localtoolkit.applescript.utils.applescript_runner import applescript_execute

def send_mail_logic(
    to: List[str],
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    attachments: Optional[List[str]] = None,
    html: bool = False
) -> Dict[str, Any]:
    """
    Send an email through the macOS Mail app.
    
    Args:
        to: List of recipient email addresses
        subject: Email subject line
        body: Email message body
        cc: List of CC recipients (optional)
        bcc: List of BCC recipients (optional)
        attachments: List of file paths to attach (optional)
        html: Whether the body is HTML content (default: False)
        
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,      # True if email was sent successfully
            "message": str,       # Description of what happened
            "error": str          # Only present if success is False
        }
    """
    # Default empty lists for optional parameters
    cc = cc or []
    bcc = bcc or []
    attachments = attachments or []
    
    # Validate attachments
    valid_attachments = []
    for path in attachments:
        if os.path.exists(path) and os.path.isfile(path):
            valid_attachments.append(os.path.abspath(path))
    
    # Build the recipient lists as safe, quoted strings
    to_list = ", ".join([f'"{email.strip()}"' for email in to if email.strip()])
    cc_list = ", ".join([f'"{email.strip()}"' for email in cc if email.strip()]) if cc else ""
    bcc_list = ", ".join([f'"{email.strip()}"' for email in bcc if email.strip()]) if bcc else ""
    
    # Escape quotes in strings
    subject_escaped = subject.replace('"', '\\"')
    
    # Determine content type
    content_type = "html" if html else "text"
    
    # Create attachment list for AppleScript
    attachment_list = ", ".join([f'POSIX file "{path}"' for path in valid_attachments])
    
    # Escape special characters in body
    body_escaped = body.replace('"', '\\"').replace('\n', '\\n')
    
    # Create the AppleScript
    applescript_code = f"""
on run argv
    set toRecipients to {{{to_list}}}
    set theSubject to "{subject_escaped}"
    {"set ccRecipients to {" + cc_list + "}" if cc_list else "set ccRecipients to {}"}
    {"set bccRecipients to {" + bcc_list + "}" if bcc_list else "set bccRecipients to {}"}
    {"set theAttachments to {" + attachment_list + "}" if attachment_list else "set theAttachments to {}"}
    
    -- Get message body from JSON string to preserve formatting
    set messageBody to "{body_escaped}"
    
    tell application "Mail"
        -- Create a new message
        set newMessage to make new outgoing message with properties {{subject:theSubject, content:messageBody, visible:false}}
        
        -- Set the content type (plain text or HTML)
        tell newMessage
            set content type to "{content_type}"
            
            -- Add recipients
            repeat with recipientAddress in toRecipients
                make new to recipient at end of to recipients with properties {{address:recipientAddress}}
            end repeat
            
            -- Add CC recipients if any
            if (count of ccRecipients) > 0 then
                repeat with recipientAddress in ccRecipients
                    make new cc recipient at end of cc recipients with properties {{address:recipientAddress}}
                end repeat
            end if
            
            -- Add BCC recipients if any
            if (count of bccRecipients) > 0 then
                repeat with recipientAddress in bccRecipients
                    make new bcc recipient at end of bcc recipients with properties {{address:recipientAddress}}
                end repeat
            end if
            
            -- Add attachments if any
            if (count of theAttachments) > 0 then
                repeat with theAttachment in theAttachments
                    try
                        make new attachment with properties {{file name:theAttachment}} at after the last paragraph
                    on error errMsg
                        return "ERROR: Failed to attach file: " & errMsg
                    end try
                end repeat
            end if
            
            -- Send the message
            send
            
            return "SUCCESS: Email sent successfully"
        end tell
    end tell
on error errMsg
    return "ERROR: " & errMsg
end try
end run
"""
    
    # Execute the AppleScript
    result = applescript_execute(code=applescript_code)
    
    if not result.get("success", False):
        return {
            "success": False,
            "message": "Failed to execute mail sending script",
            "error": result.get("error", "Unknown error")
        }
    
    # Process the result
    output = result.get("data", "")
    
    if isinstance(output, str) and output.startswith("ERROR:"):
        return {
            "success": False,
            "message": "Failed to send email",
            "error": output[6:].strip()  # Remove "ERROR: " prefix
        }
    elif isinstance(output, str) and output.startswith("SUCCESS:"):
        return {
            "success": True,
            "message": output[9:].strip()  # Remove "SUCCESS: " prefix
        }
    else:
        return {
            "success": True,
            "message": "Email sent successfully"
        }

def register_to_mcp(mcp: FastMCP) -> None:
    @mcp.tool()
    def mail_send_email(
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        Send an email through the macOS Mail app.
        
        Creates and sends an email message using the user's default Mail app
        settings. Supports multiple recipients, CC, BCC, and file attachments.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body: Email message body
            cc: List of CC recipients (optional)
            bcc: List of BCC recipients (optional)
            attachments: List of file paths to attach (optional)
            html: Whether the body is HTML content (default: False)
            
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,    # True if email was sent successfully
                "message": str,     # Description of what happened
                "error": str        # Only present if success is False
            }
            
        Error Handling:
            - Invalid recipients: Returns error with message
            - Invalid attachments: Skips files that don't exist
            - Mail app not running: Attempts to launch the app
            - Permission denied: Returns error message
            
        Performance:
            - Typical response time: 1-3 seconds
            
        Examples:
            ```python
            # Send a simple email
            result = mail_send_email(
                to=["recipient@example.com"],
                subject="Hello from LocalToolkit",
                body="This is a test email sent from Python."
            )
            if result["success"]:
                print("Email sent!")
            else:
                print(f"Failed to send email: {result['error']}")
                
            # Send email with attachments and CC
            result = mail_send_email(
                to=["primary@example.com"],
                cc=["manager@example.com"],
                subject="Report attached",
                body="Please find the report attached.",
                attachments=["/path/to/report.pdf"]
            )
            ```
        """
        return send_mail_logic(to, subject, body, cc, bcc, attachments, html)