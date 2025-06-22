#!/usr/bin/env python3
"""
dhtconfig_platform_utils.py - Platform-specific utilities for DHT configuration  This module handles platform-specific configuration overrides and merging.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
dhtconfig_platform_utils.py - Platform-specific utilities for DHT configuration

This module handles platform-specific configuration overrides and merging.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from dhtconfig.py to reduce file size
# - Contains platform override generation and config merging logic
#

from __future__ import annotations

import copy
import platform
from typing import Any


class PlatformUtils:
    """Handles platform-specific configuration operations."""

    def generate_platform_overrides(self, project_info: dict[str, Any], system_info: dict[str, Any]) -> dict[str, Any]:
        """Generate platform-specific configuration overrides."""
        overrides = {}

        current_platform = platform.system().lower()
        if current_platform == "darwin":
            current_platform = "macos"

        # Add platform-specific system packages
        if current_platform == "macos":
            overrides["macos"] = {
                "dependencies": {
                    "system_packages": [
                        {"name": "xcode-select"},
                    ]
                }
            }
        elif current_platform == "linux":
            overrides["linux"] = {
                "dependencies": {
                    "system_packages": [
                        {"name": "build-essential"},
                        {"name": "python3-dev"},
                        {"name": "python3-venv"},
                    ]
                }
            }
        elif current_platform == "windows":
            overrides["windows"] = {
                "dependencies": {
                    "system_packages": [
                        {"name": "visualstudio2019buildtools"},
                    ]
                },
                "environment": {"required": {"PYTHONIOENCODING": "utf-8"}},
            }

        return overrides

    def merge_platform_config(self, base_config: dict[str, Any], platform_name: str | None = None) -> dict[str, Any]:
        """
        Merge platform-specific overrides into base configuration.

        Args:
            base_config: Base configuration dictionary
            platform_name: Platform to merge (None for current platform)

        Returns:
            Merged configuration
        """
        if platform_name is None:
            platform_name = platform.system().lower()
            if platform_name == "darwin":
                platform_name = "macos"

        # Deep copy base config
        merged = copy.deepcopy(base_config)

        # Apply platform overrides if they exist
        if "platform_overrides" in base_config:
            platform_config = base_config["platform_overrides"].get(platform_name, {})

            # Merge each section
            for section, overrides in platform_config.items():
                if section not in merged:
                    merged[section] = {}

                # Deep merge
                merged[section] = self._deep_merge(merged[section], overrides)

        return merged

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge override into base dictionary and return the result."""
        import copy

        result = copy.deepcopy(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                # Extend lists
                result[key] = result[key] + value
            else:
                result[key] = value

        return result


# Export public API
__all__ = ["PlatformUtils"]
