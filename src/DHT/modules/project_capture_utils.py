#!/usr/bin/env python3
"""
project_capture_utils.py - Utilities for capturing project information  This module contains utilities for capturing project-specific information including configuration files, lock files, and project metadata.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
project_capture_utils.py - Utilities for capturing project information

This module contains utilities for capturing project-specific information
including configuration files, lock files, and project metadata.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_reproducer.py to reduce file size
# - Contains project information capture utilities
#

from __future__ import annotations

import hashlib
from pathlib import Path

from prefect import get_run_logger

from DHT.modules.environment_configurator import EnvironmentConfigurator
from DHT.modules.environment_snapshot_models import EnvironmentSnapshot
from DHT.modules.lock_file_manager import LockFileManager


class ProjectCaptureUtils:
    """Utilities for capturing project information."""

    def __init__(self):
        """Initialize project capture utilities."""
        self.logger = None
        self.configurator = EnvironmentConfigurator()
        self.lock_manager = LockFileManager()

    def _get_logger(self):
        """Get logger with fallback."""
        if self.logger is None:
            try:
                self.logger = get_run_logger()
            except Exception:
                import logging

                self.logger = logging.getLogger(__name__)
        return self.logger

    def capture_project_info(self, snapshot: EnvironmentSnapshot, project_path: Path, include_configs: bool):
        """Capture project-specific information."""
        logger = self._get_logger()

        snapshot.project_path = str(project_path)

        # Analyze project with configurator
        try:
            analysis = self.configurator.analyze_environment_requirements(
                project_path=project_path, include_system_info=False
            )

            project_info = analysis.get("project_info", {})
            snapshot.project_type = project_info.get("project_type", "unknown")

        except Exception as e:
            logger.warning(f"Failed to analyze project: {e}")

        # Capture lock files
        self._capture_lock_files(snapshot, project_path)

        # Capture configuration files if requested
        if include_configs:
            self._capture_config_files(snapshot, project_path)

    def _capture_lock_files(self, snapshot: EnvironmentSnapshot, project_path: Path):
        """Capture project lock files."""
        logger = self._get_logger()

        try:
            lock_files_info = self.lock_manager.generate_project_lock_files(project_path, snapshot.project_type)

            for filename, lock_info in lock_files_info.items():
                snapshot.lock_files[filename] = lock_info.content
                snapshot.checksums[filename] = lock_info.checksum
        except Exception as e:
            logger.warning(f"Failed to capture lock files: {e}")

    def _capture_config_files(self, snapshot: EnvironmentSnapshot, project_path: Path):
        """Capture project configuration files."""
        logger = self._get_logger()

        config_files = [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "package.json",
            "tsconfig.json",
            ".python-version",
            ".node-version",
            "ruff.toml",
            "mypy.ini",
            "pytest.ini",
            ".pre-commit-config.yaml",
            ".gitignore",
        ]

        for config_file in config_files:
            config_path = project_path / config_file
            if config_path.exists():
                try:
                    content = config_path.read_text(encoding="utf-8")
                    snapshot.config_files[config_file] = content
                    checksum = hashlib.sha256(content.encode()).hexdigest()
                    snapshot.checksums[config_file] = checksum
                except Exception as e:
                    logger.warning(f"Failed to read {config_file}: {e}")


# Export public API
__all__ = ["ProjectCaptureUtils"]
