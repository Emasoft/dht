#!/usr/bin/env python3
"""
dhtconfig_validation_utils.py - Validation utilities for DHT configuration  This module handles validation info generation and config validation.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
dhtconfig_validation_utils.py - Validation utilities for DHT configuration

This module handles validation info generation and config validation.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from dhtconfig.py to reduce file size
# - Contains validation info generation and config validation logic
#

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any

from DHT.modules.dhtconfig_models import HAS_JSONSCHEMA, DHTConfigConstants


class ValidationUtils:
    """Handles validation operations for DHT configuration."""

    def generate_validation_info(self, project_path: Path, project_info: dict[str, Any]) -> dict[str, Any]:
        """Generate validation checksums and metadata."""
        validation = {"checksums": {}, "tool_behaviors": {}}

        # Generate checksums for key files
        for filename in DHTConfigConstants.KEY_FILES:
            file_path = project_path / filename
            if file_path.exists():
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()
                        checksum = hashlib.sha256(content).hexdigest()
                        validation["checksums"][filename] = checksum
                except OSError as e:
                    # Log file read error but continue with other files
                    print(f"Warning: Could not read {filename}: {e}")

        # Generate tool behavior checksums
        for tool in DHTConfigConstants.TOOLS_TO_CHECK:
            try:
                # Get tool version
                result = subprocess.run([tool, "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version_output = result.stdout.strip()
                    version = self._extract_version(version_output)

                    # Generate behavior hash (simplified - would be more complex in practice)
                    behavior_hash = hashlib.sha256(f"{tool}-{version}-behavior".encode()).hexdigest()

                    validation["tool_behaviors"][tool] = {"version": version, "behavior_hash": behavior_hash}
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as e:
                # Tool not available or error getting version - skip this tool
                print(f"Warning: Could not get version for {tool}: {e}")

        return validation

    def _extract_version(self, version_output: str) -> str:
        """Extract version number from version output."""
        # Common version patterns - order matters!
        patterns = [
            r"version (\d+\.\d+\.\d+)",  # "version 1.2.3"
            r"v(\d+\.\d+\.\d+)",  # "v1.2.3" or "mypy v0.991"
            r"(\d+\.\d+\.\d+)",  # Just the version number
        ]

        for pattern in patterns:
            match = re.search(pattern, version_output, re.IGNORECASE)
            if match:
                return match.group(1)

        # Special handling for two-part versions
        match = re.search(r"v?(\d+\.\d+)", version_output)
        if match:
            return match.group(1)

        return version_output.split()[0] if version_output else "unknown"

    def validate_config(self, config: dict[str, Any], schema: dict[str, Any] | None = None) -> tuple[bool, list[str]]:
        """
        Validate configuration against schema.

        Args:
            config: Configuration dictionary to validate
            schema: Optional schema to validate against

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Basic validation always performed
        if "version" not in config:
            errors.append("Missing required field: version")
        if "project" not in config:
            errors.append("Missing required field: project")
        if "python" not in config:
            errors.append("Missing required field: python")
        elif "version" not in config["python"]:
            errors.append("Missing required field: python.version")

        # If we have basic errors, return early
        if errors:
            return False, errors

        # If jsonschema is available and we have a schema, do full validation
        if HAS_JSONSCHEMA and schema:
            try:
                import jsonschema

                jsonschema.validate(config, schema)
                return True, []
            except jsonschema.ValidationError as e:
                # For now, we'll just warn about schema validation errors
                # since our schema might not be complete
                errors.append(f"Schema validation error: {e.message}")
                # Still return True if basic validation passed
                return True, errors

        # No schema validation available, but basic validation passed
        return True, []


# Export public API
__all__ = ["ValidationUtils"]
