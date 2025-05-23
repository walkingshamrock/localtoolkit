"""
Get Process Info Logic for LocalToolKit

Gets detailed information about a specific process.
"""

import subprocess
import os
import time
import json
from typing import Dict, List, Any, Optional
from fastmcp import FastMCP

def get_process_info_logic(pid: int,
                          include_memory_details: bool = False,
                          include_file_handles: bool = False) -> Dict[str, Any]:
    """
    Get detailed information about a specific process.
    
    Args:
        pid: Process ID to get information for
        include_memory_details: Whether to include detailed memory usage
        include_file_handles: Whether to include open file handles
        
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,
            "process": Dict,
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
        
        # Get basic process information
        cmd = ["ps", "-p", str(pid), "-o", "pid,ppid,user,%cpu,%mem,lstart,command", "-w", "-w"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return {
                "success": False,
                "pid": pid,
                "error": f"Failed to get process info: {result.stderr}",
                "message": "Error while retrieving process information"
            }
            
        # Parse the output
        lines = result.stdout.strip().split("\n")
        if len(lines) < 2:
            return {
                "success": False,
                "pid": pid,
                "error": "Process not found in ps output",
                "message": f"No information found for PID {pid}"
            }
            
        # Parse the process information line
        # Split only the first 5 fields, leaving the rest for lstart and command
        parts = lines[1].split(None, 5)
        if len(parts) < 6:
            return {
                "success": False,
                "pid": pid,
                "error": "Invalid process information format",
                "message": "Failed to parse process details"
            }
            
        # The lstart format is like "Mon Jan 15 10:00:00 2024"
        # We need to extract this carefully from the remaining string
        remaining = parts[5]
        
        # lstart has a fixed format with day, month, date, time, year
        # Try to match the pattern
        import re
        date_pattern = r'^(\w{3}\s+\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\d{4})\s+(.+)$'
        match = re.match(date_pattern, remaining)
        
        if not match:
            return {
                "success": False,
                "pid": pid,
                "error": "Failed to parse process start time and command",
                "message": "Unexpected output format"
            }
            
        start_time = match.group(1)
        command = match.group(2)
            
        # Extract basic details
        process_info = {
            "pid": int(parts[0]),
            "ppid": int(parts[1]),
            "user": parts[2],
            "cpu_percent": float(parts[3]),
            "memory_percent": float(parts[4]),
            "start_time": start_time,
            "command": command,
            "name": os.path.basename(command.split()[0])
        }
        
        # Get parent process name if applicable
        if process_info["ppid"] > 0:
            try:
                parent_cmd = ["ps", "-p", str(process_info["ppid"]), "-o", "command="]
                parent_result = subprocess.run(parent_cmd, capture_output=True, text=True)
                if parent_result.returncode == 0:
                    parent_command = parent_result.stdout.strip()
                    process_info["parent_name"] = os.path.basename(parent_command.split()[0])
            except:
                process_info["parent_name"] = "Unknown"
        
        # Add detailed memory information if requested
        if include_memory_details:
            try:
                # Use vm_stat for system memory stats
                vm_stat_cmd = ["vm_stat"]
                vm_stat_result = subprocess.run(vm_stat_cmd, capture_output=True, text=True)
                
                if vm_stat_result.returncode == 0:
                    # Parse vm_stat output
                    vm_stats = {}
                    for line in vm_stat_result.stdout.strip().split("\n")[1:]:
                        if ":" in line:
                            key, value = line.split(":", 1)
                            value = value.strip().replace(".", "")
                            if value.isdigit():
                                vm_stats[key.strip()] = int(value)
                                
                    # Page size is typically 4096 bytes (4 KB) on macOS
                    page_size = 4096
                    
                    # Calculate memory metrics
                    process_info["memory_details"] = {
                        "system_total_mb": (sum(vm_stats.values()) * page_size) // (1024 * 1024),
                        "system_free_mb": (vm_stats.get("Pages free", 0) * page_size) // (1024 * 1024),
                        "system_active_mb": (vm_stats.get("Pages active", 0) * page_size) // (1024 * 1024),
                        "system_inactive_mb": (vm_stats.get("Pages inactive", 0) * page_size) // (1024 * 1024),
                        "system_wired_mb": (vm_stats.get("Pages wired down", 0) * page_size) // (1024 * 1024)
                    }
                    
                # Use ps for process-specific memory
                mem_cmd = ["ps", "-p", str(pid), "-o", "rss,vsz"]
                mem_result = subprocess.run(mem_cmd, capture_output=True, text=True)
                
                if mem_result.returncode == 0:
                    mem_lines = mem_result.stdout.strip().split("\n")
                    if len(mem_lines) > 1:
                        rss, vsz = map(int, mem_lines[1].split())
                        process_info["memory_details"]["rss_kb"] = rss
                        process_info["memory_details"]["rss_mb"] = rss // 1024
                        process_info["memory_details"]["vsz_kb"] = vsz
                        process_info["memory_details"]["vsz_mb"] = vsz // 1024
            except Exception as mem_e:
                process_info["memory_details_error"] = str(mem_e)
        
        # Add open file handles if requested
        if include_file_handles:
            try:
                # Use lsof to get open files
                lsof_cmd = ["lsof", "-p", str(pid)]
                lsof_result = subprocess.run(lsof_cmd, capture_output=True, text=True)
                
                if lsof_result.returncode == 0:
                    # Parse lsof output
                    file_handles = []
                    for line in lsof_result.stdout.strip().split("\n")[1:]:  # Skip header
                        parts = line.split(None, 8)
                        if len(parts) >= 9:
                            file_handle = {
                                "fd": parts[3],
                                "type": parts[4],
                                "device": parts[5],
                                "size": parts[6],
                                "node": parts[7],
                                "name": parts[8]
                            }
                            file_handles.append(file_handle)
                            
                    process_info["file_handles"] = file_handles
                    process_info["file_handles_count"] = len(file_handles)
            except Exception as file_e:
                process_info["file_handles_error"] = str(file_e)
                
        return {
            "success": True,
            "process": process_info,
            "message": f"Successfully retrieved information for process {pid}",
            "metadata": {
                "include_memory_details": include_memory_details,
                "include_file_handles": include_file_handles,
                "timestamp": time.time()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "pid": pid,
            "error": f"Failed to get process info: {str(e)}",
            "message": "Error while retrieving process information"
        }

def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the process_get_process_info tool to the FastMCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    @mcp.tool()
    def process_get_process_info(
        pid: int,
        include_memory_details: bool = False,
        include_file_handles: bool = False
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific process.
        
        Retrieves comprehensive information about a process, including basic details,
        resource usage, and optionally detailed memory statistics and open file handles.
        
        Args:
            pid: Process ID to get information for
            include_memory_details: Whether to include detailed memory usage
            include_file_handles: Whether to include open file handles
            
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,
                "process": Dict,
                "message": str,
                "metadata": Dict,
                "error": str  # Only present if success is False
            }
            
            The process object contains detailed information about the process,
            including user, command, CPU and memory usage, start time, and
            optionally memory details and file handles.
        """
        return get_process_info_logic(pid, include_memory_details, include_file_handles)