#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_environment_2.sh
# - Provides environment detection and setup
# - Cross-platform compatible
# 

"""
DHT Dhtl Environment 2 Module.

Provides environment detection and setup functionality.
"""

import os
import sys
import platform
from pathlib import Path
from typing import Optional, Dict, Any

from .dhtl_error_handling import log_error, log_warning, log_info, log_success
from .common_utils import find_project_root, detect_platform


def setup_environment() -> Dict[str, str]:
    """Set up environment variables."""
    env = os.environ.copy()
    
    # Add DHT-specific variables
    project_root = find_project_root()
    env["PROJECT_ROOT"] = str(project_root)
    env["PLATFORM"] = detect_platform()
    
    return env


def env_command(*args, **kwargs) -> int:
    """Show environment information."""
    log_info("🌍 Environment Information")
    log_info("=" * 50)
    
    # Platform info
    log_info(f"Platform: {platform.system()} {platform.release()}")
    log_info(f"Architecture: {platform.machine()}")
    log_info(f"Python: {sys.version.split()[0]} ({sys.executable})")
    
    # Project info
    project_root = find_project_root()
    log_info(f"Project root: {project_root}")
    
    # Virtual environment
    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        log_info(f"Virtual env: {venv}")
    else:
        # Check for .venv directory
        venv_dir = project_root / ".venv"
        if venv_dir.exists():
            log_info(f"Virtual env: {venv_dir} (not activated)")
        else:
            log_info("Virtual env: None")
    
    # DHT environment variables
    log_info("\nDHT Environment Variables:")
    for key, value in os.environ.items():
        if key.startswith(("DHT_", "PROJECT_", "PYTHON_")):
            log_info(f"  {key}={value}")
    
    # Git info
    git_dir = project_root / ".git"
    if git_dir.exists():
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            if result.returncode == 0:
                log_info(f"\nGit branch: {result.stdout.strip()}")
        except Exception:
            pass
    
    return 0


def placeholder_function(*args, **kwargs):
    """Placeholder for backward compatibility."""
    return env_command(*args, **kwargs)
