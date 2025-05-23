# Notes App Integration

The Notes app integration provides comprehensive access to the macOS Notes application, allowing you to create, read, update, and list notes programmatically.

## Features

- **List Notes**: Retrieve notes with optional folder filtering and result limiting
- **Create Notes**: Create new notes with optional folder placement
- **Get Notes**: Retrieve specific notes by their unique ID
- **Update Notes**: Modify existing note names and content
- **Folder Support**: Organize notes in folders and filter by folder
- **Rich Metadata**: Access note creation dates, modification dates, and previews

## Available Endpoints

### `notes_list_notes`

List notes from the Notes app with optional filtering and limiting.

**Parameters:**
- `limit` (int, optional): Maximum number of notes to return (default: 20)
- `folder` (str, optional): Name of specific folder to list notes from

**Returns:**
```json
{
  "success": bool,
  "notes": [
    {
      "id": "x-coredata://...",
      "name": "Note Title",
      "body": "Full note content",
      "preview": "Preview of content...",
      "modification_date": "Monday, January 1, 2024 at 12:00:00 PM",
      "folder": "Folder Name"
    }
  ],
  "message": "Found 3 note(s)",
  "metadata": {
    "total_matches": 15,
    "execution_time_ms": 156,
    "folder_filter": null
  }
}
```

**Examples:**
```python
# List all notes (up to 20)
result = notes_list_notes()

# List notes from specific folder
result = notes_list_notes(folder="Work")

# List more notes
result = notes_list_notes(limit=50)

# List notes from personal folder with limit
result = notes_list_notes(folder="Personal", limit=10)
```

### `notes_create_note`

Create a new note in the Notes app.

