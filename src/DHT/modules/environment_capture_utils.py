#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, cast

"""
environment_capture_utils.py - Utilities for capturing environment details  This module contains utilities for capturing various aspects of the development environment including Python packages, system tools, and environment variables.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
environment_capture_utils.py - Utilities for capturing environment details

This module contains utilities for capturing various aspects of the
development environment including Python packages, system tools, and
environment variables.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_reproducer.py to reduce file size
# - Contains environment capture utilities
#


import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from prefect import get_run_logger

from DHT.modules.environment_snapshot_models import EnvironmentSnapshot
from DHT.modules.uv_prefect_tasks import check_uv_available


class EnvironmentCaptureUtils:
    """Utilities for capturing environment details."""

    def __init__(self) -> None:
        """Initialize environment capture utilities."""
        self.logger: logging.Logger | None = None

    def _get_logger(self) -> logging.Logger:
        """Get logger with fallback."""
        if self.logger is None:
            try:
                self.logger = cast(logging.Logger, get_run_logger())
            except Exception:
                self.logger = logging.getLogger(__name__)
        return self.logger

    def get_dht_version(self) -> str:
        """Get DHT version from pyproject.toml or return development."""
        try:
            # Try to get version from pyproject.toml
            pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                try:
                    import tomllib
                except ImportError:
                    import tomli as tomllib

                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)

                return cast(str, data.get("project", {}).get("version", "unknown"))
        except Exception:
            pass

        return "development"

    def capture_python_packages(self, snapshot: EnvironmentSnapshot) -> Any:
        """Capture Python package information."""
        logger = self._get_logger()

        try:
            # Get installed packages using pip list
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"], capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                packages = json.loads(result.stdout)
                for pkg in packages:
                    snapshot.python_packages[pkg["name"]] = pkg["version"]

        except Exception as e:
            logger.warning(f"Failed to capture Python packages: {e}")

        # Try to get UV packages if available
        try:
            uv_check = check_uv_available()
            if uv_check["available"]:
                # Get UV managed packages
                result = subprocess.run(
                    ["uv", "pip", "list", "--format=json"], capture_output=True, text=True, timeout=30
                )

                if result.returncode == 0:
                    uv_packages = json.loads(result.stdout)
                    for pkg in uv_packages:
                        # UV packages take precedence as they're more precisely managed
                        snapshot.python_packages[pkg["name"]] = pkg["version"]

        except Exception as e:
            logger.debug(f"UV package listing failed: {e}")

    def capture_environment_variables(self, snapshot: EnvironmentSnapshot) -> None:
        """Capture relevant environment variables."""
        # Important environment variables for development
        important_vars = {
            "PATH",
            "PYTHONPATH",
            "VIRTUAL_ENV",
            "CONDA_DEFAULT_ENV",
            "NODE_ENV",
            "UV_PYTHON",
            "PIP_INDEX_URL",
            "PIP_EXTRA_INDEX_URL",
            "PYTHONDONTWRITEBYTECODE",
            "PYTHONUNBUFFERED",
            "CC",
            "CXX",
            "CFLAGS",
            "CXXFLAGS",
        }

        env_vars = {}
        for var in important_vars:
            value = os.environ.get(var)
            if value:
                env_vars[var] = value

        # Import normalization function
        from DHT.modules.platform_normalizer import normalize_environment_variables

        # Normalize environment variables for platform compatibility
        snapshot.environment_variables = normalize_environment_variables(env_vars)

        # Capture PATH entries separately for analysis
        path_var = os.environ.get("PATH", "")
        if path_var:
            snapshot.path_entries = path_var.split(os.pathsep)


# Export public API
__all__ = ["EnvironmentCaptureUtils"]
