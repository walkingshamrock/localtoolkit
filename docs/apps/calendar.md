# Calendar App Integration

## Overview

The Calendar integration provides access to the macOS Calendar application, allowing you to list calendars, retrieve events, and create new events.

## Endpoints

| Endpoint                   | File                | Description                                |
| -------------------------- | ------------------- | ------------------------------------------ |
| `calendar_list_calendars`  | `list_calendars.py` | List all available calendars               |
| `calendar_list_events`     | `list_events.py`    | Retrieve events from a specific calendar  |
| `calendar_create_event`    | `create_event.py`   | Create a new event in a specific calendar |

## Key Features

- **Multi-calendar support** - Access events from different calendar accounts (iCloud, Exchange, etc.)
- **Event filtering** - Filter events by date range for focused queries
- **Event creation** - Create new events with full details (title, dates, location, description)
- **All-day event support** - Handle both timed and all-day events
- **Structured data** - Consistent response format with comprehensive event metadata

## Usage Examples

### List Calendars

```python
from localtoolkit.calendar.list_calendars import list_calendars_logic

# Get all calendars sorted by name (default)
result = list_calendars_logic()
if result["success"]:
    for calendar in result["data"]:
        print(f"Calendar: {calendar['name']} (ID: {calendar['id']})")
        print(f"  Type: {calendar['type']}, Color: {calendar['color']}")

# Sort by calendar type
result = list_calendars_logic(sort_by="type")
```

### List Events

```python
from localtoolkit.calendar.list_events import list_events_logic

# First get a calendar ID
calendars = list_calendars_logic()
if calendars["success"] and calendars["data"]:
    calendar_id = calendars["data"][0]["id"]
    
    # Get all events in the calendar
    result = list_events_logic(calendar_id)
    if result["success"]:
        for event in result["data"]:
            print(f"Event: {event['summary']}")
            print(f"  Time: {event['start_date']} to {event['end_date']}")
            if event['location']:
                print(f"  Location: {event['location']}")

    # Get events for today only
    from datetime import date
    today = date.today().isoformat()
    today_events = list_events_logic(
        calendar_id, 
        start_date=today, 
        end_date=today
    )

    # Get upcoming events (next 7 days)
    from datetime import date, timedelta
    end_date = (date.today() + timedelta(days=7)).isoformat()
    upcoming = list_events_logic(
        calendar_id,
        start_date=date.today().isoformat(),
        end_date=end_date,
        sort_by="start_date"
    )
```

### Create Events

```python
from localtoolkit.calendar.create_event import create_event_logic

# Get a calendar to create events in
calendars = list_calendars_logic()
if calendars["success"] and calendars["data"]:
    calendar_id = calendars["data"][0]["id"]
    
    # Create a simple meeting
    result = create_event_logic(
        calendar_id=calendar_id,
        summary="Team Standup",
        start_date="2024-01-15T09:00:00",
        end_date="2024-01-15T09:30:00"
    )
    
    # Create a detailed event
    detailed_event = create_event_logic(
        calendar_id=calendar_id,
        summary="Project Review Meeting",
        start_date="2024-01-16T14:00:00",
        end_date="2024-01-16T15:30:00",
        location="Conference Room A",
        description="Quarterly review of project progress and next steps"
    )
    
    # Create an all-day event
    vacation = create_event_logic(
        calendar_id=calendar_id,
        summary="Vacation Day",
        start_date="2024-01-20",
        end_date="2024-01-20",
        all_day=True
    )
```

## Response Formats

### List Calendars Response

```json
{
  "success": true,
  "data": [
    {
      "name": "Work",
      "id": "calendar-id-123",
      "description": "Work-related events",
      "color": "blue",
      "type": "local"
    },
    {
      "name": "Personal",
      "id": "calendar-id-456",
      "description": "Personal appointments",
      "color": "green",
      "type": "iCloud"
    }
  ],
  "message": "Successfully retrieved 2 calendars",
  "metadata": {
    "count": 2,
    "execution_time_ms": 234,
    "sort_by": "name"
  }
}
```

### List Events Response

```json
{
  "success": true,
  "data": [
    {
      "id": "event-id-789",
      "summary": "Team Meeting",
      "start_date": "2024-01-15T10:00:00",
      "end_date": "2024-01-15T11:00:00",
      "location": "Conference Room B",
      "description": "Weekly team sync",
      "all_day": false,
      "calendar_id": "calendar-id-123"
    }
  ],
  "message": "Successfully retrieved 1 events from calendar ID: calendar-id-123",
  "metadata": {
    "count": 1,
    "execution_time_ms": 456,
    "sort_by": "start_date",
    "calendar_id": "calendar-id-123",
    "start_date": null,
    "end_date": null,
    "limit": 50
  }
}
```

### Create Event Response

```json
{
  "success": true,
  "data": {
    "event_id": "new-event-id-101",
    "summary": "New Meeting",
    "start_date": "2024-01-17T15:00:00",
    "end_date": "2024-01-17T16:00:00",
    "location": "Room 301",
    "description": "Important discussion",
    "all_day": false,
    "calendar_id": "calendar-id-123"
  },
  "message": "Successfully created event 'New Meeting' in calendar ID: calendar-id-123",
  "metadata": {
    "execution_time_ms": 678,
    "calendar_id": "calendar-id-123"
  }
}
```

## Date and Time Formats

### Event Dates
- **Timed events**: Use ISO format `YYYY-MM-DDTHH:MM:SS` (e.g., `2024-01-15T14:30:00`)
- **All-day events**: Use date format `YYYY-MM-DD` (e.g., `2024-01-15`)

### Date Filtering
- **Date range filtering**: Use date format `YYYY-MM-DD` for start_date and end_date parameters
- **Time zone**: All times are in the system's local time zone

## Implementation Notes

- Uses AppleScript to interact with the Calendar app
- Requires Calendar app to be installed and configured
- All operations respect calendar permissions and access controls
- Event creation requires write access to the specified calendar
- Large event lists are automatically limited to prevent timeouts
- Handles multiple calendar types (local, iCloud, Exchange, etc.)

## Error Handling

Common error scenarios:
- **Calendar not found**: Invalid calendar ID provided
- **Permission denied**: No access to Calendar app or specific calendar
- **Invalid date format**: Incorrect date/time format in requests
- **Calendar app not running**: Calendar app needs to be available

## Security Considerations

- All calendar and event names are validated and sanitized
- AppleScript execution follows established security patterns
- No sensitive calendar data is logged
- Access respects macOS Calendar app permissions