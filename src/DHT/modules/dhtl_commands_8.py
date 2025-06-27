#!/usr/bin/env python3
"""
Dhtl Commands 8 module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_commands_8.sh
# - Implements clean command functionality
# - Integrated with DHT command dispatcher
# - Cleans build artifacts and temporary files
#

"""
DHT Clean Commands Module.

Provides project cleanup functionality to remove build artifacts and temporary files.
"""

import os
import shutil
from pathlib import Path

from .common_utils import find_project_root
from .dhtl_error_handling import log_debug, log_info, log_success, log_warning


def clean_command(args: list[str] | None = None) -> int:
    """Clean project by removing build artifacts and temporary files."""
    log_info("🧹 Cleaning project...")

    # Find project root
    project_root = find_project_root()

    # Patterns to clean
    patterns_to_clean = [
        # Python
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".Python",
        "*.so",
        "*.egg",
        "*.egg-info",
        "dist",
        "build",
        "develop-eggs",
        ".eggs",
        "*.egg-link",
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        ".tox",
        ".nox",
        ".hypothesis",
        ".mypy_cache",
        ".ruff_cache",
        # Node.js
        "node_modules",
        "npm-debug.log*",
        "yarn-debug.log*",
        "yarn-error.log*",
        # IDE
        ".idea",
        ".vscode",
        "*.swp",
        "*.swo",
        "*~",
        ".DS_Store",
        "Thumbs.db",
        # Other
        "*.log",
        "*.tmp",
        "*.temp",
        ".cache",
    ]

    # Default args to empty list
    if args is None:
        args = []

    # Keep these directories if --all is not specified
    keep_dirs = {".venv", ".git", ".github", ".env"}

    if "--all" in args:
        log_warning("Cleaning ALL artifacts (including virtual environment)")
        keep_dirs = {".git", ".github"}  # Never delete git
        # Add .venv to patterns when --all is specified
        patterns_to_clean.append(".venv")

    # Count items cleaned
    cleaned_count = 0

    # Clean patterns
    for pattern in patterns_to_clean:
        # Skip if in keep list
        if pattern in keep_dirs:
            continue

        # Use glob to find matches
        if "*" in pattern:
            # It's a glob pattern
            for item in project_root.rglob(pattern):
                if any(keep in item.parts for keep in keep_dirs):
                    continue

                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                        log_debug(f"Removed directory: {item}")
                    else:
                        item.unlink()
                        log_debug(f"Removed file: {item}")
                    cleaned_count += 1
                except Exception as e:
                    log_warning(f"Could not remove {item}: {e}")
        else:
            # It's a specific directory/file name
            for item in project_root.rglob(pattern):
                if any(keep in item.parts for keep in keep_dirs):
                    continue

                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                        log_debug(f"Removed directory: {item}")
                    else:
                        item.unlink()
                        log_debug(f"Removed file: {item}")
                    cleaned_count += 1
                except Exception as e:
                    log_warning(f"Could not remove {item}: {e}")

    # Clean empty directories
    if "--empty-dirs" in args:
        log_info("Removing empty directories...")
        for root, dirs, _files in os.walk(project_root, topdown=False):
            for dirname in dirs:
                dirpath = Path(root) / dirname
                if dirpath.name in keep_dirs:
                    continue

                try:
                    if not any(dirpath.iterdir()):
                        dirpath.rmdir()
                        log_debug(f"Removed empty directory: {dirpath}")
                        cleaned_count += 1
                except Exception:
                    pass  # Directory not empty or permission denied

    if cleaned_count > 0:
        log_success(f"Cleaned {cleaned_count} items")
    else:
        log_info("Nothing to clean")

    return 0


# Export command functions
__all__ = ["clean_command"]
