#!/usr/bin/env python3
"""
dhtconfig_models.py - Data models for DHT configuration

This module contains data models and constants used by the DHT configuration system.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from dhtconfig.py to reduce file size
# - Contains constants and schema-related functionality
#

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


class DHTConfigConstants:
    """Constants for DHT configuration."""

    SCHEMA_VERSION = "1.0.0"
    CONFIG_FILENAME = ".dhtconfig"
    DHT_VERSION = "0.1.0"

    # Lock file patterns
    LOCK_FILE_PATTERNS = {
        "uv": "uv.lock",
        "poetry": "poetry.lock",
        "pipenv": "Pipfile.lock",
        "npm": "package-lock.json",
        "yarn": "yarn.lock",
        "pnpm": "pnpm-lock.yaml",
    }

    # Key files for checksum generation
    KEY_FILES = [
        "requirements.txt",
        "requirements.in",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "package.json",
        "Makefile",
        "CMakeLists.txt",
    ]

    # Tools to check for behavior validation
    TOOLS_TO_CHECK = ["black", "ruff", "mypy", "pytest"]

    # Environment files
    ENV_FILES = [".env", ".env.example", ".env.sample"]


class SchemaLoader:
    """Handles loading of DHT configuration schema."""

    @staticmethod
    def load_schema() -> dict[str, Any] | None:
        """Load the JSON schema for validation."""
        if not HAS_YAML:
            return None

        schema_path = Path(__file__).parent.parent / "schemas" / "dhtconfig_schema.yaml"
        if not schema_path.exists():
            return None

        try:
            with open(schema_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            import sys
            print(f"Warning: Failed to load schema: {e}", file=sys.stderr)
            return None


# Export public API
__all__ = [
    "DHTConfigConstants",
    "SchemaLoader",
    "HAS_YAML",
    "HAS_JSONSCHEMA"
]
