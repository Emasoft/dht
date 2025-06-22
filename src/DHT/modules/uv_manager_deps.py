#!/usr/bin/env python3
"""
uv_manager_deps.py - Dependency management for UV Manager  This module contains dependency installation, management, and lock file operations.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
uv_manager_deps.py - Dependency management for UV Manager

This module contains dependency installation, management, and lock file operations.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from uv_manager.py to reduce file size
# - Contains dependency installation, sync, add/remove, and lock file operations
#

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from prefect import task

from DHT.modules.uv_manager_exceptions import DependencyError
from DHT.modules.uv_manager_utils import load_toml


class DependencyManager:
    """Manages dependency operations for UV."""

    def __init__(self, run_command_func):
        """
        Initialize dependency manager.

        Args:
            run_command_func: Function to run UV commands
        """
        self.logger = logging.getLogger(__name__)
        self.run_command = run_command_func

    def install_dependencies(
        self,
        project_path: Path,
        requirements_file: Path | None = None,
        dev: bool = False,
        extras: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Install project dependencies.

        Args:
            project_path: Project root directory
            requirements_file: Specific requirements file to use
            dev: Whether to install development dependencies
            extras: List of extras to install

        Returns:
            Installation result information
        """
        project_path = Path(project_path)

        # Check if project has uv.lock
        lock_file = project_path / "uv.lock"
        if lock_file.exists():
            # Use uv sync for lock file
            return self._sync_dependencies(project_path, dev=dev, extras=extras)

        # Otherwise use pip install
        if requirements_file:
            return self._pip_install_requirements(project_path, requirements_file)

        # Look for pyproject.toml
        pyproject = project_path / "pyproject.toml"
        if pyproject.exists():
            return self._pip_install_project(project_path, dev=dev, extras=extras)

        # Look for requirements.txt
        requirements_txt = project_path / "requirements.txt"
        if requirements_txt.exists():
            return self._pip_install_requirements(project_path, requirements_txt)

        self.logger.warning("No dependencies found to install")
        return {"success": True, "message": "No dependencies found"}

    def _sync_dependencies(
        self, project_path: Path, dev: bool = False, extras: list[str] | None = None
    ) -> dict[str, Any]:
        """Sync dependencies from uv.lock file."""
        args = ["sync"]

        if dev:
            args.append("--dev")

        if extras:
            for extra in extras:
                args.extend(["--extra", extra])

        result = self.run_command(args, cwd=project_path)

        return {
            "success": result["success"],
            "method": "uv sync",
            "message": result["stdout"] if result["success"] else result["stderr"],
        }

    def _pip_install_requirements(self, project_path: Path, requirements_file: Path) -> dict[str, Any]:
        """Install from requirements file using uv pip."""
        args = ["pip", "install", "-r", str(requirements_file)]

        result = self.run_command(args, cwd=project_path)

        return {
            "success": result["success"],
            "method": "uv pip install -r",
            "requirements_file": str(requirements_file),
            "message": result["stdout"] if result["success"] else result["stderr"],
        }

    def _pip_install_project(
        self, project_path: Path, dev: bool = False, extras: list[str] | None = None
    ) -> dict[str, Any]:
        """Install project with optional extras."""
        # Install the project itself
        install_spec = "."

        if extras:
            extras_str = ",".join(extras)
            install_spec = f".[{extras_str}]"

        args = ["pip", "install", "-e", install_spec]

        result = self.run_command(args, cwd=project_path)

        if not result["success"]:
            return {"success": False, "method": "uv pip install -e", "message": result["stderr"]}

        # Install dev dependencies if requested
        if dev:
            # Check for dev dependencies in pyproject.toml
            try:
                pyproject = project_path / "pyproject.toml"
                data = load_toml(pyproject)

                # Check for dev dependencies in various locations
                dev_deps = (
                    data.get("project", {}).get("optional-dependencies", {}).get("dev", [])
                    or data.get("dependency-groups", {}).get("dev", [])
                    or data.get("tool", {}).get("pdm", {}).get("dev-dependencies", {})
                )

                if dev_deps:
                    # Try installing as extra first
                    dev_result = self.run_command(["pip", "install", "-e", ".[dev]"], cwd=project_path, check=False)

                    if not dev_result["success"]:
                        # Try installing individually
                        for dep in dev_deps:
                            self.run_command(["pip", "install", dep], cwd=project_path, check=False)
            except Exception as e:
                self.logger.warning(f"Could not install dev dependencies: {e}")

        return {"success": True, "method": "uv pip install -e", "message": "Dependencies installed successfully"}

    @task
    def generate_lock_file(self, project_path: Path) -> Path:
        """
        Generate uv.lock file for reproducible installs.

        Args:
            project_path: Project root directory

        Returns:
            Path to generated lock file
        """
        project_path = Path(project_path)

        result = self.run_command(["lock"], cwd=project_path)

        if not result["success"]:
            raise DependencyError(f"Failed to generate lock file: {result['stderr']}")

        lock_file = project_path / "uv.lock"
        self.logger.info(f"Generated lock file at {lock_file}")

        return lock_file

    @task
    def add_dependency(
        self, project_path: Path, package: str, dev: bool = False, extras: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Add a dependency to the project.

        Args:
            project_path: Project root directory
            package: Package specification (e.g., "requests>=2.28")
            dev: Whether this is a development dependency
            extras: Optional extras for the package

        Returns:
            Result of the operation
        """
        project_path = Path(project_path)

        args = ["add"]

        if dev:
            args.append("--dev")

        if extras:
            for extra in extras:
                args.extend(["--extra", extra])

        args.append(package)

        result = self.run_command(args, cwd=project_path)

        if result["success"]:
            # Regenerate lock file
            try:
                self.generate_lock_file(project_path)
            except Exception as e:
                self.logger.warning(f"Failed to regenerate lock file: {e}")

        return {
            "success": result["success"],
            "package": package,
            "dev": dev,
            "message": result["stdout"] if result["success"] else result["stderr"],
        }

    def remove_dependency(self, project_path: Path, package: str) -> dict[str, Any]:
        """Remove a dependency from the project."""
        project_path = Path(project_path)

        args = ["remove", package]

        result = self.run_command(args, cwd=project_path)

        if result["success"]:
            # Regenerate lock file
            try:
                self.generate_lock_file(project_path)
            except Exception as e:
                self.logger.warning(f"Failed to regenerate lock file: {e}")

        return {
            "success": result["success"],
            "package": package,
            "message": result["stdout"] if result["success"] else result["stderr"],
        }

    def check_outdated(self, project_path: Path) -> list[dict[str, Any]]:
        """Check for outdated dependencies."""
        # UV doesn't have a direct outdated command yet
        # This would need to be implemented differently
        self.logger.info("Checking for outdated dependencies")

        # For now, return empty list
        return []
