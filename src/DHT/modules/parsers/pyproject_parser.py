#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pyproject_parser.py - Parser for pyproject.toml files

Handles parsing of:
- PEP 517/518 build system configuration
- PEP 621 project metadata
- Poetry configuration
- UV configuration
- Tool-specific settings
"""

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10 and below
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from .base_parser import BaseParser


class PyProjectParser(BaseParser):
    """
    Parser for pyproject.toml files.

    Supports multiple formats:
    - Standard PEP 621 project metadata
    - Poetry-specific configuration
    - UV-specific configuration
    - Build system requirements
    - Tool configurations (black, isort, pytest, etc.)
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a pyproject.toml file and extract all information.

        Args:
            file_path: Path to pyproject.toml

        Returns:
            Dictionary containing parsed information
        """
        content = self.read_file_safe(file_path)
        if content is None:
            return {"error": f"Could not read file {file_path}"}

        try:
            data = tomllib.loads(content)
        except tomllib.TOMLDecodeError as e:
            return {"error": f"Invalid TOML: {e}"}

        result = {
            "file_metadata": self.get_file_metadata(file_path),
            "format": "pyproject",
        }

        # Parse standard project metadata (PEP 621)
        if "project" in data:
            result["project"] = self._parse_project_metadata(data["project"])

        # Parse build system (PEP 517/518)
        if "build-system" in data:
            result["build_system"] = self._parse_build_system(data["build-system"])

        # Parse tool configurations
        if "tool" in data:
            result["tool"] = self._parse_tools(data["tool"])

        return result

    def _parse_project_metadata(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Parse PEP 621 project metadata."""
        metadata = {}

        # Basic metadata
        for key in ["name", "version", "description", "readme", "license"]:
            if key in project:
                metadata[key] = project[key]

        # Python version requirement
        if "requires-python" in project:
            metadata["requires_python"] = project["requires-python"]

        # Authors and maintainers
        for key in ["authors", "maintainers"]:
            if key in project:
                metadata[key] = self._parse_people(project[key])

        # URLs
        if "urls" in project:
            metadata["urls"] = project["urls"]

        # Keywords and classifiers
        for key in ["keywords", "classifiers"]:
            if key in project:
                metadata[key] = project[key]

        # Dependencies
        if "dependencies" in project:
            metadata["dependencies"] = self._parse_dependencies(project["dependencies"])

        # Optional dependencies
        if "optional-dependencies" in project:
            metadata["optional_dependencies"] = {}
            for group, deps in project["optional-dependencies"].items():
                metadata["optional_dependencies"][group] = self._parse_dependencies(
                    deps
                )

        # Entry points
        if "scripts" in project:
            metadata["scripts"] = project["scripts"]

        if "gui-scripts" in project:
            metadata["gui_scripts"] = project["gui-scripts"]

        if "entry-points" in project:
            metadata["entry_points"] = project["entry-points"]

        return metadata

    def _parse_build_system(self, build_system: Dict[str, Any]) -> Dict[str, Any]:
        """Parse PEP 517/518 build system configuration."""
        result = {}

        if "requires" in build_system:
            result["requires"] = self._parse_dependencies(build_system["requires"])

        if "build-backend" in build_system:
            result["backend"] = build_system["build-backend"]

        if "backend-path" in build_system:
            result["backend_path"] = build_system["backend-path"]

        return result

    def _parse_tools(self, tools: Dict[str, Any]) -> Dict[str, Any]:
        """Parse tool-specific configurations."""
        result = {}

        # Poetry configuration
        if "poetry" in tools:
            result["poetry"] = self._parse_poetry(tools["poetry"])

        # UV configuration
        if "uv" in tools:
            result["uv"] = self._parse_uv(tools["uv"])

        # Black configuration
        if "black" in tools:
            result["black"] = tools["black"]

        # Isort configuration
        if "isort" in tools:
            result["isort"] = tools["isort"]

        # Pytest configuration
        if "pytest" in tools:
            result["pytest"] = tools["pytest"]

        # Mypy configuration
        if "mypy" in tools:
            result["mypy"] = tools["mypy"]

        # Ruff configuration
        if "ruff" in tools:
            result["ruff"] = tools["ruff"]

        # Coverage configuration
        if "coverage" in tools:
            result["coverage"] = tools["coverage"]

        # Other tools (preserve as-is)
        for tool, config in tools.items():
            if tool not in result:
                result[tool] = config

        return result

    def _parse_poetry(self, poetry: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Poetry-specific configuration."""
        result = {}

        # Basic metadata
        for key in [
            "name",
            "version",
            "description",
            "license",
            "readme",
            "homepage",
            "repository",
            "documentation",
            "keywords",
        ]:
            if key in poetry:
                result[key] = poetry[key]

        # Authors and maintainers
        for key in ["authors", "maintainers"]:
            if key in poetry:
                result[key] = poetry[key]

        # Dependencies
        if "dependencies" in poetry:
            result["dependencies"] = self._parse_poetry_dependencies(
                poetry["dependencies"]
            )

        # Dev dependencies (old style)
        if "dev-dependencies" in poetry:
            result["dev_dependencies"] = self._parse_poetry_dependencies(
                poetry["dev-dependencies"]
            )

        # Group dependencies (new style)
        if "group" in poetry:
            result["groups"] = {}
            for group_name, group_config in poetry["group"].items():
                if "dependencies" in group_config:
                    result["groups"][group_name] = self._parse_poetry_dependencies(
                        group_config["dependencies"]
                    )

        # Extras
        if "extras" in poetry:
            result["extras"] = poetry["extras"]

        # Scripts
        if "scripts" in poetry:
            result["scripts"] = poetry["scripts"]

        # Plugins
        if "plugins" in poetry:
            result["plugins"] = poetry["plugins"]

        return result

    def _parse_uv(self, uv: Dict[str, Any]) -> Dict[str, Any]:
        """Parse UV-specific configuration."""
        result = {}

        # Dev dependencies
        if "dev-dependencies" in uv:
            result["dev-dependencies"] = self._parse_dependencies(
                uv["dev-dependencies"]
            )

        # Sources (custom package sources)
        if "sources" in uv:
            result["sources"] = uv["sources"]

        # Other UV settings
        for key in ["index-strategy", "resolution", "prerelease", "exclude-newer"]:
            if key in uv:
                result[key] = uv[key]

        return result

    def _parse_dependencies(self, deps: List[str]) -> List[Dict[str, Any]]:
        """Parse a list of dependency specifications."""
        parsed = []

        for dep in deps:
            parsed_dep = self._parse_dependency_spec(dep)
            if parsed_dep:
                parsed.append(parsed_dep)

        return parsed

    def _parse_poetry_dependencies(self, deps: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Poetry-style dependencies."""
        parsed = []

        for name, spec in deps.items():
            if name == "python":
                continue  # Skip Python version constraint

            dep = {"name": name}

            if isinstance(spec, str):
                # Simple version string
                dep["version"] = spec
            elif isinstance(spec, dict):
                # Complex specification
                if "version" in spec:
                    dep["version"] = spec["version"]
                if "git" in spec:
                    dep["git"] = spec["git"]
                    if "branch" in spec:
                        dep["branch"] = spec["branch"]
                    if "tag" in spec:
                        dep["tag"] = spec["tag"]
                    if "rev" in spec:
                        dep["rev"] = spec["rev"]
                if "path" in spec:
                    dep["path"] = spec["path"]
                if "url" in spec:
                    dep["url"] = spec["url"]
                if "optional" in spec:
                    dep["optional"] = spec["optional"]
                if "extras" in spec:
                    dep["extras"] = spec["extras"]
                if "markers" in spec:
                    dep["markers"] = spec["markers"]

            parsed.append(dep)

        return parsed

    def _parse_dependency_spec(self, spec: str) -> Optional[Dict[str, Any]]:
        """Parse a single dependency specification string."""
        import re

        # Handle environment markers
        marker = None
        if ";" in spec:
            spec, marker = spec.split(";", 1)
            marker = marker.strip()

        # Parse package name and version
        match = re.match(
            r"^([A-Za-z0-9][\w.-]*)"  # Package name
            r"(?:\[([^\]]+)\])?"  # Optional extras
            r"(.*)$",  # Version specifier
            spec.strip(),
        )

        if not match:
            self.logger.warning(f"Could not parse dependency: {spec}")
            return None

        name, extras_str, version_spec = match.groups()

        dep = {"name": name}

        if extras_str:
            dep["extras"] = [e.strip() for e in extras_str.split(",")]

        if version_spec:
            dep["version"] = version_spec.strip()

        if marker:
            dep["marker"] = marker

        return dep

    def _parse_people(self, people: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Parse author/maintainer entries."""
        parsed = []

        for person in people:
            entry = {}
            if "name" in person:
                entry["name"] = person["name"]
            if "email" in person:
                entry["email"] = person["email"]
            parsed.append(entry)

        return parsed

    def read_file_safe(self, file_path: Path, encoding: str = "utf-8") -> Optional[str]:
        """Safely read file contents."""
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read {file_path}: {e}")
            return None

    def get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Get file metadata."""
        try:
            stat = file_path.stat()
            return {
                "name": file_path.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "absolute_path": str(file_path.absolute()),
            }
        except Exception as e:
            self.logger.error(f"Failed to get metadata for {file_path}: {e}")
            return {"name": file_path.name, "error": str(e)}

    def extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract just the dependency names for quick access."""
        result = self.parse_file(file_path)
        if "error" in result:
            return []

        deps = []

        # Standard project dependencies
        if "project" in result and "dependencies" in result["project"]:
            for dep in result["project"]["dependencies"]:
                if "name" in dep:
                    deps.append(dep["name"])

        # Poetry dependencies
        if "tool" in result and "poetry" in result["tool"]:
            poetry = result["tool"]["poetry"]
            if "dependencies" in poetry:
                for dep in poetry["dependencies"]:
                    if "name" in dep:
                        deps.append(dep["name"])

        # UV dependencies
        if "tool" in result and "uv" in result["tool"]:
            uv = result["tool"]["uv"]
            if "dev-dependencies" in uv:
                for dep in uv["dev-dependencies"]:
                    if "name" in dep:
                        deps.append(dep["name"])

        return list(set(deps))  # Remove duplicates
