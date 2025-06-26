#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

"""
dependencies_installer.py - Project dependencies installation

This module handles installation of project dependencies from lock files
during environment reproduction.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_reproducer.py to reduce file size
# - Contains dependency installation logic for various package managers
#


from pathlib import Path

from prefect import get_run_logger, task

from DHT.modules.environment_snapshot_models import EnvironmentSnapshot, ReproductionResult
from DHT.modules.guardian_prefect import ResourceLimits, run_with_guardian


class DependenciesInstaller:
    """Handles installation of project dependencies."""

    @task(name="install_project_dependencies", description="Install project dependencies")
    def install_project_dependencies(
        self, snapshot: EnvironmentSnapshot, result: ReproductionResult, target_path: Path
    ) -> Any:
        """Install project dependencies."""
        logger = get_run_logger()

        try:
            if "uv.lock" in snapshot.lock_files:
                # Use UV sync
                cmd_result = run_with_guardian(
                    ["uv", "sync"], limits=ResourceLimits(memory_mb=2048, timeout=600), cwd=str(target_path)
                )

                if cmd_result.success:
                    result.actions_completed.append("Installed dependencies via UV sync")
                else:
                    result.actions_failed.append(f"UV sync failed: {cmd_result.stderr}")

            elif "requirements.txt" in snapshot.lock_files:
                # Use pip install
                cmd_result = run_with_guardian(
                    ["pip", "install", "-r", "requirements.txt"],
                    limits=ResourceLimits(memory_mb=2048, timeout=600),
                    cwd=str(target_path),
                )

                if cmd_result.success:
                    result.actions_completed.append("Installed dependencies via pip")
                else:
                    result.actions_failed.append(f"Pip install failed: {cmd_result.stderr}")

            elif "package-lock.json" in snapshot.lock_files:
                # Use npm ci
                cmd_result = run_with_guardian(
                    ["npm", "ci"], limits=ResourceLimits(memory_mb=2048, timeout=600), cwd=str(target_path)
                )

                if cmd_result.success:
                    result.actions_completed.append("Installed dependencies via npm ci")
                else:
                    result.actions_failed.append(f"npm ci failed: {cmd_result.stderr}")

            elif "yarn.lock" in snapshot.lock_files:
                # Use yarn install
                cmd_result = run_with_guardian(
                    ["yarn", "install", "--frozen-lockfile"],
                    limits=ResourceLimits(memory_mb=2048, timeout=600),
                    cwd=str(target_path),
                )

                if cmd_result.success:
                    result.actions_completed.append("Installed dependencies via yarn")
                else:
                    result.actions_failed.append(f"yarn install failed: {cmd_result.stderr}")

            elif "poetry.lock" in snapshot.lock_files:
                # Use poetry install
                cmd_result = run_with_guardian(
                    ["poetry", "install"], limits=ResourceLimits(memory_mb=2048, timeout=600), cwd=str(target_path)
                )

                if cmd_result.success:
                    result.actions_completed.append("Installed dependencies via poetry")
                else:
                    result.actions_failed.append(f"poetry install failed: {cmd_result.stderr}")

        except Exception as e:
            logger.error(f"Failed to install dependencies: {e}")
            result.actions_failed.append(f"dependency_installation_error: {str(e)}")


# Export public API
__all__ = ["DependenciesInstaller"]
