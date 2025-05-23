"""
LocalToolKit - Main Entry Point

This file serves as a simple entry point for the LocalToolKit project,
importing from the new package structure.
"""

import logging
from pathlib import Path
import os
import json

from localtoolkit.mcp.server.fastmcp.server import FastMCP
from localtoolkit.messages import register_to_mcp as register_messages
from localtoolkit.contacts import register_to_mcp as register_contacts
from localtoolkit.mail import register_to_mcp as register_mail
from localtoolkit.applescript import register_to_mcp as register_applescript
from localtoolkit.process import register_to_mcp as register_process
from localtoolkit.filesystem import register_to_mcp as register_filesystem
from localtoolkit.reminders import register_to_mcp as register_reminders
from localtoolkit.calendar import register_to_mcp as register_calendar
from localtoolkit.notes import register_to_mcp as register_notes
from localtoolkit.cli.main import load_filesystem_settings
from localtoolkit.cli.run import run_command

# Create a global FastMCP server object that can be found by the MCP runtime
mcp = FastMCP("localtoolkit")

# Set up logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("localtoolkit")

# Load filesystem settings
filesystem_settings, _ = load_filesystem_settings()

# Register tools from app modules
register_messages(mcp)
register_contacts(mcp)
register_mail(mcp)
register_applescript(mcp)
register_process(mcp)
register_reminders(mcp)
register_calendar(mcp)
register_notes(mcp)
register_filesystem(mcp, filesystem_settings)

if __name__ == "__main__":
    # When run directly, use the run_command function to properly handle command-line arguments
    run_command()