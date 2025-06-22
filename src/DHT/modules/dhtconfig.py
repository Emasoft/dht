#!/usr/bin/env python3
"""
Dhtconfig module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Initial implementation of dhtconfig module
# - Implements .dhtconfig generation from project analysis
# - Implements .dhtconfig parsing and validation
# - Integrates with diagnostic_reporter_v2 for system information
# - Integrates with project_analyzer for project analysis
# - Supports platform-specific configurations
# - Implements validation checksum generation
# - Implements configuration merging for platform overrides
# - Refactored to extract functionality into separate modules
#

"""
DHT Configuration Module.

This module handles generation, parsing, and validation of .dhtconfig files.
These files capture exact project requirements for deterministic environment
regeneration across different platforms.
"""

from __future__ import annotations

import platform
from datetime import datetime
from pathlib import Path
from typing import Any

# Import DHT modules - use try/except for flexibility in import paths
try:
    # Try absolute import first (when running as installed package)
    from DHT import diagnostic_reporter_v2
    from DHT.modules import project_analyzer
except ImportError:
    try:
        # Try relative import (when running from within package)
        from .. import diagnostic_reporter_v2
        from . import project_analyzer
    except ImportError:
        # Try direct import (when modules are in path) - already imported above
        pass

# Import extracted modules
from DHT.modules.dhtconfig_build_extractor import BuildConfigExtractor
from DHT.modules.dhtconfig_dependency_extractor import DependencyExtractor
from DHT.modules.dhtconfig_env_extractor import EnvironmentVariablesExtractor
from DHT.modules.dhtconfig_io_utils import ConfigIOUtils
from DHT.modules.dhtconfig_models import DHTConfigConstants, SchemaLoader
from DHT.modules.dhtconfig_platform_utils import PlatformUtils
from DHT.modules.dhtconfig_tool_extractor import ToolRequirementsExtractor
from DHT.modules.dhtconfig_validation_utils import ValidationUtils


class DHTConfig:
    """
    Handles .dhtconfig file generation, parsing, and validation.
    """

    def __init__(self):
        """Initialize DHTConfig handler."""
        self.schema = SchemaLoader.load_schema()
        self.project_analyzer = project_analyzer.ProjectAnalyzer()

        # Add constants as attributes for backward compatibility
        self.SCHEMA_VERSION = DHTConfigConstants.SCHEMA_VERSION
        self.CONFIG_FILENAME = DHTConfigConstants.CONFIG_FILENAME

        # Initialize helper modules
        self.dependency_extractor = DependencyExtractor()
        self.tool_extractor = ToolRequirementsExtractor()
        self.build_extractor = BuildConfigExtractor()
        self.env_extractor = EnvironmentVariablesExtractor()
        self.platform_utils = PlatformUtils()
        self.validation_utils = ValidationUtils()
        self.io_utils = ConfigIOUtils()

    def _extract_version(self, version_output: str) -> str:
        """Extract version from command output (backward compatibility)."""
        return self.validation_utils._extract_version(version_output)

    def _generate_validation_info(self, project_path: Path, config: dict[str, Any]) -> dict[str, Any]:
        """Generate validation info for config (backward compatibility)."""
        return self.validation_utils.generate_validation_info(project_path, config)

    def _extract_dependencies(self, project_info: dict[str, Any]) -> dict[str, Any]:
        """Extract dependencies from project info (backward compatibility)."""
        return self.dependency_extractor.extract_dependencies(project_info)

    def _extract_tool_requirements(self, project_info: dict[str, Any]) -> dict[str, Any]:
        """Extract tool requirements from project info (backward compatibility)."""
        return self.tool_extractor.extract_tool_requirements(project_info)

    def _extract_build_config(self, project_info: dict[str, Any]) -> dict[str, Any]:
        """Extract build config from project info (backward compatibility)."""
        return self.build_extractor.extract_build_config(project_info)

    def _extract_environment_vars(self, project_path: Path) -> dict[str, Any]:
        """Extract environment variables from project path (backward compatibility)."""
        return self.env_extractor.extract_environment_vars(project_path)

    def _deep_merge(self, base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
        """Deep merge dictionaries (backward compatibility)."""
        return self.platform_utils._deep_merge(base, overlay)

    def generate_from_project(
        self, project_path: Path, include_system_info: bool = True, include_checksums: bool = True
    ) -> dict[str, Any]:
        """
        Generate .dhtconfig from project analysis.

        Args:
            project_path: Path to the project root
            include_system_info: Whether to include current system information
            include_checksums: Whether to generate validation checksums

        Returns:
            Generated configuration dictionary
        """
        project_path = Path(project_path).resolve()

        # Analyze the project
        print("Analyzing project structure...")
        project_info = self.project_analyzer.analyze_project(project_path)

        # Get current Python version
        python_version = platform.python_version()

        # Start building config
        config = {
            "version": DHTConfigConstants.SCHEMA_VERSION,
            "project": {
                "name": project_info.get("name", project_path.name),
                "type": project_info.get("project_type", "unknown"),
                "subtypes": project_info.get("project_subtypes", []),
                "generated_at": datetime.now().isoformat(),
                "generated_by": f"DHT {DHTConfigConstants.DHT_VERSION}",
            },
            "python": {
                "version": python_version,
                "implementation": platform.python_implementation().lower(),
                "virtual_env": {
                    "name": ".venv",
                },
            },
            "dependencies": self.dependency_extractor.extract_dependencies(project_info),
            "tools": self.tool_extractor.extract_tool_requirements(project_info),
            "build": self.build_extractor.extract_build_config(project_info),
            "environment": self.env_extractor.extract_environment_vars(project_path),
        }

        # Add platform-specific overrides if we detect differences
        if include_system_info:
            system_info = diagnostic_reporter_v2.build_system_report(
                include_system_info=True, categories=["build_tools", "compilers", "package_managers"]
            )
            config["platform_overrides"] = self.platform_utils.generate_platform_overrides(project_info, system_info)

        # Add validation checksums
        if include_checksums:
            config["validation"] = self.validation_utils.generate_validation_info(project_path, project_info)

        return config

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
        return self.io_utils.save_config(config, project_path, format)

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
        return self.io_utils.load_config(config_path)

    def validate_config(self, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate configuration against schema.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        return self.validation_utils.validate_config(config, self.schema)

    def merge_platform_config(self, base_config: dict[str, Any], platform_name: str | None = None) -> dict[str, Any]:
        """
        Merge platform-specific overrides into base configuration.

        Args:
            base_config: Base configuration dictionary
            platform_name: Platform to merge (None for current platform)

        Returns:
            Merged configuration
        """
        return self.platform_utils.merge_platform_config(base_config, platform_name)


# Export public API
__all__ = ["DHTConfig"]
