"""
Start Process Logic for LocalToolKit

Starts a new process with the specified command and options.
"""

import subprocess
import os
import signal
import time
import shlex
from typing import Dict, List, Any, Optional
from fastmcp import FastMCP

def start_process_logic(command: str, 
                       args: List[str] = None,
                       env: Dict[str, str] = None,
                       background: bool = True,
                       wait_for_completion: bool = False) -> Dict[str, Any]:
    """
    Start a new process with the specified command and options.
    
    Args:
        command: The command or path to the application to launch
        args: Arguments to pass to the command
        env: Environment variables to set for the process
        background: Whether to run the process in the background
        wait_for_completion: Whether to wait for the process to complete before returning
        
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,
            "pid": int,
            "command": str,
            "exit_code": int,  # Only if wait_for_completion is True
            "stdout": str,     # Only if wait_for_completion is True
            "stderr": str,     # Only if wait_for_completion is True
            "message": str,
            "error": str       # Only present if success is False
        }
    """
    try:
        # Set up environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
            
        # Prepare command arguments
        args = args or []
        
        # Check if this is an application bundle
        is_app = command.endswith(".app")
        
        # Handle application bundles differently
        if is_app:
            full_command = ["open", command] + args
        else:
            # Parse command to handle shell syntax properly
            cmd_parts = shlex.split(command)
            full_command = cmd_parts + args
        
        # Determine how to run the process
        if wait_for_completion:
            # Run in foreground and wait for completion
            process = subprocess.run(
                full_command,
                env=process_env,
                text=True,
                capture_output=True
            )
            
            result = {
                "success": process.returncode == 0,
                "command": command,
                "full_command": " ".join(full_command),
                "exit_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "message": f"Process completed with exit code {process.returncode}"
            }
            
            if process.returncode != 0:
                result["error"] = f"Process failed with exit code {process.returncode}: {process.stderr}"
                
            return result
        else:
            # Run in background
            process = subprocess.Popen(
                full_command,
                env=process_env,
                text=True,
                stdout=subprocess.PIPE if not background else subprocess.DEVNULL,
                stderr=subprocess.PIPE if not background else subprocess.DEVNULL,
                start_new_session=background
            )
            
            # Return immediately with process information
            return {
                "success": True,
                "pid": process.pid,
                "command": command,
                "full_command": " ".join(full_command),
                "message": f"Process started with PID {process.pid}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "command": command,
            "error": f"Failed to start process: {str(e)}",
            "message": "Error while starting process"
        }

def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the process_start_process tool to the FastMCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    @mcp.tool()
    def process_start_process(
        command: str,
        args: List[str] = None,
        env: Dict[str, str] = None,
        background: bool = True,
        wait_for_completion: bool = False
    ) -> Dict[str, Any]:
        """
        Start a new process with the specified command and options.
        
        Launches a new process or application on macOS. Can run in the background
        or foreground, with optional arguments and environment variables.
        
        Args:
            command: The command or path to the application to launch
            args: Arguments to pass to the command
            env: Environment variables to set for the process
            background: Whether to run the process in the background
            wait_for_completion: Whether to wait for the process to complete before returning
            
        Returns:
            A dictionary with the following structure for background processes:
            {
                "success": bool,
                "pid": int,
                "command": str,
                "full_command": str,
                "message": str,
                "error": str  # Only present if success is False
            }
            
            Or for foreground processes (wait_for_completion=True):
            {
                "success": bool,
                "command": str,
                "full_command": str,
                "exit_code": int,
                "stdout": str,
                "stderr": str,
                "message": str,
                "error": str  # Only present if success is False
            }
        """
        return start_process_logic(command, args, env, background, wait_for_completion)