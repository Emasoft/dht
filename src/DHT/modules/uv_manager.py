#!/usr/bin/env python3
"""
uv_manager.py - UV package manager integration for DHT  This module provides a comprehensive interface to UV (ultra-fast Python package manager) for DHT's environment management, dependency resolution, and project configuration.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
uv_manager.py - UV package manager integration for DHT

This module provides a comprehensive interface to UV (ultra-fast Python package manager)
for DHT's environment management, dependency resolution, and project configuration.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Refactored to use helper modules to reduce file size
# - Imports functionality from specialized managers
# - Maintains backward compatibility with original API
#

import logging
from pathlib import Path
from typing import Any, cast

from DHT.modules.uv_manager_deps import DependencyManager

# Import exceptions
from DHT.modules.uv_manager_exceptions import UVNotFoundError

# Re-export for backward compatibility
__all__ = ["UVManager", "UVNotFoundError"]

# Import specialized managers
from DHT.modules.uv_manager_python import PythonVersionManager
from DHT.modules.uv_manager_script import ScriptExecutor

# Import utilities
from DHT.modules.uv_manager_utils import (
    find_uv_executable,
    is_dev_dependency,
    load_toml,
    run_uv_command,
    verify_uv_version,
)
from DHT.modules.uv_manager_venv import VirtualEnvironmentManager
from DHT.modules.uv_manager_workflow import ProjectWorkflowManager


class UVManager:
    """
    Central UV integration manager for DHT.

    Provides high-level interface to UV functionality including:
    - Python version management
    - Virtual environment creation and management
    - Dependency resolution and installation
    - Lock file generation and validation
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.uv_path = find_uv_executable(self.logger)
        self._min_uv_version = "0.4.0"  # Minimum required UV version

        if self.uv_path:
            verify_uv_version(self.uv_path, self._min_uv_version, self.run_command)

        # Initialize specialized managers
        self.python_manager = PythonVersionManager(self.run_command)
        self.venv_manager = VirtualEnvironmentManager(self.run_command)
        self.deps_manager = DependencyManager(self.run_command)
        self.script_executor = ScriptExecutor(self.run_command)
        self.workflow_manager = ProjectWorkflowManager(self.python_manager, self.venv_manager, self.deps_manager)

    @property
    def is_available(self) -> bool:
        """Check if UV is available and functional."""
        return self.uv_path is not None

    def run_command(
        self,
        args: list[str],
        cwd: Path | None = None,
        capture_output: bool = True,
        check: bool = True,
        timeout: int = 300,  # 5 minutes default
    ) -> dict[str, Any]:
        """
        Run UV command and return structured output.

        Args:
            args: Command arguments (without 'uv' prefix)
            cwd: Working directory for command
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise on non-zero exit code
            timeout: Command timeout in seconds

        Returns:
            Dict with 'stdout', 'stderr', 'returncode', and 'success' keys

        Raises:
            UVNotFoundError: If UV is not available
        """
        if not self.is_available:
            raise UVNotFoundError("UV is not available. Please install UV first.")

        return cast(
            dict[str, Any],
            run_uv_command(self.uv_path, args, cwd=cwd, capture_output=capture_output, check=check, timeout=timeout),
        )

    # Delegate to Python version manager
    def detect_python_version(self, project_path: Path) -> str | None:
        """Detect required Python version for a project."""
        return cast(str | None, self.python_manager.detect_python_version(project_path))

    def list_python_versions(self) -> list[dict[str, Any]]:
        """List all available Python versions."""
        return cast(list[dict[str, Any]], self.python_manager.list_python_versions())

    def ensure_python_version(self, version: str) -> Path:
        """Ensure specific Python version is available."""
        return cast(Path, self.python_manager.ensure_python_version(version))

    # Delegate to virtual environment manager
    def create_venv(self, project_path: Path, python_version: str | None = None, venv_path: Path | None = None) -> Path:
        """Create virtual environment for project."""
        return cast(Path, self.venv_manager.create_venv(project_path, python_version, venv_path))

    # Delegate to dependency manager
    def install_dependencies(
        self,
        project_path: Path,
        requirements_file: Path | None = None,
        dev: bool = False,
        extras: list[str] | None = None,
    ) -> dict[str, Any]:
        """Install project dependencies."""
        return cast(
            dict[str, Any], self.deps_manager.install_dependencies(project_path, requirements_file, dev, extras)
        )

    def generate_lock_file(self, project_path: Path) -> Path:
        """Generate uv.lock file for reproducible installs."""
        return cast(Path, self.deps_manager.generate_lock_file(project_path))

    def add_dependency(
        self, project_path: Path, package: str, dev: bool = False, extras: list[str] | None = None
    ) -> dict[str, Any]:
        """Add a dependency to the project."""
        return cast(dict[str, Any], self.deps_manager.add_dependency(project_path, package, dev, extras))

    def remove_dependency(self, project_path: Path, package: str) -> dict[str, Any]:
        """Remove a dependency from the project."""
        return cast(dict[str, Any], self.deps_manager.remove_dependency(project_path, package))

    def check_outdated(self, project_path: Path) -> list[dict[str, Any]]:
        """Check for outdated dependencies."""
        return cast(list[dict[str, Any]], self.deps_manager.check_outdated(project_path))

    # Delegate to script executor
    def run_script(self, project_path: Path, script: str, args: list[str] | None = None) -> dict[str, Any]:
        """Run a Python script in the project environment."""
        return cast(dict[str, Any], self.script_executor.run_script(project_path, script, args))

    # Delegate to workflow manager
    def setup_project(
        self, project_path: Path, python_version: str | None = None, install_deps: bool = True, dev: bool = False
    ) -> dict[str, Any]:
        """Complete project setup flow."""
        return cast(
            dict[str, Any], self.workflow_manager.setup_project(project_path, python_version, install_deps, dev)
        )

    # Utility methods
    def _load_toml(self, file_path: Path) -> dict[str, Any]:
        """Load TOML file with Python version compatibility."""
        return cast(dict[str, Any], load_toml(file_path))

    def _is_dev_dependency(self, package_name: str) -> bool:
        """Check if a package is likely a development dependency."""
        return cast(bool, is_dev_dependency(package_name))
