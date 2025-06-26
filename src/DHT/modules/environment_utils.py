#!/usr/bin/env python3
"""
DHT Environment Utilities Module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE FILE:
# - Consolidated all duplicate environment modules into one
# - Combined functionality from environment.py, environment_2.py, and dhtl_environment_*.py
# - Provides environment detection, setup, and info display
# - Cross-platform compatible
#

"""
DHT Environment Utilities Module.

Consolidated module for all environment-related functionality.
Replaces multiple duplicate modules with a single source of truth.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

from .common_utils import detect_platform, find_project_root, find_virtual_env
from .dhtl_error_handling import log_info


def setup_environment() -> Dict[str, str]:
    """Set up environment variables for DHT.

    Returns:
        Dictionary of environment variables
    """
    env = os.environ.copy()

    # Add DHT-specific variables
    project_root = find_project_root()
    env["PROJECT_ROOT"] = str(project_root)
    env["PLATFORM"] = detect_platform()

    # Add Python-specific variables
    env["PYTHON_VERSION"] = f"{sys.version_info.major}.{sys.version_info.minor}"
    env["PYTHON_EXECUTABLE"] = sys.executable

    # Virtual environment info
    venv_dir = find_virtual_env(project_root)
    if venv_dir:
        env["VIRTUAL_ENV"] = str(venv_dir)

    # DHT configuration
    dhtconfig = project_root / ".dhtconfig"
    if dhtconfig.exists():
        env["DHT_CONFIG"] = str(dhtconfig)

    return env


def get_environment_info() -> Dict[str, Any]:
    """Get comprehensive environment information.

    Returns:
        Dictionary with environment details
    """
    info: Dict[str, Any] = {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "python": {
            "version": sys.version.split()[0],
            "executable": sys.executable,
            "prefix": sys.prefix,
            "path": sys.path,
        },
        "project": {
            "root": str(find_project_root()),
        },
        "environment": {},
        "git": {},
    }

    # Virtual environment
    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        info["environment"]["virtual_env"] = venv
        info["environment"]["virtual_env_active"] = True
    else:
        project_root = find_project_root()
        venv_dir = find_virtual_env(project_root)
        if venv_dir:
            info["environment"]["virtual_env"] = str(venv_dir)
            info["environment"]["virtual_env_active"] = False

    # DHT environment variables
    dht_vars = {}
    for key, value in os.environ.items():
        if key.startswith(("DHT_", "PROJECT_", "PYTHON_")):
            dht_vars[key] = value
    info["environment"]["dht_variables"] = dht_vars

    # Git information
    project_root = find_project_root()
    git_dir = project_root / ".git"
    if git_dir.exists():
        try:
            # Get current branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, cwd=project_root
            )
            if result.returncode == 0:
                info["git"]["branch"] = result.stdout.strip()

            # Get commit hash
            result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=project_root)
            if result.returncode == 0:
                info["git"]["commit"] = result.stdout.strip()[:8]

            # Check for uncommitted changes
            result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=project_root)
            info["git"]["has_changes"] = bool(result.stdout.strip())

        except Exception:
            pass

    return info


def env_command(*args: Any, **kwargs: Any) -> int:
    """Show environment information command.

    Args:
        *args: Command arguments
        **kwargs: Command options

    Returns:
        Exit code (0 for success)
    """
    log_info("🌍 Environment Information")
    log_info("=" * 50)

    info = get_environment_info()

    # Platform info
    platform_info = info["platform"]
    log_info(f"Platform: {platform_info['system']} {platform_info['release']}")
    log_info(f"Architecture: {platform_info['machine']}")

    # Python info
    python_info = info["python"]
    log_info(f"Python: {python_info['version']} ({python_info['executable']})")

    # Project info
    project_info = info["project"]
    log_info(f"Project root: {project_info['root']}")

    # Virtual environment
    env_info = info["environment"]
    if "virtual_env" in env_info:
        venv_status = "activated" if env_info.get("virtual_env_active") else "not activated"
        log_info(f"Virtual env: {env_info['virtual_env']} ({venv_status})")
    else:
        log_info("Virtual env: None")

    # DHT environment variables
    dht_vars = env_info.get("dht_variables", {})
    if dht_vars:
        log_info("\nDHT Environment Variables:")
        for key, value in sorted(dht_vars.items()):
            log_info(f"  {key}={value}")

    # Git info
    git_info = info.get("git", {})
    if git_info:
        branch = git_info.get("branch", "unknown")
        commit = git_info.get("commit", "unknown")
        changes = " (uncommitted changes)" if git_info.get("has_changes") else ""
        log_info(f"\nGit: {branch} @ {commit}{changes}")

    return 0


def is_virtual_env_active() -> bool:
    """Check if a virtual environment is currently active.

    Returns:
        True if virtual environment is active
    """
    return (
        bool(os.environ.get("VIRTUAL_ENV"))
        or hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
    )


def get_python_version() -> str:
    """Get the current Python version.

    Returns:
        Python version string (e.g., "3.10")
    """
    return f"{sys.version_info.major}.{sys.version_info.minor}"


def ensure_virtual_env() -> Path | None:
    """Ensure a virtual environment exists and return its path.

    Returns:
        Path to virtual environment or None
    """
    project_root = find_project_root()
    venv_dir = find_virtual_env(project_root)

    if not venv_dir:
        # Create .venv if it doesn't exist
        venv_dir = project_root / ".venv"
        if not venv_dir.exists():
            log_info("Creating virtual environment...")
            try:
                subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
                log_info(f"Virtual environment created at: {venv_dir}")
            except subprocess.CalledProcessError:
                return None

    return venv_dir


# Export all functions
__all__ = [
    "setup_environment",
    "get_environment_info",
    "env_command",
    "is_virtual_env_active",
    "get_python_version",
    "ensure_virtual_env",
]
