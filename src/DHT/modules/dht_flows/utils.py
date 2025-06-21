#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial creation of utils module for DHT flows
# - Common utility functions to avoid code duplication
#

"""
Utility functions for DHT Prefect flows.

This module contains common utility functions used across different flows
to avoid code duplication and improve maintainability.
"""

import shlex
import sys
from pathlib import Path
from typing import Any


def get_venv_executable_path(venv_path: Path, executable: str) -> Path:
    """
    Get executable path for virtual environment.

    Handles platform differences between Windows and Unix-like systems.

    Args:
        venv_path: Path to virtual environment
        executable: Executable name (e.g., 'python', 'pip', 'pytest')

    Returns:
        Path to the executable

    Raises:
        FileNotFoundError: If executable not found in virtual environment
    """
    if sys.platform == "win32":
        exe_path = venv_path / "Scripts" / f"{executable}.exe"
        alt_path = venv_path / "Scripts" / f"{executable}3.exe"
    else:
        exe_path = venv_path / "bin" / executable
        alt_path = venv_path / "bin" / f"{executable}3"

    # Try primary path first, then alternative
    if exe_path.exists():
        return exe_path
    elif alt_path.exists():
        return alt_path
    else:
        raise FileNotFoundError(f"{executable} executable not found in virtual environment: {venv_path}")


def get_venv_python_path(venv_path: Path) -> Path:
    """
    Get Python executable path for virtual environment.

    Handles platform differences between Windows and Unix-like systems.

    Args:
        venv_path: Path to virtual environment

    Returns:
        Path to Python executable

    Raises:
        FileNotFoundError: If Python executable not found in virtual environment
    """
    return get_venv_executable_path(venv_path, "python")


def get_venv_pip_path(venv_path: Path) -> Path:
    """
    Get pip executable path for virtual environment.

    Args:
        venv_path: Path to virtual environment

    Returns:
        Path to pip executable

    Raises:
        FileNotFoundError: If pip not found in virtual environment
    """
    return get_venv_executable_path(venv_path, "pip")


def safe_command_join(command_parts: list[str]) -> str:
    """
    Safely join command parts into a shell command string.

    Uses shlex.quote to properly escape each part.

    Args:
        command_parts: List of command parts

    Returns:
        Safely escaped command string
    """
    return " ".join(shlex.quote(part) for part in command_parts)


def normalize_path_for_platform(path: Path) -> str:
    """
    Normalize path for cross-platform compatibility.

    Args:
        path: Path to normalize

    Returns:
        Platform-appropriate path string
    """
    if sys.platform == "win32":
        return str(path).replace("/", "\\")
    else:
        return path.as_posix()


def get_default_resource_limits() -> dict[str, Any]:
    """
    Get default resource limits for DHT operations.

    These can be overridden by environment variables or configuration.

    Returns:
        Dictionary with default resource limits
    """
    import os

    return {
        "memory_limit_mb": int(os.environ.get("DHT_MEMORY_LIMIT_MB", "2048")),
        "timeout_seconds": int(os.environ.get("DHT_TIMEOUT_SECONDS", "900")),
        "cpu_limit_percent": int(os.environ.get("DHT_CPU_LIMIT_PERCENT", "100")),
    }


def validate_project_path(path: Path) -> Path:
    """
    Validate and resolve project path.

    Prevents directory traversal attacks and ensures path exists.

    Args:
        path: Path to validate

    Returns:
        Resolved absolute path

    Raises:
        ValueError: If path is invalid or contains suspicious patterns
        FileNotFoundError: If path doesn't exist
    """
    # Resolve to absolute path
    abs_path = path.resolve()

    # Check for suspicious patterns
    path_str = str(abs_path)
    suspicious_patterns = ["/..", "\\.."]
    for pattern in suspicious_patterns:
        if pattern in path_str:
            raise ValueError(f"Suspicious path pattern detected: {path}")

    # Ensure path exists
    if not abs_path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    return abs_path
