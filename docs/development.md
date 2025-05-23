# Development Guide

This document outlines the development workflow, coding standards and best practices for contributing to LocalToolKit.

## Getting Started

```bash
# Clone the repository
git clone https://github.com/walkingshamrock/localtoolkit.git
cd localtoolkit

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Development Workflow

1. **Create an issue** describing the feature or bug fix
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/42-new-feature
   ```
3. **Implement your changes**, following project standards
4. **Test your changes** locally
5. **Submit a pull request**, referencing the issue
6. **Address review comments**
7. **Merge** once approved

## Coding Standards

### File Structure

- One endpoint per file
- Endpoint files named after their action (e.g., `search_by_name.py`)
- Function name follows the pattern `<app>_<action>` (e.g., `contacts_search_by_name`)
- Logic function named `<action>_logic` (e.g., `search_by_name_logic`)

### Function Format

```python
def function_name(param1: str, param2: Optional[int] = None) -> Dict[str, Any]:
    """
    One-line summary of what the function does.

    Detailed description of functionality and context.

    Args:
        param1: Description of the parameter
        param2: Description with default behavior

    Returns:
        A dictionary with standard response format
    """
    try:
        # Function implementation
        return {
            "success": True,
            "data": result,
            "message": "Operation successful"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Operation failed"
        }
```

## Adding a New App Integration

1. **Create the app directory**:

   ```
   src/localtoolkit/new_app_name/
   ```

2. **Add **init**.py with MCP registration**:

   ```python
   def register_to_mcp(mcp):
       from .feature_one import feature_one_function
       mcp.tool("new_app_feature_one")(feature_one_function)
   ```

3. **Create endpoint files** with logic and API functions

4. **Add documentation** in `docs/apps/new_app.md`

5. **Update main.py** to register your app:
   ```python
   from localtoolkit.new_app_name import register_to_mcp as register_new_app
   register_new_app(mcp)
   ```

## Response Format

All endpoints should follow this response format:

```python
{
    "success": True,  # Boolean indicating success/failure
    "data": [],       # Primary response data (could be named specifically)
    "message": "",    # Human-readable status message
    "metadata": {},   # Optional metadata about the request/response
    "error": None     # Error details (only present when success=False)
}
```

## Best Practices

1. **Separate Logic from API**: Keep core logic separate from API layer
2. **Error Handling**: Always catch exceptions and return meaningful errors
3. **Type Annotations**: Use Python type hints for better code quality
4. **Documentation**: Keep docstrings up to date with implementation
5. **Security First**: Validate all inputs and use secure patterns
6. **Testing**: Write tests for each new endpoint

## Common Patterns

### Using AppleScript

```python
from localtoolkit.applescript.utils.applescript_runner import applescript_execute

def my_function(parameter):
    script = f"""
    tell application "App Name"
        -- Do something with {parameter}
    end tell
    """

    result = applescript_execute(script)

    if result["success"]:
        # Process the result
        return {
            "success": True,
            "data": processed_data
        }
    else:
        return result  # Forward the error
```
