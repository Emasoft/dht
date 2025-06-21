#!/usr/bin/env python3
"""
dhtconfig_dependency_extractor.py - Dependency extraction for DHT configuration

This module handles extraction of dependencies from project analysis.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from dhtconfig.py to reduce file size
# - Contains dependency extraction logic
#

from __future__ import annotations

from pathlib import Path
from typing import Any

from DHT.modules.dhtconfig_models import DHTConfigConstants


class DependencyExtractor:
    """Extracts dependencies from project analysis."""

    def extract_dependencies(self, project_info: dict[str, Any]) -> dict[str, Any]:
        """Extract dependencies from project analysis."""
        deps: dict[str, Any] = {"python_packages": [], "lock_files": {}, "system_packages": []}

        # Extract Python dependencies
        if "dependencies" in project_info:
            project_deps = project_info["dependencies"]

            # Python packages
            if "python" in project_deps:
                python_deps = project_deps["python"]
                # Handle both dict and list formats
                if isinstance(python_deps, dict):
                    # project_analyzer returns a dict with 'runtime', 'development', 'all'
                    for dep_name in python_deps.get("runtime", []):
                        deps["python_packages"].append(
                            {
                                "name": dep_name,
                                "version": "*",
                                "extras": [],
                            }
                        )
                elif isinstance(python_deps, list):
                    # Handle list format
                    for dep in python_deps:
                        if isinstance(dep, dict):
                            deps["python_packages"].append(
                                {
                                    "name": dep["name"],
                                    "version": dep.get("version", "*"),
                                    "extras": dep.get("extras", []),
                                }
                            )
                        elif isinstance(dep, str):
                            deps["python_packages"].append(
                                {
                                    "name": dep,
                                    "version": "*",
                                    "extras": [],
                                }
                            )

        # Check for lock files in the project directory
        project_path = Path(project_info.get("root_path", "."))

        for lock_type, filename in DHTConfigConstants.LOCK_FILE_PATTERNS.items():
            lock_path = project_path / filename
            if lock_path.exists():
                deps["lock_files"][lock_type] = filename

        # Extract system packages based on project type
        if project_info.get("project_type") == "python":
            # Common Python development system packages
            deps["system_packages"].extend(
                [
                    {"name": "python3-dev", "platform": "linux"},
                    {"name": "build-essential", "platform": "linux"},
                    {"name": "xcode-select", "platform": "macos"},
                ]
            )

        return deps


# Export public API
__all__ = ["DependencyExtractor"]
