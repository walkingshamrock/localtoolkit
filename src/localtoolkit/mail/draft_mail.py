"""
Implementation of draft_mail for the Mail app.

This module provides functionality to create draft email messages in
the macOS Mail app via AppleScript.
"""

from fastmcp import FastMCP
from typing import Dict, Any, List, Optional
import os
import datetime
from localtoolkit.applescript.utils.applescript_runner import applescript_execute

def draft_mail_logic(
    to: List[str],
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    attachments: Optional[List[str]] = None,
    html_body: Optional[bool] = False,
) -> Dict[str, Any]:
    """
    Create a draft email using the macOS Mail app.
    
    Args:
        to: List of recipient email addresses
        subject: Email subject line
        body: Email body content
        cc: Optional list of CC recipients
        bcc: Optional list of BCC recipients
        attachments: Optional list of file paths to attach to the email
        html_body: Whether to format the body as HTML instead of plain text
    
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,     # True if operation was successful
            "draft_id": str,     # Identifier for the created draft (timestamp + "||" + subject)
            "message": str,      # Context message about the results
            "error": str         # Only present if success is False
        }
    """
    # Input validation
    if not to or not isinstance(to, list) or len(to) == 0:
        return {
            "success": False,
            "error": "Invalid recipients: Must provide at least one recipient",
            "message": "Failed to create draft email due to missing recipients"
        }
    
    # Validate email addresses in to, cc, and bcc lists
    for email_list, list_name in [(to, "to"), (cc or [], "cc"), (bcc or [], "bcc")]:
        for email in email_list:
            if not isinstance(email, str) or not email or "@" not in email:
                return {
                    "success": False,
                    "error": f"Invalid email address in {list_name} list: {email}",
                    "message": f"Failed to create draft email due to invalid {list_name} address"
                }
    
    # Validate subject and body
    if not subject or not isinstance(subject, str):
        return {
            "success": False,
            "error": "Invalid subject: Must be a non-empty string",
            "message": "Failed to create draft email due to missing subject"
        }
    
    if not body or not isinstance(body, str):
        return {
            "success": False,
            "error": "Invalid body: Must be a non-empty string",
            "message": "Failed to create draft email due to missing body content"
        }
    
    # Validate attachments if provided
    if attachments:
        if not isinstance(attachments, list):
            return {
                "success": False,
                "error": "Invalid attachments: Must be a list of file paths",
                "message": "Failed to create draft email due to invalid attachment format"
            }
        
        # Verify attachments exist and are accessible
        for attachment in attachments:
            if not isinstance(attachment, str) or not attachment:
                return {
                    "success": False,
                    "error": f"Invalid attachment path: {attachment}",
                    "message": "Failed to create draft email due to invalid attachment path"
                }
            
            if not os.path.exists(attachment):
                return {
                    "success": False,
                    "error": f"Attachment file not found: {attachment}",
                    "message": "Failed to create draft email due to missing attachment file"
                }
    
    # Generate a timestamp for draft identification
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Build AppleScript for creating the draft email
    escaped_subject = subject.replace('"', '\\"')
    applescript_code_parts = [f"""
    on run argv
        try
            tell application "Mail"
                set newMessage to make new outgoing message with properties {{subject:"{escaped_subject}"}}
                
                -- Set recipients
    """]
    
    # Add recipients
    recipient_parts = []
    for recipient in to:
        escaped_recipient = recipient.replace('"', '\\"')
        recipient_parts.append(f"""
                tell newMessage
                    make new to recipient with properties {{address:"{escaped_recipient}"}}
                end tell
        """)
    
    # Add CC recipients if provided
    cc_parts = []
    if cc and len(cc) > 0:
        for cc_recipient in cc:
            escaped_cc = cc_recipient.replace('"', '\\"')
            cc_parts.append(f"""
                tell newMessage
                    make new cc recipient with properties {{address:"{escaped_cc}"}}
                end tell
            """)
    
    # Add BCC recipients if provided
    bcc_parts = []
    if bcc and len(bcc) > 0:
        for bcc_recipient in bcc:
            escaped_bcc = bcc_recipient.replace('"', '\\"')
            bcc_parts.append(f"""
                tell newMessage
                    make new bcc recipient with properties {{address:"{escaped_bcc}"}}
                end tell
            """)
    
    # Set the content of the email
    content_type = "html content" if html_body else "content"
    
    # Escape the body content
    escaped_body = body.replace('"', '\\"').replace('\\', '\\\\')
    
    content_part = f"""
                set {content_type} of newMessage to "{escaped_body}"
    """
    
    # Add attachment handling if needed
    attachment_parts = []
    if attachments and len(attachments) > 0:
        for attachment in attachments:
            # Use POSIX path to handle spaces and special characters
            escaped_attachment = attachment.replace('"', '\\"')
            attachment_parts.append(f"""
                tell newMessage
                    make new attachment with properties {{file name:POSIX file "{escaped_attachment}"}} at after the last paragraph
                end tell
            """)
    
    # Instead of sending, we're saving as a draft
    # The timestamp is returned to help identify the draft
    final_part = f"""
                -- Ensure draft is visible
                set visible of newMessage to true
                
                -- Return a pseudo-identifier with timestamp and subject
                return "{timestamp}||" & subject of newMessage
            end tell
        on error errMsg
            return "ERROR:" & errMsg
        end try
    end run
    """
    
    # Combine all parts of the AppleScript
    all_parts = [
        applescript_code_parts[0],
        *recipient_parts,
        *cc_parts,
        *bcc_parts,
        content_part,
        *attachment_parts,
        final_part
    ]
    applescript_code = ''.join(all_parts)
    
    # Execute the AppleScript
    result = applescript_execute(code=applescript_code, timeout=60)
    
    if not result.get("success", False):
        return {
            "success": False,
            "error": result.get("error", "Unknown error when creating draft email"),
            "message": "Failed to create draft email via Mail app"
        }
    
    # Check if the data contains an error message
    data = result.get("data", "")
    if isinstance(data, str) and data.startswith("ERROR:"):
        return {
            "success": False,
            "error": data[6:].strip(),  # Remove the "ERROR:" prefix and strip whitespace
            "message": "Failed to create draft email via Mail app"
        }
    
    # Process successful result
    # Extract the draft_id (timestamp) from the response
    draft_id = data if isinstance(data, str) else str(data)
    recipients_str = ", ".join(to)
    
    return {
        "success": True,
        "draft_id": draft_id,
        "message": f"Successfully created draft email to {recipients_str}"
    }

