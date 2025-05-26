# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LocalToolKit (LTK) is a macOS automation toolkit that provides AI assistants with structured access to native macOS applications (Messages, Contacts, Mail, Processes, etc.) through the Model Context Protocol (MCP) standard. The project emphasizes security and controlled system access.

## Development Commands

### Setup and Installation
```bash
pip install -e ".[dev]"  # Development mode with test dependencies
```

### Running the MCP Server
```bash
# Default stdio mode
localtoolkit
# or
ltk

# HTTP mode
localtoolkit --transport http --port 8000

# With custom configs
localtoolkit --config /path/to/config.json --filesystem-config /path/to/fs-config.json
```

### Testing
```bash
# Run all tests
pytest

# Run specific app module tests
pytest tests/apps/messages/
pytest tests/apps/reminders/

# Run with coverage
pytest --cov=localtoolkit

# Test markers:
# unit: Individual function tests
# integration: Component interaction tests
# e2e: End-to-end tests (excluded by default, require real system)
```

## Architecture

### Module Structure
The codebase follows a strict modular architecture where each macOS app integration is isolated:

- **applescript/**: AppleScript execution with security validation
- **contacts/**: Contact search by name/phone
- **filesystem/**: Secure file operations with permission controls  
- **mail/**: Email drafting and sending
- **messages/**: SMS/iMessage via SQLite database access
- **process/**: System process management and monitoring
- **reminders/**: Reminders app integration
- **mcp/**: MCP server wrapper using FastMCP

### Key Patterns

#### Standardized Response Format
All API endpoints return this consistent format:
```json
{
  "success": true/false,
  "data": [],           // or specific field name like "messages", "contacts"
  "message": "...",     // Human-readable status
  "metadata": {},       // Optional request/response info
  "error": null         // Only present when success=false
}
```

#### Module Registration Pattern
Each app module registers its tools via `register_to_mcp(mcp: FastMCP)` function in its `__init__.py`, then gets imported and registered in `main.py`.

#### Security Architecture
- Filesystem operations require explicit directory permissions via configuration
- AppleScript execution goes through centralized secure runner with validation
- All user inputs are validated and sanitized
- Activity logging for sensitive operations

### Code Organization Rules
- **One endpoint per file**: Each API function gets its own module file
- **Logic separation**: Core business logic separate from MCP API layer (use `*_logic` functions)
- **No cross-app dependencies**: App modules are completely isolated
- **Consistent naming**: `<app>_<action>` for API functions, `<action>_logic` for core logic

### Testing Structure
- `tests/conftest.py`: Project-wide fixtures including AppleScript mocking
- `tests/apps/`: App-specific test suites organized by module
- `tests/utils/`: Custom assertions, mocks, helpers, and test data generators
- Tests automatically mock AppleScript execution and validate response formats

## Language Convention
All code, documentation, comments, and communication in this project must be in English. This ensures consistency and accessibility for all contributors.

## Workflow Requirements

### Mandatory Convention Checks
**ALWAYS** research project conventions before taking action. Use the Task tool to search for:

1. **Branch naming conventions** - Check `docs/development.md` and existing branches
   - Required pattern: `feature/<issue-number>-<description>`
   - Example: `feature/42-new-feature`

2. **Commit message conventions** - Check recent git history for patterns

3. **Code style conventions** - Check existing code in the same module

4. **Testing patterns** - Check existing tests in the relevant module

**Never assume standard practices. Always verify project-specific conventions first.**

## GitHub Tool Preference
If GitHub MCP tools are not available, do not attempt to use alternative commands like `gh` CLI or `git` for remote repository operations. Instead, inform the user that GitHub tools are not accessible.

## Security Considerations
This toolkit provides extensive system access to LLMs. Always validate inputs, use permission controls, and follow the established security patterns when adding new functionality.