#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Consolidated common utilities to avoid duplication
# - Contains find_project_root, detect_platform, find_virtual_env
# - Single source of truth for common functionality
# 

"""
DHT Common Utilities Module.

Consolidated utilities to avoid duplication across modules.
"""

import os
import sys
import platform
from pathlib import Path
from typing import Optional


def find_project_root(start_dir: Optional[Path] = None) -> Path:
    """
    Find the project root directory.
    
    Args:
        start_dir: Starting directory for search (default: current directory)
        
    Returns:
        Path to project root directory
    """
    if start_dir is None:
        start_dir = Path.cwd()
    
    current = Path(start_dir).resolve()
    
    # Project markers to look for
    markers = [
        ".git", "package.json", "pyproject.toml", "setup.py",
        "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
        "Gemfile", "composer.json", ".dhtconfig"
    ]
    
    # Traverse up looking for markers
    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent
    
    # If no project root found, use current directory
    return Path.cwd()


def detect_platform() -> str:
    """
    Detect the current platform.
    
    Returns:
        Platform name: "macos", "linux", "windows", "bsd", or "unknown"
    """
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    elif "bsd" in system:
        return "bsd"
    else:
        return "unknown"


def find_virtual_env(project_root: Optional[Path] = None) -> Optional[Path]:
    """
    Find the virtual environment directory.
    
    Args:
        project_root: Project root directory (default: auto-detect)
        
    Returns:
        Path to virtual environment or None if not found
    """
    if project_root is None:
        project_root = find_project_root()
    
    # Check common virtual environment locations
    venv_names = [".venv", "venv", ".venv_windows", "env"]
    
    for venv_name in venv_names:
        venv_path = project_root / venv_name
        if venv_path.is_dir():
            # Check if it's a valid venv
            if (venv_path / "bin").is_dir() or (venv_path / "Scripts").is_dir():
                return venv_path
    
    # Check VIRTUAL_ENV environment variable
    if os.environ.get("VIRTUAL_ENV"):
        return Path(os.environ["VIRTUAL_ENV"])
    
    return None


def setup_environment() -> dict:
    """
    Set up common environment variables.
    
    Returns:
        Dictionary of environment variables
    """
    env = os.environ.copy()
    
    # Add DHT-specific variables
    project_root = find_project_root()
    env["PROJECT_ROOT"] = str(project_root)
    env["PLATFORM"] = detect_platform()
    
    # Virtual environment
    venv = find_virtual_env(project_root)
    if venv:
        env["VIRTUAL_ENV"] = str(venv)
    
    return env