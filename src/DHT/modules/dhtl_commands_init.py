#!/usr/bin/env python3
from __future__ import annotations

"""
dhtl_commands_init.py - Implementation of dhtl init command  This module implements the init command functionality extracted from dhtl_commands.py

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
dhtl_commands_init.py - Implementation of dhtl init command

This module implements the init command functionality extracted from dhtl_commands.py
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted init command from dhtl_commands.py to reduce file size
# - Maintains same functionality and interface
# - Part of refactoring to keep files under 10KB
#


import logging
from pathlib import Path
from typing import Any

import tomli_w

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10 and below

from prefect import task
from prefect.cache_policies import NO_CACHE

from DHT.modules.dhtl_commands_utils import parse_requirements
from DHT.modules.dhtl_project_templates import (
    get_apache_license,
    get_github_actions_ci,
    get_mit_license,
    get_python_gitignore,
)
from DHT.modules.uv_manager import UVManager


class InitCommand:
    """Implementation of dhtl init command."""

    def __init__(self) -> None:
        """Initialize init command."""
        self.logger = logging.getLogger(__name__)

    @task(name="dhtl_init", cache_policy=NO_CACHE)  # type: ignore[misc]
    def init(
        self,
        uv_manager: UVManager,
        path: str,
        name: str | None = None,
        python: str = "3.11",
        package: bool = False,
        with_dev: bool = False,
        author: str | None = None,
        email: str | None = None,
        license: str | None = None,
        with_ci: str | None = None,
        from_requirements: bool = False,
    ) -> dict[str, Any]:
        """
        Initialize a new Python project using UV.

        Args:
            path: Path where to create the project
            name: Project name (defaults to directory name)
            python: Python version to use
            package: Create as a package (not just scripts)
            with_dev: Add common development dependencies
            author: Author name
            email: Author email
            license: License type (e.g., MIT, Apache-2.0)
            with_ci: CI/CD system to set up (e.g., "github")
            from_requirements: Import from existing requirements.txt

        Returns:
            Result dictionary with success status and message
        """
        project_path = Path(path).resolve()

        # Determine project name
        if name is None:
            name = project_path.name

        # Check if already initialized
        if (project_path / "pyproject.toml").exists():
            self.logger.info(f"Project at {project_path} already initialized")
            return {
                "success": True,
                "message": f"Project '{name}' already initialized at {project_path}",
                "path": str(project_path),
            }

        try:
            # Create directory if needed
            project_path.mkdir(parents=True, exist_ok=True)

            # Create basic project structure
            self.logger.info(f"Creating project '{name}' at {project_path}")

            # Create .python-version file
            python_version_file = project_path / ".python-version"
            python_version_file.write_text(python + "\n")

            # Import from requirements.txt if requested
            if from_requirements:
                req_file = project_path / "requirements.txt"
                if req_file.exists():
                    # Create pyproject.toml from requirements
                    self._create_pyproject_from_requirements(project_path, name, python, author, email, req_file)
                else:
                    self.logger.warning("requirements.txt not found, creating empty project")

            # Use UV init command
            init_args = ["init", "--name", name, "--python", python]

            if package:
                init_args.append("--package")
            else:
                init_args.append("--app")

            if author:
                init_args.extend(["--author-from", "none"])

            result = uv_manager.run_command(init_args, cwd=project_path)
            if not result["success"]:
                return result

            # Enhance pyproject.toml if needed
            pyproject_path = project_path / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)

                # Add author information if provided
                if author or email:
                    data["project"]["authors"] = [{"name": author or "", "email": email or ""}]

                # Add license if provided
                if license:
                    data["project"]["license"] = {"text": license}

                # Add development dependencies if requested
                if with_dev:
                    data["project"]["optional-dependencies"] = {
                        "dev": [
                            "pytest>=7.0",
                            "pytest-cov>=4.0",
                            "ruff>=0.1.0",
                            "mypy>=1.0",
                            "black>=23.0",
                        ]
                    }

                # Write enhanced pyproject.toml
                with open(pyproject_path, "wb") as f:
                    tomli_w.dump(data, f)

            # Create license file if requested
            if license:
                self._create_license_file(project_path, license, author)

            # Create basic .gitignore
            gitignore_path = project_path / ".gitignore"
            if not gitignore_path.exists():
                gitignore_path.write_text(get_python_gitignore())

            # Set up CI/CD if requested
            if with_ci == "github":
                self._setup_github_actions(project_path)

            # Create virtual environment
            try:
                venv_path = uv_manager.create_venv(
                    project_path=project_path, python_version=python, venv_path=project_path / ".venv"
                )
                self.logger.info(f"Created virtual environment at {venv_path}")
            except Exception as e:
                self.logger.warning(f"Failed to create venv: {e}")

            # Install development dependencies if requested
            if with_dev:
                sync_result = uv_manager.run_command(["sync", "--extra", "dev"], cwd=project_path)
                if not sync_result["success"]:
                    self.logger.warning(f"Failed to install dev deps: {sync_result.get('stderr', '')}")

            return {
                "success": True,
                "message": f"Initialized project '{name}' at {project_path}",
                "path": str(project_path),
                "python_version": python,
            }

        except Exception as e:
            self.logger.error(f"Failed to initialize project: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _create_pyproject_from_requirements(
        self,
        project_path: Path,
        name: str,
        python: str,
        author: str | None,
        email: str | None,
        req_file: Path,
    ) -> None:
        """Create pyproject.toml from requirements.txt."""
        # Parse requirements
        deps = parse_requirements(req_file)

        # Create pyproject.toml
        pyproject_data = {
            "project": {
                "name": name,
                "version": "0.1.0",
                "description": "A Python project",
                "requires-python": f">={python}",
                "dependencies": deps,
            },
            "build-system": {
                "requires": ["hatchling"],
                "build-backend": "hatchling.build",
            },
        }

        if author or email:
            pyproject_data["project"]["authors"] = [{"name": author or "", "email": email or ""}]

        pyproject_path = project_path / "pyproject.toml"
        with open(pyproject_path, "wb") as f:
            tomli_w.dump(pyproject_data, f)

    def _create_license_file(self, project_path: Path, license_type: str, author: str | None) -> None:
        """Create a license file.

        Args:
            project_path: Path to the project directory
            license_type: Type of license (MIT or APACHE-2.0)
            author: Author name for the license
        """
        license_path = project_path / "LICENSE"

        if license_type.upper() == "MIT":
            license_path.write_text(get_mit_license(author))
        elif license_type.upper() == "APACHE-2.0":
            license_path.write_text(get_apache_license(author))

    def _setup_github_actions(self, project_path: Path) -> None:
        """Set up GitHub Actions CI/CD."""
        workflows_dir = project_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        ci_path = workflows_dir / "ci.yml"
        ci_path.write_text(get_github_actions_ci())


# Export the command class
__all__ = ["InitCommand"]
