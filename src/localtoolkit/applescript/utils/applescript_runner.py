"""
Simple, enhanced AppleScript runner for LocalToolkit.

A streamlined implementation that focuses on direct parameter injection
for more reliable AppleScript execution.
"""

import subprocess
import json
import re
import time
from typing import Dict, Any, Optional

def check_security(code: str) -> Optional[Dict[str, Any]]:
    """
    Check for security issues in the AppleScript code.
    
    Args:
        code: The AppleScript code to check
        
    Returns:
        None if secure, error response dictionary if potentially dangerous
    """
    # Shell commands to block
    dangerous_shell_patterns = [
        r"rm\s+-rf",
        r"sudo",
        r"rm\s+/",
        r"mkfs",
        r"dd\s+if=",
        r">\s+/dev/sd"
    ]
    
    # AppleScript-specific dangerous patterns
    dangerous_applescript_patterns = [
        r"do shell script.*sudo",
        r"with administrator privileges",
        r"system attribute",
        r"delete file"
    ]
    
    all_patterns = dangerous_shell_patterns + dangerous_applescript_patterns
    
    for pattern in all_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return {
                "success": False,
                "error": f"Potentially dangerous pattern detected: {pattern}",
                "data": None
            }
    
    return None

def applescript_execute(code: str, params: Optional[Dict[str, Any]] = None, 
                       timeout: int = 30, debug: bool = False) -> Dict[str, Any]:
    """
    Execute AppleScript with simple, direct parameter injection.
    
    Args:
        code: The AppleScript code to execute
        params: Parameters to inject directly into the script
        timeout: Execution timeout in seconds (default: 30)
        debug: Enable debug logging for troubleshooting
        
    Returns:
        Dict with success, data, and error information
    """
    # Start timing
    start_time = time.time()
    
    # Debug output
    if debug:
        print(f"Executing AppleScript with timeout: {timeout}s")
        print(f"Script length: {len(code)} characters")
        if params:
            print(f"Parameters: {params}")
    
    # Check security first
    security_error = check_security(code)
    if security_error:
        security_error["execution_time_ms"] = 0
        return security_error
    
    # Prepare script with parameters
    script_to_execute = code
    
    if params:
        # Simple parameter injection at the beginning of the script
        declarations = []
        for key, value in params.items():
            # Format the value based on its type
            if isinstance(value, str):
                # Escape quotes in strings
                escaped = value.replace('"', '\\"')
                formatted_value = f'"{escaped}"'
            elif isinstance(value, bool):
                formatted_value = "true" if value else "false"
            elif value is None:
                formatted_value = "missing value"
            else:
                # Numbers and other types
                formatted_value = str(value)
                
            declarations.append(f"set {key} to {formatted_value}")
        
        # Add declarations at the beginning
        param_block = "\n".join(declarations)
        script_to_execute = param_block + "\n\n" + code
    
    # Execute the script
    try:
        result = subprocess.run(
            ["osascript", "-e", script_to_execute],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Debug output
        if debug:
            print(f"Execution time: {execution_time:.2f}s")
            print(f"Return code: {result.returncode}")
            if result.returncode != 0:
                print(f"Error: {result.stderr}")
        
        # Handle errors
        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr.strip(),
                "data": None,
                "metadata": {
                    "execution_time_ms": int(execution_time * 1000),
                    "parsed": False
                },
                "message": "AppleScript execution failed"
            }
        
        # Process output
        output = result.stdout.strip()
        
        # Try to parse as JSON if it looks like JSON
        data = output
        parsed = False
        
        if (output.startswith("{") and output.endswith("}")) or \
           (output.startswith("[") and output.endswith("]")):
            try:
                data = json.loads(output)
                parsed = True
            except json.JSONDecodeError:
                # Keep as string if not valid JSON
                pass
        
        return {
            "success": True,
            "data": data,
            "message": "AppleScript execution successful",
            "metadata": {
                "execution_time_ms": int(execution_time * 1000),
                "parsed": parsed
            }
        }
        
    except subprocess.TimeoutExpired:
        if debug:
            print(f"TIMEOUT after {timeout}s")
            
        return {
            "success": False,
            "error": f"Script execution timed out after {timeout} seconds",
            "data": None,
            "message": "AppleScript execution timed out",
            "metadata": {
                "execution_time_ms": timeout * 1000,
                "parsed": False
            }
        }
    except Exception as e:
        if debug:
            print(f"EXCEPTION: {str(e)}")
            
        return {
            "success": False,
            "error": str(e),
            "data": None,
            "message": "AppleScript execution failed with exception",
            "metadata": {
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "parsed": False
            }
        }