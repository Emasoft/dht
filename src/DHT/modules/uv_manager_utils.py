#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
uv_manager_utils.py - Utility functions for UV Manager

This module contains utility functions used by the UV Manager.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from uv_manager.py to reduce file size
# - Contains UV executable discovery, version checking, and command execution
#

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

from DHT.modules.uv_manager_exceptions import UVError, UVNotFoundError


# Development dependency patterns for intelligent classification
DEV_DEPENDENCY_PATTERNS = {
    "testing": ["pytest", "unittest", "mock", "coverage", "tox", "nose", "hypothesis"],
    "linting": ["flake8", "pylint", "pycodestyle", "pydocstyle", "bandit", "ruff"],
    "formatting": ["black", "autopep8", "yapf", "isort"],
    "type_checking": ["mypy", "pytype", "pyre-check", "pyright"],
    "documentation": ["sphinx", "mkdocs", "pdoc", "pydoc-markdown"],
    "development": ["pre-commit", "ipython", "jupyter", "notebook", "ipdb"],
}


def find_uv_executable(logger: logging.Logger) -> Optional[Path]:
    """Find UV executable in PATH or common locations."""
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
    
    logger.warning("UV executable not found in PATH or common locations")
    return None


def verify_uv_version(uv_path: Path, min_version: str, run_command_func) -> None:
    """Verify UV version meets minimum requirements."""
    logger = logging.getLogger(__name__)
    try:
        result = run_command_func(["--version"])
        version_output = result["stdout"].strip()
        # Parse version from output like "uv 0.4.27"
        version = version_output.split()[-1]
        
        if not version_meets_minimum(version, min_version):
            raise UVError(
                f"UV version {version} is below minimum required {min_version}"
            )
        
        logger.info(f"UV version {version} verified")
    except Exception as e:
        logger.error(f"Failed to verify UV version: {e}")
        raise


def version_meets_minimum(version: str, minimum: str) -> bool:
    """Check if version meets minimum requirement."""
    def parse_version(v: str) -> Tuple[int, ...]:
        return tuple(int(x) for x in v.split('.'))
    
    try:
        return parse_version(version) >= parse_version(minimum)
    except ValueError:
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not parse version: {version}")
        return True  # Assume it's okay if we can't parse


def load_toml(file_path: Path) -> Dict[str, Any]:
    """
    Load TOML file with Python version compatibility.
    
    Args:
        file_path: Path to TOML file
        
    Returns:
        Parsed TOML data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If parsing fails
    """
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
        
    with open(file_path, "rb") as f:
        return tomllib.load(f)


def is_dev_dependency(package_name: str) -> bool:
    """
    Check if a package is likely a development dependency.
    
    Args:
        package_name: Name of the package
        
    Returns:
        True if package is likely a dev dependency
    """
    package_lower = package_name.lower()
    
    # Check against known patterns
    for category, patterns in DEV_DEPENDENCY_PATTERNS.items():
        for pattern in patterns:
            if pattern in package_lower:
                return True
    
    # Check for common dev dependency prefixes
    dev_prefixes = ["pytest-", "flake8-", "mypy-", "sphinx-"]
    for prefix in dev_prefixes:
        if package_lower.startswith(prefix):
            return True
    
    return False


def run_uv_command(
    uv_path: Path,
    args: List[str], 
    cwd: Optional[Path] = None,
    capture_output: bool = True,
    check: bool = True,
    timeout: int = 300  # 5 minutes default
) -> Dict[str, Any]:
    """
    Run UV command and return structured output.
    
    Args:
        uv_path: Path to UV executable
        args: Command arguments (without 'uv' prefix)
        cwd: Working directory for command
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise on non-zero exit code
        timeout: Command timeout in seconds
        
    Returns:
        Dict with 'stdout', 'stderr', 'returncode', and 'success' keys
        
    Raises:
        UVNotFoundError: If UV is not available
    """
    logger = logging.getLogger(__name__)
    
    if not uv_path or not uv_path.exists():
        raise UVNotFoundError("UV is not available. Please install UV first.")
    
    cmd = [str(uv_path)] + args
    
    logger.debug(f"Running UV command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            check=check,
            timeout=timeout
        )
        
        return {
            "stdout": result.stdout if capture_output else "",
            "stderr": result.stderr if capture_output else "",
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "stdout": e.stdout if capture_output else "",
            "stderr": e.stderr if capture_output else "",
            "returncode": e.returncode,
            "success": False
        }
    except subprocess.TimeoutExpired as e:
        logger.error(f"UV command timed out after {timeout} seconds")
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "returncode": -1,
            "success": False
        }
    except Exception as e:
        logger.error(f"Unexpected error running UV command: {e}")
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "success": False
        }


def extract_min_version(constraint: str) -> str:
    """
    Extract minimum version from constraint string.
    
    Args:
        constraint: Version constraint (e.g., ">=3.8,<4.0")
        
    Returns:
        Minimum version string (e.g., "3.8")
    """
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
    
    # Default to 3.8
    return "3.8"