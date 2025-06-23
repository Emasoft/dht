#!/usr/bin/env python3
from __future__ import annotations

"""
dhtconfig_env_extractor.py - Environment variables extraction for DHT configuration  This module handles extraction of environment variables from project files.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
dhtconfig_env_extractor.py - Environment variables extraction for DHT configuration

This module handles extraction of environment variables from project files.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from dhtconfig.py to reduce file size
# - Contains environment variables extraction logic
#


from pathlib import Path
from typing import Any

from DHT.modules.dhtconfig_models import DHTConfigConstants


class EnvironmentVariablesExtractor:
    """Extracts environment variables from project files."""

    def extract_environment_vars(self, project_path: Path) -> dict[str, Any]:
        """Extract environment variables from project."""
        env: dict[str, dict[str, str]] = {"required": {}, "optional": {}}

        # Check for .env files
        for env_file in DHTConfigConstants.ENV_FILES:
            env_path = project_path / env_file
            if env_path.exists():
                try:
                    with open(env_path) as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                key, value = line.split("=", 1)
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")

                                # Determine if required or optional based on value
                                if value in ("", "CHANGE_ME", "YOUR_VALUE_HERE"):
                                    env["required"][key] = ""
                                else:
                                    env["optional"][key] = value
                except Exception:
                    pass

        return env


# Export public API
__all__ = ["EnvironmentVariablesExtractor"]
