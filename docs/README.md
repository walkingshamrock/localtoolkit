# LocalToolKit Documentation

## What is LocalToolKit?

LocalToolKit (LTK) provides a structured API layer for macOS application integration, allowing programmatic access to native macOS apps like Messages, Contacts, Mail and more through a consistent API following Anthropic's Model Context Protocol (MCP) standard.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server (stdio mode for direct LLM integration)
python main.py

# OR run in HTTP mode with OpenAPI support
mcpo run --mcp main.py
```

## Documentation Structure

- **[Core Concepts](core-concepts.md)** - Project architecture and principles
- **App Integrations**:
  - [Messages](apps/messages.md) - Work with iMessage conversations and messages
  - [Contacts](apps/contacts.md) - Search and manage macOS Contacts
  - [Mail](apps/mail.md) - Send and manage emails
  - [Calendar](apps/calendar.md) - List calendars, view and create events
  - [Notes](apps/notes.md) - Create, read, update, and manage notes
  - [Filesystem](apps/filesystem.md) - Read and write files safely
  - [Process](apps/process.md) - Manage macOS processes
  - [AppleScript](apps/applescript.md) - Run AppleScript securely
  - [Reminders](apps/reminders.md) - Create and manage reminders
- **[Integration Patterns](integration-patterns.md)** - Examples of common workflows
- **[Development](development.md)** - Development workflow, guidelines and contributions
- **[Testing](testing.md)** - Testing and debugging your apps

## Core Features

- **Structured API** - Consistent response formats across all integrations
- **Secure** - Controlled access to system resources
- **Modular** - Each app integration is self-contained and independently maintained
- **Documented** - Comprehensive documentation for each endpoint
- **Extensible** - Easy to add new app integrations
