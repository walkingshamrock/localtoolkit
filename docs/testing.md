# Testing and Debugging Guide

This document provides guidance on testing and debugging LocalToolKit applications.

## Running the MCP Server

### Standard Mode (stdio)

```bash
python main.py
```

### HTTP Mode with OpenAPI

```bash
mcpo run --mcp main.py
```

This will expose endpoints at http://localhost:3000 with OpenAPI documentation.

### Direct HTTP Mode

```bash
python -c "from main import mcp; mcp.run(transport='http', host='127.0.0.1', port=8000)"
```

## Testing Methods

### 1. Direct Function Testing

Test by importing the logic functions directly:

```python
from localtoolkit.messages.get_messages import get_messages_logic

result = get_messages_logic("conversation_id", limit=10)
print(result)
```

### 2. HTTP API Testing

Test the HTTP API endpoints:

```bash
curl -X POST "http://127.0.0.1:8000/api/tools/contacts_search_by_name" \
  -H "Content-Type: application/json" \
  -d '{"name": "John"}'
```

### 3. Automated Testing

LocalToolKit includes a comprehensive test framework:

```
tests/
├── conftest.py               # Project-level fixtures
├── utils/                    # Test utilities
│   ├── mocks.py              # Common mocks
│   ├── assertions.py         # Custom assertions
│   └── helpers.py            # Test helpers
└── apps/                     # Tests by app
```

Run tests with pytest:

```bash
# Run all tests
pytest

# Run tests for a specific app
pytest tests/apps/messages/

# Run with coverage
pytest --cov=apps
```

## Test Utilities

### Mocking

```python
# Mock AppleScript execution
def test_with_mock_applescript(monkeypatch):
    def mock_execute(script):
        return {
            "success": True,
            "data": "Mock response",
            "message": "Success"
        }

    monkeypatch.setattr("apps.applescript.utils.applescript_runner.applescript_execute", mock_execute)

    # Test your function that uses AppleScript
    result = your_function()
    assert result["success"] == True
```

### Custom Assertions

```python
from tests.utils.assertions import assert_valid_response_format

def test_response_format():
    result = your_function()
    assert_valid_response_format(result, expected_keys=["data"])
```

## Debugging Tips

### 1. Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. Common Issues

- **Permission Issues**: macOS may prompt for permissions on first use
- **Database Access**: Check file permissions for Messages database
- **AppleScript Errors**: Verify AppleScript syntax in script templates
- **HTTP API Errors**: Ensure using correct endpoint path `/api/tools/{tool_name}`

### 3. Troubleshooting Process

1. **Check Permissions**: System Preferences → Security & Privacy → Automation
2. **Verify AppleScript**: Test script in Script Editor first
3. **Check Logs**: Look for error messages in the console output
4. **Test in Isolation**: Test each component separately

### 4. Monitoring Tools

- **AppleScript Execution Time**: Check the metadata in responses
- **Process Resource Usage**: Use the process monitoring endpoints

```python
# Check performance of an operation
from localtoolkit.process.monitor_process import monitor_process_logic
import os

pid = os.getpid()  # Current process
result = monitor_process_logic(pid=pid, duration=5.0)
print(f"CPU: {result['summary']['cpu_percent']['avg']}%")
```
