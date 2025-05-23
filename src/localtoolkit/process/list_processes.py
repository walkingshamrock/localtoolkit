"""
List Processes Logic for LocalToolKit

Lists running processes on macOS with optional filtering.
"""

import subprocess
import json
import os
import time
from typing import Dict, List, Any, Optional
from fastmcp import FastMCP

def list_processes_logic(filter_name: Optional[str] = None, 
                        include_background: bool = False,
                        limit: int = 20) -> Dict[str, Any]:
    """
    List running processes on macOS with optional filtering.
    
    Args:
        filter_name: Optional name filter to match against process names
        include_background: Whether to include background processes
        limit: Maximum number of processes to return
        
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,
            "processes": List[Dict],
            "count": int,
            "message": str,
            "metadata": Dict,
            "error": str  # Only present if success is False
        }
    """
    try:
        # Use a simpler AppleScript approach
        applescript_code = """
        tell application "System Events"
            set allProcesses to every process
            set processInfoList to {}
            
            repeat with currentProcess in allProcesses
                try
                    set processName to the name of currentProcess
                    set processId to the unix id of currentProcess
                    
                    -- Only include if it matches filter (or no filter)
                    set shouldInclude to true
                    
                    -- Add to list
                    if shouldInclude then
                        set end of processInfoList to processName & ":::" & processId
                    end if
                end try
            end repeat
            
            return processInfoList
        end tell
        """
        
        # Run the AppleScript
        from localtoolkit.applescript.utils.applescript_runner import applescript_execute
        result = applescript_execute(code=applescript_code, timeout=30)
        
        # Handle the result
        if not result.get("success", False):
            return {
                "success": False,
                "error": result.get("error", "Unknown error occurred"),
                "message": "Failed to get processes from System Events"
            }
        
        # Process the data
        processes = []
        raw_data = result.get("data", [])
        
        if isinstance(raw_data, list):
            for process_info_str in raw_data:
                try:
                    parts = process_info_str.split(":::")
                    if len(parts) >= 2:
                        name = parts[0]
                        pid = int(parts[1])
                        
                        # Apply filter if specified
                        if filter_name and filter_name.lower() not in name.lower():
                            continue
                        
                        # Get additional info using ps command
                        try:
                            cmd = ["ps", "-p", str(pid), "-o", "%cpu,%mem,user="]
                            ps_result = subprocess.run(cmd, capture_output=True, text=True)
                            
                            if ps_result.returncode == 0:
                                ps_output = ps_result.stdout.strip().split("\n")
                                if len(ps_output) > 1:
                                    cpu_mem_user = ps_output[1].split()
                                    
                                    if len(cpu_mem_user) >= 3:
                                        cpu = float(cpu_mem_user[0])
                                        mem = float(cpu_mem_user[1])
                                        user = cpu_mem_user[2]
                                    else:
                                        cpu = 0.0
                                        mem = 0.0
                                        user = ""
                                else:
                                    cpu = 0.0
                                    mem = 0.0
                                    user = ""
                            else:
                                cpu = 0.0
                                mem = 0.0
                                user = ""
                        except:
                            cpu = 0.0
                            mem = 0.0
                            user = ""
                        
                        # Create process object
                        process = {
                            "pid": pid,
                            "name": name,
                            "cpu_percent": cpu,
                            "memory_percent": mem,
                            "user": user
                        }
                        
                        processes.append(process)
                except:
                    continue
        
        # Sort by CPU usage (highest first) and apply limit
        processes.sort(key=lambda p: p.get("cpu_percent", 0), reverse=True)
        processes = processes[:limit]
        
        return {
            "success": True,
            "processes": processes,
            "count": len(processes),
            "message": f"Successfully retrieved {len(processes)} processes" + 
                      (f" matching '{filter_name}'" if filter_name else ""),
            "metadata": {
                "include_background": include_background,
                "filter_applied": filter_name is not None,
                "limit_applied": limit,
                "timestamp": time.time()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list processes: {str(e)}",
            "message": "Error while retrieving process list"
        }

def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the process_list_processes tool to the FastMCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    @mcp.tool()
    def process_list_processes(
        filter_name: Optional[str] = None, 
        include_background: bool = False,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        List running processes on macOS with optional filtering.
        
        Lists processes with detailed information including PID, CPU usage, memory usage,
        and command line. Results can be filtered by name or limited to a specific number.
        
        Args:
            filter_name: Optional name filter to match against process names or commands
            include_background: Whether to include background processes
            limit: Maximum number of processes to return
            
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,
                "processes": List[Dict],
                "count": int,
                "message": str,
                "metadata": Dict,
                "error": str  # Only present if success is False
            }
            
            Each process object contains:
            - "pid": Process identifier
            - "user": User running the process
            - "name": Process name
            - "cpu_percent": CPU usage percentage
            - "memory_percent": Memory usage percentage
        """
        return list_processes_logic(filter_name, include_background, limit)