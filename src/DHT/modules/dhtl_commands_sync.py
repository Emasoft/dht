#!/usr/bin/env python3
from __future__ import annotations

"""
dhtl_commands_sync.py - Implementation of dhtl sync command  This module implements the sync command functionality extracted from dhtl_commands.py

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
dhtl_commands_sync.py - Implementation of dhtl sync command

This module implements the sync command functionality extracted from dhtl_commands.py
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted sync command from dhtl_commands.py to reduce file size
# - Maintains same functionality and interface
# - Part of refactoring to keep files under 10KB
#


import logging
from pathlib import Path
from typing import Any

from prefect import task
from prefect.cache_policies import NO_CACHE

from DHT.modules.dhtl_commands_utils import count_site_packages
from DHT.modules.uv_manager import UVManager


class SyncCommand:
    """Implementation of dhtl sync command."""

    def __init__(self) -> None:
        """Initialize sync command."""
        self.logger = logging.getLogger(__name__)

    @task(name="dhtl_sync", cache_policy=NO_CACHE)
    def sync(
        self,
        uv_manager: UVManager,
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
        project_path = Path(path).resolve()

        # Check if project exists
        if not project_path.exists():
            return {
                "success": False,
                "message": f"Project path does not exist: {project_path}",
                "error": "Path not found",
            }

        # Check for pyproject.toml
        if not (project_path / "pyproject.toml").exists():
            return {
                "success": False,
                "message": "No pyproject.toml found",
                "error": "No pyproject.toml found. Not a Python project",
            }

        try:
            # Build sync command
            sync_args = ["sync"]

            if locked:
                sync_args.append("--locked")

            if no_dev:
                sync_args.append("--no-dev")
            elif dev and not all_extras:
                # Check if dev extras exist in the project
                pyproject = project_path / "pyproject.toml"
                if pyproject.exists():
                    try:
                        import tomllib
                    except ImportError:
                        import tomli as tomllib

                    try:
                        with open(pyproject, "rb") as f:
                            data = tomllib.load(f)

                        # Check if [project.optional-dependencies] has 'dev'
                        opt_deps = data.get("project", {}).get("optional-dependencies", {})
                        if "dev" in opt_deps:
                            sync_args.extend(["--extra", "dev"])
                    except Exception:
                        # If we can't read the file, don't add the extra
                        pass

            if all_extras:
                sync_args.append("--all-extras")
            elif extras:
                for extra in extras:
                    sync_args.extend(["--extra", extra])

            if upgrade:
                sync_args.append("--upgrade")

            if package:
                sync_args.extend(["--package", package])

            # Run UV sync
            self.logger.info(f"Syncing dependencies in {project_path}...")
            result = uv_manager.run_command(sync_args, cwd=project_path)

            if not result["success"]:
                return {"success": False, "error": f"Sync failed: {result.get('stderr', 'Unknown error')}"}

            # Check what was installed
            venv_path = project_path / ".venv"
            lock_file_path = project_path / "uv.lock"

            if venv_path.exists():
                # Count installed packages
                package_count = count_site_packages(venv_path)

                return {
                    "success": True,
                    "message": "Successfully synced dependencies",
                    "installed": package_count,  # Keep for backward compatibility
                    "packages_installed": package_count,
                    "venv_path": str(venv_path),
                    "lock_file": str(lock_file_path) if lock_file_path.exists() else None,
                    "dev_dependencies_installed": dev and not no_dev,
                    "extras": extras if extras else [],
                    "upgraded": upgrade,
                }
            else:
                return {
                    "success": True,
                    "message": "Dependencies synced (no venv found to count packages)",
                    "installed": 0,
                    "lock_file": str(lock_file_path) if lock_file_path.exists() else None,
                    "dev_dependencies_installed": dev and not no_dev,
                    "extras": extras if extras else [],
                    "upgraded": upgrade,
                }

        except Exception as e:
            self.logger.error(f"Sync error: {e}")
            return {"success": False, "error": str(e)}


# Export the command class
__all__ = ["SyncCommand"]
