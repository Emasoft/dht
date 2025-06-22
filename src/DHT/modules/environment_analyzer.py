#!/usr/bin/env python3
"""
environment_analyzer.py - Environment analysis and requirements detection  This module analyzes project environments and determines requirements.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
environment_analyzer.py - Environment analysis and requirements detection

This module analyzes project environments and determines requirements.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_configurator.py to reduce file size
# - Contains environment analysis and requirement detection functions
#

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from prefect import get_run_logger, task

from DHT.diagnostic_reporter_v2 import build_system_report
from DHT.modules.project_analyzer import ProjectAnalyzer


class EnvironmentAnalyzer:
    """Analyzes project environment and determines requirements."""

    def __init__(self):
        """Initialize the environment analyzer."""
        self.analyzer = ProjectAnalyzer()

        # Tool configuration mapping
        self.tool_configs = {
            "black": {"config_files": ["pyproject.toml", ".black"], "command": "black"},
            "ruff": {"config_files": ["pyproject.toml", "ruff.toml", ".ruff.toml"], "command": "ruff"},
            "mypy": {"config_files": ["mypy.ini", ".mypy.ini", "pyproject.toml"], "command": "mypy"},
            "pytest": {"config_files": ["pytest.ini", "tox.ini", "pyproject.toml"], "command": "pytest"},
            "coverage": {"config_files": [".coveragerc", "pyproject.toml"], "command": "coverage"},
            "pre-commit": {"config_files": [".pre-commit-config.yaml"], "command": "pre-commit"},
        }

    @task(name="analyze_environment_requirements", description="Analyze project and determine environment requirements")
    def analyze_environment_requirements(
        self, project_path: Path, custom_requirements: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Analyze project environment and determine requirements.

        Args:
            project_path: Path to the project directory
            custom_requirements: Optional custom requirements to apply

        Returns:
            Dictionary containing environment analysis and requirements
        """
        logger = get_run_logger()
        logger.info(f"Analyzing environment requirements for {project_path}")

        # Get system information tree
        info_tree = build_system_report()

        # Analyze project structure
        project_info = self.analyzer.analyze_project(project_path)

        # Detect existing tools
        existing_tools = self._detect_tools_from_project(project_path, project_info)

        # Determine requirements
        analysis = {
            "project_path": str(project_path),
            "project_info": project_info,
            "system_info": info_tree,
            "existing_tools": existing_tools,
            "recommended_tools": self._recommend_tools(project_info),
            "system_requirements": self._determine_system_requirements(project_info),
            "python_requirements": self._determine_python_requirements(project_path, project_info),
            "quality_tools": self._recommend_quality_tools(project_info),
            "ci_setup": self._recommend_ci_setup(project_info),
            "platform": info_tree["system"]["platform"],
        }

        # Apply custom requirements if provided
        if custom_requirements:
            for key, value in custom_requirements.items():
                if key in analysis and isinstance(analysis[key], list):
                    analysis[key].extend(value)
                elif key in analysis and isinstance(analysis[key], dict):
                    analysis[key].update(value)
                else:
                    analysis[key] = value

        return analysis

    def _detect_tools_from_project(self, project_path: Path, project_info: dict[str, Any]) -> list[str]:
        """Detect tools already configured in the project."""
        detected = []

        # Check for Python tools in pyproject.toml
        pyproject = project_path / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib

            try:
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)

                # Check tool configurations
                tools_section = data.get("tool", {})
                for tool in ["black", "ruff", "mypy", "pytest", "coverage"]:
                    if tool in tools_section:
                        detected.append(tool)

                # Check dependencies
                project_deps = data.get("project", {}).get("dependencies", [])
                optional_deps = data.get("project", {}).get("optional-dependencies", {})

                for dep_list in [project_deps] + list(optional_deps.values()):
                    for dep in dep_list:
                        dep_name = dep.split("[")[0].split("=")[0].split(">")[0].split("<")[0].strip()
                        if dep_name in self.tool_configs:
                            detected.append(dep_name)

            except Exception as e:
                logger = get_run_logger()
                logger.warning(f"Failed to parse pyproject.toml: {e}")

        # Check for configuration files
        for tool, config in self.tool_configs.items():
            for config_file in config["config_files"]:
                if (project_path / config_file).exists():
                    detected.append(tool)
                    break

        return list(set(detected))

    def _recommend_tools(self, project_info: dict[str, Any]) -> list[str]:
        """Recommend tools based on project type and structure."""
        recommended = []
        project_type = project_info.get("project_type", "unknown")

        if project_type == "python":
            # Core Python development tools
            recommended.extend(["black", "ruff", "mypy", "pytest"])

            # If it's a package/library
            if project_info.get("configurations", {}).get("has_pyproject"):
                recommended.extend(["build", "twine"])

            # Quality tools
            recommended.append("pre-commit")

        elif project_type == "nodejs":
            recommended.extend(["eslint", "prettier", "jest"])

        # Universal tools
        if not project_info.get("configurations", {}).get("has_git"):
            recommended.append("git")

        return recommended

    def _determine_system_requirements(self, project_info: dict[str, Any]) -> list[str]:
        """Determine system-level package requirements."""
        requirements = []
        project_type = project_info.get("project_type", "unknown")
        configs = project_info.get("configurations", {})

        if project_type == "python":
            requirements.extend(["python-dev", "build-essential"])

            # SSL support for pip installs
            requirements.append("openssl")

        if configs.get("has_git", False):
            requirements.append("git")

        if configs.get("has_dockerfile", False):
            requirements.append("docker")

        # Universal tools
        requirements.extend(["curl"])

        return requirements

    def _determine_python_requirements(self, project_path: Path, project_info: dict[str, Any]) -> dict[str, Any]:
        """Determine Python version and package requirements."""
        requirements = {"version": None, "runtime_packages": [], "dev_packages": [], "build_packages": []}

        # Detect Python version
        if project_info.get("project_type") == "python":
            # Try to detect from project files
            version = None

            # Check .python-version
            python_version_file = project_path / ".python-version"
            if python_version_file.exists():
                try:
                    version = python_version_file.read_text().strip()
                except OSError as e:
                    # Continue without version if file can't be read
                    print(f"Warning: Could not read .python-version: {e}")

            # Check pyproject.toml
            if not version:
                pyproject = project_path / "pyproject.toml"
                if pyproject.exists():
                    try:
                        import tomllib
                    except ImportError:
                        import tomli as tomllib

                    try:
                        with open(pyproject, "rb") as f:
                            data = tomllib.load(f)

                        requires_python = data.get("project", {}).get("requires-python")
                        if requires_python:
                            # Extract minimum version
                            match = re.search(r">=?\s*(\d+\.\d+)", requires_python)
                            if match:
                                version = match.group(1)
                    except (OSError, tomllib.TOMLDecodeError) as e:
                        # Continue without version if pyproject.toml can't be parsed
                        print(f"Warning: Could not parse pyproject.toml: {e}")

            requirements["version"] = version or "3.11"  # Default to 3.11

            # Standard development packages
            requirements["dev_packages"] = ["pip", "setuptools", "wheel", "build"]

            # Build packages for compiled extensions
            requirements["build_packages"] = ["Cython", "pybind11"]

        return requirements

    def _recommend_quality_tools(self, project_info: dict[str, Any]) -> dict[str, Any]:
        """Recommend quality and testing tools."""
        quality = {"linting": [], "formatting": [], "testing": [], "type_checking": [], "pre_commit": False}

        project_type = project_info.get("project_type", "unknown")

        if project_type == "python":
            quality["linting"] = ["ruff", "flake8"]
            quality["formatting"] = ["black", "isort"]
            quality["testing"] = ["pytest", "coverage"]
            quality["type_checking"] = ["mypy"]
            quality["pre_commit"] = True

        elif project_type == "nodejs":
            quality["linting"] = ["eslint"]
            quality["formatting"] = ["prettier"]
            quality["testing"] = ["jest", "mocha"]
            quality["type_checking"] = ["typescript"]
            quality["pre_commit"] = True

        return quality

    def _recommend_ci_setup(self, project_info: dict[str, Any]) -> dict[str, Any]:
        """Recommend CI/CD setup based on project structure."""
        ci_config = {"recommended": False, "platforms": [], "workflows": [], "matrix_testing": False}

        # If it's a substantial project, recommend CI
        configs = project_info.get("configurations", {})
        if configs.get("has_tests") or configs.get("has_pyproject"):
            ci_config["recommended"] = True
            ci_config["platforms"] = ["github_actions", "gitlab_ci"]

            project_type = project_info.get("project_type", "unknown")
            if project_type == "python":
                ci_config["workflows"] = ["test", "lint", "build"]
                ci_config["matrix_testing"] = True  # Multiple Python versions
            elif project_type == "nodejs":
                ci_config["workflows"] = ["test", "lint", "build"]
                ci_config["matrix_testing"] = True  # Multiple Node versions

        return ci_config
