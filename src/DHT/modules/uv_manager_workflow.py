#!/usr/bin/env python3
"""
uv_manager_workflow.py - Project setup workflow for UV Manager

This module contains the project setup workflow and related operations.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from uv_manager.py to reduce file size
# - Contains project setup workflow and orchestration
#

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from prefect import flow


class ProjectWorkflowManager:
    """Manages project setup workflows for UV."""

    def __init__(self, python_manager, venv_manager, deps_manager):
        """
        Initialize project workflow manager.

        Args:
            python_manager: Python version manager instance
            venv_manager: Virtual environment manager instance
            deps_manager: Dependency manager instance
        """
        self.logger = logging.getLogger(__name__)
        self.python_manager = python_manager
        self.venv_manager = venv_manager
        self.deps_manager = deps_manager

    def _setup_python_environment(
        self, project_path: Path, python_version: str | None, results: dict[str, Any]
    ) -> str | None:
        """Set up Python environment and return version."""
        # Detect Python version if not specified
        if not python_version:
            python_version = self.python_manager.detect_python_version(project_path)
            if python_version:
                results["detected_python_version"] = python_version
                self.logger.info(f"Detected Python version: {python_version}")

        # Ensure Python version is available
        if python_version:
            try:
                python_path = self.python_manager.ensure_python_version(python_version)
                results["python_path"] = str(python_path)
                results["steps"].append(
                    {"step": "ensure_python", "success": True, "version": python_version, "path": str(python_path)}
                )
                return python_version
            except Exception as e:
                results["steps"].append({"step": "ensure_python", "success": False, "error": str(e)})
                results["success"] = False
                return None

        return python_version

    def _setup_virtual_environment(
        self, project_path: Path, python_version: str | None, results: dict[str, Any]
    ) -> Path | None:
        """Set up virtual environment and return path."""
        try:
            venv_path = self.venv_manager.create_venv(project_path, python_version)
            results["venv_path"] = str(venv_path)
            results["steps"].append({"step": "create_venv", "success": True, "path": str(venv_path)})
            return venv_path
        except Exception as e:
            results["steps"].append({"step": "create_venv", "success": False, "error": str(e)})
            results["success"] = False
            return None

    def _setup_dependencies(self, project_path: Path, dev: bool, results: dict[str, Any]) -> None:
        """Set up project dependencies."""
        try:
            deps_result = self.deps_manager.install_dependencies(project_path, dev=dev)
            results["steps"].append(
                {
                    "step": "install_dependencies",
                    "success": deps_result["success"],
                    "method": deps_result.get("method"),
                    "message": deps_result.get("message"),
                }
            )
        except Exception as e:
            results["steps"].append({"step": "install_dependencies", "success": False, "error": str(e)})

    def _generate_lock_if_needed(self, project_path: Path, results: dict[str, Any]) -> None:
        """Generate lock file if needed."""
        lock_file = project_path / "uv.lock"
        if not lock_file.exists() and (project_path / "pyproject.toml").exists():
            try:
                lock_path = self.deps_manager.generate_lock_file(project_path)
                results["steps"].append({"step": "generate_lock", "success": True, "path": str(lock_path)})
            except Exception as e:
                results["steps"].append({"step": "generate_lock", "success": False, "error": str(e)})

    @flow(name="setup_project", description="Complete project setup flow")
    def setup_project(
        self, project_path: Path, python_version: str | None = None, install_deps: bool = True, dev: bool = False
    ) -> dict[str, Any]:
        """
        Complete project setup flow.

        Args:
            project_path: Project root directory
            python_version: Specific Python version to use
            install_deps: Whether to install dependencies
            dev: Whether to install development dependencies

        Returns:
            Setup result information
        """
        project_path = Path(project_path)
        results = {"project_path": str(project_path), "timestamp": datetime.now().isoformat(), "steps": []}

        # Setup Python environment
        python_version = self._setup_python_environment(project_path, python_version, results)
        if results.get("success") is False:
            return results

        # Create virtual environment
        venv_path = self._setup_virtual_environment(project_path, python_version, results)
        if venv_path is None:
            return results

        # Install dependencies
        if install_deps:
            self._setup_dependencies(project_path, dev, results)

        # Generate lock file if needed
        self._generate_lock_if_needed(project_path, results)

        # Set overall success
        results["success"] = all(step.get("success", False) for step in results["steps"]) if results["steps"] else True

        return results
