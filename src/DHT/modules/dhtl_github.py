#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_github.sh
# - Implements GitHub commands (clone, fork)
# - Uses gh CLI for GitHub operations
# - Maintains compatibility with shell version
#

"""
DHT GitHub Module.

Provides GitHub repository operations (clone, fork).
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

from .dhtl_error_handling import log_error, log_info, log_success, log_warning


def clone_command(*args, **kwargs) -> int:
    """Clone a GitHub repository."""
    log_info("📥 Cloning GitHub repository...")

    # Check if gh CLI is available
    if not shutil.which("gh"):
        # Fall back to git
        if not shutil.which("git"):
            log_error("Neither gh CLI nor git is installed")
            log_info("Install gh CLI: https://cli.github.com/")
            return 1
        else:
            return git_clone_fallback(args)

    # Parse arguments
    repo_url = None
    target_dir = None
    fork = False

    i = 0
    while i < len(args):
        if args[i] == "--fork":
            fork = True
        elif not repo_url:
            repo_url = args[i]
        elif not target_dir:
            target_dir = args[i]
        i += 1

    if not repo_url:
        log_error("No repository URL provided")
        log_info("Usage: dhtl clone <repo-url> [target-dir] [--fork]")
        return 1

    # Extract owner/repo from URL
    owner_repo = extract_owner_repo(repo_url)
    if not owner_repo:
        log_error(f"Invalid repository URL: {repo_url}")
        return 1

    # Use gh repo clone
    clone_cmd = ["gh", "repo", "clone", owner_repo]

    if target_dir:
        clone_cmd.append(target_dir)

    # Clone the repository
    result = subprocess.run(clone_cmd)

    if result.returncode == 0:
        log_success(f"Repository cloned: {owner_repo}")

        # Fork if requested
        if fork:
            log_info("Creating fork...")
            result = subprocess.run(["gh", "repo", "fork", "--clone=false"])
            if result.returncode == 0:
                log_success("Fork created")
            else:
                log_warning("Failed to create fork (may already exist)")
    else:
        log_error("Failed to clone repository")
        return 1

    # Run dhtl setup if .dhtconfig exists
    clone_dir = Path(target_dir if target_dir else owner_repo.split("/")[-1])
    if (clone_dir / ".dhtconfig").exists():
        log_info("Found .dhtconfig - running dhtl setup...")
        os.chdir(clone_dir)
        from .dhtl_commands import DHTLCommands
        commands = DHTLCommands()
        result = commands.setup(path=str(clone_dir))
        if result.get("success"):
            log_success("Project setup completed")
        else:
            log_warning("Project setup failed")

    return 0


def fork_command(*args, **kwargs) -> int:
    """Fork a GitHub repository."""
    log_info("🍴 Forking GitHub repository...")

    # Check if gh CLI is available
    if not shutil.which("gh"):
        log_error("gh CLI is not installed")
        log_info("Install gh CLI: https://cli.github.com/")
        return 1

    # Parse arguments
    repo_url = None
    clone = True
    remote = True

    i = 0
    while i < len(args):
        if args[i] == "--no-clone":
            clone = False
        elif args[i] == "--no-remote":
            remote = False
        elif not repo_url:
            repo_url = args[i]
        i += 1

    # If no repo URL, try to fork current repo
    if not repo_url:
        # Check if we're in a git repo
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            repo_url = result.stdout.strip()
            log_info(f"Forking current repository: {repo_url}")
        else:
            log_error("No repository URL provided and not in a git repository")
            log_info("Usage: dhtl fork <repo-url> [--no-clone] [--no-remote]")
            return 1

    # Extract owner/repo from URL
    owner_repo = extract_owner_repo(repo_url)
    if not owner_repo:
        log_error(f"Invalid repository URL: {repo_url}")
        return 1

    # Build fork command
    fork_cmd = ["gh", "repo", "fork", owner_repo]

    if not clone:
        fork_cmd.append("--clone=false")

    if not remote:
        fork_cmd.append("--remote=false")

    # Fork the repository
    result = subprocess.run(fork_cmd)

    if result.returncode == 0:
        log_success(f"Repository forked: {owner_repo}")

        # If cloned, run dhtl setup if .dhtconfig exists
        if clone:
            repo_name = owner_repo.split("/")[-1]
            clone_dir = Path(repo_name)
            if (clone_dir / ".dhtconfig").exists():
                log_info("Found .dhtconfig - running dhtl setup...")
                os.chdir(clone_dir)
                from .dhtl_commands import DHTLCommands
                commands = DHTLCommands()
                result = commands.setup(path=str(clone_dir))
                if result.get("success"):
                    log_success("Project setup completed")
                else:
                    log_warning("Project setup failed")
    else:
        log_error("Failed to fork repository")
        return 1

    return 0


def git_clone_fallback(args: list[str]) -> int:
    """Fallback to git clone when gh CLI is not available."""
    log_info("Using git clone (gh CLI not available)...")

    # Parse arguments
    repo_url = None
    target_dir = None

    for arg in args:
        if arg != "--fork" and not repo_url:
            repo_url = arg
        elif arg != "--fork" and not target_dir:
            target_dir = arg

    if not repo_url:
        log_error("No repository URL provided")
        return 1

    # Build git clone command
    clone_cmd = ["git", "clone", repo_url]

    if target_dir:
        clone_cmd.append(target_dir)

    # Clone the repository
    result = subprocess.run(clone_cmd)

    if result.returncode == 0:
        log_success(f"Repository cloned: {repo_url}")
    else:
        log_error("Failed to clone repository")
        return 1

    return 0


def extract_owner_repo(url: str) -> str | None:
    """Extract owner/repo from GitHub URL."""
    # Handle various GitHub URL formats
    patterns = [
        r"github\.com[/:]([^/]+/[^/]+?)(?:\.git)?$",
        r"^([^/]+/[^/]+)$"  # Already in owner/repo format
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1).rstrip("/")

    return None


# For backward compatibility
def placeholder_function():
    """Placeholder function."""
    log_warning("Use clone_command or fork_command instead")
    return True
