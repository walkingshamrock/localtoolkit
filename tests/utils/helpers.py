"""
General test helpers for mac-mcp tests.

This module provides utility functions that help with common testing tasks,
such as comparing data structures, extracting specific information from
responses, and other testing operations.
"""

import json
import re
from typing import Dict, Any, List, Union, Optional, Callable


def extract_applescript_from_code(code: str) -> str:
    """
    Extract the AppleScript code from a code string.
    
    This is useful for isolating the core AppleScript part without parameter
    declarations or other boilerplate.
    
    Args:
        code (str): The full code string containing AppleScript
        
    Returns:
        str: The extracted AppleScript portion
    """
    # Remove parameter declarations at the beginning
    lines = code.strip().split('\n')
    applescript_lines = []
    
    # Skip variable declaration lines
    for line in lines:
        # Skip lines that look like variable declarations
        if re.match(r'^\s*set\s+\w+\s+to\s+', line) and ' of ' not in line:
            continue
        applescript_lines.append(line)
    
    return '\n'.join(applescript_lines)


def verify_script_contains(code: str, expected_parts: List[str]) -> List[str]:
    """
    Verify that a script contains all expected parts.
    
    Args:
        code (str): The script to verify
        expected_parts (list): List of strings expected to be in the script
        
    Returns:
        list: List of missing parts, empty if all parts are found
    """
    missing_parts = []
    for part in expected_parts:
        if part not in code:
            missing_parts.append(part)
    return missing_parts


def normalize_dict_for_comparison(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a dictionary for comparison by sorting lists and standardizing values.
    
    Args:
        d (dict): Dictionary to normalize
        
    Returns:
        dict: Normalized dictionary
    """
    if not isinstance(d, dict):
        return d
    
    result = {}
    
    for key, value in d.items():
        # Recursively normalize nested dictionaries
        if isinstance(value, dict):
            result[key] = normalize_dict_for_comparison(value)
        # Sort and normalize lists
        elif isinstance(value, list):
            if all(isinstance(item, dict) for item in value):
                # For lists of dictionaries, normalize each dictionary
                result[key] = sorted(
                    [normalize_dict_for_comparison(item) for item in value],
                    key=lambda x: json.dumps(x, sort_keys=True)
                )
            else:
                # For other lists, just sort them if possible
                try:
                    result[key] = sorted(value)
                except TypeError:
                    # If not sortable, keep as is
                    result[key] = value
        else:
            result[key] = value
    
    return result


def compare_dicts(actual: Dict[str, Any], expected: Dict[str, Any], 
                  ignore_keys: Optional[List[str]] = None) -> List[str]:
    """
    Compare dictionaries and return differences.
    
    Args:
        actual (dict): The actual dictionary
        expected (dict): The expected dictionary
        ignore_keys (list, optional): Keys to ignore in the comparison
        
    Returns:
        list: List of differences, empty if dictionaries match
    """
    ignore_keys = ignore_keys or []
    differences = []
    
    # Check for missing keys in actual
    for key in expected:
        if key in ignore_keys:
            continue
        
        if key not in actual:
            differences.append(f"Missing key in actual: {key}")
            continue
        
        # Check value differences
        if isinstance(expected[key], dict) and isinstance(actual[key], dict):
            # Recursively compare dictionaries
            nested_differences = compare_dicts(actual[key], expected[key], ignore_keys)
            differences.extend([f"{key}.{diff}" for diff in nested_differences])
        elif isinstance(expected[key], list) and isinstance(actual[key], list):
            # Check list length
            if len(expected[key]) != len(actual[key]):
                differences.append(f"List length mismatch for {key}: expected {len(expected[key])}, got {len(actual[key])}")
            
            # If lists contain dictionaries, compare each item
            if expected[key] and isinstance(expected[key][0], dict):
                for i, (exp_item, act_item) in enumerate(zip(expected[key], actual[key])):
                    nested_differences = compare_dicts(act_item, exp_item, ignore_keys)
                    differences.extend([f"{key}[{i}].{diff}" for diff in nested_differences])
        elif expected[key] != actual[key]:
            differences.append(f"Value mismatch for {key}: expected {expected[key]}, got {actual[key]}")
    
    # Check for extra keys in actual
    for key in actual:
        if key in ignore_keys:
            continue
        
        if key not in expected:
            differences.append(f"Extra key in actual: {key}")
    
    return differences


def extract_response_data(response: Dict[str, Any], 
                         data_key: str) -> Any:
    """
    Extract data from a response by key path.
    
    Args:
        response (dict): The response dictionary
        data_key (str): Key or dot-notation path to the data
        
    Returns:
        Any: The extracted data
        
    Raises:
        KeyError: If the key path does not exist
    """
    if '.' not in data_key:
        return response[data_key]
    
    parts = data_key.split('.')
    current = response
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise KeyError(f"Key path '{data_key}' not found in response")
    
    return current


def filter_responses(responses: List[Dict[str, Any]], 
                    filter_fn: Callable[[Dict[str, Any]], bool]) -> List[Dict[str, Any]]:
    """
    Filter a list of responses using a filter function.
    
    Args:
        responses (list): List of response dictionaries
        filter_fn (callable): Function that takes a response and returns a boolean
        
    Returns:
        list: Filtered list of responses
    """
    return [response for response in responses if filter_fn(response)]


def find_response_by_key_value(responses: List[Dict[str, Any]], 
                              key: str, value: Any) -> Optional[Dict[str, Any]]:
    """
    Find the first response with a matching key-value pair.
    
    Args:
        responses (list): List of response dictionaries
        key (str): Key to match
        value (any): Value to match
        
    Returns:
        dict or None: Matching response or None if not found
    """
    for response in responses:
        if key in response and response[key] == value:
            return response
    return None


def extract_script_params(code: str) -> Dict[str, str]:
    """
    Extract parameter declarations from an AppleScript.
    
    Args:
        code (str): The AppleScript code
        
    Returns:
        dict: Dictionary of parameter names and their values
    """
    params = {}
    param_pattern = r'set\s+(\w+)\s+to\s+(.+)'
    
    for line in code.split('\n'):
        match = re.match(param_pattern, line.strip())
        if match:
            name = match.group(1)
            value = match.group(2)
            params[name] = value.strip()
    
    return params


def parse_applescript_error(error_message: str) -> Dict[str, Any]:
    """
    Parse an AppleScript error message into structured information.
    
    Args:
        error_message (str): The error message from AppleScript
        
    Returns:
        dict: Structured error information
    """
    error_info = {
        "message": error_message,
        "line_number": None,
        "error_code": None,
        "error_type": None
    }
    
    # Extract line number
    line_match = re.search(r'line (\d+)', error_message)
    if line_match:
        error_info["line_number"] = int(line_match.group(1))
    
    # Extract error code
    code_match = re.search(r'error (\-?\d+)', error_message)
    if code_match:
        error_info["error_code"] = int(code_match.group(1))
    
    # Determine error type
    if "syntax error" in error_message.lower():
        error_info["error_type"] = "syntax"
    elif "execution error" in error_message.lower():
        error_info["error_type"] = "execution"
    elif "permission" in error_message.lower():
        error_info["error_type"] = "permission"
    elif "timeout" in error_message.lower():
        error_info["error_type"] = "timeout"
    
    return error_info


def create_mock_response(success: bool = True, data: Any = None, 
                        error: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a standardized mock response for testing.
    
    Args:
        success (bool, optional): Whether the response is successful. Default is True.
        data (any, optional): Data to include in the response.
        error (str, optional): Error message for unsuccessful responses.
        
    Returns:
        dict: A standardized response dictionary
    """
    response = {
        "success": success,
        "message": "Operation completed successfully" if success else "Operation failed"
    }
    
    if data is not None:
        if isinstance(data, dict):
            response.update(data)
        else:
            response["data"] = data
    
    if not success and error:
        response["error"] = error
    
    return response


def expected_applescript_output(template: str, **kwargs) -> str:
    """
    Generate expected AppleScript output based on a template.
    
    Args:
        template (str): The template string
        **kwargs: Values to substitute in the template
        
    Returns:
        str: The formatted output
    """
    return template.format(**kwargs)


def get_response_timestamp(response: Dict[str, Any], 
                          timestamp_key: str = "timestamp") -> float:
    """
    Get the timestamp from a response.
    
    Args:
        response (dict): The response dictionary
        timestamp_key (str, optional): Key for the timestamp. Default is "timestamp".
        
    Returns:
        float: The timestamp value
        
    Raises:
        KeyError: If the timestamp key does not exist
    """
    if timestamp_key in response:
        return float(response[timestamp_key])
    
    raise KeyError(f"Timestamp key '{timestamp_key}' not found in response")


def validate_uuid(uuid_str: str) -> bool:
    """
    Validate that a string is a valid UUID.
    
    Args:
        uuid_str (str): The string to validate
        
    Returns:
        bool: True if the string is a valid UUID, False otherwise
    """
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, uuid_str.lower()))


