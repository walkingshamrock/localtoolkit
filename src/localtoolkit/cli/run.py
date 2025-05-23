"""
CLI entry point for running the LocalToolkit MCP server.

This module provides the run command to start the LocalToolkit MCP server
from the command line.
"""

import sys
import argparse
from typing import List, Optional

from localtoolkit.cli.main import main

def run_command(args: Optional[List[str]] = None) -> None:
    """
    Parse command line arguments and run the LocalToolkit MCP server.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:] if None)
    """
    parser = argparse.ArgumentParser(description="LocalToolkit MCP Server")
    
    parser.add_argument(
        "--transport", 
        choices=["stdio", "http"], 
        default="stdio",
        help="Transport protocol to use (default: stdio)"
    )
    
    parser.add_argument(
        "--host", 
        default="127.0.0.1",
        help="Host to bind to for HTTP transport (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port", 
        type=int,
        default=8000,
        help="Port to bind to for HTTP transport (default: 8000)"
    )
    
    parser.add_argument(
        "--config", 
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--filesystem-config", 
        help="Path to filesystem configuration file"
    )
    
    parser.add_argument(
        "--verbose", 
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    # Run the main function with the parsed arguments
    main(
        transport=parsed_args.transport,
        host=parsed_args.host,
        port=parsed_args.port,
        config_path=parsed_args.config,
        filesystem_config_path=parsed_args.filesystem_config,
        verbose=parsed_args.verbose
    )

if __name__ == "__main__":
    run_command()