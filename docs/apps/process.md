# Process Management Integration

## Overview

The Process Management integration provides tools for starting, monitoring, and controlling processes on macOS.

## Endpoints

| Endpoint                    | File                   | Description                           |
| --------------------------- | ---------------------- | ------------------------------------- |
| `process_list_processes`    | `list_processes.py`    | List running processes with filtering |
| `process_start_process`     | `start_process.py`     | Start an application or process       |
| `process_terminate_process` | `terminate_process.py` | Terminate a process by PID            |
| `process_get_process_info`  | `get_process_info.py`  | Get detailed process information      |
| `process_monitor_process`   | `monitor_process.py`   | Monitor process resource usage        |

## Key Features

- Process listing with filtering capabilities
- Process launching with arguments
- CPU and memory usage monitoring
- Detailed process information
- Safe process termination

## Usage Examples

### List Processes

```python
from apps.process.list_processes import list_processes_logic

# List processes matching "Safari"
result = list_processes_logic(filter_name="Safari")

# List top 5 processes including background processes
result = list_processes_logic(limit=5, include_background=True)
```

### Start a Process

```python
from apps.process.start_process import start_process_logic

# Start Safari in the background
result = start_process_logic(
    command="open",
    args=["-a", "Safari"],
    background=True
)

# Run a command and get output
result = start_process_logic(
    command="ls",
    args=["-la", "/Users/username/Documents"],
    wait_for_completion=True
)
```

### Monitor Process Usage

```python
from apps.process.monitor_process import monitor_process_logic

# Monitor process for 10 seconds
result = monitor_process_logic(
    pid=12345,
    duration=10.0,
    interval=1.0
)

if result["success"]:
    cpu_stats = result["summary"]["cpu_percent"]
    print(f"CPU: Min={cpu_stats['min']}%, Max={cpu_stats['max']}%, Avg={cpu_stats['avg']}%")
```

### Terminate a Process

```python
from apps.process.terminate_process import terminate_process_logic

# Gracefully terminate
result = terminate_process_logic(pid=12345)

# Force terminate if needed
result = terminate_process_logic(pid=12345, force=True)
```

## Response Formats

### List Processes

```json
{
  "success": true,
  "processes": [
    {
      "pid": 12345,
      "ppid": 1,
      "user": "username",
      "name": "Safari",
      "command": "/Applications/Safari.app/Contents/MacOS/Safari",
      "cpu_percent": 1.5,
      "memory_percent": 2.3,
      "start_time": "Sat May 17 10:30:45 2025"
    }
  ],
  "count": 1,
  "message": "Successfully retrieved 1 process matching 'Safari'"
}
```

### Process Monitoring

```json
{
  "success": true,
  "summary": {
    "pid": 12345,
    "process_name": "Safari",
    "cpu_percent": {
      "min": 1.1,
      "max": 5.6,
      "avg": 2.3
    },
    "memory_percent": {
      "min": 2.3,
      "max": 2.5,
      "avg": 2.4
    }
  },
  "metrics": [
    /* Detailed measurement points */
  ]
}
```
