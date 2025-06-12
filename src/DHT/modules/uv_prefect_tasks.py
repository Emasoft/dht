#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Created dedicated Prefect tasks module for UV operations
# - Implemented proper resource management and monitoring
# - Added structured error handling with retry policies
# - Created task-specific configurations and timeouts
# - Implemented caching for expensive operations
# - Added comprehensive logging and metrics collection
# 

"""
UV Prefect Tasks Module.

This module provides Prefect task wrappers for all UV operations with proper
resource management, error handling, and monitoring capabilities.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from functools import lru_cache

from prefect import task, flow, get_run_logger
from prefect.artifacts import create_markdown_artifact
from prefect.tasks import exponential_backoff

from DHT.modules.guardian_prefect import run_with_guardian, ResourceLimits


# Task configuration defaults
DEFAULT_TIMEOUT = 300  # 5 minutes
INSTALL_TIMEOUT = 600  # 10 minutes for installations
BUILD_TIMEOUT = 900    # 15 minutes for builds

# Memory limits for different operations
UV_MEMORY_LIMITS = {
    "version_check": 256,      # MB
    "list_versions": 512,      # MB
    "create_venv": 1024,       # MB
    "install_deps": 2048,      # MB
    "build_project": 4096,     # MB
}

# Retry configurations
RETRY_DELAYS = [1, 2, 5]  # Exponential backoff in seconds


class UVTaskError(Exception):
    """Base exception for UV task errors."""
    pass


def _get_logger():
    """Get logger with fallback for testing."""
    try:
        return get_run_logger()
    except Exception:
        # Fallback for testing
        import logging
        return logging.getLogger(__name__)


@lru_cache(maxsize=1)
def find_uv_executable() -> Optional[Path]:
    """
    Find UV executable in PATH or common locations.
    
    Returns:
        Path to UV executable or None if not found
    """
    # First check if UV is in PATH
    uv_in_path = shutil.which("uv")
    if uv_in_path:
        return Path(uv_in_path)
    
    # Check common installation locations
    common_paths = [
        Path.home() / ".local" / "bin" / "uv",
        Path.home() / ".cargo" / "bin" / "uv",
        Path("/usr/local/bin/uv"),
        Path("/opt/homebrew/bin/uv"),
    ]
    
    for path in common_paths:
        if path.exists() and path.is_file():
            return path
    
    return None


@task(
    name="check_uv_available",
    description="Check if UV is available and return version info",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def check_uv_available() -> Dict[str, Any]:
    """
    Check if UV is available and return version information.
    
    Returns:
        Dict with availability status and version info
    """
    logger = _get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        logger.warning("UV executable not found")
        return {
            "available": False,
            "error": "UV not found in PATH or common locations"
        }
    
    # Check version
    try:
        result = run_with_guardian(
            [str(uv_path), "--version"],
            limits=ResourceLimits(
                memory_mb=UV_MEMORY_LIMITS["version_check"],
                timeout=30
            )
        )
        
        if result.success:
            version_output = result.stdout.strip()
            # Parse version from output like "uv 0.4.27"
            version = version_output.split()[-1] if version_output else "unknown"
            
            logger.info(f"UV version {version} found at {uv_path}")
            
            return {
                "available": True,
                "version": version,
                "path": str(uv_path),
                "output": version_output
            }
        else:
            return {
                "available": False,
                "error": f"Version check failed: {result.stderr}"
            }
            
    except Exception as e:
        logger.error(f"Failed to check UV version: {e}")
        return {
            "available": False,
            "error": str(e)
        }


@task(
    name="detect_python_version",
    description="Detect required Python version for a project",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def detect_python_version(project_path: Path) -> Optional[str]:
    """
    Detect required Python version for a project.
    
    Checks in order:
    1. .python-version file
    2. pyproject.toml requires-python
    3. setup.py python_requires
    
    Args:
        project_path: Project root directory
        
    Returns:
        Python version string (e.g., "3.11", "3.11.6") or None
    """
    logger = _get_logger()
    project_path = Path(project_path)
    
    # Check .python-version file
    python_version_file = project_path / ".python-version"
    if python_version_file.exists():
        try:
            version = python_version_file.read_text().strip()
            logger.info(f"Found Python version in .python-version: {version}")
            return version
        except Exception as e:
            logger.warning(f"Failed to read .python-version: {e}")
    
    # Check pyproject.toml
    pyproject_file = project_path / "pyproject.toml"
    if pyproject_file.exists():
        try:
            # Import tomllib with fallback
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
            
            with open(pyproject_file, "rb") as f:
                data = tomllib.load(f)
            
            requires_python = data.get("project", {}).get("requires-python")
            if requires_python:
                # Extract minimum version from constraint
                version = extract_min_python_version(requires_python)
                logger.info(f"Found Python requirement in pyproject.toml: {version}")
                return version
                
        except Exception as e:
            logger.warning(f"Failed to parse pyproject.toml: {e}")
    
    # Check setup.py (would need AST parsing for accuracy)
    setup_py = project_path / "setup.py"
    if setup_py.exists():
        logger.info("Found setup.py but skipping parsing (would need AST analysis)")
    
    return None


def extract_min_python_version(constraint: str) -> str:
    """Extract minimum Python version from constraint string."""
    import re
    
    constraint = constraint.strip()
    
    # Handle common patterns
    if constraint.startswith(">="):
        version = constraint[2:].split(",")[0].strip()
        return version
    elif constraint.startswith("^"):
        # Caret notation - use base version
        return constraint[1:].strip()
    elif constraint.startswith("~"):
        # Tilde notation - use base version
        return constraint[1:].strip()
    else:
        # Try to extract any version number
        match = re.search(r'\d+\.\d+(?:\.\d+)?', constraint)
        if match:
            return match.group()
    
    # Default to current Python version
    import sys
    return f"{sys.version_info.major}.{sys.version_info.minor}"


@task(
    name="list_python_versions",
    description="List all available Python versions",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def list_python_versions() -> List[Dict[str, Any]]:
    """
    List all available Python versions (installed and downloadable).
    
    Returns:
        List of version information dictionaries
    """
    logger = _get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV executable not found")
    
    result = run_with_guardian(
        [str(uv_path), "python", "list", "--all-versions"],
        limits=ResourceLimits(
            memory_mb=UV_MEMORY_LIMITS["list_versions"],
            timeout=60
        )
    )
    
    if not result.success:
        logger.error(f"Failed to list Python versions: {result.stderr}")
        return []
    
    versions = []
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            # Parse version info from UV output
            parts = line.strip().split()
            if parts:
                version_info = {
                    "version": parts[0],
                    "installed": "(installed)" in line,
                    "path": parts[-1] if "(installed)" in line else None
                }
                versions.append(version_info)
    
    logger.info(f"Found {len(versions)} Python versions")
    return versions


@task(
    name="ensure_python_version",
    description="Ensure specific Python version is available",
    retries=3,
    retry_delay_seconds=exponential_backoff(backoff_factor=2),
)
def ensure_python_version(version: str) -> Path:
    """
    Ensure specific Python version is available, installing if needed.
    
    Args:
        version: Python version to ensure (e.g., "3.11", "3.11.6")
        
    Returns:
        Path to Python executable
        
    Raises:
        UVTaskError: If Python version cannot be ensured
    """
    logger = _get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV executable not found")
    
    # First check if already installed
    result = run_with_guardian(
        [str(uv_path), "python", "find", version],
        limits=ResourceLimits(
            memory_mb=UV_MEMORY_LIMITS["version_check"],
            timeout=30
        )
    )
    
    if result.success and result.stdout.strip():
        python_path = Path(result.stdout.strip())
        logger.info(f"Python {version} already available at {python_path}")
        return python_path
    
    # Not installed, try to install
    logger.info(f"Python {version} not found, attempting to install...")
    
    install_result = run_with_guardian(
        [str(uv_path), "python", "install", version],
        limits=ResourceLimits(
            memory_mb=UV_MEMORY_LIMITS["install_deps"],
            timeout=INSTALL_TIMEOUT
        )
    )
    
    if not install_result.success:
        raise UVTaskError(
            f"Failed to install Python {version}: {install_result.stderr}"
        )
    
    # Find the newly installed Python
    find_result = run_with_guardian(
        [str(uv_path), "python", "find", version],
        limits=ResourceLimits(
            memory_mb=UV_MEMORY_LIMITS["version_check"],
            timeout=30
        )
    )
    
    if find_result.success and find_result.stdout.strip():
        python_path = Path(find_result.stdout.strip())
        logger.info(f"Successfully installed Python {version} at {python_path}")
        return python_path
    else:
        raise UVTaskError(
            f"Python {version} was installed but cannot be found"
        )


@task(
    name="create_virtual_environment",
    description="Create virtual environment for project",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def create_virtual_environment(
    project_path: Path,
    python_version: Optional[str] = None,
    venv_path: Optional[Path] = None
) -> Path:
    """
    Create virtual environment for project.
    
    Args:
        project_path: Project root directory
        python_version: Specific Python version to use
        venv_path: Custom path for virtual environment
        
    Returns:
        Path to created virtual environment
        
    Raises:
        UVTaskError: If virtual environment creation fails
    """
    logger = _get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV executable not found")
    
    project_path = Path(project_path)
    
    if venv_path is None:
        venv_path = project_path / ".venv"
    
    args = [str(uv_path), "venv"]
    
    if python_version:
        args.extend(["--python", python_version])
    
    # Add path if not default
    if venv_path != project_path / ".venv":
        args.append(str(venv_path))
    
    result = run_with_guardian(
        args,
        cwd=str(project_path),
        limits=ResourceLimits(
            memory_mb=UV_MEMORY_LIMITS["create_venv"],
            timeout=DEFAULT_TIMEOUT
        )
    )
    
    if not result.success:
        raise UVTaskError(f"Failed to create virtual environment: {result.stderr}")
    
    logger.info(f"Created virtual environment at {venv_path}")
    return venv_path


@task(
    name="install_dependencies",
    description="Install project dependencies",
    retries=3,
    retry_delay_seconds=exponential_backoff(backoff_factor=2),
)
def install_dependencies(
    project_path: Path,
    requirements_file: Optional[Path] = None,
    dev: bool = False,
    extras: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Install project dependencies using UV.
    
    Args:
        project_path: Project root directory
        requirements_file: Specific requirements file to use
        dev: Whether to install development dependencies
        extras: List of extras to install
        
    Returns:
        Installation result information
    """
    logger = _get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV executable not found")
    
    project_path = Path(project_path)
    
    # Check if project has uv.lock
    lock_file = project_path / "uv.lock"
    if lock_file.exists():
        # Use uv sync for lock file
        return sync_dependencies(project_path, dev=dev, extras=extras)
    
    # Otherwise use pip install
    if requirements_file:
        return pip_install_requirements(project_path, requirements_file)
    
    # Look for pyproject.toml
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        return pip_install_project(project_path, dev=dev, extras=extras)
    
    # Look for requirements.txt
    requirements_txt = project_path / "requirements.txt"
    if requirements_txt.exists():
        return pip_install_requirements(project_path, requirements_txt)
    
    logger.warning("No dependencies found to install")
    return {"success": True, "message": "No dependencies found"}


