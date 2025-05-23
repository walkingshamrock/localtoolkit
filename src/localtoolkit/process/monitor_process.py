"""
Monitor Process Logic for LocalToolKit

Monitors a process for a specified duration and returns resource usage statistics.
"""

import subprocess
import os
import time
import json
import statistics
from typing import Dict, List, Any, Optional
from fastmcp import FastMCP

def monitor_process_logic(pid: int,
                         interval: float = 1.0,
                         duration: float = 10.0,
                         include_cpu: bool = True,
                         include_memory: bool = True,
                         include_io: bool = False) -> Dict[str, Any]:
    """
    Monitor a process for a specified duration and return resource usage statistics.
    
    Args:
        pid: Process ID to monitor
        interval: Monitoring interval in seconds
        duration: Total monitoring duration in seconds
        include_cpu: Whether to monitor CPU usage
        include_memory: Whether to monitor memory usage
        include_io: Whether to monitor I/O activity
        
    Returns:
        A dictionary with the following structure:
        {
            "success": bool,
            "pid": int,
            "metrics": List[Dict],
            "summary": Dict,
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
            
        # Get initial process information
        cmd = ["ps", "-p", str(pid), "-o", "command="]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return {
                "success": False,
                "pid": pid,
                "error": f"Failed to get process info: {result.stderr}",
                "message": "Error while retrieving process information"
            }
            
        process_name = os.path.basename(result.stdout.strip().split()[0])
        
        # Prepare monitoring
        metrics = []
        start_time = time.time()
        end_time = start_time + duration
        
        # Determine which PS columns to fetch
        columns = ["pid"]
        if include_cpu:
            columns.extend(["%cpu"])
        if include_memory:
            columns.extend(["%mem", "rss", "vsz"])
            
        columns_str = ",".join(columns)
        
        # Get initial IO statistics if requested
        if include_io:
            io_before = {}
            try:
                # Use lsof to count open files
                lsof_cmd = ["lsof", "-p", str(pid)]
                lsof_result = subprocess.run(lsof_cmd, capture_output=True, text=True)
                
                if lsof_result.returncode == 0:
                    io_before["open_files_count"] = len(lsof_result.stdout.strip().split("\n")) - 1
            except:
                # IO monitoring might not be available
                include_io = False
        
        # Monitor the process
        while time.time() < end_time:
            current_time = time.time()
            sample_time = current_time - start_time
            
            # Get current metrics
            ps_cmd = ["ps", "-p", str(pid), "-o", columns_str]
            ps_result = subprocess.run(ps_cmd, capture_output=True, text=True)
            
            if ps_result.returncode != 0:
                # Process might have terminated
                metrics.append({
                    "timestamp": current_time,
                    "elapsed_seconds": sample_time,
                    "error": "Process terminated during monitoring"
                })
                break
                
            # Parse metrics
            try:
                lines = ps_result.stdout.strip().split("\n")
                if len(lines) < 2:
                    metrics.append({
                        "timestamp": current_time,
                        "elapsed_seconds": sample_time,
                        "error": "Process not found in ps output"
                    })
                    break
                    
                # Get header and values
                headers = lines[0].split()
                values = lines[1].split()
                
                # Create sample data
                sample = {
                    "timestamp": current_time,
                    "elapsed_seconds": sample_time
                }
                
                # Add metrics based on requested monitoring
                for i, header in enumerate(headers):
                    if header == "%cpu" and include_cpu:
                        sample["cpu_percent"] = float(values[i])
                    elif header == "%mem" and include_memory:
                        sample["memory_percent"] = float(values[i])
                    elif header == "rss" and include_memory:
                        sample["rss_kb"] = int(values[i])
                    elif header == "vsz" and include_memory:
                        sample["vsz_kb"] = int(values[i])
                
                # Add IO metrics if requested
                if include_io:
                    try:
                        lsof_cmd = ["lsof", "-p", str(pid)]
                        lsof_result = subprocess.run(lsof_cmd, capture_output=True, text=True)
                        
                        if lsof_result.returncode == 0:
                            open_files_count = len(lsof_result.stdout.strip().split("\n")) - 1
                            sample["open_files_count"] = open_files_count
                    except Exception as io_e:
                        sample["io_error"] = str(io_e)
                
                # Add sample to metrics
                metrics.append(sample)
                
                # Sleep for the interval
                time.sleep(interval)
            except Exception as sample_e:
                metrics.append({
                    "timestamp": current_time,
                    "elapsed_seconds": sample_time,
                    "error": f"Error collecting sample: {str(sample_e)}"
                })
                break
        
        # Generate summary statistics
        summary = {
            "pid": pid,
            "process_name": process_name,
            "monitoring_start": start_time,
            "monitoring_end": time.time(),
            "samples_collected": len(metrics),
            "monitoring_duration_seconds": time.time() - start_time
        }
        
        # Calculate statistics for numeric metrics
        if len(metrics) > 0:
            # Find all numeric metrics
            numeric_keys = set()
            for sample in metrics:
                for key, value in sample.items():
                    if isinstance(value, (int, float)) and key not in ["timestamp", "elapsed_seconds"]:
                        numeric_keys.add(key)
            
            # Calculate statistics for each numeric metric
            for key in numeric_keys:
                values = [sample[key] for sample in metrics if key in sample]
                if values:
                    summary[key] = {
                        "min": min(values),
                        "max": max(values),
                        "avg": statistics.mean(values),
                        "median": statistics.median(values) if len(values) > 1 else values[0]
                    }
                    
                    # Add standard deviation if we have enough samples
                    if len(values) > 1:
                        summary[key]["std_dev"] = statistics.stdev(values)
                        
                    # Add first and last values for trend analysis
                    first_value = next((sample[key] for sample in metrics if key in sample), None)
                    last_value = next((sample[key] for sample in reversed(metrics) if key in sample), None)
                    
                    if first_value is not None and last_value is not None:
                        summary[key]["first"] = first_value
                        summary[key]["last"] = last_value
                        summary[key]["change"] = last_value - first_value
                        summary[key]["change_percent"] = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0
        
        return {
            "success": True,
            "pid": pid,
            "process_name": process_name,
            "metrics": metrics,
            "summary": summary,
            "message": f"Successfully monitored process {pid} ({process_name}) for {summary['monitoring_duration_seconds']:.2f} seconds",
            "metadata": {
                "include_cpu": include_cpu,
                "include_memory": include_memory,
                "include_io": include_io,
                "interval": interval,
                "requested_duration": duration
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "pid": pid,
            "error": f"Failed to monitor process: {str(e)}",
            "message": "Error while monitoring process"
        }

def register_to_mcp(mcp: FastMCP) -> None:
    """
    Register the process_monitor_process tool to the FastMCP server.
    
    Args:
        mcp (FastMCP): The FastMCP server instance.
    """
    @mcp.tool()
    def process_monitor_process(
        pid: int,
        interval: float = 1.0,
        duration: float = 10.0,
        include_cpu: bool = True,
        include_memory: bool = True,
        include_io: bool = False
    ) -> Dict[str, Any]:
        """
        Monitor a process for a specified duration and return resource usage statistics.
        
        Collects performance metrics for a process over time, taking periodic samples
        and calculating statistics like minimum, maximum, average, and trends.
        
        Args:
            pid: Process ID to monitor
            interval: Monitoring interval in seconds
            duration: Total monitoring duration in seconds
            include_cpu: Whether to monitor CPU usage
            include_memory: Whether to monitor memory usage
            include_io: Whether to monitor I/O activity
            
        Returns:
            A dictionary with the following structure:
            {
                "success": bool,
                "pid": int,
                "process_name": str,
                "metrics": List[Dict],
                "summary": Dict,
                "message": str,
                "metadata": Dict,
                "error": str  # Only present if success is False
            }
            
            The metrics list contains periodic samples of resource usage,
            while the summary object contains statistical analysis of the metrics.
        """
        return monitor_process_logic(pid, interval, duration, include_cpu, include_memory, include_io)