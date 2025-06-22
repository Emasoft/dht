#!/usr/bin/env python3
"""
Constants and configuration for Process Guardian  This module defines all constants and configuration settings used by the Process Guardian system, including: - Default timeout values - Memory limits - Process type configurations - Critical process definitions

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
Constants and configuration for Process Guardian

This module defines all constants and configuration settings used by the
Process Guardian system, including:
- Default timeout values
- Memory limits
- Process type configurations
- Critical process definitions
- Directory and file paths
- Platform-specific settings
"""

import os
import platform
from typing import Any

import psutil

# Platform detection
SYSTEM = platform.system().lower()
IS_WINDOWS = SYSTEM == "windows"
IS_MACOS = SYSTEM == "darwin"
IS_LINUX = SYSTEM == "linux"
IS_UNIX = not IS_WINDOWS

# Try to import psutil for resource detection, fall back to defaults if not available
HAS_PSUTIL = False
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    pass

# Process monitoring settings
DEFAULT_TIMEOUT_SECONDS = 900  # 15 minutes
CHECK_INTERVAL_SECONDS = 5  # Check processes every 5 seconds
HEARTBEAT_TIMEOUT = 60  # Time between heartbeat checks

# Directory structure
GUARDIAN_STATE_DIR = os.path.expanduser("~/.process_guardian")
PROCESS_STATE_FILE = os.path.join(GUARDIAN_STATE_DIR, "monitored_processes.json")
PROCESS_LOG_FILE = os.path.join(GUARDIAN_STATE_DIR, "process_guardian.log")
HEARTBEAT_FILE = os.path.join(GUARDIAN_STATE_DIR, "heartbeat.json")

# Queue settings
MAX_PROCESS_QUEUE_SIZE = 50  # Maximum processes in queue

# Initialize global variables with default values
DEFAULT_MAX_MEMORY_MB = 1024  # 1 GB per process
MAX_TOTAL_MEMORY_MB = 3072  # 3 GB total (3 processes at 1 GB each)
MAX_CONCURRENT_PROCESSES = 3  # Allow 3 concurrent processes by default


# Calculate system resources based on available memory
def calculate_system_resources() -> None:
    """Calculate system resources and set appropriate limits."""
    global MAX_TOTAL_MEMORY_MB, DEFAULT_MAX_MEMORY_MB, MAX_CONCURRENT_PROCESSES, HAS_PSUTIL

    # Only calculate if psutil is available
    if not HAS_PSUTIL:
        return

    try:
        # Get system memory
        mem = psutil.virtual_memory()
        total_memory_mb = mem.total / (1024 * 1024)

        # Calculate values based on system memory
        if total_memory_mb >= 16384:  # >= 16 GB
            MAX_TOTAL_MEMORY_MB = 8192  # 8 GB
            DEFAULT_MAX_MEMORY_MB = 2048  # 2 GB per process
            MAX_CONCURRENT_PROCESSES = 4
        elif total_memory_mb >= 8192:  # >= 8 GB
            MAX_TOTAL_MEMORY_MB = 4096  # 4 GB
            DEFAULT_MAX_MEMORY_MB = 1024  # 1 GB per process
            MAX_CONCURRENT_PROCESSES = 4
        elif total_memory_mb >= 4096:  # >= 4 GB
            MAX_TOTAL_MEMORY_MB = 2048  # 2 GB
            DEFAULT_MAX_MEMORY_MB = 768  # 768 MB per process
            MAX_CONCURRENT_PROCESSES = 3
        else:  # < 4 GB (limited memory)
            MAX_TOTAL_MEMORY_MB = 1024  # 1 GB
            DEFAULT_MAX_MEMORY_MB = 512  # 512 MB per process
            MAX_CONCURRENT_PROCESSES = 2

        # Further restrict concurrent processes on limited systems
        cpu_count = os.cpu_count() or 2
        if cpu_count <= 2:
            MAX_CONCURRENT_PROCESSES = 1  # Single process only on limited CPU
            MAX_TOTAL_MEMORY_MB = min(MAX_TOTAL_MEMORY_MB, 1536)  # 1.5 GB max

        # Platform-specific adjustments
        if IS_WINDOWS:
            # Windows has more overhead, restrict more aggressively
            MAX_CONCURRENT_PROCESSES = max(1, MAX_CONCURRENT_PROCESSES - 1)
            MAX_TOTAL_MEMORY_MB = int(MAX_TOTAL_MEMORY_MB * 0.85)  # 85% of calculated value

    except Exception:
        # Fall back to conservative defaults if calculation fails
        DEFAULT_MAX_MEMORY_MB = 1024  # 1 GB per process
        MAX_TOTAL_MEMORY_MB = 3072  # 3 GB total
        MAX_CONCURRENT_PROCESSES = 3  # 3 concurrent processes


