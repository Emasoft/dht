#!/usr/bin/env python3
"""
uv_dependency_tasks.py - Dependency management tasks for UV  This module contains Prefect tasks for managing project dependencies with UV.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
uv_dependency_tasks.py - Dependency management tasks for UV

This module contains Prefect tasks for managing project dependencies with UV.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from uv_prefect_tasks.py to reduce file size
# - Contains dependency installation, sync, and management tasks
#

from __future__ import annotations

from pathlib import Path
from typing import Any

from prefect import task

from DHT.modules.guardian_prefect import ResourceLimits, run_with_guardian
from DHT.modules.uv_task_models import DEFAULT_TIMEOUT, INSTALL_TIMEOUT, RETRY_DELAYS, UV_MEMORY_LIMITS, UVTaskError
from DHT.modules.uv_task_utils import find_uv_executable, get_logger


@task(
    name="install_dependencies",
    description="Install project dependencies using UV",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def install_dependencies(project_path: Path, extras: list[str] | None = None, dev: bool = True) -> dict[str, Any]:
    """
    Install project dependencies using UV.

    Args:
        project_path: Path to project directory
        extras: Optional extras to install
        dev: Include development dependencies

    Returns:
        Dict with installation results
    """
    logger = get_logger()
    project_path = Path(project_path)

    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV not found")

    try:
        # Check if pyproject.toml exists
        pyproject_path = project_path / "pyproject.toml"
        requirements_path = project_path / "requirements.txt"

        if pyproject_path.exists():
            # Use UV sync for projects with pyproject.toml
            cmd = [str(uv_path), "sync"]

            if extras:
                for extra in extras:
                    cmd.extend(["--extra", extra])

            if dev:
                cmd.append("--dev")

            logger.info("Installing dependencies with UV sync")
        elif requirements_path.exists():
            # Fall back to pip install for requirements.txt
            cmd = [str(uv_path), "pip", "install", "-r", str(requirements_path)]
            logger.info("Installing dependencies from requirements.txt")
        else:
            logger.warning("No dependency files found")
            return {"success": False, "error": "No pyproject.toml or requirements.txt found"}

        # Run installation
        result = run_with_guardian(
            command=cmd,
            limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["install_deps"], timeout=INSTALL_TIMEOUT),
            cwd=str(project_path),
        )

        if result.return_code != 0:
            raise UVTaskError(f"Dependency installation failed: {result.stderr}")

        logger.info("Dependencies installed successfully")

        return {"success": True, "method": "sync" if pyproject_path.exists() else "pip", "output": result.stdout}

    except Exception as e:
        logger.error(f"Error installing dependencies: {e}")
        raise UVTaskError(f"Failed to install dependencies: {e}") from e


@task(
    name="sync_dependencies",
    description="Sync dependencies to match lock file",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def sync_dependencies(project_path: Path, frozen: bool = True) -> dict[str, Any]:
    """
    Sync dependencies to match lock file exactly.

    Args:
        project_path: Path to project directory
        frozen: Use frozen/locked dependencies

    Returns:
        Dict with sync results
    """
    logger = get_logger()
    project_path = Path(project_path)

    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV not found")

    try:
        cmd = [str(uv_path), "sync"]

        if frozen:
            cmd.append("--frozen")

        logger.info("Syncing dependencies with UV")
        result = run_with_guardian(
            command=cmd,
            limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["install_deps"], timeout=INSTALL_TIMEOUT),
            cwd=str(project_path),
        )

        if result.return_code != 0:
            raise UVTaskError(f"Dependency sync failed: {result.stderr}")

        return {"success": True, "frozen": frozen, "output": result.stdout}

    except Exception as e:
        logger.error(f"Error syncing dependencies: {e}")
        raise UVTaskError(f"Failed to sync dependencies: {e}") from e


@task(
    name="generate_lock_file",
    description="Generate UV lock file for reproducible installs",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def generate_lock_file(project_path: Path) -> dict[str, Any]:
    """
    Generate UV lock file for the project.

    Args:
        project_path: Path to project directory

    Returns:
        Dict with lock file generation results
    """
    logger = get_logger()
    project_path = Path(project_path)

    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV not found")

    try:
        cmd = [str(uv_path), "lock"]

        logger.info("Generating UV lock file")
        result = run_with_guardian(
            command=cmd,
            limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["install_deps"], timeout=INSTALL_TIMEOUT),
            cwd=str(project_path),
        )

        if result.return_code != 0:
            raise UVTaskError(f"Failed to generate lock file: {result.stderr}")

        lock_file = project_path / "uv.lock"
        logger.info(f"Generated lock file at {lock_file}")

        return {"success": True, "path": str(lock_file), "exists": lock_file.exists(), "output": result.stdout}

    except Exception as e:
        logger.error(f"Error generating lock file: {e}")
        raise UVTaskError(f"Failed to generate lock file: {e}") from e


@task(
    name="add_dependency",
    description="Add a dependency to the project",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def add_dependency(
    project_path: Path, package: str, version: str | None = None, dev: bool = False, optional: str | None = None
) -> dict[str, Any]:
    """
    Add a dependency to the project.

    Args:
        project_path: Path to project directory
        package: Package name to add
        version: Optional version constraint
        dev: Add as development dependency
        optional: Add to optional dependency group

    Returns:
        Dict with addition results
    """
    logger = get_logger()
    project_path = Path(project_path)

    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV not found")

    try:
        # Build package specification
        package_spec = package
        if version:
            package_spec = f"{package}{version}"

        cmd = [str(uv_path), "add", package_spec]

        if dev:
            cmd.append("--dev")

        if optional:
            cmd.extend(["--optional", optional])

        logger.info(f"Adding dependency: {package_spec}")
        result = run_with_guardian(
            command=cmd,
            limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["install_deps"], timeout=INSTALL_TIMEOUT),
            cwd=str(project_path),
        )

        if result.return_code != 0:
            raise UVTaskError(f"Failed to add dependency: {result.stderr}")

        logger.info(f"Successfully added {package}")

        return {
            "success": True,
            "package": package,
            "version": version,
            "dev": dev,
            "optional": optional,
            "output": result.stdout,
        }

    except Exception as e:
        logger.error(f"Error adding dependency: {e}")
        raise UVTaskError(f"Failed to add dependency {package}: {e}") from e


@task(
    name="remove_dependency",
    description="Remove a dependency from the project",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def remove_dependency(project_path: Path, package: str) -> dict[str, Any]:
    """
    Remove a dependency from the project.

    Args:
        project_path: Path to project directory
        package: Package name to remove

    Returns:
        Dict with removal results
    """
    logger = get_logger()
    project_path = Path(project_path)

    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV not found")

    try:
        cmd = [str(uv_path), "remove", package]

        logger.info(f"Removing dependency: {package}")
        result = run_with_guardian(
            command=cmd,
            limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["install_deps"], timeout=DEFAULT_TIMEOUT),
            cwd=str(project_path),
        )

        if result.return_code != 0:
            raise UVTaskError(f"Failed to remove dependency: {result.stderr}")

        logger.info(f"Successfully removed {package}")

        return {"success": True, "package": package, "output": result.stdout}

    except Exception as e:
        logger.error(f"Error removing dependency: {e}")
        raise UVTaskError(f"Failed to remove dependency {package}: {e}") from e
