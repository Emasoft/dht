#!/usr/bin/env python3
"""
Improvements and refactoring suggestions for uv_manager.py

This file contains improved code snippets that address the issues found.
"""

import subprocess
from pathlib import Path
from typing import Any


class UVNotFoundError(Exception):
    """Raised when UV is not found on the system."""
    pass


class UVManagerImproved:
    """Improved version with fixes for identified issues."""

    def _load_toml(self, file_path: Path) -> dict[str, Any]:
        """
        Load TOML file with Python version compatibility.

        Args:
            file_path: Path to TOML file

        Returns:
            Parsed TOML data

        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If parsing fails
        """
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        with open(file_path, "rb") as f:
            return tomllib.load(f)

    def run_command_with_timeout(
        self,
        args: list[str],
        cwd: Path | None = None,
        timeout: int = 300,  # 5 minutes default
        capture_output: bool = True,
        check: bool = True
    ) -> dict[str, Any]:
        """
        Run UV command with proper timeout handling.

        Args:
            args: Command arguments
            cwd: Working directory
            timeout: Command timeout in seconds
            capture_output: Whether to capture output
            check: Whether to raise on non-zero exit

        Returns:
            Command result dictionary
        """
        if not self.is_available:
            raise UVNotFoundError("UV is not available")

        cmd = [str(self.uv_path)] + args

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                check=check,
                timeout=timeout
            )

            return {
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
                "returncode": result.returncode,
                "success": result.returncode == 0
            }

        except subprocess.TimeoutExpired as e:
            return {
                "stdout": e.stdout if e.stdout else "",
                "stderr": f"Command timed out after {timeout} seconds",
                "returncode": -1,
                "success": False,
                "error": "timeout"
            }
        except subprocess.CalledProcessError as e:
            return {
                "stdout": e.stdout if capture_output else "",
                "stderr": e.stderr if capture_output else "",
                "returncode": e.returncode,
                "success": False,
                "error": str(e)
            }

    def _setup_python_environment(
        self,
        project_path: Path,
        python_version: str | None = None
    ) -> dict[str, Any]:
        """
        Setup Python environment (extracted from setup_project).

        Args:
            project_path: Project directory
            python_version: Python version to use

        Returns:
            Setup result with python_path
        """
        result = {"success": True, "steps": []}

        # Detect Python version if not specified
        if not python_version:
            python_version = self.detect_python_version(project_path)
            if python_version:
                result["detected_python_version"] = python_version

        # Ensure Python version is available
        if python_version:
            try:
                python_path = self.ensure_python_version(python_version)
                result["python_path"] = str(python_path)
                result["steps"].append({
                    "step": "ensure_python",
                    "success": True,
                    "version": python_version
                })
            except Exception as e:
                result["steps"].append({
                    "step": "ensure_python",
                    "success": False,
                    "error": str(e)
                })
                result["success"] = False

        return result

    def _create_project_venv(
        self,
        project_path: Path,
        python_version: str | None = None
    ) -> dict[str, Any]:
        """
        Create virtual environment (extracted from setup_project).

        Args:
            project_path: Project directory
            python_version: Python version to use

        Returns:
            Creation result with venv_path
        """
        result = {"success": True, "steps": []}

        try:
            venv_path = self.create_venv(project_path, python_version)
            result["venv_path"] = str(venv_path)
            result["steps"].append({
                "step": "create_venv",
                "success": True,
                "path": str(venv_path)
            })
        except Exception as e:
            result["steps"].append({
                "step": "create_venv",
                "success": False,
                "error": str(e)
            })
            result["success"] = False

        return result


# Configuration for dependency detection
DEV_DEPENDENCY_PATTERNS = {
    "testing": ["pytest", "unittest", "mock", "coverage", "tox", "nose", "hypothesis"],
    "linting": ["flake8", "pylint", "pycodestyle", "pydocstyle", "bandit"],
    "formatting": ["black", "autopep8", "yapf", "isort"],
    "type_checking": ["mypy", "pytype", "pyre-check"],
    "documentation": ["sphinx", "mkdocs", "pdoc"],
    "development": ["pre-commit", "ipython", "jupyter", "notebook"],
}


def is_dev_dependency(package_name: str) -> bool:
    """
    Check if a package is likely a development dependency.

    Args:
        package_name: Name of the package

    Returns:
        True if package is likely a dev dependency
    """
    package_lower = package_name.lower()

    for _category, patterns in DEV_DEPENDENCY_PATTERNS.items():
        for pattern in patterns:
            if pattern in package_lower:
                return True

    # Check for common dev dependency prefixes
    dev_prefixes = ["pytest-", "flake8-", "mypy-", "sphinx-"]
    for prefix in dev_prefixes:
        if package_lower.startswith(prefix):
            return True

    return False
