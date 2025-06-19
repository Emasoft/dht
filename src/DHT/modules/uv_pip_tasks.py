#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
uv_pip_tasks.py - Pip-specific tasks for UV

This module contains Prefect tasks for UV pip operations.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from uv_prefect_tasks.py to reduce file size
# - Contains pip-specific installation tasks
#

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any, Optional

from prefect import task
from prefect.tasks import exponential_backoff

from DHT.modules.guardian_prefect import run_with_guardian, ResourceLimits
from DHT.modules.uv_task_models import (
    INSTALL_TIMEOUT, UV_MEMORY_LIMITS,
    UVTaskError
)
from DHT.modules.uv_task_utils import get_logger, find_uv_executable


@task(
    name="pip_install_requirements",
    description="Install from requirements file using uv pip",
    retries=3,
    retry_delay_seconds=exponential_backoff(backoff_factor=2),
)
def pip_install_requirements(
    project_path: Path,
    requirements_file: Path
) -> Dict[str, Any]:
    """
    Install from requirements file using uv pip.
    
    Args:
        project_path: Path to project directory
        requirements_file: Path to requirements.txt file
        
    Returns:
        Dict with installation results
    """
    logger = get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV not found")
    
    args = [str(uv_path), "pip", "install", "-r", str(requirements_file)]
    
    result = run_with_guardian(
        command=args,
        limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["install_deps"], timeout=INSTALL_TIMEOUT),
        cwd=str(project_path)
    )
    
    return {
        "success": result.return_code == 0,
        "method": "uv pip install -r",
        "requirements_file": str(requirements_file),
        "message": result.stdout if result.return_code == 0 else result.stderr
    }


@task(
    name="pip_install_project",
    description="Install project with optional extras",
    retries=3,
    retry_delay_seconds=exponential_backoff(backoff_factor=2),
)
def pip_install_project(
    project_path: Path,
    dev: bool = False,
    extras: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Install project with optional extras.
    
    Args:
        project_path: Path to project directory
        dev: Install development dependencies
        extras: Optional extras to install
        
    Returns:
        Dict with installation results
    """
    logger = get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV not found")
    
    # Install the project itself
    install_spec = "."
    
    if extras:
        extras_str = ",".join(extras)
        install_spec = f".[{extras_str}]"
    
    args = [str(uv_path), "pip", "install", "-e", install_spec]
    
    result = run_with_guardian(
        command=args,
        limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["install_deps"], timeout=INSTALL_TIMEOUT),
        cwd=str(project_path)
    )
    
    if result.return_code != 0:
        return {
            "success": False,
            "method": "uv pip install -e",
            "message": result.stderr
        }
    
    # Install dev dependencies if requested
    if dev:
        # Check for dev dependencies in pyproject.toml
        try:
            pyproject = project_path / "pyproject.toml"
            if pyproject.exists():
                # Import tomllib with fallback
                try:
                    import tomllib
                except ImportError:
                    import tomli as tomllib
                
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                
                # Check for dev dependencies in various locations
                dev_deps = (
                    data.get("project", {}).get("optional-dependencies", {}).get("dev", []) or
                    data.get("dependency-groups", {}).get("dev", []) or
                    data.get("tool", {}).get("pdm", {}).get("dev-dependencies", {})
                )
                
                if dev_deps:
                    # Try installing as extra first
                    dev_result = run_with_guardian(
                        command=[str(uv_path), "pip", "install", "-e", ".[dev]"],
                        limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["install_deps"], timeout=INSTALL_TIMEOUT),
                        cwd=str(project_path)
                    )
                    
                    if dev_result.return_code != 0:
                        # Try installing individually
                        logger.warning("Failed to install dev extras, trying individual packages")
                        for dep in dev_deps:
                            run_with_guardian(
                                command=[str(uv_path), "pip", "install", dep],
                                limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["install_deps"], timeout=300),
                                cwd=str(project_path)
                            )
        except Exception as e:
            logger.warning(f"Could not install dev dependencies: {e}")
    
    return {
        "success": True,
        "method": "uv pip install -e",
        "message": "Dependencies installed successfully"
    }