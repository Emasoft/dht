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


def detect_platform() -> str:
    """Detect the current platform."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"


def find_project_root(start_dir: Optional[Path] = None) -> Path:
    """Find the project root directory."""
    if start_dir is None:
        start_dir = Path.cwd()
    
    current = Path(start_dir).resolve()
    
    # Project markers
    markers = [".git", "pyproject.toml", "package.json", ".dhtconfig"]
    
    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent
    
    return Path.cwd()


def setup_environment() -> Dict[str, str]:
    """Set up environment variables."""
    env = os.environ.copy()
    
    # Add DHT-specific variables
    project_root = find_project_root()
    env["PROJECT_ROOT"] = str(project_root)
    env["PLATFORM"] = detect_platform()
    
    return env
