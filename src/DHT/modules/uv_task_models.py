#!/usr/bin/env python3
"""
uv_task_models.py - Data models and constants for UV Prefect tasks  This module contains data models, constants, and configurations used by UV Prefect tasks.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
uv_task_models.py - Data models and constants for UV Prefect tasks

This module contains data models, constants, and configurations used by
UV Prefect tasks.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from uv_prefect_tasks.py to reduce file size
# - Contains task configuration defaults, memory limits, and exception classes
#

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Task configuration defaults
DEFAULT_TIMEOUT = 300  # 5 minutes
INSTALL_TIMEOUT = 600  # 10 minutes for installations
BUILD_TIMEOUT = 900  # 15 minutes for builds

# Memory limits for different operations
UV_MEMORY_LIMITS = {
    "version_check": 256,  # MB
    "list_versions": 512,  # MB
    "create_venv": 1024,  # MB
    "install_deps": 2048,  # MB
    "build_project": 4096,  # MB
}

# Retry configurations
RETRY_DELAYS = [1, 2, 5]  # Exponential backoff in seconds


class UVTaskError(Exception):
    """Base exception for UV task errors."""

    pass


@dataclass
class UVVersionInfo:
    """UV version information."""

    version: str
    path: str
    is_available: bool
    error: str | None = None


@dataclass
class PythonVersionInfo:
    """Python version information."""

    version: str
    path: str | None = None
    is_default: bool = False
    is_managed: bool = False
    source: str | None = None


@dataclass
class DependencyResult:
    """Result from dependency operations."""

    success: bool
    package: str
    version: str | None = None
    error: str | None = None
    stdout: str | None = None
    stderr: str | None = None


@dataclass
class BuildResult:
    """Result from build operations."""

    success: bool
    output_dir: Path | None = None
    artifacts: list[str] = field(default_factory=list)
    error: str | None = None
    stdout: str | None = None
    stderr: str | None = None


@dataclass
class ScriptResult:
    """Result from script execution."""

    success: bool
    return_code: int
    stdout: str
    stderr: str
    error: str | None = None
    execution_time: float | None = None
