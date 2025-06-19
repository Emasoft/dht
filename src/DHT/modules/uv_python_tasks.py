#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
uv_python_tasks.py - Python version management tasks for UV

This module contains Prefect tasks for managing Python versions with UV.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from uv_prefect_tasks.py to reduce file size
# - Contains Python version detection, listing, and management tasks
#

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from prefect import task

from DHT.modules.guardian_prefect import run_with_guardian, ResourceLimits
from DHT.modules.uv_task_models import (
    RETRY_DELAYS, UV_MEMORY_LIMITS,
    UVTaskError
)
from DHT.modules.uv_task_utils import get_logger, find_uv_executable, extract_min_python_version


@task(
    name="check_uv_available",
    description="Check if UV is available and return version info",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def check_uv_available() -> Dict[str, Any]:
    """
    Check if UV is available on the system.
    
    Returns:
        Dict with UV availability and version information
    """
    logger = get_logger()
    
    try:
        uv_path = find_uv_executable()
        
        if not uv_path:
            logger.warning("UV not found in PATH or common locations")
            return {
                "available": False,
                "error": "UV not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
            }
        
        # Get UV version
        result = run_with_guardian(
            command=[str(uv_path), "--version"],
            limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["version_check"], timeout=30)
        )
        
        if result.return_code == 0:
            version_output = result.stdout.strip()
            # Parse version from output like "uv 0.1.24"
            version_match = re.search(r"uv\s+(\d+\.\d+\.\d+)", version_output)
            version = version_match.group(1) if version_match else "unknown"
            
            return {
                "available": True,
                "version": version,
                "path": str(uv_path),
                "output": version_output
            }
        else:
            return {
                "available": False,
                "error": f"UV check failed: {result.stderr}"
            }
            
    except Exception as e:
        logger.error(f"Error checking UV availability: {e}")
        return {
            "available": False,
            "error": str(e)
        }


@task(
    name="detect_python_version",
    description="Detect required Python version from project files",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def detect_python_version(project_path: Path) -> Optional[str]:
    """
    Detect the required Python version from project files.
    
    Checks in order:
    1. .python-version file
    2. pyproject.toml requires-python
    3. setup.py python_requires
    4. Default to current Python version
    
    Args:
        project_path: Path to project directory
        
    Returns:
        Python version string or None
    """
    logger = get_logger()
    project_path = Path(project_path)
    
    # Check .python-version file
    python_version_file = project_path / ".python-version"
    if python_version_file.exists():
        try:
            version = python_version_file.read_text().strip()
            if version:
                logger.info(f"Found Python version {version} in .python-version")
                return version
        except Exception as e:
            logger.warning(f"Error reading .python-version: {e}")
    
    # Check pyproject.toml
    pyproject_file = project_path / "pyproject.toml"
    if pyproject_file.exists():
        try:
            import tomllib
            with open(pyproject_file, "rb") as f:
                data = tomllib.load(f)
            
            # Check project.requires-python
            requires_python = data.get("project", {}).get("requires-python")
            if requires_python:
                version = extract_min_python_version(requires_python)
                logger.info(f"Found Python version {version} from pyproject.toml")
                return version
        except Exception as e:
            logger.warning(f"Error parsing pyproject.toml: {e}")
    
    # Check setup.py
    setup_py = project_path / "setup.py"
    if setup_py.exists():
        try:
            content = setup_py.read_text()
            # Look for python_requires
            match = re.search(r'python_requires\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                constraint = match.group(1)
                version = extract_min_python_version(constraint)
                logger.info(f"Found Python version {version} from setup.py")
                return version
        except Exception as e:
            logger.warning(f"Error parsing setup.py: {e}")
    
    return None


@task(
    name="list_python_versions",
    description="List available Python versions",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def list_python_versions() -> List[Dict[str, Any]]:
    """
    List all available Python versions (installed and downloadable).
    
    Returns:
        List of Python version information
    """
    logger = get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV not found")
    
    try:
        # Run uv python list
        result = run_with_guardian(
            command=[str(uv_path), "python", "list", "--all-versions"],
            limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["list_versions"], timeout=60)
        )
        
        if result.return_code != 0:
            raise UVTaskError(f"Failed to list Python versions: {result.stderr}")
        
        versions = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            
            # Parse UV output format
            # Example: "cpython-3.11.7-linux-x86_64-gnu     <download available>"
            parts = line.split()
            if parts:
                version_info = {
                    "version": parts[0],
                    "installed": "<download available>" not in line,
                    "source": "uv-managed" if "cpython" in parts[0] else "system"
                }
                versions.append(version_info)
        
        logger.info(f"Found {len(versions)} Python versions")
        return versions
        
    except Exception as e:
        logger.error(f"Error listing Python versions: {e}")
        raise UVTaskError(f"Failed to list Python versions: {e}")


@task(
    name="ensure_python_version",
    description="Ensure specific Python version is available",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def ensure_python_version(version: str) -> Path:
    """
    Ensure a specific Python version is available, installing if necessary.
    
    Args:
        version: Python version to ensure (e.g., "3.11", "3.11.7")
        
    Returns:
        Path to Python executable
    """
    logger = get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV not found")
    
    try:
        # First check if version is already available
        logger.info(f"Checking for Python {version}...")
        
        # Try to find the Python version
        find_result = run_with_guardian(
            command=[str(uv_path), "python", "find", version],
            limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["version_check"], timeout=30)
        )
        
        if find_result.return_code == 0:
            python_path = find_result.stdout.strip()
            if python_path and Path(python_path).exists():
                logger.info(f"Python {version} already available at {python_path}")
                return Path(python_path)
        
        # Install Python version
        logger.info(f"Installing Python {version}...")
        install_result = run_with_guardian(
            command=[str(uv_path), "python", "install", version],
            limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["install_deps"], timeout=300)
        )
        
        if install_result.return_code != 0:
            raise UVTaskError(f"Failed to install Python {version}: {install_result.stderr}")
        
        # Find the installed Python
        find_result = run_with_guardian(
            command=[str(uv_path), "python", "find", version],
            limits=ResourceLimits(memory_mb=UV_MEMORY_LIMITS["version_check"], timeout=30)
        )
        
        if find_result.return_code == 0:
            python_path = find_result.stdout.strip()
            if python_path and Path(python_path).exists():
                logger.info(f"Python {version} installed at {python_path}")
                return Path(python_path)
        
        raise UVTaskError(f"Failed to find Python {version} after installation")
        
    except Exception as e:
        logger.error(f"Error ensuring Python version: {e}")
        raise UVTaskError(f"Failed to ensure Python {version}: {e}")