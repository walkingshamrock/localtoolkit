"""
Terminate Process Logic for LocalToolKit

Terminates a process by its PID.
"""

import os
import signal
import time
import subprocess
from typing import Dict, Any
from fastmcp import FastMCP

def terminate_process_logic(pid: int, 
                           signal_num: int = signal.SIGTERM,
                           force: bool = False) -> Dict[str, Any]:
    """
    Terminate a process by its PID.
    
    Args:
        pid: Process ID to terminate
        signal_num: Signal to send (default is SIGTERM)
        force: Whether to force termination with SIGKILL if SIGTERM fails
        
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,
            "pid": int,
            "signal": int,
            "forced_kill": bool,
            "message": str,
            "error": str  # Only present if success is False
        }
    """
    try:
        # Check if process exists
        try:
            # This will raise an error if the process doesn't exist
            os.kill(pid, 0)
        except OSError:
            return {
                "success": False,
                "pid": pid,
                "error": f"Process with PID {pid} does not exist or permission denied",
                "message": f"No such process: {pid}"
            }
        
        # Try to get process name for better feedback
        process_name = ""
        try:
            cmd = ["ps", "-p", str(pid), "-o", "command="]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                process_name = result.stdout.strip()
        except:
            pass
            
        process_info = f"PID {pid}" + (f" ({process_name})" if process_name else "")
        
        # Send the requested signal
        os.kill(pid, signal_num)
        
        # If force is True, we need to check if the process is still running
        # and then kill it with SIGKILL if necessary
        forced_kill = False
        if force:
            # Wait a bit to see if the process terminates
            time.sleep(0.5)
            
            try:
                # Check if process still exists
                os.kill(pid, 0)
                
                # Process still exists, send SIGKILL
                os.kill(pid, signal.SIGKILL)
                forced_kill = True
                
                # Wait a bit to make sure it's gone
                time.sleep(0.1)
                
                # Final check
                try:
                    os.kill(pid, 0)
                    return {
                        "success": False,
                        "pid": pid,
                        "signal": signal_num,
                        "forced_kill": forced_kill,
                        "error": f"Failed to terminate {process_info} even with SIGKILL",
                        "message": "Process could not be terminated"
                    }
                except OSError:
                    # Process is gone
                    return {
                        "success": True,
                        "pid": pid,
                        "signal": signal_num,
                        "forced_kill": forced_kill,
                        "message": f"Successfully terminated {process_info} with SIGKILL after SIGTERM"
                    }
            except OSError:
                # Process is already gone
                return {
                    "success": True,
                    "pid": pid,
                    "signal": signal_num,
                    "forced_kill": False,
                    "message": f"Successfully terminated {process_info} with signal {signal_num}"
                }
        
        # If we're not forcing, just assume it worked
        return {
            "success": True,
            "pid": pid,
            "signal": signal_num,
            "forced_kill": False,
            "message": f"Successfully sent signal {signal_num} to {process_info}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "pid": pid,
            "error": f"Failed to terminate process: {str(e)}",
            "message": "Error while terminating process"
        }

def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the process_terminate_process tool to the FastMCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    @mcp.tool()
    def process_terminate_process(
        pid: int,
        signal_num: int = 15,  # SIGTERM
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Terminate a process by its PID.
        
        Sends a signal to a process to terminate it. Can optionally force termination
        with SIGKILL if SIGTERM fails to terminate the process.
        
        Args:
            pid: Process ID to terminate
            signal_num: Signal to send (default is 15/SIGTERM)
            force: Whether to force termination with SIGKILL if SIGTERM fails
            
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,
                "pid": int,
                "signal": int,
                "forced_kill": bool,
                "message": str,
                "error": str  # Only present if success is False
            }
        """
        return terminate_process_logic(pid, signal_num, force)