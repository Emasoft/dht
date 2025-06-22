#!/usr/bin/env python3
"""
uv_environment_tasks.py - Virtual environment management tasks for UV  This module contains Prefect tasks for managing virtual environments with UV.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
uv_environment_tasks.py - Virtual environment management tasks for UV

This module contains Prefect tasks for managing virtual environments with UV.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from uv_prefect_tasks.py to reduce file size
# - Contains virtual environment creation and management tasks
#

from __future__ import annotations

from pathlib import Path
from typing import Any

from prefect import flow, task
from prefect.artifacts import create_markdown_artifact

from DHT.modules.guardian_prefect import ResourceLimits, run_with_guardian
from DHT.modules.uv_dependency_tasks import install_dependencies
from DHT.modules.uv_python_tasks import check_uv_available, detect_python_version, ensure_python_version
from DHT.modules.uv_task_models import DEFAULT_TIMEOUT, RETRY_DELAYS, UV_MEMORY_LIMITS, UVTaskError
from DHT.modules.uv_task_utils import find_uv_executable, get_logger


@task(
    name="create_virtual_environment",
    description="Create a virtual environment using UV",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def create_virtual_environment(
    project_path: Path, python_version: str | None = None, force: bool = False
) -> dict[str, Any]:
    """
    Create a virtual environment for the project.

    Args:
        project_path: Path to project directory
        python_version: Specific Python version to use
        force: Force recreation if venv exists

    Returns:
        Dict with venv creation results
    """
    logger = get_logger()
    project_path = Path(project_path)
    venv_path = project_path / ".venv"

    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV not found")

    # Check if venv already exists
    if venv_path.exists() and not force:
        logger.info(f"Virtual environment already exists at {venv_path}")
        return {"created": False, "path": str(venv_path), "message": "Virtual environment already exists"}

    try:
        # Build UV venv command
        cmd = [str(uv_path), "venv"]

        if python_version:
            cmd.extend(["--python", python_version])

        if force:
            cmd.append("--force")

        # Add venv path
        cmd.append(str(venv_path))

        # Create virtual environment
        logger.info(f"Creating virtual environment at {venv_path}")
        result = run_with_guardian(
            command=cmd,
            limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["create_venv"], timeout=DEFAULT_TIMEOUT),
            cwd=str(project_path),
        )

        if result.return_code != 0:
            raise UVTaskError(f"Failed to create venv: {result.stderr}")

        logger.info("Virtual environment created successfully")

        return {"created": True, "path": str(venv_path), "python_version": python_version, "output": result.stdout}

    except Exception as e:
        logger.error(f"Error creating virtual environment: {e}")
        raise UVTaskError(f"Failed to create virtual environment: {e}") from e


@flow(name="setup_project_environment", description="Complete project environment setup with UV")
def setup_project_environment(
    project_path: Path, python_version: str | None = None, install_deps: bool = True, force_recreate: bool = False
) -> dict[str, Any]:
    """
    Complete project environment setup flow.

    This flow:
    1. Checks UV availability
    2. Detects or ensures Python version
    3. Creates virtual environment
    4. Installs dependencies

    Args:
        project_path: Path to project directory
        python_version: Specific Python version (auto-detect if None)
        install_deps: Whether to install dependencies
        force_recreate: Force recreation of venv

    Returns:
        Dict with setup results
    """
    logger = get_logger()
    results = {"success": False, "steps": {}, "errors": []}

    try:
        # Check UV availability
        uv_check = check_uv_available()
        results["steps"]["uv_check"] = uv_check

        if not uv_check["available"]:
            results["errors"].append("UV not available")
            return results

        # Detect or ensure Python version
        if not python_version:
            python_version = detect_python_version(project_path)
            if not python_version:
                import sys

                python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
                logger.info(f"Using current Python version: {python_version}")

        results["steps"]["python_version"] = python_version

        # Ensure Python version is available
        python_path = ensure_python_version(python_version)
        results["steps"]["python_path"] = str(python_path)

        # Create virtual environment
        venv_result = create_virtual_environment(project_path, python_version=python_version, force=force_recreate)
        results["steps"]["venv_creation"] = venv_result

        # Install dependencies
        if install_deps:
            deps_result = install_dependencies(project_path)
            results["steps"]["dependencies"] = deps_result

        results["success"] = True

        # Create artifact with setup summary
        create_markdown_artifact(
            key="project-setup-summary",
            markdown=f"""
# Project Environment Setup Summary

## UV Version
- Available: {uv_check["available"]}
- Version: {uv_check.get("version", "N/A")}

## Python Configuration
- Version: {python_version}
- Path: {python_path}

## Virtual Environment
- Created: {venv_result.get("created", False)}
- Path: {venv_result.get("path", "N/A")}

## Dependencies
- Installed: {results["steps"].get("dependencies", {}).get("success", False)}

## Status
Setup completed {"successfully" if results["success"] else "with errors"}
""",
        )

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        results["errors"].append(str(e))

    return results
