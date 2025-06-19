#!/usr/bin/env python3
"""
dhtl_commands.py - Implementation of dhtl CLI commands using UV

This module implements the main dhtl commands (init, setup, build, sync)
following UV documentation best practices.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Refactored to delegate to command-specific modules to reduce file size
# - Maintains backward compatibility with same public interface
# - Each command is now in its own module under 10KB
# - DHTLCommands acts as orchestrator using delegation pattern
#

from __future__ import annotations

import logging
from typing import Any

from DHT.modules.dhtl_commands_build import BuildCommand
from DHT.modules.dhtl_commands_deploy import DeployCommand
from DHT.modules.dhtl_commands_init import InitCommand
from DHT.modules.dhtl_commands_setup import SetupCommand
from DHT.modules.dhtl_commands_sync import SyncCommand
from DHT.modules.uv_manager import UVManager


class DHTLCommands:
    """Implementation of dhtl CLI commands."""

    def __init__(self):
        """Initialize dhtl commands."""
        self.logger = logging.getLogger(__name__)
        self.uv_manager = UVManager()

        if not self.uv_manager.is_available:
            raise RuntimeError("UV is not available. Please install UV first.")

        # Initialize command instances
        self._init_cmd = InitCommand()
        self._setup_cmd = SetupCommand()
        self._build_cmd = BuildCommand()
        self._sync_cmd = SyncCommand()
        self._deploy_cmd = DeployCommand()

    def init(
        self,
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
        return self._init_cmd.init(
            self.uv_manager,
            path=path,
            name=name,
            python=python,
            package=package,
            with_dev=with_dev,
            author=author,
            email=email,
            license=license,
            with_ci=with_ci,
            from_requirements=from_requirements,
        )

    def setup(
        self,
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
        return self._setup_cmd.setup(
            self.uv_manager,
            path=path,
            python=python,
            dev=dev,
            from_requirements=from_requirements,
            all_packages=all_packages,
            compile_bytecode=compile_bytecode,
            editable=editable,
            index_url=index_url,
            install_pre_commit=install_pre_commit,
        )

    def build(
        self,
        path: str = ".",
        wheel: bool = False,
        sdist: bool = False,
        no_checks: bool = False,
        out_dir: str | None = None,
    ) -> dict[str, Any]:
        """Build Python package distributions.

        Args:
            path: Project path to build
            wheel: Build wheel only
            sdist: Build source distribution only
            no_checks: Skip pre-build checks (linting, tests)
            out_dir: Custom output directory for artifacts

        Returns:
            Dict with build results
        """
        return self._build_cmd.build(
            self.uv_manager,
            path=path,
            wheel=wheel,
            sdist=sdist,
            no_checks=no_checks,
            out_dir=out_dir,
        )

    def sync(
        self,
        path: str = ".",
        locked: bool = False,
        dev: bool = True,
        no_dev: bool = False,
        extras: list[str] | None = None,
        upgrade: bool = False,
        all_extras: bool = False,
        package: str | None = None,
    ) -> dict[str, Any]:
        """
        Sync project dependencies using UV.

        Args:
            path: Project path
            locked: Use locked dependencies (uv.lock)
            dev: Include development dependencies
            no_dev: Exclude development dependencies
            extras: List of extra dependency groups to include
            upgrade: Upgrade dependencies
            all_extras: Include all extras
            package: Specific package to sync (workspace projects)

        Returns:
            Result dictionary with success status and message
        """
        return self._sync_cmd.sync(
            self.uv_manager,
            path=path,
            locked=locked,
            dev=dev,
            no_dev=no_dev,
            extras=extras,
            upgrade=upgrade,
            all_extras=all_extras,
            package=package,
        )

    def deploy_project_in_container(
        self,
        project_path: str | None = None,
        run_tests: bool = True,
        python_version: str | None = None,
        detach: bool = False,
        port_mapping: dict[str, int] | None = None,
        environment: dict[str, str] | None = None,
        multi_stage: bool = False,
        production: bool = False,
    ) -> dict[str, Any]:
        """
        Deploy project in a Docker container with UV environment.

        Args:
            project_path: Path to project (defaults to current directory)
            run_tests: Run tests after deployment
            python_version: Python version to use (auto-detected if not specified)
            detach: Run container in background
            port_mapping: Custom port mapping
            environment: Environment variables
            multi_stage: Use multi-stage Dockerfile
            production: Use production optimizations

        Returns:
            Result dictionary with deployment info and test results
        """
        return self._deploy_cmd.deploy_project_in_container(
            project_path=project_path,
            run_tests=run_tests,
            python_version=python_version,
            detach=detach,
            port_mapping=port_mapping,
            environment=environment,
            multi_stage=multi_stage,
            production=production,
        )


# Export the main class
__all__ = ["DHTLCommands"]
