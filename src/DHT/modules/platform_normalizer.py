#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
platform_normalizer.py - Platform normalization and abstraction utilities

This module handles platform-specific differences and provides normalized 
interfaces for cross-platform compatibility.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_reproducer.py to reduce file size
# - Contains platform compatibility checking and normalization functions
#

from __future__ import annotations

import platform
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from prefect import task


# Platform-specific tool mappings
TOOL_COMMAND_MAPPINGS = {
    "git": {
        "darwin": ["git", "--version"],
        "linux": ["git", "--version"],
        "windows": ["git.exe", "--version"]
    },
    "python": {
        "darwin": ["python3", "--version"],
        "linux": ["python3", "--version"],
        "windows": ["python.exe", "--version"]
    },
    "pip": {
        "darwin": ["python3", "-m", "pip", "--version"],
        "linux": ["python3", "-m", "pip", "--version"],
        "windows": ["python.exe", "-m", "pip", "--version"]
    },
    "uv": {
        "darwin": ["uv", "--version"],
        "linux": ["uv", "--version"],
        "windows": ["uv.exe", "--version"]
    },
    "docker": {
        "darwin": ["docker", "--version"],
        "linux": ["docker", "--version"],
        "windows": ["docker.exe", "--version"]
    },
    "node": {
        "darwin": ["node", "--version"],
        "linux": ["node", "--version"],
        "windows": ["node.exe", "--version"]
    },
    "npm": {
        "darwin": ["npm", "--version"],
        "linux": ["npm", "--version"],
        "windows": ["npm.exe", "--version"]
    }
}

# Platform-specific path separators and conventions
PATH_CONVENTIONS = {
    "darwin": {
        "separator": ":",
        "home": "$HOME",
        "config_dir": "$HOME/.config",
        "cache_dir": "$HOME/.cache"
    },
    "linux": {
        "separator": ":",
        "home": "$HOME",
        "config_dir": "$HOME/.config",
        "cache_dir": "$HOME/.cache"
    },
    "windows": {
        "separator": ";",
        "home": "%USERPROFILE%",
        "config_dir": "%APPDATA%",
        "cache_dir": "%LOCALAPPDATA%"
    }
}


def get_platform_info() -> Dict[str, str]:
    """Get normalized platform information."""
    return {
        "system": platform.system().lower(),
        "architecture": platform.machine().lower(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown"
    }


def normalize_platform_name(platform_name: str) -> str:
    """Normalize platform name to standard format."""
    platform_map = {
        "darwin": "darwin",
        "macos": "darwin",
        "mac": "darwin",
        "osx": "darwin",
        "linux": "linux",
        "linux2": "linux",
        "windows": "windows",
        "win32": "windows",
        "win64": "windows",
        "cygwin": "windows"
    }
    return platform_map.get(platform_name.lower(), platform_name.lower())


def get_platform_conventions() -> Dict[str, str]:
    """Get platform-specific conventions."""
    current_platform = normalize_platform_name(platform.system())
    return PATH_CONVENTIONS.get(current_platform, PATH_CONVENTIONS["linux"])


def normalize_path(path: str) -> str:
    """Normalize path for current platform."""
    path_obj = Path(path)
    
    # Convert to absolute path
    if not path_obj.is_absolute():
        path_obj = path_obj.resolve()
    
    # Use forward slashes on all platforms for consistency
    return str(path_obj).replace('\\', '/')


def get_tool_command(tool: str, platform_name: Optional[str] = None) -> Optional[List[str]]:
    """Get platform-specific command for a tool."""
    if platform_name is None:
        platform_name = normalize_platform_name(platform.system())
    else:
        platform_name = normalize_platform_name(platform_name)
    
    tool_commands = TOOL_COMMAND_MAPPINGS.get(tool, {})
    return tool_commands.get(platform_name)


@task(name="verify_platform_compatibility")
def verify_platform_compatibility(
    snapshot_platform: str,
    current_platform: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Verify platform compatibility between snapshot and current system.
    
    Returns:
        Tuple of (is_compatible, list_of_warnings)
    """
    if current_platform is None:
        current_platform = platform.system().lower()
    
    snapshot_platform = normalize_platform_name(snapshot_platform)
    current_platform = normalize_platform_name(current_platform)
    
    warnings = []
    
    # Same platform = fully compatible
    if snapshot_platform == current_platform:
        return True, []
    
    # Check cross-platform compatibility
    compatible_pairs = [
        ("darwin", "linux"),  # macOS <-> Linux usually compatible
        ("linux", "darwin"),
    ]
    
    if (snapshot_platform, current_platform) in compatible_pairs:
        warnings.append(
            f"Platform differs ({snapshot_platform} -> {current_platform}), "
            "but environments are generally compatible"
        )
        return True, warnings
    
    # Windows has more compatibility issues
    if "windows" in [snapshot_platform, current_platform]:
        warnings.append(
            f"Platform differs significantly ({snapshot_platform} -> {current_platform}), "
            "some tools and configurations may need adjustment"
        )
        warnings.append("Consider using WSL2 on Windows for better compatibility")
        return True, warnings  # Still allow, but with warnings
    
    return True, warnings


def normalize_environment_variables(env_vars: Dict[str, str]) -> Dict[str, str]:
    """Normalize environment variables for current platform."""
    current_platform = normalize_platform_name(platform.system())
    normalized = {}
    
    for key, value in env_vars.items():
        # Skip platform-specific variables
        if any(skip in key for skip in ["WINDIR", "SYSTEMROOT", "PROGRAMFILES"]):
            if current_platform != "windows":
                continue
        
        # Normalize paths in values
        if any(path_indicator in value for path_indicator in ["/", "\\", os.pathsep]):
            if os.pathsep in value:
                # Multiple paths
                paths = value.split(os.pathsep)
                normalized_paths = [normalize_path(p) for p in paths if p]
                value = os.pathsep.join(normalized_paths)
            else:
                # Single path
                value = normalize_path(value)
        
        normalized[key] = value
    
    return normalized


def get_home_directory() -> Path:
    """Get home directory in a platform-independent way."""
    return Path.home()


def get_config_directory() -> Path:
    """Get configuration directory in a platform-independent way."""
    if platform.system() == "Windows":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config)
        return Path.home() / ".config"


def get_cache_directory() -> Path:
    """Get cache directory in a platform-independent way."""
    if platform.system() == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        xdg_cache = os.environ.get("XDG_CACHE_HOME")
        if xdg_cache:
            return Path(xdg_cache)
        return Path.home() / ".cache"