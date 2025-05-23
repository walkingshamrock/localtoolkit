# Reminders Integration

## Overview

The Reminders integration provides full read and write access to the macOS Reminders app, allowing you to list, create, update, and delete both reminders and reminder lists.

## Endpoints

| Endpoint                       | File                      | Description                              |
| ------------------------------ | ------------------------- | ---------------------------------------- |
| `reminders_list_reminder_lists` | `list_reminder_lists.py` | List all available reminder lists       |
| `reminders_list_reminders`     | `list_reminders.py`      | List reminders from a specific list     |
| `reminders_create_reminder`    | `create_reminder.py`     | Create a new reminder in a list         |
| `reminders_update_reminder`    | `update_reminder.py`     | Update an existing reminder             |
| `reminders_complete_reminder`  | `complete_reminder.py`   | Mark a reminder as complete/incomplete  |
| `reminders_delete_reminder`    | `delete_reminder.py`     | Delete a reminder                       |
| `reminders_create_reminder_list`| `create_reminder_list.py`| Create a new reminder list              |

## Key Features

- **Read Operations**: Retrieve all reminder lists with sorting options
- **Write Operations**: Create, update, complete, and delete reminders and lists
- **Flexible Updates**: Update any reminder property (title, notes, due date, priority, completion status)
- **Filter & Sort**: Filter reminders by completion status and sort by multiple criteria
- **List Management**: Create new reminder lists for organization
- **Performance Monitoring**: Execution timing for performance tracking
- **Standardized Responses**: Consistent error handling and response format

## Usage Examples

### List All Reminder Lists

```python
from apps.reminders.list_reminder_lists import reminders_list_reminder_lists

# Get all reminder lists sorted by name (default)
result = reminders_list_reminder_lists()

if result["success"]:
    for reminder_list in result["data"]:
        print(f"List: {reminder_list['name']}, ID: {reminder_list['id']}")

# Sort by ID instead
result = reminders_list_reminder_lists(sort_by="id")
```

### List Reminders from a Specific List

```python
from apps.reminders.list_reminders import reminders_list_reminders

# First get available lists
lists = reminders_list_reminder_lists()

if lists["success"] and lists["data"]:
    list_id = lists["data"][0]["id"]
    
    # Get all reminders in the list
    result = reminders_list_reminders(list_id)
    
    if result["success"]:
        for reminder in result["data"]:
            status = "✓" if reminder["completed"] else "○"
            print(f"{status} {reminder['title']}")
```

### Filter and Sort Reminders

```python
# Get only incomplete reminders
incomplete = reminders_list_reminders(
    list_id="your-list-id", 
    show_completed=False
)

# Sort by due date
sorted_by_date = reminders_list_reminders(
    list_id="your-list-id",
    sort_by="due_date"
)

# Sort by priority
sorted_by_priority = reminders_list_reminders(
    list_id="your-list-id",
    sort_by="priority"
)

# Limit results
limited = reminders_list_reminders(
    list_id="your-list-id",
    limit=10
)
```

### Create Reminders

```python
from localtoolkit.reminders.create_reminder import reminders_create_reminder

# Create a simple reminder
result = reminders_create_reminder(
    list_id="your-list-id",
    title="Buy groceries"
)

# Create a detailed reminder
detailed_reminder = reminders_create_reminder(
    list_id="your-list-id",
    title="Doctor appointment",
    notes="Annual checkup - bring insurance card",
    due_date="2024-01-20T14:30:00",  # ISO 8601 format - auto-converted to AppleScript format
    priority=0  # High priority
)

if detailed_reminder["success"]:
    print(f"Created reminder: {detailed_reminder['message']}")
```

### Update Reminders

```python
from localtoolkit.reminders.update_reminder import reminders_update_reminder

# Update reminder title and notes
result = reminders_update_reminder(
    reminder_id="reminder-id-123",
    title="Updated title",
    notes="New notes"
)

# Update due date and priority
result = reminders_update_reminder(
    reminder_id="reminder-id-123",
    due_date="2024-01-25T10:00:00",
    priority=5
)

# Clear due date (set to None)
result = reminders_update_reminder(
    reminder_id="reminder-id-123",
    due_date=""  # Empty string clears the due date
)
```

### Complete/Uncomplete Reminders

```python
from localtoolkit.reminders.complete_reminder import reminders_complete_reminder

# Mark reminder as complete
result = reminders_complete_reminder("reminder-id-123", completed=True)

# Mark reminder as incomplete
result = reminders_complete_reminder("reminder-id-123", completed=False)

# Default is to mark as complete
result = reminders_complete_reminder("reminder-id-123")
```

### Delete Reminders

```python
from localtoolkit.reminders.delete_reminder import reminders_delete_reminder

# Delete a reminder (returns the deleted reminder's details)
result = reminders_delete_reminder("reminder-id-123")

if result["success"]:
    print(f"Deleted reminder: {result['message']}")
    print(f"Deleted reminder data: {result['data']}")
```

### Create Reminder Lists

```python
from localtoolkit.reminders.create_reminder_list import reminders_create_reminder_list

# Create a new reminder list
result = reminders_create_reminder_list("Project Tasks")

if result["success"]:
    print(f"Created list: {result['message']}")
    # Use the returned list ID for creating reminders
    list_data = json.loads(result['data'])
    new_list_id = list_data['id']
```

## Response Format

### List Reminder Lists Response

