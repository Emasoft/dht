#!/usr/bin/env python3
"""
requirements_parser.py - Parser for Python requirements files  Handles parsing of: - requirements.txt - requirements.in (pip-tools) - constraints.txt - Various pip options and formats

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
requirements_parser.py - Parser for Python requirements files

Handles parsing of:
- requirements.txt
- requirements.in (pip-tools)
- constraints.txt
- Various pip options and formats
"""

import logging
import re
from pathlib import Path
from typing import Any

from .base_parser import BaseParser


class RequirementsParser(BaseParser):
    """
    Parser for Python requirements files.

    Supports:
    - Version specifiers (==, >=, <=, <, >, ~=, !=)
    - Extras (package[extra1,extra2])
    - Environment markers (package; python_version >= "3.6")
    - Comments and blank lines
    - Include files (-r, --requirement)
    - Index URLs (--index-url, --extra-index-url)
    - Editable installs (-e, --editable)
    - Direct URLs (git+https://, https://, file://)
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_file(self, file_path: Path) -> dict[str, Any]:
        """
        Parse a requirements file and extract all information.

        Args:
            file_path: Path to requirements file

        Returns:
            Dictionary containing parsed information
        """
        content = self.read_file_safe(file_path)
        if content is None:
            return {"error": f"Could not read file {file_path}"}

        result = {
            "file_metadata": self.get_file_metadata(file_path),
            "dependencies": [],
            "comments": [],
            "options": {
                "index_url": None,
                "extra_index_urls": [],
                "find_links": [],
                "trusted_hosts": [],
                "includes": [],
                "constraints": [],
            },
            "format": "requirements",
        }

        lines = content.splitlines()
        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Handle comments
            if line.startswith("#"):
                result["comments"].append({"text": line[1:].strip(), "line": line_num})
                continue

            # Handle options
            if self._parse_option_line(line, result["options"], line_num):
                continue

            # Parse dependency line
            dep = self._parse_dependency_line(line, line_num)
            if dep:
                result["dependencies"].append(dep)

        return result

    def _parse_option_line(self, line: str, options: dict[str, Any], line_num: int) -> bool:
        """
        Parse pip option lines.

        Returns True if line was an option, False otherwise.
        """
        # Index URLs
        if line.startswith("--index-url") or line.startswith("-i"):
            parts = line.split(None, 1)
            if len(parts) > 1:
                options["index_url"] = parts[1]
            return True

        # Extra index URLs
        if line.startswith("--extra-index-url"):
            parts = line.split(None, 1)
            if len(parts) > 1:
                options["extra_index_urls"].append(parts[1])
            return True

        # Find links
        if line.startswith("--find-links") or line.startswith("-f"):
            parts = line.split(None, 1)
            if len(parts) > 1:
                options["find_links"].append(parts[1])
            return True

        # Trusted hosts
        if line.startswith("--trusted-host"):
            parts = line.split(None, 1)
            if len(parts) > 1:
                options["trusted_hosts"].append(parts[1])
            return True

        # Include files
        if line.startswith("-r") or line.startswith("--requirement"):
            parts = line.split(None, 1)
            if len(parts) > 1:
                options["includes"].append({"path": parts[1], "line": line_num})
            return True

        # Constraint files
        if line.startswith("-c") or line.startswith("--constraint"):
            parts = line.split(None, 1)
            if len(parts) > 1:
                options["constraints"].append({"path": parts[1], "line": line_num})
            return True

        return False

    def _parse_dependency_line(self, line: str, line_num: int) -> dict[str, Any] | None:
        """Parse a dependency specification line."""
        # Handle editable installs
        editable = False
        if line.startswith("-e") or line.startswith("--editable"):
            editable = True
            line = line.split(None, 1)[1] if " " in line else line[2:].strip()

        # Handle direct URLs (git, https, file)
        if self._is_url(line):
            return self._parse_url_dependency(line, line_num, editable)

        # Handle local paths
        if line.startswith("./") or line.startswith("../") or line.startswith("/"):
            return {
                "path": line,
                "editable": editable,
                "line": line_num,
                "type": "path",
            }

        # Parse regular package dependency
        return self._parse_package_dependency(line, line_num)

    def _is_url(self, line: str) -> bool:
        """Check if line is a URL."""
        url_prefixes = (
            "git+",
            "hg+",
            "svn+",
            "bzr+",
            "http://",
            "https://",
            "file://",
            "ftp://",
        )
        return any(line.startswith(prefix) for prefix in url_prefixes)

    def _parse_url_dependency(self, line: str, line_num: int, editable: bool) -> dict[str, Any]:
        """Parse URL-based dependency."""
        dep = {"line": line_num, "type": "url", "editable": editable}

        # Extract egg name if present
        egg_match = re.search(r"#egg=([^&\s]+)", line)
        if egg_match:
            dep["name"] = egg_match.group(1)

        # Extract VCS type
        vcs_match = re.match(r"^(git|hg|svn|bzr)\+", line)
        if vcs_match:
            dep["vcs"] = vcs_match.group(1)

        # Clean URL (remove egg parameter)
        url = re.sub(r"#egg=[^&\s]+", "", line).strip()
        dep["url"] = url

        # Extract subdirectory if present
        subdir_match = re.search(r"&subdirectory=([^&\s]+)", line)
        if subdir_match:
            dep["subdirectory"] = subdir_match.group(1)

        return dep

    def _parse_package_dependency(self, line: str, line_num: int) -> dict[str, Any]:
        """Parse a regular package dependency line."""
        # Handle environment markers (e.g., ; python_version >= "3.6")
        marker = None
        if ";" in line:
            line, marker = line.split(";", 1)
            marker = marker.strip()

        # Parse package name and version
        # Match: name[extras]version_spec
        match = re.match(
            r"^([A-Za-z0-9][\w.-]*)"  # Package name
            r"(?:\[([^\]]+)\])?"  # Optional extras
            r"(.*)$",  # Version specifier
            line.strip(),
        )

        if not match:
            self.logger.warning(f"Could not parse dependency: {line}")
            return None

        name, extras_str, version_spec = match.groups()

        dep = {"name": name, "line": line_num, "type": "package"}

        # Parse extras
        if extras_str:
            dep["extras"] = [e.strip() for e in extras_str.split(",")]

        # Parse version specifier
        version_spec = version_spec.strip()
        if version_spec:
            dep["version"] = version_spec
        else:
            dep["version"] = None

        # Add environment marker if present
        if marker:
            dep["marker"] = marker

        # Infer version type
        if version_spec:
            dep["version_type"] = self._infer_version_type(version_spec)

        return dep

    def _infer_version_type(self, version_spec: str) -> str:
        """Infer the type of version specification."""
        if version_spec.startswith("=="):
            return "exact"
        elif version_spec.startswith("~="):
            return "compatible"
        elif version_spec.startswith(">="):
            return "minimum"
        elif any(version_spec.startswith(op) for op in [">", "<", "<=", "!="]):
            return "range"
        elif "," in version_spec:
            return "complex"
        else:
            return "unknown"

    def read_file_safe(self, file_path: Path, encoding: str = "utf-8") -> str | None:
        """Safely read file contents."""
        try:
            with open(file_path, encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, encoding="latin-1") as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"Failed to read {file_path}: {e}")
                return None
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
        for dep in result.get("dependencies", []):
            if "name" in dep:
                deps.append(dep["name"])

        return deps
