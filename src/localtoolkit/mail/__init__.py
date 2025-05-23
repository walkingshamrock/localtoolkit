"""
Mail app integration for localtoolkit.

This module provides functionality for interacting with the macOS Mail app.
"""

from typing import Dict, Any, Optional
from fastmcp import FastMCP
from localtoolkit.mail.send_mail import register_to_mcp as register_mail_send_mail
from localtoolkit.mail.draft_mail import register_to_mcp as register_mail_draft_mail

def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the Mail app tools to the FastMCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    # Define the Mail app tools
    register_mail_send_mail(mcp)
    register_mail_draft_mail(mcp)
    
__all__ = [
    "register_to_mcp",
]
