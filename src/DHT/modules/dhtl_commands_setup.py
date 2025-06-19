#!/usr/bin/env python3
"""
dhtl_commands_setup.py - Implementation of dhtl setup command

This module implements the setup command functionality extracted from dhtl_commands.py
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted setup command from dhtl_commands.py to reduce file size
# - Maintains same functionality and interface
# - Part of refactoring to keep files under 10KB
#

from __future__ import annotations

import glob
import logging
import re
from pathlib import Path
from typing import Any

import tomli_w

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10 and below

from prefect import task

from DHT.modules.dhtl_commands_utils import parse_requirements
from DHT.modules.uv_manager import UVManager
from DHT.modules.uv_manager_exceptions import UVError


class SetupCommand:
    """Implementation of dhtl setup command."""

    def __init__(self):
        """Initialize setup command."""
        self.logger = logging.getLogger(__name__)

    @task(name="dhtl_setup")
    def setup(
        self,
        uv_manager: UVManager,
        path: str = ".",
        python: str | None = None,
        dev: bool = False,
        from_requirements: bool = False,
        all_packages: bool = False,
        compile_bytecode: bool = False,
        editable: bool = False,
        index_url: str | None = None,
        install_pre_commit: bool = False,
    ) -> dict[str, Any]:
        """
        Setup a Python project environment using UV.

        Args:
            path: Path to the project directory
            python: Python version to use (e.g., "3.11")
            dev: Install development dependencies
            from_requirements: Import from requirements.txt files
            all_packages: Install all workspace packages
            compile_bytecode: Compile Python files to bytecode
            editable: Install project in editable mode
            index_url: Custom package index URL
            install_pre_commit: Install pre-commit hooks if available

        Returns:
            Result dictionary with success status and details
        """
        project_path = Path(path).resolve()

        if not project_path.exists():
            return {
                "success": False,
                "message": f"Project path does not exist: {project_path}",
                "error": "Path not found",
            }

        try:
            result_info: dict[str, Any] = {
                "success": True,
                "message": "Setup completed successfully",
                "path": str(project_path),
                "installed": {"dependencies": 0, "dev_dependencies": 0},
                "options": {"compile_bytecode": compile_bytecode, "editable": editable},
                "workspace": {"packages_installed": 0},
            }

            # Handle requirements.txt import first
            if from_requirements and (project_path / "requirements.txt").exists():
                if not (project_path / "pyproject.toml").exists():
                    self._create_pyproject_from_requirements(project_path)

            # Ensure pyproject.toml exists
            if not (project_path / "pyproject.toml").exists():
                # Create minimal pyproject.toml
                project_name = project_path.name
                minimal_pyproject = {
                    "project": {
                        "name": project_name,
                        "version": "0.1.0",
                        "description": "Python project",
                        "requires-python": f">={python or '3.11'}",
                        "dependencies": [],
                    }
                }
                with open(project_path / "pyproject.toml", "wb") as f:
                    tomli_w.dump(minimal_pyproject, f)

            # Set Python version if specified
            if python:
                pin_result = uv_manager.run_command(["python", "pin", python], cwd=project_path)
                if not pin_result["success"]:
                    self.logger.warning(f"Failed to pin Python version: {pin_result.get('stderr', '')}")

            # Create virtual environment
            venv_path = project_path / ".venv"
            if not venv_path.exists():
                try:
                    venv_path = uv_manager.create_venv(project_path, python_version=python)
                    self.logger.info(f"Created virtual environment at {venv_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to create venv: {e}")

            # Generate lock file
            lock_result = uv_manager.generate_lock_file(project_path)
            if lock_result:
                self.logger.info("Generated lock file")

            # Build sync command
            sync_args = ["sync"]

            if dev:
                sync_args.append("--all-extras")

            if all_packages:
                sync_args.append("--all-packages")
                # Count workspace packages
                if (project_path / "pyproject.toml").exists():
                    with open(project_path / "pyproject.toml", "rb") as f:
                        pyproject = tomllib.load(f)
                    if "tool" in pyproject and "uv" in pyproject["tool"] and "workspace" in pyproject["tool"]["uv"]:
                        members = pyproject["tool"]["uv"]["workspace"].get("members", [])
                        # Expand glob patterns to count actual packages
                        package_count = 0
                        for member in members:
                            if "*" in member:
                                # Handle glob patterns
                                matched_paths = glob.glob(str(project_path / member))
                                for path in matched_paths:
                                    if Path(path).is_dir() and (Path(path) / "pyproject.toml").exists():
                                        package_count += 1
                            else:
                                # Direct path
                                if (project_path / member / "pyproject.toml").exists():
                                    package_count += 1
                        result_info["workspace"]["packages_installed"] = package_count

            if compile_bytecode:
                sync_args.append("--compile-bytecode")

            # Custom index URL
            if index_url:
                sync_args.extend(["--index-url", index_url])
                result_info["options"]["index_url"] = index_url

            # Run sync to install dependencies
            sync_result = uv_manager.run_command(sync_args, cwd=project_path)
            if not sync_result["success"]:
                raise UVError(f"UV sync failed: {sync_result.get('stderr', '')}")

            # Parse sync output to count installed packages
            # UV outputs to stderr, not stdout
            output = sync_result.get("stderr", "") or sync_result.get("stdout", "")
            if output:
                # Count lines with package installation indicators
                installed_count = 0

                # UV sync output patterns:
                # - "Resolved X packages"
                # - "Installed X packages"
                # - Package lines like "+ package-name==version"

                # Look for "Installed X packages" pattern
                installed_match = re.search(r"Installed (\d+) packages?", output)
                if installed_match:
                    installed_count = int(installed_match.group(1))
                else:
                    # Count individual package lines (fallback)
                    # UV uses + prefix for installed packages
                    installed_lines = [
                        line for line in output.split("\n") if line.strip().startswith("+ ") and "==" in line
                    ]
                    installed_count = len(installed_lines)

                # If still 0, check if already up to date
                if installed_count == 0 and ("up to date" in output.lower() or "audited" in output.lower()):
                    # Packages were already installed, count from pyproject.toml
                    if (project_path / "pyproject.toml").exists():
                        with open(project_path / "pyproject.toml", "rb") as f:
                            pyproject = tomllib.load(f)
                        deps = pyproject.get("project", {}).get("dependencies", [])
                        installed_count = len(deps)

                result_info["installed"]["dependencies"] = installed_count

                if dev:
                    # Count dev dependencies from pyproject.toml
                    if (project_path / "pyproject.toml").exists():
                        with open(project_path / "pyproject.toml", "rb") as f:
                            pyproject = tomllib.load(f)
                        dev_deps = pyproject.get("project", {}).get("optional-dependencies", {}).get("dev", [])
                        result_info["installed"]["dev_dependencies"] = len(dev_deps)

            # Install project in editable mode if requested
            if editable and (project_path / "pyproject.toml").exists():
                install_result = uv_manager.run_command(["pip", "install", "-e", "."], cwd=project_path)
                if not install_result["success"]:
                    self.logger.warning(f"Failed to install in editable mode: {install_result.get('stderr', '')}")

            # Install pre-commit hooks if requested
            if install_pre_commit and (project_path / ".pre-commit-config.yaml").exists():
                result_info["options"]["install_pre_commit"] = True
                # Check if git repo exists
                if (project_path / ".git").exists():
                    pre_commit_result = uv_manager.run_command(["run", "pre-commit", "install"], cwd=project_path)
                    if not pre_commit_result["success"]:
                        self.logger.warning("Failed to install pre-commit hooks")
                else:
                    self.logger.warning("Not a git repository, skipping pre-commit install")

            return result_info

        except Exception as e:
            self.logger.error(f"Failed to setup project: {e}")
            return {
                "success": False,
                "message": f"Setup failed: {str(e)}",
                "error": str(e),
            }

    def _create_pyproject_from_requirements(self, project_path: Path) -> None:
        """Create pyproject.toml from requirements.txt."""
        req_file = project_path / "requirements.txt"
        if not req_file.exists():
            return

        # Parse requirements
        deps = parse_requirements(req_file)

        # Create pyproject.toml
        project_name = project_path.name
        pyproject_data = {
            "project": {
                "name": project_name,
                "version": "0.1.0",
                "description": "Python project",
                "requires-python": ">=3.11",
                "dependencies": deps,
            },
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }

        pyproject_path = project_path / "pyproject.toml"
        with open(pyproject_path, "wb") as f:
            tomli_w.dump(pyproject_data, f)


# Export the command class
__all__ = ["SetupCommand"]
