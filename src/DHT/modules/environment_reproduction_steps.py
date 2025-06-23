#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

"""
environment_reproduction_steps.py - Generate platform-specific reproduction steps  This module generates detailed reproduction steps based on the environment snapshot and target platform.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
environment_reproduction_steps.py - Generate platform-specific reproduction steps

This module generates detailed reproduction steps based on the environment
snapshot and target platform.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_reproducer.py to reduce file size
# - Contains reproduction step generation logic
#


from DHT.modules.environment_snapshot_models import EnvironmentSnapshot


class ReproductionStepsGenerator:
    """Generates platform-specific reproduction steps."""

    def __init__(self, version_critical_tools: set[Any]) -> None:
        """Initialize the steps generator."""
        self.version_critical_tools = version_critical_tools

    def generate_reproduction_steps(self, snapshot: EnvironmentSnapshot) -> None:
        """Generate platform-specific reproduction steps."""
        steps = []

        # 1. Python version setup
        steps.append(f"Install Python {snapshot.python_version}")
        if "uv" in snapshot.tool_versions:
            steps.append(f"Install UV {snapshot.tool_versions['uv']}")
            steps.append(f"uv python pin {snapshot.python_version}")

        # 2. Create virtual environment
        steps.append("Create virtual environment")
        if "uv" in snapshot.tool_versions:
            steps.append("uv venv")
        else:
            steps.append("python -m venv .venv")

        # 3. Install packages
        if snapshot.lock_files:
            if "uv.lock" in snapshot.lock_files:
                steps.append("uv sync")
            elif "requirements.txt" in snapshot.lock_files:
                steps.append("pip install -r requirements.txt")
            elif "package-lock.json" in snapshot.lock_files:
                steps.append("npm ci")

        # 4. Verify tool versions
        for tool, version in snapshot.tool_versions.items():
            if tool in self.version_critical_tools:
                steps.append(f"Verify {tool} version {version}")

        # 5. Platform-specific notes
        platform_notes = self._generate_platform_notes(snapshot.platform)

        snapshot.reproduction_steps = steps
        snapshot.platform_notes = platform_notes

    def _generate_platform_notes(self, platform: str) -> list[str]:
        """Generate platform-specific notes."""
        platform_notes = []

        if platform == "darwin":
            platform_notes.append("macOS: Use Homebrew for system packages")
            platform_notes.append("Install Xcode Command Line Tools if needed")
        elif platform == "linux":
            platform_notes.append("Linux: Use system package manager (apt/yum/etc)")
            platform_notes.append("Install build-essential if needed")
        elif platform == "windows":
            platform_notes.append("Windows: Use chocolatey or winget")
            platform_notes.append("Install Visual Studio Build Tools if needed")

        return platform_notes


# Export public API
__all__ = ["ReproductionStepsGenerator"]
