#!/usr/bin/env python3
from __future__ import annotations

"""
environment_validator.py - Environment validation and verification utilities  This module provides utilities for validating and verifying that environments match expected configurations and dependencies.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
environment_validator.py - Environment validation and verification utilities

This module provides utilities for validating and verifying that environments
match expected configurations and dependencies.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_reproducer.py to reduce file size
# - Contains environment validation and verification functions
#


import re
import subprocess
from pathlib import Path
from typing import Any

from packaging import version
from prefect import get_run_logger, task

from DHT.modules.platform_normalizer import get_tool_command


class EnvironmentValidator:
    """Validates environment configurations and tool versions."""

    def __init__(self) -> None:
        """Initialize the validator."""
        self.version_extractors = {
            "python": self._extract_python_version,
            "pip": self._extract_pip_version,
            "uv": self._extract_uv_version,
            "git": self._extract_git_version,
            "node": self._extract_node_version,
            "npm": self._extract_npm_version,
            "docker": self._extract_docker_version,
        }

    @task(name="verify_python_version")  # type: ignore[misc]
    def verify_python_version(
        self, expected_version: str, python_executable: str | None = None
    ) -> tuple[bool, str, list[str]]:
        """
        Verify Python version matches expected version.

        Returns:
            Tuple of (is_match, actual_version, warnings)
        """
        logger = get_run_logger()
        warnings: list[Any] = []

        try:
            # Get Python version
            if python_executable:
                cmd = [python_executable, "--version"]
            else:
                cmd = ["python3", "--version"]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return False, "unknown", [f"Failed to get Python version: {result.stderr}"]

            # Extract version
            actual_version = self._extract_python_version(result.stdout)
            if not actual_version:
                return False, "unknown", ["Could not parse Python version"]

            # Compare versions
            is_match, version_warnings = self._compare_versions("python", expected_version, actual_version)
            warnings.extend(version_warnings)

            if is_match:
                logger.info(f"Python version verified: {actual_version}")
            else:
                logger.warning(f"Python version mismatch: expected {expected_version}, got {actual_version}")

            return is_match, actual_version, warnings

        except Exception as e:
            return False, "unknown", [f"Error verifying Python version: {str(e)}"]

    @task(name="verify_tools")  # type: ignore[misc]
    def verify_tools(
        self, expected_tools: dict[str, str], platform_name: str | None = None
    ) -> dict[str, dict[str, Any]]:
        """
        Verify tool versions match expected versions.

        Returns:
            Dict mapping tool name to verification result
        """
        logger = get_run_logger()
        results: dict[str, Any] = {}

        for tool, expected_version in expected_tools.items():
            logger.info(f"Verifying {tool} version...")

            # Get tool command for platform
            cmd = get_tool_command(tool, platform_name)
            if not cmd:
                results[tool] = {
                    "installed": False,
                    "version": None,
                    "matched": False,
                    "warning": f"No command mapping for {tool} on this platform",
                }
                continue

            # Check if tool is installed
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    results[tool] = {
                        "installed": False,
                        "version": None,
                        "matched": False,
                        "warning": f"{tool} not found or returned error",
                    }
                    continue

                # Extract version
                output = result.stdout + result.stderr
                actual_version = self._extract_tool_version(tool, output)

                if not actual_version:
                    results[tool] = {
                        "installed": True,
                        "version": "unknown",
                        "matched": False,
                        "warning": f"Could not parse {tool} version from output",
                    }
                    continue

                # Compare versions
                is_match, warnings = self._compare_versions(tool, expected_version, actual_version)

                results[tool] = {
                    "installed": True,
                    "version": actual_version,
                    "matched": is_match,
                    "warnings": warnings,
                }

            except Exception as e:
                results[tool] = {"installed": False, "version": None, "matched": False, "error": str(e)}

        return results

    @task(name="verify_python_packages")  # type: ignore[misc]
    def verify_python_packages(
        self, expected_packages: dict[str, str], python_executable: str | None = None
    ) -> dict[str, dict[str, Any]]:
        """Verify Python package versions."""
        logger = get_run_logger()
        results: dict[str, Any] = {}

        # Get installed packages
        try:
            if python_executable:
                cmd = [python_executable, "-m", "pip", "list", "--format=json"]
            else:
                cmd = ["python3", "-m", "pip", "list", "--format=json"]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Failed to list packages: {result.stderr}")
                return results

            import json

            installed_packages = {pkg["name"].lower(): pkg["version"] for pkg in json.loads(result.stdout)}

        except Exception as e:
            logger.error(f"Error getting installed packages: {e}")
            return results

        # Compare packages
        for package, expected_version in expected_packages.items():
            package_lower = package.lower()

            if package_lower not in installed_packages:
                results[package] = {"installed": False, "version": None, "matched": False}
                continue

            actual_version = installed_packages[package_lower]

            # Simple version comparison
            if expected_version == actual_version:
                results[package] = {"installed": True, "version": actual_version, "matched": True}
            else:
                results[package] = {
                    "installed": True,
                    "version": actual_version,
                    "matched": False,
                    "expected": expected_version,
                }

        return results

    def _extract_tool_version(self, tool: str, output: str) -> str | None:
        """Extract version from tool output."""
        if tool in self.version_extractors:
            return self.version_extractors[tool](output)
        else:
            return self._extract_generic_version(output)

    def _extract_python_version(self, output: str) -> str | None:
        """Extract Python version from output."""
        match = re.search(r"Python (\d+\.\d+\.\d+)", output)
        if match:
            return match.group(1)
        return None

    def _extract_pip_version(self, output: str) -> str | None:
        """Extract pip version from output."""
        match = re.search(r"pip (\d+\.\d+(?:\.\d+)?)", output)
        if match:
            return match.group(1)
        return None

    def _extract_uv_version(self, output: str) -> str | None:
        """Extract uv version from output."""
        match = re.search(r"uv (\d+\.\d+\.\d+)", output)
        if match:
            return match.group(1)
        return None

    def _extract_git_version(self, output: str) -> str | None:
        """Extract git version from output."""
        match = re.search(r"git version (\d+\.\d+\.\d+)", output)
        if match:
            return match.group(1)
        return None

    def _extract_node_version(self, output: str) -> str | None:
        """Extract node version from output."""
        match = re.search(r"v?(\d+\.\d+\.\d+)", output)
        if match:
            return match.group(1)
        return None

    def _extract_npm_version(self, output: str) -> str | None:
        """Extract npm version from output."""
        match = re.search(r"(\d+\.\d+\.\d+)", output)
        if match:
            return match.group(1)
        return None

    def _extract_docker_version(self, output: str) -> str | None:
        """Extract docker version from output."""
        match = re.search(r"Docker version (\d+\.\d+\.\d+)", output)
        if match:
            return match.group(1)
        return None

    def _extract_generic_version(self, output: str) -> str | None:
        """Generic version extraction."""
        # Try common patterns
        patterns = [r"version[:\s]+v?(\d+\.\d+(?:\.\d+)?)", r"v?(\d+\.\d+(?:\.\d+)?)", r"(\d+\.\d+(?:\.\d+)?)"]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _compare_versions(self, tool: str, expected: str, actual: str) -> tuple[bool, list[str]]:
        """
        Compare tool versions with flexibility.

        Returns:
            Tuple of (versions_match, warnings)
        """
        warnings: list[Any] = []

        # Exact match
        if expected == actual:
            return True, warnings

        # Try semantic version comparison
        try:
            expected_v = version.parse(expected)
            actual_v = version.parse(actual)

            # Check major.minor match for Python
            if tool == "python":
                if expected_v.major == actual_v.major and expected_v.minor == actual_v.minor:
                    warnings.append(f"Python patch version differs ({expected} vs {actual}), but major.minor match")
                    return True, warnings

            # For other tools, warn but allow if actual >= expected
            if actual_v >= expected_v:
                warnings.append(f"{tool} version {actual} is newer than expected {expected}")
                return True, warnings
            else:
                warnings.append(f"{tool} version {actual} is older than expected {expected}")
                return False, warnings

        except Exception:
            # Fallback to string comparison
            warnings.append(f"Could not parse versions for {tool}, expected '{expected}' but got '{actual}'")
            return False, warnings

    def verify_configurations(
        self, target_path: Path, expected_configs: dict[str, str], expected_checksums: dict[str, str]
    ) -> dict[str, Any]:
        """
        Verify configuration files match expected content.

        Returns:
            Dict with 'verified' and 'differences' keys
        """
        verified: dict[str, Any] = {}
        differences: dict[str, Any] = {}

        for filename, expected_content in expected_configs.items():
            config_path = target_path / filename

            if not config_path.exists():
                verified[filename] = False
                differences[filename] = "File missing"
                continue

            try:
                actual_content = config_path.read_text(encoding="utf-8")

                # Check content match
                if actual_content == expected_content:
                    verified[filename] = True
                else:
                    verified[filename] = False

                    # Check if we have checksums to compare
                    if filename in expected_checksums:
                        import hashlib

                        actual_checksum = hashlib.sha256(actual_content.encode()).hexdigest()
                        expected_checksum = expected_checksums[filename]

                        if actual_checksum == expected_checksum:
                            differences[filename] = "Content differs but checksum matches (whitespace?)"
                        else:
                            differences[filename] = "Content differs (checksum mismatch)"
                    else:
                        differences[filename] = "Content differs"

            except Exception as e:
                verified[filename] = False
                differences[filename] = f"Read error: {e}"

        return {"verified": verified, "differences": differences}


# Export public API
__all__ = ["EnvironmentValidator"]
