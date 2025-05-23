# Filesystem Integration

## Overview

The Filesystem integration provides secure access to files and directories on macOS with controlled permissions.

## Endpoints

| Endpoint                    | File                | Description                  |
| --------------------------- | ------------------- | ---------------------------- |
| `filesystem_read_file`      | `read_file.py`      | Read a file's contents       |
| `filesystem_write_file`     | `write_file.py`     | Write content to a file      |
| `filesystem_list_directory` | `list_directory.py` | List contents of a directory |

## Key Features

- Path validation for security
- Directory-based access control
- File read/write with proper encoding handling
- Security logging of all operations

## Usage Examples

### Read a File

```python
from apps.filesystem.read_file import read_file_logic

result = read_file_logic(
    path="/Users/username/Documents/example.txt",
    encoding="utf-8"
)

if result["success"]:
    print(f"File content: {result['content']}")
```

### Write to a File

```python
from apps.filesystem.write_file import write_file_logic

result = write_file_logic(
    path="/Users/username/Documents/example.txt",
    content="Hello, world!",
    encoding="utf-8",
    append=False
)

if result["success"]:
    print(f"File written successfully: {result['bytes_written']} bytes")
```

### List Directory Contents

```python
from apps.filesystem.list_directory import list_directory_logic

result = list_directory_logic(
    path="/Users/username/Documents",
    include_hidden=False
)

if result["success"]:
    for item in result["items"]:
        item_type = "Folder" if item["type"] == "directory" else "File"
        print(f"{item_type}: {item['name']} ({item['size']} bytes)")
```

## Security

- All operations are restricted to allowed directories
- Each allowed directory has specific permissions (read/write/list)
- All operations are logged with timestamps and user information

## Response Formats

### Read File Response

```json
{
  "success": true,
  "content": "File content here...",
  "path": "/path/to/file.txt",
  "bytes_read": 123,
  "encoding": "utf-8"
}
```

### List Directory Response

```json
{
  "success": true,
  "items": [
    {
      "name": "example.txt",
      "type": "file",
      "size": 1024,
      "modified": 1621234567.89
    },
    {
      "name": "subfolder",
      "type": "directory",
      "size": 0,
      "modified": 1621234567.89
    }
  ],
  "path": "/path/to/directory",
  "count": 2
}
```
