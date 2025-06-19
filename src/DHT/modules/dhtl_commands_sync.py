#!/usr/bin/env python3
"""
dhtl_commands_sync.py - Implementation of dhtl sync command

This module implements the sync command functionality extracted from dhtl_commands.py
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted sync command from dhtl_commands.py to reduce file size
# - Maintains same functionality and interface
# - Part of refactoring to keep files under 10KB
#

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from prefect import task

from DHT.modules.uv_manager import UVManager


class SyncCommand:
    """Implementation of dhtl sync command."""

    def __init__(self):
        """Initialize sync command."""
        self.logger = logging.getLogger(__name__)

    @task(name="dhtl_sync")
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
            return {"success": False, "message": "No pyproject.toml found", "error": "Not a Python project"}

        try:
            # Build sync command
            sync_args = ["sync"]

            if locked:
                sync_args.append("--locked")

            if no_dev:
                sync_args.append("--no-dev")
            elif dev and not all_extras:
                # Default behavior includes dev dependencies
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
                return {"success": False, "error": f"Sync failed: {result.get('error', 'Unknown error')}"}

            # Check what was installed
            venv_path = project_path / ".venv"
            if venv_path.exists():
                # Count installed packages
                site_packages = venv_path / "lib"
                package_count = 0
                if site_packages.exists():
                    for python_dir in site_packages.iterdir():
                        if python_dir.name.startswith("python"):
                            sp_dir = python_dir / "site-packages"
                            if sp_dir.exists():
                                # Count .dist-info directories
                                package_count = len(list(sp_dir.glob("*.dist-info")))
                                break

                return {
                    "success": True,
                    "message": "Successfully synced dependencies",
                    "packages_installed": package_count,
                    "venv_path": str(venv_path),
                }
            else:
                return {"success": True, "message": "Dependencies synced (no venv found to count packages)"}

        except Exception as e:
            self.logger.error(f"Sync error: {e}")
            return {"success": False, "error": str(e)}


# Export the command class
__all__ = ["SyncCommand"]
