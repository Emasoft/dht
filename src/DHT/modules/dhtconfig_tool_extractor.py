#!/usr/bin/env python3
"""
dhtconfig_tool_extractor.py - Tool requirements extraction for DHT configuration

This module handles extraction of tool requirements from project analysis.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from dhtconfig.py to reduce file size
# - Contains tool requirements extraction logic
#

from __future__ import annotations

from typing import Any


class ToolRequirementsExtractor:
    """Extracts tool requirements from project analysis."""

    def extract_tool_requirements(self, project_info: dict[str, Any]) -> dict[str, Any]:
        """Extract tool requirements from project analysis."""
        tools = {
            "required": [],
            "optional": []
        }

        # Add tools based on project configuration files
        configs = project_info.get("configurations", {})

        # Version control
        if configs.get("has_git", True):  # Assume git by default
            tools["required"].append({"name": "git"})

        # Build tools
        if configs.get("has_makefile"):
            tools["required"].append({"name": "make"})

        if configs.get("has_cmake"):
            tools["required"].append({"name": "cmake", "version": ">=3.10"})

        # Python tools
        if project_info.get("project_type") == "python":
            tools["required"].extend([
                {"name": "pip"},
                {"name": "setuptools"},
                {"name": "wheel"},
            ])

            # Optional Python tools
            tools["optional"].extend([
                {"name": "pytest", "purpose": "Running tests"},
                {"name": "mypy", "purpose": "Type checking"},
                {"name": "ruff", "purpose": "Linting and formatting"},
                {"name": "black", "purpose": "Code formatting"},
            ])

        # Container tools
        if configs.get("has_dockerfile"):
            tools["optional"].append({
                "name": "docker",
                "purpose": "Container builds"
            })

        return tools


# Export public API
__all__ = ["ToolRequirementsExtractor"]
