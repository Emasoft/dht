#!/usr/bin/env python3
"""
tool_version_manager.py - Tool version management and comparison

This module handles tool version extraction, comparison, and installation
suggestions for cross-platform environment reproduction.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_reproducer.py to reduce file size
# - Contains tool version extraction and comparison logic
# - Provides platform-specific installation commands
#

from __future__ import annotations

import platform
import re
import shutil
import subprocess
from typing import Any

from prefect import get_run_logger, task


class ToolVersionManager:
    """Manages tool versions for environment reproduction."""

    def __init__(self):
        """Initialize the tool version manager."""
        # Critical tools that must match versions exactly
        self.version_critical_tools = {
            "python", "pip", "uv", "git", "node", "npm",
            "black", "ruff", "mypy", "pytest"
        }

        # Tools where behavior compatibility is more important than exact versions
        self.behavior_compatible_tools = {
            "curl", "wget", "tar", "zip", "make", "gcc", "clang"
        }

        # Installation commands by platform
        self.installation_commands = {
            "darwin": {
                "git": "brew install git",
                "node": "brew install node",
                "uv": "curl -LsSf https://astral.sh/uv/install.sh | sh",
                "docker": "brew install --cask docker",
                "python": "brew install python@{version}",
                "black": "uv pip install black",
                "ruff": "uv pip install ruff",
                "mypy": "uv pip install mypy",
                "pytest": "uv pip install pytest"
            },
            "linux": {
                "git": "apt-get install git",  # Ubuntu/Debian
                "node": "apt-get install nodejs npm",
                "uv": "curl -LsSf https://astral.sh/uv/install.sh | sh",
                "docker": "apt-get install docker.io",
                "python": "apt-get install python{version}",
                "black": "uv pip install black",
                "ruff": "uv pip install ruff",
                "mypy": "uv pip install mypy",
                "pytest": "uv pip install pytest"
            },
            "windows": {
                "git": "choco install git",
                "node": "choco install nodejs",
                "uv": "powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"",
                "docker": "choco install docker-desktop",
                "python": "choco install python --version={version}",
                "black": "uv pip install black",
                "ruff": "uv pip install ruff",
                "mypy": "uv pip install mypy",
                "pytest": "uv pip install pytest"
            }
        }

    @task(name="capture_tool_versions")
    def capture_tool_versions(self) -> dict[str, dict[str, str]]:
        """Capture versions of all installed development tools."""
        logger = get_run_logger()
        tools_info = {}

        # Define tools to check with their version commands
        tools_to_check = {
            "git": ["git", "--version"],
            "uv": ["uv", "--version"],
            "node": ["node", "--version"],
            "npm": ["npm", "--version"],
            "docker": ["docker", "--version"],
            "make": ["make", "--version"],
            "gcc": ["gcc", "--version"],
            "clang": ["clang", "--version"],
            "python": ["python", "--version"],
            "pip": ["pip", "--version"],
            "black": ["black", "--version"],
            "ruff": ["ruff", "--version"],
            "mypy": ["mypy", "--version"],
            "pytest": ["pytest", "--version"],
        }

        for tool_name, version_cmd in tools_to_check.items():
            try:
                # Check if tool is available
                tool_path = shutil.which(version_cmd[0])
                if tool_path:
                    # Get version
                    result = subprocess.run(
                        version_cmd,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    if result.returncode == 0:
                        version = self.extract_version_from_output(
                            result.stdout + result.stderr
                        )
                        if version:
                            tools_info[tool_name] = {
                                "version": version,
                                "path": tool_path
                            }

            except Exception as e:
                logger.debug(f"Failed to check {tool_name}: {e}")

        return tools_info

    def extract_version_from_output(self, output: str) -> str | None:
        """Extract version number from tool output."""
        # Common version patterns
        patterns = [
            r'(\d+\.\d+\.\d+)',           # x.y.z
            r'(\d+\.\d+)',                # x.y
            r'v(\d+\.\d+\.\d+)',          # vx.y.z
            r'version (\d+\.\d+\.\d+)',   # version x.y.z
        ]

        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1)

        return None

    def compare_versions(
        self,
        expected: str,
        actual: str,
        tool: str,
        strict_mode: bool
    ) -> bool:
        """Compare versions with appropriate tolerance."""
        if expected == actual:
            return True

        # For critical tools, require exact match in strict mode
        if strict_mode and tool in self.version_critical_tools:
            return False

        # For behavior-compatible tools, allow different versions
        if tool in self.behavior_compatible_tools:
            return True

        # For other tools, check semantic compatibility
        try:
            expected_parts = [int(x) for x in expected.split(".")]
            actual_parts = [int(x) for x in actual.split(".")]

            # Same major version is usually compatible
            if len(expected_parts) >= 1 and len(actual_parts) >= 1:
                return expected_parts[0] == actual_parts[0]

        except ValueError:
            # Non-numeric versions, fall back to string comparison
            pass

        return not strict_mode

    def get_installation_command(
        self,
        tool: str,
        version: str | None = None,
        platform_name: str | None = None
    ) -> str | None:
        """Get platform-specific installation command for a tool."""
        if platform_name is None:
            platform_name = platform.system().lower()

        platform_commands = self.installation_commands.get(platform_name, {})
        command = platform_commands.get(tool)

        if command and version and "{version}" in command:
            # Format version for the command
            if tool == "python":
                # Python version formatting varies by platform
                if platform_name == "darwin":
                    # brew wants major.minor format
                    version_parts = version.split(".")
                    if len(version_parts) >= 2:
                        version = f"{version_parts[0]}.{version_parts[1]}"
                elif platform_name == "linux":
                    # apt wants major.minor format without dots
                    version_parts = version.split(".")
                    if len(version_parts) >= 2:
                        version = f"{version_parts[0]}.{version_parts[1]}"

            command = command.format(version=version)

        return command

    @task(name="verify_tool_compatibility")
    def verify_tool_compatibility(
        self,
        expected_tools: dict[str, str],
        actual_tools: dict[str, str],
        strict_mode: bool = True
    ) -> dict[str, dict[str, Any]]:
        """Verify tool compatibility between environments."""
        logger = get_run_logger()
        results = {}

        for tool, expected_version in expected_tools.items():
            if tool not in actual_tools:
                results[tool] = {
                    "compatible": False,
                    "reason": "Tool not installed",
                    "expected": expected_version,
                    "actual": None,
                    "action": self.get_installation_command(tool, expected_version)
                }
                continue

            actual_version = actual_tools[tool]
            compatible = self.compare_versions(
                expected_version, actual_version, tool, strict_mode
            )

            results[tool] = {
                "compatible": compatible,
                "expected": expected_version,
                "actual": actual_version
            }

            if not compatible:
                if tool in self.version_critical_tools:
                    results[tool]["reason"] = "Version must match exactly"
                else:
                    results[tool]["reason"] = "Version incompatible"

                results[tool]["action"] = self.get_installation_command(
                    tool, expected_version
                )

        return results


# Export public API
__all__ = ["ToolVersionManager"]
