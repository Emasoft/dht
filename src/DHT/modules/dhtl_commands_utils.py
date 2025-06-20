#!/usr/bin/env python3
"""
dhtl_commands_utils.py - Shared utilities for dhtl commands

This module contains utilities shared by multiple dhtl command modules.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Created to share common functionality between command modules
# - Contains parse_requirements and other shared utilities
#

from pathlib import Path


def parse_requirements(requirements_path: Path) -> list[str]:
    """Parse requirements.txt file and return list of dependencies.

    Args:
        requirements_path: Path to requirements.txt file

    Returns:
        List of dependency strings

    Raises:
        OSError: If file cannot be read
    """
    deps = []
    try:
        with open(requirements_path) as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    # Handle inline comments
                    if "#" in line:
                        line = line.split("#")[0].strip()
                    if line:
                        deps.append(line)
    except OSError as e:
        # Log error but return empty list
        print(f"Warning: Could not read requirements file: {e}")
        return []
    return deps


def count_site_packages(venv_path: Path) -> int:
    """Count installed packages in a virtual environment.

    Args:
        venv_path: Path to the virtual environment

    Returns:
        Number of installed packages
    """
    site_packages = venv_path / "lib"
    package_count = 0

    if site_packages.exists():
        # Look for python directories (python3.X)
        for python_dir in site_packages.iterdir():
            if python_dir.name.startswith("python"):
                sp_dir = python_dir / "site-packages"
                if sp_dir.exists():
                    # Count .dist-info directories
                    package_count = len(list(sp_dir.glob("*.dist-info")))
                    break

    return package_count


__all__ = ["parse_requirements", "count_site_packages"]