**Parameters:**
- `name` (str, required): The title/name of the note
- `body` (str, required): The content of the note
- `folder` (str, optional): Name of folder to create the note in (creates folder if it doesn't exist)

**Returns:**
```json
{
  "success": bool,
  "note": {
    "id": "x-coredata://...",
    "name": "New Note",
    "body": "Note content",
    "modification_date": "Monday, January 1, 2024 at 12:00:00 PM",
    "folder": "Work"
  },
  "message": "Note 'New Note' created successfully in folder 'Work'",
  "metadata": {
    "execution_time_ms": 215,
    "folder": "Work"
  }
}
```

**Examples:**
```python
# Create a simple note
result = notes_create_note(
    name="Meeting Notes",
    body="Discussed project timeline and deliverables."
)

# Create note in specific folder
result = notes_create_note(
    name="Shopping List",
    body="- Milk\n- Bread\n- Eggs",
    folder="Personal"
)

# Create note with multiline content
result = notes_create_note(
    name="Recipe",
    body="Ingredients:\n- 2 cups flour\n- 1 egg\n\nInstructions:\n1. Mix ingredients\n2. Bake at 350°F",
    folder="Recipes"
)
```

### `notes_get_note`

Retrieve a specific note by its unique identifier.

**Parameters:**
- `note_id` (str, required): The unique identifier of the note to retrieve

**Returns:**
```json
{
  "success": bool,
  "note": {
    "id": "x-coredata://...",
    "name": "Note Title",
    "body": "Full note content",
    "preview": "Preview text...",
    "modification_date": "Monday, January 1, 2024 at 12:00:00 PM",
    "creation_date": "Sunday, December 31, 2023 at 11:30:00 PM",
    "folder": "Work"
  },
  "message": "Retrieved note 'Note Title'",
  "metadata": {
    "execution_time_ms": 123
  }
}
```

**Examples:**
```python
# Get a specific note
result = notes_get_note("x-coredata://12345678-1234-1234-1234-123456789012/Note/p1")

if result["success"]:
    note = result["note"]
    print(f"Note: {note['name']}")
    print(f"Content: {note['body']}")
    print(f"Last modified: {note['modification_date']}")
```

### `notes_update_note`

Update an existing note's name and/or content.

**Parameters:**
- `note_id` (str, required): The unique identifier of the note to update
- `name` (str, optional): New name/title for the note
- `body` (str, optional): New content for the note

**Note:** At least one of `name` or `body` must be provided.

**Returns:**
```json
{
  "success": bool,
  "note": {
    "id": "x-coredata://...",
    "name": "Updated Note Title",
    "body": "Updated content",
    "preview": "Updated content preview...",
    "modification_date": "Monday, January 1, 2024 at 1:00:00 PM",
    "creation_date": "Sunday, December 31, 2023 at 11:30:00 PM",
    "folder": "Work"
  },
  "message": "Updated name and content for note 'Updated Note Title'",
  "metadata": {
    "execution_time_ms": 189,
    "updated_fields": ["name", "content"]
  }
}
```

**Examples:**
```python
# Update note content only
result = notes_update_note(
    note_id="x-coredata://12345678-1234-1234-1234-123456789012/Note/p1",
    body="Updated content for this note."
)

# Update note name only
result = notes_update_note(
    note_id="x-coredata://12345678-1234-1234-1234-123456789012/Note/p1",
    name="New Note Title"
)

# Update both name and content
result = notes_update_note(
    note_id="x-coredata://12345678-1234-1234-1234-123456789012/Note/p1",
    name="Updated Meeting Notes",
    body="Meeting was postponed to next week.\nNew agenda items to discuss."
)
```

## Working with Folders

The Notes integration supports organizing notes in folders:

### Creating Notes in Folders

When creating a note with a folder parameter, the integration will:
1. Check if the folder exists
2. Create the folder if it doesn't exist
3. Place the note in the specified folder

```python
# This will create the "Projects" folder if it doesn't exist
result = notes_create_note(
    name="Project Plan",
    body="Initial project planning notes",
    folder="Projects"
)
```

### Filtering by Folder

You can filter notes when listing by specifying a folder:

```python
# List only notes in the "Work" folder
work_notes = notes_list_notes(folder="Work")

# List notes in "Personal" folder with a limit
personal_notes = notes_list_notes(folder="Personal", limit=10)
```

## Note IDs

Notes are identified by unique Core Data URLs that look like:
```
x-coredata://12345678-1234-1234-1234-123456789012/Note/p1
```

These IDs are:
- **Persistent**: They remain constant across app restarts
- **Unique**: Each note has a globally unique identifier
- **Required**: Needed for `get_note` and `update_note` operations

You can obtain note IDs from the `list_notes` operation.

## Error Handling

All endpoints follow consistent error handling patterns:

### Common Error Scenarios

1. **Permission Issues**: Notes app access is restricted
2. **Note Not Found**: Invalid or non-existent note ID
3. **Invalid Input**: Malformed parameters or invalid note names
4. **App Not Available**: Notes app is not installed or accessible

### Error Response Format

```json
{
  "success": false,
  "notes": [],  // or "note": null for single-note operations
  "message": "Error description",
  "error": "Specific error details",
  "metadata": {
    "execution_time_ms": 67
  }
}
```

### Example Error Handling

```python
result = notes_get_note("invalid-note-id")

if not result["success"]:
    if result["error"] == "Note not found":
        print("The note doesn't exist")
    elif "Permission" in result["error"]:
        print("Need to grant Notes app access")
    else:
        print(f"Error: {result['error']}")
```

## Performance Considerations

### Response Times
- **List Notes**: 1-3 seconds (depends on total number of notes)
- **Create Note**: 1-3 seconds
- **Get Note**: 0.5-2 seconds
- **Update Note**: 1-3 seconds

### Optimization Tips

1. **Use Folder Filtering**: Improves list performance significantly
2. **Limit Results**: Use the `limit` parameter to reduce processing time
3. **Batch Operations**: When working with multiple notes, process them in batches
4. **Cache Note IDs**: Store frequently accessed note IDs to avoid repeated list operations

## Security and Privacy

### Permissions Required

The Notes integration requires:
- **Automation permissions** for the Notes app
- **AppleScript execution** privileges

### Data Access

- Only accesses notes and folder information
- No network communication
- All operations are local to your Mac
- Follows macOS security and privacy guidelines

### Best Practices

1. **Validate Input**: Always validate note names and content before creation
2. **Handle Errors Gracefully**: Implement proper error handling for all operations
3. **Respect User Privacy**: Only access notes when necessary for your application
4. **Monitor Performance**: Be mindful of large note collections affecting performance

## Integration Examples

### Basic Note Management

```python
# Create a daily journal entry
def create_daily_journal(content):
    from datetime import date
    today = date.today().strftime("%B %d, %Y")
    
    result = notes_create_note(
        name=f"Journal - {today}",
        body=content,
        folder="Journal"
    )
    
    if result["success"]:
        return result["note"]["id"]
    else:
        raise Exception(f"Failed to create journal: {result['error']}")

# Find and update a note
def update_meeting_notes(meeting_name, new_content):
    # Find the note
    notes = notes_list_notes(folder="Work")
    
    target_note = None
    for note in notes["notes"]:
        if meeting_name.lower() in note["name"].lower():
            target_note = note
            break
    
    if target_note:
        result = notes_update_note(
            note_id=target_note["id"],
            body=new_content
        )
        return result["success"]
    
    return False
```

### Note Search and Organization

```python
# Search notes by content
def search_notes_by_content(search_term):
    all_notes = notes_list_notes(limit=100)
    matching_notes = []
    
    for note in all_notes["notes"]:
        if search_term.lower() in note["body"].lower():
            matching_notes.append(note)
    
    return matching_notes

# Organize notes by creating folder structure
def organize_notes_by_topic():
    topics = ["Work", "Personal", "Ideas", "References"]
    
    for topic in topics:
        # Create a sample note in each folder to ensure folders exist
        notes_create_note(
            name=f"{topic} Index",
            body=f"Index note for {topic} category",
            folder=topic
        )
```

This integration provides a robust foundation for building Notes-based workflows and automation within your macOS applications.