@task(
    name="sync_dependencies",
    description="Sync dependencies from uv.lock file",
    retries=3,
    retry_delay_seconds=exponential_backoff(backoff_factor=2),
)
def sync_dependencies(
    project_path: Path,
    dev: bool = False,
    extras: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Sync dependencies from uv.lock file."""
    logger = _get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV executable not found")
    
    args = [str(uv_path), "sync"]
    
    if dev:
        args.append("--dev")
    
    if extras:
        for extra in extras:
            args.extend(["--extra", extra])
    
    result = run_with_guardian(
        args,
        cwd=str(project_path),
        limits=ResourceLimits(
            memory_mb=UV_MEMORY_LIMITS["install_deps"],
            timeout=INSTALL_TIMEOUT
        )
    )
    
    return {
        "success": result.success,
        "method": "uv sync",
        "message": result.stdout if result.success else result.stderr
    }


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
    """Install from requirements file using uv pip."""
    logger = _get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV executable not found")
    
    args = [str(uv_path), "pip", "install", "-r", str(requirements_file)]
    
    result = run_with_guardian(
        args,
        cwd=str(project_path),
        limits=ResourceLimits(
            memory_mb=UV_MEMORY_LIMITS["install_deps"],
            timeout=INSTALL_TIMEOUT
        )
    )
    
    return {
        "success": result.success,
        "method": "uv pip install -r",
        "requirements_file": str(requirements_file),
        "message": result.stdout if result.success else result.stderr
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
    """Install project with optional extras."""
    logger = _get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV executable not found")
    
    # Install the project itself
    install_spec = "."
    
    if extras:
        extras_str = ",".join(extras)
        install_spec = f".[{extras_str}]"
    
    args = [str(uv_path), "pip", "install", "-e", install_spec]
    
    result = run_with_guardian(
        args,
        cwd=str(project_path),
        limits=ResourceLimits(
            memory_mb=UV_MEMORY_LIMITS["install_deps"],
            timeout=INSTALL_TIMEOUT
        )
    )
    
    if not result.success:
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
                        [str(uv_path), "pip", "install", "-e", ".[dev]"],
                        cwd=str(project_path),
                        limits=ResourceLimits(
                            memory_mb=UV_MEMORY_LIMITS["install_deps"],
                            timeout=INSTALL_TIMEOUT
                        )
                    )
                    
                    if not dev_result.success:
                        # Try installing individually
                        logger.warning("Failed to install dev extras, trying individual packages")
                        for dep in dev_deps:
                            run_with_guardian(
                                [str(uv_path), "pip", "install", dep],
                                cwd=str(project_path),
                                limits=ResourceLimits(
                                    memory_mb=UV_MEMORY_LIMITS["install_deps"],
                                    timeout=300
                                )
                            )
        except Exception as e:
            logger.warning(f"Could not install dev dependencies: {e}")
    
    return {
        "success": True,
        "method": "uv pip install -e",
        "message": "Dependencies installed successfully"
    }


@task(
    name="generate_lock_file",
    description="Generate uv.lock file for reproducible installs",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def generate_lock_file(project_path: Path) -> Path:
    """
    Generate uv.lock file for reproducible installs.
    
    Args:
        project_path: Project root directory
        
    Returns:
        Path to generated lock file
        
    Raises:
        UVTaskError: If lock file generation fails
    """
    logger = _get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV executable not found")
    
    project_path = Path(project_path)
    
    result = run_with_guardian(
        [str(uv_path), "lock"],
        cwd=str(project_path),
        limits=ResourceLimits(
            memory_mb=UV_MEMORY_LIMITS["install_deps"],
            timeout=INSTALL_TIMEOUT
        )
    )
    
    if not result.success:
        raise UVTaskError(f"Failed to generate lock file: {result.stderr}")
    
    lock_file = project_path / "uv.lock"
    logger.info(f"Generated lock file at {lock_file}")
    
    return lock_file


@task(
    name="add_dependency",
    description="Add a dependency to the project",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def add_dependency(
    project_path: Path,
    package: str,
    dev: bool = False,
    extras: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Add a dependency to the project.
    
    Args:
        project_path: Project root directory
        package: Package specification (e.g., "requests>=2.28")
        dev: Whether this is a development dependency
        extras: Optional extras for the package
        
    Returns:
        Result of the operation
    """
    logger = _get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV executable not found")
    
    project_path = Path(project_path)
    
    args = [str(uv_path), "add"]
    
    if dev:
        args.append("--dev")
    
    if extras:
        for extra in extras:
            args.extend(["--extra", extra])
    
    args.append(package)
    
    result = run_with_guardian(
        args,
        cwd=str(project_path),
        limits=ResourceLimits(
            memory_mb=UV_MEMORY_LIMITS["install_deps"],
            timeout=DEFAULT_TIMEOUT
        )
    )
    
    if result.success:
        # Regenerate lock file
        try:
            generate_lock_file(project_path)
        except Exception as e:
            logger.warning(f"Failed to regenerate lock file: {e}")
    
    return {
        "success": result.success,
        "package": package,
        "dev": dev,
        "message": result.stdout if result.success else result.stderr
    }


@task(
    name="remove_dependency",
    description="Remove a dependency from the project",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def remove_dependency(project_path: Path, package: str) -> Dict[str, Any]:
    """Remove a dependency from the project."""
    logger = _get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV executable not found")
    
    project_path = Path(project_path)
    
    args = [str(uv_path), "remove", package]
    
    result = run_with_guardian(
        args,
        cwd=str(project_path),
        limits=ResourceLimits(
            memory_mb=UV_MEMORY_LIMITS["install_deps"],
            timeout=DEFAULT_TIMEOUT
        )
    )
    
    if result.success:
        # Regenerate lock file
        try:
            generate_lock_file(project_path)
        except Exception as e:
            logger.warning(f"Failed to regenerate lock file: {e}")
    
    return {
        "success": result.success,
        "package": package,
        "message": result.stdout if result.success else result.stderr
    }


@task(
    name="build_project",
    description="Build Python project",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def build_project(
    project_path: Path,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Build Python project using UV.
    
    Args:
        project_path: Project root directory
        output_dir: Output directory for built artifacts
        
    Returns:
        Build result information
    """
    logger = _get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV executable not found")
    
    project_path = Path(project_path)
    
    args = [str(uv_path), "build"]
    
    if output_dir:
        args.extend(["--out-dir", str(output_dir)])
    
    result = run_with_guardian(
        args,
        cwd=str(project_path),
        limits=ResourceLimits(
            memory_mb=UV_MEMORY_LIMITS["build_project"],
            timeout=BUILD_TIMEOUT
        )
    )
    
    return {
        "success": result.success,
        "output": result.stdout if result.success else result.stderr,
        "artifacts": list((output_dir or project_path / "dist").glob("*"))
        if result.success else []
    }


@task(
    name="run_python_script",
    description="Run a Python script in the project environment",
    retries=2,
    retry_delay_seconds=RETRY_DELAYS,
)
def run_python_script(
    project_path: Path,
    script: str,
    args: Optional[List[str]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    memory_mb: int = 2048
) -> Dict[str, Any]:
    """
    Run a Python script in the project environment.
    
    Args:
        project_path: Project root directory
        script: Script to run (file or module)
        args: Additional arguments for the script
        timeout: Timeout in seconds
        memory_mb: Memory limit in MB
        
    Returns:
        Execution result
    """
    logger = _get_logger()
    
    uv_path = find_uv_executable()
    if not uv_path:
        raise UVTaskError("UV executable not found")
    
    project_path = Path(project_path)
    
    cmd_args = [str(uv_path), "run"]
    
    if script.endswith(".py"):
        cmd_args.extend(["python", script])
    else:
        cmd_args.extend(["python", "-m", script])
    
    if args:
        cmd_args.extend(args)
    
    result = run_with_guardian(
        cmd_args,
        cwd=str(project_path),
        limits=ResourceLimits(
            memory_mb=memory_mb,
            timeout=timeout
        )
    )
    
    return {
        "success": result.success,
        "script": script,
        "output": result.stdout,
        "error": result.stderr,
        "duration": result.execution_time,
        "peak_memory_mb": result.peak_memory_mb
    }


@flow(
    name="setup_project_environment",
    description="Complete project setup flow using UV"
)
def setup_project_environment(
    project_path: Path,
    python_version: Optional[str] = None,
    install_deps: bool = True,
    dev: bool = False,
    create_artifact: bool = True
) -> Dict[str, Any]:
    """
    Complete project setup flow using UV with Prefect tasks.
    
    Args:
        project_path: Project root directory
        python_version: Specific Python version to use
        install_deps: Whether to install dependencies
        dev: Whether to install development dependencies
        create_artifact: Whether to create a setup report artifact
        
    Returns:
        Setup result information
    """
    logger = _get_logger()
    project_path = Path(project_path)
    
    results = {
        "project_path": str(project_path),
        "timestamp": datetime.now().isoformat(),
        "steps": []
    }
    
    # Check UV availability
    uv_check = check_uv_available()
    results["uv_info"] = uv_check
    
    if not uv_check["available"]:
        results["success"] = False
        results["error"] = "UV is not available"
        return results
    
    # Detect Python version if not specified
    if not python_version:
        python_version = detect_python_version(project_path)
        if python_version:
            results["detected_python_version"] = python_version
            logger.info(f"Detected Python version: {python_version}")
    
    # Ensure Python version is available
    if python_version:
        try:
            python_path = ensure_python_version(python_version)
            results["python_path"] = str(python_path)
            results["steps"].append({
                "step": "ensure_python",
                "success": True,
                "version": python_version,
                "path": str(python_path)
            })
        except Exception as e:
            results["steps"].append({
                "step": "ensure_python",
                "success": False,
                "error": str(e)
            })
            results["success"] = False
            return results
    
    # Create virtual environment
    try:
        venv_path = create_virtual_environment(project_path, python_version)
        results["venv_path"] = str(venv_path)
        results["steps"].append({
            "step": "create_venv",
            "success": True,
            "path": str(venv_path)
        })
    except Exception as e:
        results["steps"].append({
            "step": "create_venv",
            "success": False,
            "error": str(e)
        })
        results["success"] = False
        return results
    
    # Install dependencies
    if install_deps:
        try:
            deps_result = install_dependencies(project_path, dev=dev)
            results["steps"].append({
                "step": "install_dependencies",
                "success": deps_result["success"],
                "method": deps_result.get("method"),
                "message": deps_result.get("message")
            })
        except Exception as e:
            results["steps"].append({
                "step": "install_dependencies",
                "success": False,
                "error": str(e)
            })
    
    # Generate lock file if needed
    lock_file = project_path / "uv.lock"
    if not lock_file.exists() and (project_path / "pyproject.toml").exists():
        try:
            lock_path = generate_lock_file(project_path)
            results["steps"].append({
                "step": "generate_lock",
                "success": True,
                "path": str(lock_path)
            })
        except Exception as e:
            results["steps"].append({
                "step": "generate_lock",
                "success": False,
                "error": str(e)
            })
    
    # Set overall success
    results["success"] = all(
        step.get("success", False) for step in results["steps"]
    )
    
    # Create artifact if requested
    if create_artifact:
        report = f"""# UV Project Setup Report

**Project**: {project_path}
**Timestamp**: {results['timestamp']}
**Success**: {'✅' if results['success'] else '❌'}

## UV Information
- **Available**: {'Yes' if uv_check['available'] else 'No'}
- **Version**: {uv_check.get('version', 'N/A')}
- **Path**: {uv_check.get('path', 'N/A')}

## Python Configuration
- **Requested Version**: {python_version or 'Auto-detect'}
- **Detected Version**: {results.get('detected_python_version', 'N/A')}
- **Python Path**: {results.get('python_path', 'N/A')}
- **Venv Path**: {results.get('venv_path', 'N/A')}

## Setup Steps
"""
        for step in results["steps"]:
            status = "✅" if step["success"] else "❌"
            report += f"\n### {step['step']} {status}\n"
            if step["success"]:
                for key, value in step.items():
                    if key not in ["step", "success"]:
                        report += f"- **{key}**: {value}\n"
            else:
                report += f"- **Error**: {step.get('error', 'Unknown')}\n"
        
        create_markdown_artifact(
            key="uv-setup-report",
            markdown=report,
            description="UV project setup report"
        )
    
    return results


# Export all tasks and flows
__all__ = [
    "check_uv_available",
    "detect_python_version",
    "list_python_versions",
    "ensure_python_version",
    "create_virtual_environment",
    "install_dependencies",
    "sync_dependencies",
    "pip_install_requirements",
    "pip_install_project",
    "generate_lock_file",
    "add_dependency",
    "remove_dependency",
    "build_project",
    "run_python_script",
    "setup_project_environment",
    "UVTaskError",
]