def validate_phone_number(phone: str) -> bool:
    """
    Validate that a string is a plausible phone number.
    
    Args:
        phone (str): The string to validate
        
    Returns:
        bool: True if the string is a plausible phone number, False otherwise
    """
    # Remove non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check length (typical phone numbers have 10-15 digits)
    if 10 <= len(digits_only) <= 15:
        return True
    
    return False


def validate_email(email: str) -> bool:
    """
    Validate that a string is a plausible email address.
    
    Args:
        email (str): The string to validate
        
    Returns:
        bool: True if the string is a plausible email address, False otherwise
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def count_occurrences(text: str, pattern: str) -> int:
    """
    Count the number of occurrences of a pattern in text.
    
    Args:
        text (str): The text to search in
        pattern (str): The pattern to search for
        
    Returns:
        int: Number of occurrences
    """
    return len(re.findall(pattern, text))


def is_sorted(items: List[Any], key: Optional[Callable] = None, reverse: bool = False) -> bool:
    """
    Check if a list is sorted.
    
    Args:
        items (list): The list to check
        key (callable, optional): Function that extracts a comparison key
        reverse (bool, optional): Whether to check for reverse sorting
        
    Returns:
        bool: True if the list is sorted, False otherwise
    """
    if not items:
        return True
    
    if key is None:
        key = lambda x: x
    
    for i in range(len(items) - 1):
        if reverse:
            if key(items[i]) < key(items[i + 1]):
                return False
        else:
            if key(items[i]) > key(items[i + 1]):
                return False
    
    return True