def register_to_mcp(mcp: FastMCP) -> None:
    """Register the draft_mail tool with the MCP server."""
    @mcp.tool()
    def mail_draft_mail(
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        html_body: Optional[bool] = False,
    ) -> Dict[str, Any]:
        """
        Create a draft email using the macOS Mail app.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body: Email body content
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            attachments: Optional list of file paths to attach to the email
            html_body: Whether to format the body as HTML instead of plain text
        
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,     # True if operation was successful
                "draft_id": str,     # Identifier for the created draft
                "message": str,      # Context message about the results
                "error": str         # Only present if success is False
            }
            
        Error Handling:
            - Invalid email format: Returns error about invalid email address
            - Mail app access denied: Returns error about permissions
            - File not found: Returns error if attachment file doesn't exist
            - AppleScript execution failure: Returns detailed error message
        
        Performance:
            - Typical response time: 1-3 seconds for simple drafts
            - Attachment processing may take longer depending on file sizes
            
        Examples:
            ```python
            # Create a simple draft email
            result = mail_draft_mail(
                to=["recipient@example.com"],
                subject="Hello from mac-mcp!",
                body="This is a test draft message from mac-mcp."
            )
            # Returns: {"success": True, "draft_id": "20250518120745||Hello from mac-mcp!", "message": "Successfully created draft email to recipient@example.com"}
            
            # Create a draft with CC, BCC and attachments
            result = mail_draft_mail(
                to=["primary@example.com"],
                cc=["cc1@example.com", "cc2@example.com"],
                bcc=["bcc@example.com"],
                subject="Report from mac-mcp",
                body="<h1>Hello!</h1><p>Please see the attached report.</p>",
                html_body=True,
                attachments=["/path/to/report.pdf"]
            )
            ```
        """
        return draft_mail_logic(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            html_body=html_body,
        )