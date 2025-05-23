# Core Concepts

## Architecture Principles

### Separation of Concerns

LocalToolKit is built on strict separation between app integrations:

- Each app integration (Messages, Contacts, etc.) is isolated in its own directory
- No cross-dependencies between app modules
- One endpoint per file for clear responsibility boundaries
- App-specific utilities stay in the app's utils directory

### Standardized Response Format

All API endpoints return a consistent response structure:

```json
{
  "success": true,
  "data": [], // Or any specific field name appropriate for the endpoint
  "message": "Operation completed successfully",
  "metadata": {},
  "error": null // Present only when success is false
}
```

### Centralized Security

- AppleScript execution flows through a single, secure runner
- Input validation occurs at the API boundary
- All filesystem operations are logged and restricted

## Project Structure

```
apps/
├── applescript/     # AppleScript execution utilities
├── contacts/        # Contacts app integration
├── filesystem/      # Filesystem operations
├── mail/           # Mail app integration
├── mcp/             # MCP server components
├── messages/        # Messages app integration
└── process/         # Process management utilities
```

## Integration Patterns

- Each app exposes endpoints as individual Python files
- All endpoints register with the MCP server in their app's **init**.py
- Logic functions can be imported and used directly in Python code
- Functions follow a consistent naming pattern: `<app>_<action>`

## Future Development

When extending LocalToolKit, follow these principles:

1. **Maintain separation** - Keep each app isolated
2. **Use consistent formats** - Follow the standard response structure
3. **Error handling** - Handle errors gracefully and provide meaningful messages
4. **Document everything** - Keep documentation in sync with implementation
5. **Security first** - Use the established security patterns
6. **Modular organization** - Prefer shorter files that are appropriately modularized
