"""
LocalToolKit - Main Entry Point

This file serves as the entry point for the LocalToolKit project, which creates a
structured API layer for macOS applications following the Model Context Protocol.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Use our wrapper around the MCP's FastMCP implementation
from localtoolkit.mcp.server.fastmcp.server import FastMCP

# Import tool functions from app modules
from localtoolkit.messages import register_to_mcp as register_messages
from localtoolkit.contacts import register_to_mcp as register_contacts
from localtoolkit.mail import register_to_mcp as register_mail
from localtoolkit.applescript import register_to_mcp as register_applescript
from localtoolkit.process import register_to_mcp as register_process
from localtoolkit.filesystem import register_to_mcp as register_filesystem
from localtoolkit.reminders import register_to_mcp as register_reminders

def setup_logger():
    """Set up and return the logger."""
    # Setup basic logging
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    return logging.getLogger("localtoolkit")

def load_filesystem_settings(config_path: str = None, 
                            filesystem_config_path: str = None):
    """Load filesystem settings from various sources."""
    logger = setup_logger()
    filesystem_settings = {}

    try:
        # 0. Try direct filesystem_config_path parameter
        if filesystem_config_path and os.path.exists(filesystem_config_path):
            logger.info(f"Loading filesystem config from --filesystem-config parameter: {filesystem_config_path}")
            try:
                with open(filesystem_config_path, 'r') as f:
                    filesystem_settings = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config from {filesystem_config_path}: {e}")
        
        # 0.1 Try direct config_path parameter
        elif config_path and os.path.exists(config_path):
            logger.info(f"Loading config from --config parameter: {config_path}")
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if "settings" in config and "filesystem" in config["settings"]:
                        filesystem_settings = config["settings"]["filesystem"]
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
                
        # 1. Try environment variable for specific filesystem config
        if "LOCALTOOLKIT_FILESYSTEM_CONFIG" in os.environ:
            logger.info("Loading filesystem config from LOCALTOOLKIT_FILESYSTEM_CONFIG env var")
            try:
                filesystem_settings = json.loads(os.environ["LOCALTOOLKIT_FILESYSTEM_CONFIG"])
            except Exception as e:
                logger.warning(f"Failed to parse LOCALTOOLKIT_FILESYSTEM_CONFIG: {e}")

        # 2. Try general config environment variable
        elif "LOCALTOOLKIT_CONFIG" in os.environ:
            config_path = os.environ["LOCALTOOLKIT_CONFIG"]
            if os.path.exists(config_path):
                logger.info(f"Loading config from MAC_MCP_CONFIG path: {config_path}")
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        if "settings" in config and "filesystem" in config["settings"]:
                            filesystem_settings = config["settings"]["filesystem"]
                except Exception as e:
                    logger.warning(f"Failed to load config from {config_path}: {e}")

        # 3. Try command line arguments
        if not filesystem_settings:
            for arg in sys.argv:
                if arg.startswith("--filesystem-config="):
                    config_path = arg.split("=", 1)[1]
                    if os.path.exists(config_path):
                        logger.info(f"Loading filesystem config from command line arg: {config_path}")
                        try:
                            with open(config_path, 'r') as f:
                                filesystem_settings = json.load(f)
                        except Exception as e:
                            logger.warning(f"Failed to load config from {config_path}: {e}")
                    break
                elif arg.startswith("--config="):
                    config_path = arg.split("=", 1)[1]
                    if os.path.exists(config_path):
                        logger.info(f"Loading general config from command line arg: {config_path}")
                        try:
                            with open(config_path, 'r') as f:
                                config = json.load(f)
                                if "settings" in config and "filesystem" in config["settings"]:
                                    filesystem_settings = config["settings"]["filesystem"]
                        except Exception as e:
                            logger.warning(f"Failed to load config from {config_path}: {e}")
                    break

        # 4. Look for Claude Desktop config
        if not filesystem_settings:
            # Common Claude Desktop config paths
            config_paths = [
                os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json"),  # macOS
                os.path.expanduser("~/.config/Claude/claude_desktop_config.json"),  # Linux
                os.path.join(os.getenv("APPDATA", ""), "Claude", "claude_desktop_config.json"),  # Windows
            ]
            
            for path in config_paths:
                if os.path.exists(path):
                    logger.info(f"Found Claude Desktop config at: {path}")
                    try:
                        with open(path, 'r') as f:
                            config = json.load(f)
                            # Check for our server config
                            if "mcpServers" in config and "localtoolkit" in config["mcpServers"]:
                                server_config = config["mcpServers"]["localtoolkit"]
                                if "settings" in server_config and "filesystem" in server_config["settings"]:
                                    filesystem_settings = server_config["settings"]["filesystem"]
                                    logger.info("Successfully loaded filesystem settings from Claude Desktop config")
                    except Exception as e:
                        logger.warning(f"Failed to load Claude Desktop config from {path}: {e}")
                    break

        # 5. Default fallback settings if nothing else is found
        if not filesystem_settings or "allowed_dirs" not in filesystem_settings or not filesystem_settings["allowed_dirs"]:
            # Use project directory as default allowed directory
            project_dir = str(Path(__file__).parent.parent.parent.parent.absolute())
            logger.info(f"Using default filesystem settings with project dir: {project_dir}")
            
            filesystem_settings = {
                "allowed_dirs": [
                    {
                        "path": project_dir,
                        "permissions": ["read", "write", "list"]
                    }
                ]
            }
            
            # Add security log directory if not specified
            if "security_log_dir" not in filesystem_settings:
                log_dir = os.path.join(os.path.expanduser("~"), "Library", "Logs", "localtoolkit", "security")
                filesystem_settings["security_log_dir"] = log_dir
                # Ensure log directory exists
                os.makedirs(log_dir, exist_ok=True)

        logger.info(f"Final filesystem settings: {json.dumps(filesystem_settings, indent=2)}")
    except Exception as e:
        logger.error(f"Error setting up filesystem configuration: {e}")
        # Provide minimal safe defaults
        filesystem_settings = {
            "allowed_dirs": [
                {
                    "path": str(Path(__file__).parent.parent.parent.parent.absolute()),
                    "permissions": ["read", "list"]
                }
            ]
        }
    
    return filesystem_settings, logger

def main(transport: str = "stdio", 
          host: str = "127.0.0.1", 
          port: int = 8000,
          config_path: str = None,
          filesystem_config_path: str = None,
          verbose: bool = False):
    """Main entry point for the CLI."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
        
    filesystem_settings, logger = load_filesystem_settings(
        config_path=config_path,
        filesystem_config_path=filesystem_config_path
    )
    
    # Create FastMCP server
    mcp = FastMCP("localtoolkit")
    
    # Register tools from app modules
    register_messages(mcp)
    register_contacts(mcp)
    register_mail(mcp)
    register_applescript(mcp)
    register_process(mcp)
    register_reminders(mcp)
    
    # Register filesystem module with settings
    register_filesystem(mcp, filesystem_settings)
    
    # Run the server with the specified transport
    if transport == "http":
        logger.info(f"Starting HTTP server on {host}:{port}")
        # Set host and port in settings
        mcp.settings.host = host
        mcp.settings.port = port
        # Use streamable-http as the correct transport value
        mcp.run(transport="streamable-http")
    else:
        logger.info("Starting stdio server")
        mcp.run()

if __name__ == "__main__":
    main()