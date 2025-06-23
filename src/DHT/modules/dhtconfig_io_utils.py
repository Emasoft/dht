#!/usr/bin/env python3
"""
dhtconfig_io_utils.py - I/O utilities for DHT configuration  This module handles saving and loading of DHT configuration files.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
dhtconfig_io_utils.py - I/O utilities for DHT configuration

This module handles saving and loading of DHT configuration files.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from dhtconfig.py to reduce file size
# - Contains config save/load operations
#

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from DHT.modules.dhtconfig_models import HAS_YAML, DHTConfigConstants

if HAS_YAML:
    import yaml  # type: ignore[import-untyped]


class ConfigIOUtils:
    """Handles I/O operations for DHT configuration files."""

    def save_config(self, config: dict[str, Any], project_path: Path, format: str = "yaml") -> Path:
        """
        Save configuration to .dhtconfig file.

        Args:
            config: Configuration dictionary
            project_path: Project root directory
            format: Output format ("yaml" or "json")

        Returns:
            Path to saved config file
        """
        config_path = project_path / DHTConfigConstants.CONFIG_FILENAME

        if format == "yaml" and HAS_YAML:
            with open(config_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=120)
        else:
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2, sort_keys=False)

        return config_path

    def load_config(self, config_path: Path) -> dict[str, Any]:
        """
        Load and parse .dhtconfig file.

        Args:
            config_path: Path to .dhtconfig file

        Returns:
            Parsed configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path) as f:
                content = f.read()

            # Try YAML first
            if HAS_YAML:
                try:
                    config = yaml.safe_load(content)
                    if config:
                        return config
                except yaml.YAMLError:
                    pass

            # Fall back to JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid config file format: {e}") from e

        except Exception as e:
            raise ValueError(f"Failed to load config: {e}") from e


# Export public API
__all__ = ["ConfigIOUtils"]
