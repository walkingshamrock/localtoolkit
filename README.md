# LocalToolKit

LocalToolKit (LTK) provides a structured API for accessing macOS applications like Messages, Contacts, and Mail. This project follows Anthropic's Model Context Protocol standard, making it easy to integrate macOS capabilities with AI assistants.

## Important Risk Disclosure

LocalToolKit is designed to provide extensive flexibility for LLMs to interact with your macOS system, which comes with inherent risks:

- The project allows LLMs to access and potentially modify system data, files, and applications
- This level of access could potentially harm your Mac if misused or if exploited
- While security measures are implemented, no system is completely risk-free

By using LocalToolKit, you acknowledge these risks and understand that you're granting significant system access to AI systems. This project is intended to enhance the capabilities of LLMs to improve our lives, but should be used with appropriate caution and oversight.

We strongly recommend:

- Only using LocalToolKit with trusted LLM providers
- Regularly monitoring the activities performed through this interface
- Being selective about which permissions you grant to the application
- Running LocalToolKit with the minimum necessary privileges

## Features

- **AppleScript Integration**: Execute AppleScript safely with proper validation and error handling
- **Direct Database Access**: SQLite-based message retrieval for enhanced performance and features
- **Process Management**:
  - List running processes with filtering by name, CPU, or memory usage
  - Start applications and processes with customizable parameters
  - Monitor process resource usage over time
  - Get detailed information about specific processes
  - Terminate processes safely with optional forced termination
- **Messages App Access**:
  - List available conversations with metadata
  - Retrieve detailed message history with rich media support
  - Extract URLs from link previews
  - Identify and classify various message types (text, images, videos, links, etc.)
  - Access attachment metadata and file paths
- **Contacts App Access**:
  - Search contacts by name (first name, last name, or full name)
  - Search contacts by phone number (exact or partial matching)
  - Retrieve rich contact information (phone numbers, email addresses, physical addresses, etc.)
- **Extensible Design**: Clear architecture for adding support for additional apps and features

## Requirements

- macOS 11.0+
- Python 3.10+
- Required packages (can be installed via requirements.txt):
  ```bash
  pip install -r requirements.txt
  ```

### Dependencies

- `mcp-server`: The core MCP server implementation
- `mcpo`: OpenAPI wrapper for MCP servers (optional, for HTTP interface)

## Getting Started

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/walkingshamrock/localtoolkit.git
   cd localtoolkit
   ```

2. Install in development mode:

   ```bash
   pip install -e ".[dev]"
   ```

   This will install the package with development dependencies.

### Structure

LocalToolkit follows a modern Python package structure:

```
localtoolkit/
├── src/
│   └── localtoolkit/       # Main package code
│       ├── applescript/    # AppleScript integration
│       ├── contacts/       # Contact management
│       ├── filesystem/     # File operations
│       ├── mail/           # Mail application integration
│       ├── messages/       # Messages app access
│       ├── process/        # Process management
│       └── reminders/      # Reminders app access
├── tests/                  # Test suite
├── docs/                   # Documentation
└── pyproject.toml          # Project configuration
```

## License

MIT License - See [LICENSE](LICENSE) file for details.

This software is provided "as is", without warranty of any kind, express or implied.  
In no event shall the author be liable for any claim, damages or other liability arising from the use or misuse of this software.
