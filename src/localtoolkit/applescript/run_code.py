"""
AppleScript execution module for LocalToolkit.

This module provides functionality to safely execute AppleScript code with
parameter injection and proper error handling.
"""
from fastmcp import FastMCP
from typing import Dict, Any, List, Optional
import json

from localtoolkit.applescript.utils.applescript_runner import applescript_execute


def run_code_logic(
    code: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    return_format: str = "json"
) -> Dict[str, Any]:
    """
    Execute AppleScript code with parameter injection.
    
    Args:
        code: The AppleScript code to execute
        params: Optional dictionary of parameters to inject into the code
        timeout: Maximum execution time in seconds
        return_format: Format for the returned data (json, text, or raw)
        
    Returns:
        Dictionary containing execution results and status
    """
    # Process parameter injection if provided
    processed_code = code
    if params:
        # For each parameter, find and replace placeholders
        for key, value in params.items():
            placeholder = f"${key}"
            
            # Convert value to AppleScript friendly format
            if isinstance(value, str):
                # Escape quotes in strings
                escaped_value = value.replace('"', '\\"')
                replacement = f'"{escaped_value}"'
            elif isinstance(value, bool):
                # Convert Python booleans to AppleScript booleans
                replacement = "true" if value else "false"
            elif isinstance(value, (int, float)):
                # Numbers can be used as-is
                replacement = str(value)
            elif isinstance(value, list):
                # Convert lists to AppleScript lists
                items = []
                for item in value:
                    if isinstance(item, str):
                        escaped_item = item.replace('\"', '\\\"')
                        items.append(f'"{escaped_item}"')
                    elif isinstance(item, bool):
                        items.append("true" if item else "false")
                    else:
                        items.append(str(item))
                replacement = "{" + ", ".join(items) + "}"
            elif value is None:
                # Handle None values
                replacement = "missing value"
            else:
                # For complex objects, use JSON
                json_str = json.dumps(value)
                escaped_json = json_str.replace('"', '\\"')
                replacement = f'"{escaped_json}"'
                
            processed_code = processed_code.replace(placeholder, replacement)
    
    # Execute the code
    result = applescript_execute(processed_code, params=None, timeout=timeout)
    
    # Build the standard response
    response = {
        "success": result.get("success", False),
        "status": 1 if result.get("success", False) else 0,
        "runtime_seconds": result.get("metadata", {}).get("execution_time_ms", 0) / 1000
    }
    
    # Add error message if present
    if "error" in result:
        response["error"] = result["error"]
    
    # Process output based on requested format
    if result.get("success", False) and "data" in result:
        output = result["data"]
        
        if return_format == "json":
            # Use the already parsed JSON if available
            is_parsed = result.get("metadata", {}).get("parsed", False)
            if is_parsed:
                response["result"] = output
            else:
                # Try to parse output as JSON again if it wasn't already parsed
                try:
                    response["result"] = json.loads(output) if isinstance(output, str) else output
                except (json.JSONDecodeError, TypeError):
                    # If parsing fails, return raw output and set a warning
                    response["result"] = output
                    response["warning"] = "Output could not be parsed as JSON"
        elif return_format == "text":
            # Return as plain text
            response["result"] = output
        else:  # raw format
            # Return the raw output
            response["raw_output"] = output
    
    return response


def register_to_mcp(mcp: FastMCP) -> None:
    """Register the applescript_run_code tool with the MCP server."""
    @mcp.tool()
    def applescript_run_code(
        code: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        return_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Execute AppleScript code with parameter injection.
        
        Allows for safe execution of AppleScript with proper parameter handling
        and standardized error reporting.
        
        Args:
            code: The AppleScript code to execute
            params: Optional dictionary of parameters to inject into the code
            timeout: Maximum execution time in seconds
            return_format: Format for the returned data (json, text, or raw)
            
        Returns:
            Dictionary containing execution results and status
        """
        return run_code_logic(code, params, timeout, return_format)
