"""Process-specific test fixtures and configurations."""

import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def mock_process_list_data():
    """Return sample process list data for testing."""
    return [
        "Safari:::1234",
        "Chrome:::5678",
        "Python:::9012",
        "Code:::3456",
        "Terminal:::7890"
    ]


@pytest.fixture
def mock_ps_output():
    """Return sample ps command output for testing."""
    return """  PID  PPID USER      %CPU %MEM STARTED                 COMMAND
 1234     1 user       5.2  2.3 Mon Jan 15 10:00:00 2024 /Applications/Safari.app/Contents/MacOS/Safari
 5678     1 user      10.5  4.1 Mon Jan 15 10:00:00 2024 /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
 9012     1 user       0.5  0.8 Mon Jan 15 10:00:00 2024 /usr/local/bin/python3"""


@pytest.fixture
def mock_process_info():
    """Return sample process info for testing."""
    return {
        "pid": 1234,
        "ppid": 1,
        "user": "user",
        "cpu_percent": 5.2,
        "memory_percent": 2.3,
        "start_time": "Mon Jan 15 10:00:00 2024",
        "command": "/Applications/Safari.app/Contents/MacOS/Safari",
        "name": "Safari"
    }


@pytest.fixture
def mock_vm_stat_output():
    """Return sample vm_stat output for testing."""
    return """Mach Virtual Memory Statistics: (page size of 4096 bytes)
Pages free:                               123456.
Pages active:                             654321.
Pages inactive:                           234567.
Pages speculative:                         12345.
Pages throttled:                               0.
Pages wired down:                         345678.
Pages purgeable:                           23456.
"Translation faults":                   87654321.
Pages copy-on-write:                     1234567.
Pages zero filled:                      12345678.
Pages reactivated:                        123456.
Pages purged:                              12345.
File-backed pages:                        234567.
Anonymous pages:                          345678.
Pages stored in compressor:               456789.
Pages occupied by compressor:              56789.
Decompressions:                           123456.
Compressions:                             234567.
Pageins:                                  345678.
Pageouts:                                  12345.
Swapins:                                       0.
Swapouts:                                      0."""


@pytest.fixture
def mock_lsof_output():
    """Return sample lsof output for testing."""
    return """COMMAND   PID USER   FD   TYPE DEVICE  SIZE/OFF     NODE NAME
Safari  1234 user  cwd    DIR    1,4       768        2 /
Safari  1234 user  txt    REG    1,4   5632928 12345678 /Applications/Safari.app/Contents/MacOS/Safari
Safari  1234 user    0u   CHR   16,2   0t26781      668 /dev/ttys002
Safari  1234 user    1u   CHR   16,2   0t26781      668 /dev/ttys002
Safari  1234 user    2u   CHR   16,2   0t26781      668 /dev/ttys002"""


@pytest.fixture
def mock_monitor_metrics():
    """Return sample monitoring metrics for testing."""
    return [
        {
            "timestamp": 1705315200.0,
            "elapsed_seconds": 0.0,
            "cpu_percent": 5.0,
            "memory_percent": 2.3,
            "rss_kb": 98304,
            "vsz_kb": 4194304
        },
        {
            "timestamp": 1705315201.0,
            "elapsed_seconds": 1.0,
            "cpu_percent": 5.5,
            "memory_percent": 2.4,
            "rss_kb": 99328,
            "vsz_kb": 4194304
        },
        {
            "timestamp": 1705315202.0,
            "elapsed_seconds": 2.0,
            "cpu_percent": 4.8,
            "memory_percent": 2.3,
            "rss_kb": 98816,
            "vsz_kb": 4194304
        }
    ]


@pytest.fixture
def mock_applescript():
    """Mock AppleScript executor for process tests."""
    with patch('localtoolkit.applescript.utils.applescript_runner.applescript_execute') as mock:
        mock.return_value = {
            "success": True,
            "data": ["Safari:::1234", "Chrome:::5678", "Python:::9012"],
            "metadata": {},
            "error": None
        }
        yield mock