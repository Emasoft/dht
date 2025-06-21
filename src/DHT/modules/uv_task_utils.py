#!/usr/bin/env python3
"""
uv_task_utils.py - Utility functions for UV Prefect tasks

This module contains utility functions used by UV Prefect tasks.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from uv_prefect_tasks.py to reduce file size
# - Contains utility functions for UV executable discovery and logging
#

from __future__ import annotations

import shutil
from functools import lru_cache
from pathlib import Path

from prefect import get_run_logger


def get_logger():
    """Get logger with fallback for testing."""
    try:
        return get_run_logger()
    except Exception:
        # Fallback for testing
        import logging

        return logging.getLogger(__name__)


@lru_cache(maxsize=1)
def find_uv_executable() -> Path | None:
    """
    Find UV executable in PATH or common locations.

    Returns:
        Path to UV executable or None if not found
    """
    # First check if UV is in PATH
    uv_in_path = shutil.which("uv")
    if uv_in_path:
        return Path(uv_in_path)

    # Check common installation locations
    common_paths = [
        Path.home() / ".local" / "bin" / "uv",
        Path.home() / ".cargo" / "bin" / "uv",
        Path("/usr/local/bin/uv"),
        Path("/opt/homebrew/bin/uv"),
    ]

    for path in common_paths:
        if path.exists() and path.is_file():
            return path

    return None


def extract_min_python_version(constraint: str) -> str:
    """
    Extract minimum Python version from a constraint string.

    Args:
        constraint: Version constraint like ">=3.8,<4.0" or "^3.8"

    Returns:
        Minimum version string like "3.8"
    """
    constraint = constraint.strip()

    # Handle "python" prefix (e.g., "python>=3.10")
    if constraint.startswith("python"):
        constraint = constraint[6:].strip()

    # Handle caret notation (^3.8 means >=3.8,<4.0)
    if constraint.startswith("^"):
        return constraint[1:].split(",")[0].strip()

    # Handle tilde notation (~3.8 means >=3.8,<3.9)
    if constraint.startswith("~"):
        return constraint[1:].split(",")[0].strip()

    # Handle >= notation
    if constraint.startswith(">="):
        return constraint[2:].split(",")[0].strip()

    # Handle exact version
    if constraint[0].isdigit():
        return constraint.split(",")[0].strip()

    # Default to 3.8 if we can't parse
    return "3.8"
