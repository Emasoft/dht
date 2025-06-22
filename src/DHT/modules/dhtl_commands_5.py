#!/usr/bin/env python3
"""
Dhtl Commands 5 module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_commands_5.sh
# - Implements coverage command functionality
# - Integrated with DHT command dispatcher
# - Uses pytest-cov for coverage reporting
#

"""
DHT Coverage Commands Module.

Provides code coverage functionality for Python projects.
"""

import os
import shutil

from .common_utils import find_project_root, find_virtual_env
from .dhtl_error_handling import log_error, log_info, log_success, log_warning
from .dhtl_guardian_utils import run_with_guardian


def coverage_command(*args, **kwargs) -> int:
    """Run code coverage analysis."""
    log_info("📊 Running code coverage analysis...")

    # Find project root
    project_root = find_project_root()

    # Find virtual environment
    venv_dir = find_virtual_env(project_root)
    if not venv_dir:
        venv_dir = project_root / ".venv"

    # Check for pytest-cov
    pytest_cmd = None
    if venv_dir and (venv_dir / "bin" / "pytest").exists():
        pytest_cmd = str(venv_dir / "bin" / "pytest")
    elif venv_dir and (venv_dir / "Scripts" / "pytest.exe").exists():
        pytest_cmd = str(venv_dir / "Scripts" / "pytest.exe")
    elif shutil.which("pytest"):
        pytest_cmd = "pytest"
        log_warning("Using global pytest")

    if not pytest_cmd:
        log_error("pytest is not installed")
        log_info("Install pytest and pytest-cov: uv pip install pytest pytest-cov")
        return 1

    # Build coverage command
    coverage_cmd = [pytest_cmd, "--cov=.", "--cov-report=term-missing", "--cov-report=html", "--cov-report=xml", "-v"]

    # Add any extra arguments
    if args:
        coverage_cmd.extend(args)

    # Get memory limit
    mem_limit = int(os.environ.get("PYTHON_MEM_LIMIT", "2048"))

    # Run with guardian
    log_info("Running pytest with coverage...")
    exit_code = run_with_guardian(coverage_cmd[0], "pytest-coverage", mem_limit, *coverage_cmd[1:])

    if exit_code == 0:
        log_success("Coverage analysis completed successfully!")

        # Show coverage report location
        htmlcov_dir = project_root / "htmlcov"
        if htmlcov_dir.exists():
            log_info(f"HTML coverage report: {htmlcov_dir / 'index.html'}")

        coverage_xml = project_root / "coverage.xml"
        if coverage_xml.exists():
            log_info(f"XML coverage report: {coverage_xml}")
    else:
        log_error(f"Coverage analysis failed with exit code {exit_code}")

    return exit_code


# For backward compatibility
def placeholder_command(*args, **kwargs) -> int:
    """Placeholder command implementation."""
    return coverage_command(*args, **kwargs)


# Export command functions
__all__ = ["coverage_command", "placeholder_command"]
