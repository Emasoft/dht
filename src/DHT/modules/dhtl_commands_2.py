#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_commands_2.sh
# - Implements test command functionality
# - Integrated with DHT command dispatcher
#

"""
DHT Test Commands Module.

Provides test command functionality for running project tests.
"""

import os
import shutil
import sys

from .common_utils import find_project_root, find_virtual_env
from .dhtl_error_handling import log_error, log_info, log_success, log_warning
from .dhtl_guardian_utils import run_with_guardian


def test_command(*args, **kwargs) -> int:
    """Run project tests."""
    log_info("🧪 Running project tests...")

    # Find project root
    project_root = find_project_root()

    # Find virtual environment
    venv_dir = find_virtual_env(project_root)
    if not venv_dir:
        venv_dir = project_root / ".venv"

    # Determine test runner
    test_runner = None
    test_cmd = []

    # Check for pytest
    if venv_dir and (venv_dir / "bin" / "pytest").exists():
        test_runner = "pytest"
        test_cmd = [str(venv_dir / "bin" / "pytest")]
    elif venv_dir and (venv_dir / "Scripts" / "pytest.exe").exists():
        test_runner = "pytest"
        test_cmd = [str(venv_dir / "Scripts" / "pytest.exe")]
    elif shutil.which("pytest"):
        test_runner = "pytest"
        test_cmd = ["pytest"]
        log_warning("Using global pytest")

    # Check for unittest as fallback
    elif sys.executable:
        test_runner = "unittest"
        test_cmd = [sys.executable, "-m", "unittest", "discover"]

    if not test_runner:
        log_error("No test runner found (pytest or unittest)")
        log_info("Install pytest: uv pip install pytest")
        return 1

    # Run tests
    log_info(f"Using {test_runner} to run tests...")

    # Get memory limit
    mem_limit = int(os.environ.get("PYTHON_MEM_LIMIT", "2048"))

    # Run with guardian
    exit_code = run_with_guardian(
        test_cmd[0],
        "pytest",
        mem_limit,
        *test_cmd[1:]
    )

    if exit_code == 0:
        log_success("All tests passed!")
    else:
        log_error(f"Tests failed with exit code {exit_code}")

    return exit_code


# For backward compatibility
def placeholder_command(*args, **kwargs) -> int:
    """Placeholder command implementation."""
    return test_command(*args, **kwargs)


# Export command functions
__all__ = ['test_command', 'placeholder_command']
