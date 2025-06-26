#!/usr/bin/env python3
from __future__ import annotations

"""
uv_manager_python.py - Python version management for UV Manager  This module contains Python version detection and management functionality.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
uv_manager_python.py - Python version management for UV Manager

This module contains Python version detection and management functionality.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from uv_manager.py to reduce file size
# - Contains Python version detection, listing, and installation
#


import logging
from pathlib import Path
from typing import Any, cast

from prefect import task

from DHT.modules.uv_manager_exceptions import PythonVersionError
from DHT.modules.uv_manager_utils import extract_min_version, load_toml


class PythonVersionManager:
    """Manages Python version operations for UV."""

    def __init__(self, run_command_func: Any) -> None:
        """
        Initialize Python version manager.

        Args:
            run_command_func: Function to run UV commands
        """
        self.logger = logging.getLogger(__name__)
        self.run_command = run_command_func

    def detect_python_version(self, project_path: Path) -> str | None:
        """
        Detect required Python version for a project.

        Checks in order:
        1. .python-version file
        2. pyproject.toml requires-python
        3. setup.py python_requires
        4. Runtime detection from imports

        Returns:
            Python version string (e.g., "3.11", "3.11.6") or None
        """
        project_path = Path(project_path)

        # Check .python-version file
        python_version_file = project_path / ".python-version"
        if python_version_file.exists():
            version = python_version_file.read_text().strip()
            self.logger.info(f"Found Python version in .python-version: {version}")
            return version

        # Check pyproject.toml
        pyproject_file = project_path / "pyproject.toml"
        if pyproject_file.exists():
            try:
                data = load_toml(pyproject_file)

                requires_python = data.get("project", {}).get("requires-python")
                if requires_python:
                    # Convert constraint to specific version
                    # For now, extract minimum version
                    version = extract_min_version(requires_python)
                    self.logger.info(f"Found Python requirement in pyproject.toml: {version}")
                    return cast(str, version)
            except Exception as e:
                self.logger.warning(f"Failed to parse pyproject.toml: {e}")

        # Check setup.py
        setup_py = project_path / "setup.py"
        if setup_py.exists():
            # This is trickier - would need AST parsing
            # For now, return None and let user specify
            self.logger.debug("setup.py found but not parsing (would need AST analysis)")

        return None

    @task
    def list_python_versions(self) -> list[dict[str, Any]]:
        """List all available Python versions (installed and downloadable)."""
        result = self.run_command(["python", "list", "--all-versions"])

        if not result["success"]:
            self.logger.error(f"Failed to list Python versions: {result['stderr']}")
            return []

        versions = []
        for line in result["stdout"].strip().split("\n"):
            if line.strip():
                # Parse version info from UV output
                parts = line.strip().split()
                if parts:
                    version_info = {
                        "version": parts[0],
                        "installed": "(installed)" in line,
                        "path": parts[-1] if "(installed)" in line else None,
                    }
                    versions.append(version_info)

        return versions

    @task
    def ensure_python_version(self, version: str) -> Path:
        """
        Ensure specific Python version is available, installing if needed.

        Args:
            version: Python version to ensure (e.g., "3.11", "3.11.6")

        Returns:
            Path to Python executable
        """
        # First check if already installed
        result = self.run_command(["python", "find", version])

        if result["success"] and result["stdout"].strip():
            python_path = Path(result["stdout"].strip())
            self.logger.info(f"Python {version} already available at {python_path}")
            return python_path

        # Not installed, try to install
        self.logger.info(f"Python {version} not found, attempting to install...")

        install_result = self.run_command(["python", "install", version])

        if not install_result["success"]:
            raise PythonVersionError(f"Failed to install Python {version}: {install_result['stderr']}")

        # Find the newly installed Python
        find_result = self.run_command(["python", "find", version])

        if find_result["success"] and find_result["stdout"].strip():
            python_path = Path(find_result["stdout"].strip())
            self.logger.info(f"Successfully installed Python {version} at {python_path}")
            return python_path
        else:
            raise PythonVersionError(f"Python {version} was installed but cannot be found")
