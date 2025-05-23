# AppleScript Integration

## Overview

The AppleScript integration provides a secure way to execute AppleScript code across the LocalToolKit project, enabling interaction with macOS applications.

## Endpoints

| Endpoint               | File          | Description                         |
| ---------------------- | ------------- | ----------------------------------- |
| `applescript_run_code` | `run_code.py` | Execute AppleScript with parameters |

## Key Features

- Standardized error handling
- Security checks to prevent dangerous operations
- Performance optimization with timing metrics
- Parameter injection for dynamic script execution

## Usage Examples

### Basic Usage

```python
from apps.applescript.run_code import applescript_run_code

# Get screen dimensions
result = applescript_run_code("""
tell application "Finder"
    set screenSize to bounds of window of desktop
    set screenWidth to item 3 of screenSize
    set screenHeight to item 4 of screenSize
    return "{\\"width\\":" & screenWidth & ", \\"height\\":" & screenHeight & "}"
end tell
""")

if result["success"]:
    dimensions = json.loads(result["data"])
    print(f"Screen dimensions: {dimensions['width']} x {dimensions['height']}")
```

### Using Parameters

```python
# Count files in a folder
result = applescript_run_code(
    code="""
    tell application "Finder"
        set folderRef to POSIX file folderPath as alias
        set fileCount to count of (every file of folder folderRef whose name extension is fileType)
        return "Found " & fileCount & " " & fileType & " files in " & folderName
    end tell
    """,
    params={
        "folderPath": "/Users/username/Documents",
        "folderName": "Documents",
        "fileType": "pdf"
    }
)
```

## Response Format

```json
{
  "success": true,
  "data": "Output from the script",
  "message": "Execution status message",
  "metadata": {
    "execution_time_ms": 42
  }
}
```

## Security Features

- Input validation and type checking
- Dangerous shell command detection
- Timeout controls for script execution
- Restricted execution environment
