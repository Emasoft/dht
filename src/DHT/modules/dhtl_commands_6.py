#!/usr/bin/env python3
"""
Dhtl Commands 6 module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_commands_6.sh
# - Implements commit command functionality
# - Integrated with DHT command dispatcher
# - Provides git commit functionality with smart defaults
#

"""
DHT Commit Commands Module.

Provides git commit functionality with smart defaults and automation.
"""

import os
import shutil
import subprocess
from typing import Any

from .common_utils import find_project_root
from .dhtl_error_handling import log_error, log_info, log_success, log_warning


def commit_command(args: list[str] | None = None) -> int:
    """Create a git commit with smart defaults."""
    log_info("💾 Creating git commit...")

    # Find project root
    project_root = find_project_root()

    # Check if git is available
    if not shutil.which("git"):
        log_error("git is not installed")
        return 1

    # Check if we're in a git repo
    git_dir = project_root / ".git"
    if not git_dir.exists():
        log_error("Not in a git repository")
        log_info("Initialize with: git init")
        return 1

    # Change to project root
    os.chdir(project_root)

    # Check for changes
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)

    if not result.stdout.strip():
        log_warning("No changes to commit")
        return 0

    # Show current status
    log_info("Current git status:")
    try:
        subprocess.run(["git", "status", "--short"], check=False)
    except Exception:
        pass  # Non-critical, just for display

    # Default args to empty list
    if args is None:
        args = []

    # Stage all changes if requested
    if "--all" in args or "-a" in args:
        log_info("Staging all changes...")
        add_result: Any = subprocess.run(["git", "add", "-A"])
        if add_result.returncode != 0:
            log_error("Failed to stage changes")
            return 1

    # Get commit message
    message = None
    if "--message" in args or "-m" in args:
        try:
            idx = args.index("--message") if "--message" in args else args.index("-m")
            if idx + 1 < len(args):
                message = args[idx + 1]
        except (ValueError, IndexError):
            pass

    if not message:
        # Try to generate a smart commit message
        result = subprocess.run(["git", "diff", "--cached", "--name-status"], capture_output=True, text=True)

        if result.stdout:
            # Analyze changes
            lines = result.stdout.strip().split("\n")
            added = sum(1 for line in lines if line.startswith("A"))
            modified = sum(1 for line in lines if line.startswith("M"))
            deleted = sum(1 for line in lines if line.startswith("D"))

            parts = []
            if added:
                parts.append(f"Add {added} file{'s' if added > 1 else ''}")
            if modified:
                parts.append(f"Update {modified} file{'s' if modified > 1 else ''}")
            if deleted:
                parts.append(f"Remove {deleted} file{'s' if deleted > 1 else ''}")

            if parts:
                message = ", ".join(parts)
            else:
                message = "Update project files"
        else:
            message = "Update project files"

    # Create commit
    log_info(f"Creating commit: {message}")
    try:
        result = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True, check=False)
    except KeyboardInterrupt:
        log_warning("Commit interrupted by user")
        return 130
    except Exception as e:
        log_error(f"Failed to create commit: {e}")
        return 1

    if result.returncode == 0:
        log_success("Commit created successfully!")
        # Show the commit
        try:
            subprocess.run(["git", "log", "--oneline", "-1"], check=False)
        except Exception:
            pass  # Non-critical, just for display
    else:
        log_error("Failed to create commit")
        if result.stderr:
            log_error(result.stderr)
        return 1

    return 0


# Export command functions
__all__ = ["commit_command"]