```json
{
  "success": true,
  "data": [
    {
      "name": "Shopping",
      "id": "x-coredata://..."
    },
    {
      "name": "Work Tasks",
      "id": "x-coredata://..."
    }
  ],
  "message": "Successfully retrieved 2 reminder lists",
  "metadata": {
    "count": 2,
    "execution_time_ms": 45,
    "sort_by": "name"
  }
}
```

### List Reminders Response

```json
{
  "success": true,
  "data": [
    {
      "title": "Buy groceries",
      "id": "x-coredata://...",
      "completed": false,
      "due_date": "2024-01-15T10:00:00Z",
      "notes": "Don't forget milk",
      "priority": 5,
      "list_id": "x-coredata://..."
    },
    {
      "title": "Call dentist",
      "id": "x-coredata://...",
      "completed": true,
      "due_date": null,
      "notes": "",
      "priority": 0,
      "list_id": "x-coredata://..."
    }
  ],
  "message": "Successfully retrieved 2 reminders from list ID: x-coredata://...",
  "metadata": {
    "count": 2,
    "incomplete_count": 1,
    "execution_time_ms": 67,
    "sort_by": "title",
    "list_id": "x-coredata://...",
    "show_completed": true
  }
}
```

### Create Reminder Response

```json
{
  "success": true,
  "data": "{\"title\":\"Buy groceries\",\"id\":\"new-reminder-id\",\"completed\":false,\"due_date\":\"2024-01-20T14:30:00Z\",\"notes\":\"Annual checkup\",\"priority\":0,\"list_id\":\"list-id-123\"}",
  "message": "Successfully created reminder 'Buy groceries' in list ID: list-id-123"
}
```

### Update Reminder Response

```json
{
  "success": true,
  "data": "{\"title\":\"Updated title\",\"id\":\"reminder-id-123\",\"completed\":false,\"due_date\":\"2024-01-25T10:00:00Z\",\"notes\":\"Updated notes\",\"priority\":5,\"list_id\":\"list-id-123\"}",
  "message": "Successfully updated reminder ID: reminder-id-123"
}
```

### Complete Reminder Response

```json
{
  "success": true,
  "data": "{\"title\":\"Buy groceries\",\"id\":\"reminder-id-123\",\"completed\":true,\"due_date\":\"2024-01-20T14:30:00Z\",\"notes\":\"Don't forget milk\",\"priority\":5,\"list_id\":\"list-id-123\"}",
  "message": "Successfully marked reminder ID: reminder-id-123 as completed"
}
```

### Delete Reminder Response

```json
{
  "success": true,
  "data": "{\"title\":\"Buy groceries\",\"id\":\"reminder-id-123\",\"completed\":false,\"due_date\":\"2024-01-20T14:30:00Z\",\"notes\":\"Don't forget milk\",\"priority\":5,\"list_id\":\"list-id-123\"}",
  "message": "Successfully deleted reminder ID: reminder-id-123"
}
```

### Create Reminder List Response

```json
{
  "success": true,
  "data": "{\"name\":\"Project Tasks\",\"id\":\"new-list-id-456\"}",
  "message": "Successfully created reminder list 'Project Tasks'"
}
```

## Parameters

### Read Operations

#### reminders_list_reminder_lists

- `sort_by` (optional): Field to sort by - "name" (default) or "id"

#### reminders_list_reminders

- `list_id` (required): ID of the reminder list (obtained from list_reminder_lists)
- `show_completed` (optional): Include completed reminders (default: true)
- `sort_by` (optional): Sort field - "title" (default), "due_date", "priority", or "completed"
- `limit` (optional): Maximum number of reminders to return (default: 50)

### Write Operations

#### reminders_create_reminder

- `list_id` (required): ID of the reminder list to add the reminder to
- `title` (required): Title/name of the reminder
- `notes` (optional): Notes/body text for the reminder
- `due_date` (optional): Due date in ISO 8601 format (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD)
- `priority` (optional): Priority (0=high, 5=medium, 9=low)

#### reminders_update_reminder

- `reminder_id` (required): ID of the reminder to update
- `title` (optional): New title/name for the reminder
- `notes` (optional): New notes/body text (empty string to clear)
- `due_date` (optional): New due date in ISO 8601 format (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD, empty string to clear)
- `priority` (optional): New priority (0=high, 5=medium, 9=low)
- `completed` (optional): Completion status (true/false)

#### reminders_complete_reminder

- `reminder_id` (required): ID of the reminder to update
- `completed` (optional): True to mark complete, False to mark incomplete (default: true)

#### reminders_delete_reminder

- `reminder_id` (required): ID of the reminder to delete

#### reminders_create_reminder_list

- `name` (required): Name of the reminder list to create

## Priority Values

Reminders use the following priority system:
- `0`: High priority
- `5`: Medium priority  
- `9`: Low priority
- `null`: No priority set

## Implementation Notes

- Uses AppleScript via the `reminders_utils` module for macOS integration
- **Write operations available**: Create, update, complete, and delete reminders and lists
- Input validation and sanitization for all parameters
- Response times are tracked for performance monitoring
- Error handling follows the standardized LocalToolKit format
- List IDs use Core Data format (`x-coredata://...`)
- All string inputs are properly escaped for AppleScript security
- Date parsing supports ISO 8601 format (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD) with automatic conversion to AppleScript format
- Timezone information is stripped from dates (Z suffix or +/-offset) for local time handling