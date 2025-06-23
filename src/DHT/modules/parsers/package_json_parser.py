#!/usr/bin/env python3
"""
package_json_parser.py - Parser for Node.js package.json files  Handles parsing of: - Standard npm/yarn package.json - Dependencies and devDependencies - Scripts and engines - Workspaces (monorepo support)

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
package_json_parser.py - Parser for Node.js package.json files

Handles parsing of:
- Standard npm/yarn package.json
- Dependencies and devDependencies
- Scripts and engines
- Workspaces (monorepo support)
"""

import json
import logging
from pathlib import Path
from typing import Any

from .base_parser import BaseParser


class PackageJsonParser(BaseParser):
    """
    Parser for package.json files.

    Extracts:
    - Package metadata (name, version, description)
    - Dependencies (regular, dev, peer, optional)
    - Scripts
    - Engines (Node/npm version requirements)
    - Workspaces configuration
    - Repository and author information
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def parse_file(self, file_path: Path) -> dict[str, Any]:
        """
        Parse a package.json file and extract all information.

        Args:
            file_path: Path to package.json

        Returns:
            Dictionary containing parsed information
        """
        content = self.read_file_safe(file_path)
        if content is None:
            return {"error": f"Could not read file {file_path}"}

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {e}"}

        result = {
            "file_metadata": self.get_file_metadata(file_path),
            "format": "package.json",
        }

        # Basic metadata
        for key in [
            "name",
            "version",
            "description",
            "license",
            "private",
            "homepage",
            "repository",
            "bugs",
        ]:
            if key in data:
                result[key] = data[key]

        # Author and contributors
        if "author" in data:
            result["author"] = self._parse_person(data["author"])

        if "contributors" in data:
            result["contributors"] = [self._parse_person(p) for p in data["contributors"]]

        # Main entry points
        for key in ["main", "module", "browser", "types", "typings", "exports"]:
            if key in data:
                result[key] = data[key]

        # Dependencies
        dependency_types = [
            ("dependencies", "dependencies"),
            ("devDependencies", "devDependencies"),
            ("peerDependencies", "peerDependencies"),
            ("optionalDependencies", "optionalDependencies"),
            ("bundledDependencies", "bundledDependencies"),
            ("bundleDependencies", "bundledDependencies"),  # Alternative spelling
        ]

        for json_key, result_key in dependency_types:
            if json_key in data:
                result[result_key] = self._parse_dependencies(data[json_key])

        # Scripts
        if "scripts" in data:
            result["scripts"] = data["scripts"]

        # Engines (Node/npm version requirements)
        if "engines" in data:
            result["engines"] = data["engines"]

        # Files to include in package
        if "files" in data:
            result["files"] = data["files"]

        # Workspaces (monorepo support)
        if "workspaces" in data:
            result["workspaces"] = self._parse_workspaces(data["workspaces"])

        # Keywords
        if "keywords" in data:
            result["keywords"] = data["keywords"]

        # Bin executables
        if "bin" in data:
            result["bin"] = data["bin"]

        # Config
        if "config" in data:
            result["config"] = data["config"]

        # Package manager specific
        for key in ["packageManager", "volta", "resolutions", "overrides"]:
            if key in data:
                result[key] = data[key]

        return result

    def _parse_person(self, person: Any) -> dict[str, str]:
        """Parse author/contributor information."""
        if isinstance(person, str):
            # Parse "Name <email> (url)" format
            import re

            match = re.match(r"^([^<\(]+?)(?:\s*<([^>]+)>)?(?:\s*\(([^\)]+)\))?$", person)
            if match:
                name, email, url = match.groups()
                result = {"name": name.strip()}
                if email:
                    result["email"] = email.strip()
                if url:
                    result["url"] = url.strip()
                return result
            return {"name": person}
        elif isinstance(person, dict):
            return person
        return {}

    def _parse_dependencies(self, deps: Any) -> list[dict[str, Any]]:
        """Parse dependencies section."""
        if not isinstance(deps, dict):
            return []

        parsed = []
        for name, version_spec in deps.items():
            dep = {
                "name": name,
                "version": version_spec,
                "type": self._infer_dependency_type(version_spec),
            }

            # Parse version range type
            if version_spec.startswith("^"):
                dep["version_type"] = "caret"
            elif version_spec.startswith("~"):
                dep["version_type"] = "tilde"
            elif version_spec.startswith(">=") or version_spec.startswith(">"):
                dep["version_type"] = "range"
            elif version_spec == "*" or version_spec == "latest":
                dep["version_type"] = "any"
            elif version_spec.startswith("file:"):
                dep["version_type"] = "file"
            elif version_spec.startswith("link:"):
                dep["version_type"] = "link"
            elif "://" in version_spec:
                dep["version_type"] = "url"
            elif version_spec.startswith("git"):
                dep["version_type"] = "git"
            elif "#" in version_spec:
                dep["version_type"] = "tag"
            else:
                dep["version_type"] = "exact"

            parsed.append(dep)

        return parsed

    def _infer_dependency_type(self, version_spec: str) -> str:
        """Infer the type of dependency from version specification."""
        if version_spec.startswith("file:"):
            return "local"
        elif version_spec.startswith("link:"):
            return "link"
        elif version_spec.startswith("git") or version_spec.startswith("github:"):
            return "git"
        elif "://" in version_spec:
            return "url"
        elif version_spec.startswith("npm:"):
            return "alias"
        elif version_spec.startswith("workspace:"):
            return "workspace"
        else:
            return "registry"

    def _parse_workspaces(self, workspaces: Any) -> list[str]:
        """Parse workspaces configuration."""
        if isinstance(workspaces, list):
            return workspaces
        elif isinstance(workspaces, dict) and "packages" in workspaces:
            return workspaces["packages"]
        return []

    def read_file_safe(self, file_path: Path, encoding: str = "utf-8") -> str | None:
        """Safely read file contents."""
        try:
            with open(file_path, encoding=encoding) as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read {file_path}: {e}")
            return None

    def get_file_metadata(self, file_path: Path) -> dict[str, Any]:
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

    def extract_dependencies(self, file_path: Path) -> list[str]:
        """Extract just the dependency names for quick access."""
        result = self.parse_file(file_path)
        if "error" in result:
            return []

        deps = []

        # Collect all dependency types
        for dep_type in [
            "dependencies",
            "devDependencies",
            "peerDependencies",
            "optionalDependencies",
        ]:
            if dep_type in result:
                for dep in result[dep_type]:
                    if "name" in dep:
                        deps.append(dep["name"])

        return list(set(deps))  # Remove duplicates