# Calculate system resources on module import
calculate_system_resources()

# Special process type configurations - stricter limits for memory-intensive processes
PROCESS_TYPES = {
    # Node.js processes - typically memory hungry
    "node": {
        "max_memory_mb": 768,
        "max_concurrent": 2,
        "priority": 0,  # Lower priority (will be queued first)
    },
    # npm has stricter memory limits
    "npm": {"max_memory_mb": 768, "max_concurrent": 1, "priority": 0},
    # V8 process (used by Node.js)
    "v8": {"max_memory_mb": 768, "max_concurrent": 2, "priority": 0},
    # Python processes - typically well-behaved
    "python": {
        "max_memory_mb": DEFAULT_MAX_MEMORY_MB,
        "max_concurrent": MAX_CONCURRENT_PROCESSES,
        "priority": 5,  # Medium priority
    },
    # Critical build tools - high priority
    "build": {
        "max_memory_mb": DEFAULT_MAX_MEMORY_MB,
        "max_concurrent": 1,
        "priority": 10,  # High priority
    },
}

# Critical processes that require special monitoring
CRITICAL_PROCESSES = [
    # Build tools
    "bump-my-version",
    "pre-commit",
    # Test tools
    "pytest",
    "tox",
    # Package management
    "uv",
    "pip",
    "npm",
    # Code quality
    "coverage",
    "black",
    "flake8",
    "ruff",
    "mypy",
    "isort",
]

# Resource management flags
STRICT_SEQUENTIAL_EXECUTION = MAX_CONCURRENT_PROCESSES <= 1
RESOURCE_LIMITED_SYSTEM = DEFAULT_MAX_MEMORY_MB <= 512 or MAX_CONCURRENT_PROCESSES <= 1

# Fallback error messages
ERROR_MESSAGES = {
    "no_psutil": "psutil not available. Process monitoring will be limited.",
    "invalid_pid": "Invalid process ID.",
    "process_not_found": "Process not found or no longer exists.",
    "access_denied": "Access denied when accessing process.",
    "memory_exceeded": "Process exceeded memory limit.",
    "timeout_exceeded": "Process exceeded timeout limit.",
    "duplicate_process": "Duplicate process detected.",
    "queue_full": "Process queue is full.",
    "unknown_error": "Unknown error occurred.",
}


# Detection functions
def detect_environment() -> dict[str, Any]:
    """Detect and return environment information"""
    env_info = {
        "system": SYSTEM,
        "is_windows": IS_WINDOWS,
        "is_macos": IS_MACOS,
        "is_linux": IS_LINUX,
        "is_unix": IS_UNIX,
        "has_psutil": HAS_PSUTIL,
        "max_memory_mb": DEFAULT_MAX_MEMORY_MB,
        "max_total_memory_mb": MAX_TOTAL_MEMORY_MB,
        "max_concurrent_processes": MAX_CONCURRENT_PROCESSES,
        "strict_sequential": STRICT_SEQUENTIAL_EXECUTION,
        "resource_limited": RESOURCE_LIMITED_SYSTEM,
    }

    # Add CPU and memory info if psutil is available
    if HAS_PSUTIL:
        try:
            env_info["cpu_count"] = psutil.cpu_count()
            mem = psutil.virtual_memory()
            env_info["total_memory_mb"] = mem.total / (1024 * 1024)
            env_info["available_memory_mb"] = mem.available / (1024 * 1024)
        except Exception:
            pass

    return env_info


# Usage examples for documentation
USAGE_EXAMPLES = """
Usage examples:

Direct usage:
    python -m helpers.shell.process_guardian --monitor "bump-my-version" --timeout 900 --max-memory 2048 -- command [args]

As a context manager in Python scripts:
    with ProcessGuardian(process_name="bump-my-version", timeout=900, max_memory_mb=2048):
        subprocess.run(["command", "arg1", "arg2"])

As a CLI tool:
    python -m helpers.shell.process_guardian --list  # List monitored processes
    python -m helpers.shell.process_guardian --kill-all  # Kill all monitored processes
"""

# Print resource allocation on import if in debug mode
if os.environ.get("DEBUG_PROCESS_GUARDIAN") == "1":
    print(
        f"✅ System resources calculated: {MAX_TOTAL_MEMORY_MB}MB total memory, "
        f"{DEFAULT_MAX_MEMORY_MB}MB default per process, "
        f"{'strictly sequential execution' if STRICT_SEQUENTIAL_EXECUTION else f'max {MAX_CONCURRENT_PROCESSES} concurrent processes'}"
    )
