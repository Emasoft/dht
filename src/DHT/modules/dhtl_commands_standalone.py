#!/usr/bin/env python3
"""
Dhtl Commands Standalone module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_commands_standalone.sh
# - Implements node, python, run, and script commands
# - Uses guardian for resource management
# - Integrated with DHT command dispatcher
#

"""
DHT Standalone Commands Module.

Provides commands to run scripts and programs with resource management.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import Any

from .common_utils import get_venv_executable
from .dhtl_error_handling import log_error, log_info, log_warning
from .guardian_prefect import ResourceLimits, guardian_sequential_flow


def _normalize_args(args: Any, kwargs: Any) -> list[Any]:
    """Normalize arguments to handle both list and *args calling conventions.

    Args:
        args: Arguments passed to the command function
        kwargs: Keyword arguments passed to the command function

    Returns:
        list: Normalized list of arguments
    """
    if args is None:
        return []
    elif not isinstance(args, list):
        # If called with *args, convert to list
        return [args] + list(kwargs.get("args", []))
    return args


def python_command(args: Any = None, **kwargs: Any) -> int:
    """Run a Python script with resource management."""
    log_info("🐍 Running Python script with guardian protection...")

    args = _normalize_args(args, kwargs)

    if not args:
        log_error("No script provided")
        log_info("Usage: dhtl python <script> [args...]")
        return 1

    script = args[0]
    script_args = list(args[1:]) if len(args) > 1 else []

    # Check if script exists
    script_path = Path(script)
    if not script_path.exists():
        log_error(f"Script not found: {script}")
        return 1

    # Get Python executable
    python_exe = get_venv_executable("python")
    if not python_exe:
        log_error("Python not found")
        return 1

    # Build command
    command = f"{python_exe} {script}"
    if script_args:
        command += " " + " ".join(script_args)

    log_info(f"Script: {script}")
    if script_args:
        log_info(f"Arguments: {' '.join(script_args)}")

    # Run with guardian (default limits)
    limits = ResourceLimits(memory_mb=2048, cpu_percent=100, timeout=900)
    results = guardian_sequential_flow(commands=[command], stop_on_failure=True, default_limits=limits)

    if results and results[0]["returncode"] == 0:
        if results[0].get("stdout"):
            print(results[0]["stdout"])
        return 0
    else:
        if results and results[0].get("stderr"):
            print(results[0]["stderr"], file=sys.stderr)
        return 1


def node_command(args: Any = None, **kwargs: Any) -> int:
    """Run a Node.js script with resource management."""
    log_info("📦 Running Node.js script with guardian protection...")

    args = _normalize_args(args, kwargs)

    if not args:
        log_error("No script provided")
        log_info("Usage: dhtl node <script> [args...]")
        return 1

    script = args[0]
    script_args = list(args[1:]) if len(args) > 1 else []

    # Check if script exists
    script_path = Path(script)
    if not script_path.exists():
        log_error(f"Script not found: {script}")
        return 1

    # Check if node is available
    if not shutil.which("node"):
        log_error("Node.js is not installed")
        log_info("Install Node.js from https://nodejs.org/")
        return 1

    # Build command
    command = f"node {script}"
    if script_args:
        command += " " + " ".join(script_args)

    log_info(f"Script: {script}")
    if script_args:
        log_info(f"Arguments: {' '.join(script_args)}")

    # Run with guardian (default limits)
    limits = ResourceLimits(memory_mb=2048, cpu_percent=100, timeout=900)
    results = guardian_sequential_flow(commands=[command], stop_on_failure=True, default_limits=limits)

    if results and results[0]["returncode"] == 0:
        if results[0].get("stdout"):
            print(results[0]["stdout"])
        return 0
    else:
        if results and results[0].get("stderr"):
            print(results[0]["stderr"], file=sys.stderr)
        return 1


def run_command(args: Any = None, **kwargs: Any) -> int:
    """Run any command with resource management."""
    log_info("🚀 Running command with guardian protection...")

    args = _normalize_args(args, kwargs)

    if not args:
        log_error("No command provided")
        log_info("Usage: dhtl run <command> [args...]")
        return 1

    # Join all arguments as a single command
    command = " ".join(args)

    log_info(f"Command: {command}")

    # Run with guardian (default limits)
    limits = ResourceLimits(memory_mb=2048, cpu_percent=100, timeout=900)
    results = guardian_sequential_flow(commands=[command], stop_on_failure=True, default_limits=limits)

    if results and results[0]["returncode"] == 0:
        if results[0].get("stdout"):
            print(results[0]["stdout"])
        return 0
    else:
        if results and results[0].get("stderr"):
            print(results[0]["stderr"], file=sys.stderr)
        return 1


def script_command(args: Any = None, **kwargs: Any) -> int:
    """Run a shell script with resource management."""
    log_info("📜 Running shell script with guardian protection...")

    args = _normalize_args(args, kwargs)

    if not args:
        log_error("No script provided")
        log_info("Usage: dhtl script <script> [args...]")
        return 1

    script = args[0]
    script_args = list(args[1:]) if len(args) > 1 else []

    # Check if script exists
    script_path = Path(script)
    if not script_path.exists():
        log_error(f"Script not found: {script}")
        return 1

    # Make script executable if it isn't
    if not os.access(script_path, os.X_OK):
        log_info(f"Making script executable: {script}")
        script_path.chmod(script_path.stat().st_mode | 0o111)

    # Build command
    command = str(script_path.absolute())
    if script_args:
        command += " " + " ".join(script_args)

    log_info(f"Script: {script}")
    if script_args:
        log_info(f"Arguments: {' '.join(script_args)}")

    # Run with guardian (default limits)
    limits = ResourceLimits(memory_mb=2048, cpu_percent=100, timeout=900)
    results = guardian_sequential_flow(commands=[command], stop_on_failure=True, default_limits=limits)

    if results and results[0]["returncode"] == 0:
        if results[0].get("stdout"):
            print(results[0]["stdout"])
        return 0
    else:
        if results and results[0].get("stderr"):
            print(results[0]["stderr"], file=sys.stderr)
        return 1


# For backward compatibility
def placeholder_command(*args: Any, **kwargs: Any) -> int:
    """Placeholder command implementation."""
    log_warning("This is a placeholder command")
    return 0


# Export command functions
__all__ = ["python_command", "node_command", "run_command", "script_command", "placeholder_command"]
