"""CLI-specific test fixtures and configurations."""

import pytest
from unittest.mock import Mock
import tempfile
import json
import os


@pytest.fixture
def mock_filesystem_config():
    """Return sample filesystem configuration."""
    return {
        "allowed_dirs": [
            {
                "path": "/tmp/test",
                "permissions": ["read", "write", "list"]
            },
            {
                "path": "/home/user/documents",
                "permissions": ["read", "list"]
            }
        ],
        "security_log_dir": "/tmp/logs/security"
    }


@pytest.fixture
def mock_claude_desktop_config(mock_filesystem_config):
    """Return sample Claude Desktop configuration."""
    return {
        "mcpServers": {
            "localtoolkit": {
                "command": "localtoolkit",
                "args": [],
                "settings": {
                    "filesystem": mock_filesystem_config
                }
            }
        }
    }


@pytest.fixture
def temp_config_file(mock_filesystem_config):
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "settings": {
                "filesystem": mock_filesystem_config
            }
        }
        json.dump(config, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except:
        pass


@pytest.fixture
def temp_filesystem_config_file(mock_filesystem_config):
    """Create a temporary filesystem configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_filesystem_config, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except:
        pass


@pytest.fixture
def mock_fastmcp():
    """Create a mock FastMCP instance."""
    mock_mcp = Mock()
    mock_mcp.settings = Mock()
    mock_mcp.run = Mock()
    return mock_mcp