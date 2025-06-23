#!/usr/bin/env python3
from __future__ import annotations

"""
lock_file_manager.py - Lock file generation and management  This module handles the creation, parsing, and management of lock files for deterministic dependency resolution.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

"""
lock_file_manager.py - Lock file generation and management

This module handles the creation, parsing, and management of lock files
for deterministic dependency resolution.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from environment_reproducer.py to reduce file size
# - Contains lock file generation and parsing utilities
#


import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from prefect import get_run_logger, task

from DHT.modules.uv_prefect_tasks import generate_lock_file


@dataclass
class LockFileInfo:
    """Information about a lock file."""

    filename: str
    content: str
    checksum: str
    package_count: int
    created_at: str


class LockFileManager:
    """Manages lock files for reproducible environments."""

    def __init__(self) -> None:
        """Initialize the lock file manager."""
        self.supported_formats = {
            "uv.lock": self._parse_uv_lock,
            "requirements.txt": self._parse_requirements_txt,
            "package-lock.json": self._parse_package_lock_json,
            "yarn.lock": self._parse_yarn_lock,
            "Pipfile.lock": self._parse_pipfile_lock,
            "poetry.lock": self._parse_poetry_lock,
        }

    @task(name="generate_project_lock_files")  # type: ignore[misc]
    def generate_project_lock_files(self, project_path: Path, project_type: str) -> dict[str, LockFileInfo]:
        """Generate lock files for a project."""
        logger = get_run_logger()
        lock_files = {}

        project_path = Path(project_path)

        # Python projects
        if project_type in ["python", "hybrid"]:
            # Generate UV lock file
            if (project_path / "pyproject.toml").exists():
                logger.info("Generating UV lock file...")
                try:
                    lock_result = generate_lock_file(project_path)
                    if lock_result["success"]:
                        lock_content = (project_path / "uv.lock").read_text()
                        lock_files["uv.lock"] = self._create_lock_info("uv.lock", lock_content)
                except Exception as e:
                    logger.warning(f"Failed to generate UV lock file: {e}")

            # Generate requirements.txt if pip is used
            if (project_path / "requirements.txt").exists():
                lock_content = (project_path / "requirements.txt").read_text()
                lock_files["requirements.txt"] = self._create_lock_info("requirements.txt", lock_content)

        # Node.js projects
        if project_type in ["nodejs", "hybrid"]:
            if (project_path / "package.json").exists():
                # Check for existing lock files
                for lock_file in ["package-lock.json", "yarn.lock", "pnpm-lock.yaml"]:
                    lock_path = project_path / lock_file
                    if lock_path.exists():
                        lock_content = lock_path.read_text()
                        lock_files[lock_file] = self._create_lock_info(lock_file, lock_content)
                        break

        logger.info(f"Generated {len(lock_files)} lock files")
        return lock_files

    def _create_lock_info(self, filename: str, content: str) -> LockFileInfo:
        """Create lock file information."""
        checksum = hashlib.sha256(content.encode()).hexdigest()

        # Count packages
        package_count = 0
        if filename == "requirements.txt":
            package_count = len([line for line in content.splitlines() if line.strip() and not line.startswith("#")])
        elif filename == "uv.lock":
            # UV lock files have a specific structure
            package_count = content.count("[[package]]")
        elif filename == "package-lock.json":
            try:
                data = json.loads(content)
                package_count = len(data.get("dependencies", {}))
            except (json.JSONDecodeError, TypeError) as e:
                # Invalid JSON or unexpected structure - log but continue
                print(f"Warning: Could not parse package-lock.json: {e}")

        return LockFileInfo(
            filename=filename,
            content=content,
            checksum=checksum,
            package_count=package_count,
            created_at=datetime.now().isoformat(),
        )

    @task(name="verify_lock_files")  # type: ignore[misc]
    def verify_lock_files(self, project_path: Path, expected_lock_files: dict[str, LockFileInfo]) -> dict[str, bool]:
        """Verify lock files match expected checksums."""
        logger = get_run_logger()
        verification_results = {}

        for filename, expected_info in expected_lock_files.items():
            lock_path = project_path / filename

            if not lock_path.exists():
                logger.warning(f"Lock file {filename} not found")
                verification_results[filename] = False
                continue

            actual_content = lock_path.read_text()
            actual_checksum = hashlib.sha256(actual_content.encode()).hexdigest()

            if actual_checksum == expected_info.checksum:
                verification_results[filename] = True
                logger.info(f"Lock file {filename} verified successfully")
            else:
                verification_results[filename] = False
                logger.warning(
                    f"Lock file {filename} checksum mismatch: "
                    f"expected {expected_info.checksum[:8]}..., "
                    f"got {actual_checksum[:8]}..."
                )

        return verification_results

    def _parse_uv_lock(self, content: str) -> dict[str, str]:
        """Parse UV lock file to extract package versions."""
        packages = {}

        # UV lock files use TOML format
        lines = content.splitlines()
        current_package = None

        for line in lines:
            line = line.strip()
            if line == "[[package]]":
                current_package = {}
            elif line.startswith("name = ") and current_package is not None:
                name = line.split('"')[1]
                current_package["name"] = name
            elif line.startswith("version = ") and current_package is not None:
                version = line.split('"')[1]
                if "name" in current_package:
                    packages[current_package["name"]] = version

        return packages

    def _parse_requirements_txt(self, content: str) -> dict[str, str]:
        """Parse requirements.txt to extract package versions."""
        packages = {}

        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                # Handle different formats: package==version, package>=version, etc.
                for separator in ["==", ">=", "<=", "~=", ">"]:
                    if separator in line:
                        parts = line.split(separator)
                        if len(parts) >= 2:
                            package = parts[0].strip()
                            version = parts[1].strip().split(";")[0].strip()
                            packages[package] = f"{separator}{version}"
                            break
                else:
                    # No version specified
                    packages[line] = "*"

        return packages

    def _parse_package_lock_json(self, content: str) -> dict[str, str]:
        """Parse package-lock.json to extract package versions."""
        try:
            data = json.loads(content)
            packages = {}

            for name, info in data.get("dependencies", {}).items():
                if isinstance(info, dict) and "version" in info:
                    packages[name] = info["version"]

            return packages
        except Exception:
            return {}

    def _parse_yarn_lock(self, content: str) -> dict[str, str]:
        """Parse yarn.lock to extract package versions."""
        packages = {}

        # Simplified yarn.lock parsing
        lines = content.splitlines()
        current_package = None

        for line in lines:
            if line and not line.startswith(" "):
                # Package declaration line
                if "@" in line and ":" in line:
                    # Extract package name
                    parts = line.split("@")
                    if len(parts) >= 2:
                        current_package = parts[0].strip('"')
            elif line.strip().startswith("version ") and current_package:
                # Version line
                version = line.strip().split('"')[1]
                packages[current_package] = version
                current_package = None

        return packages

    def _parse_pipfile_lock(self, content: str) -> dict[str, str]:
        """Parse Pipfile.lock to extract package versions."""
        try:
            data = json.loads(content)
            packages = {}

            # Combine default and develop dependencies
            for section in ["default", "develop"]:
                for name, info in data.get(section, {}).items():
                    if isinstance(info, dict) and "version" in info:
                        packages[name] = info["version"]

            return packages
        except Exception:
            return {}

    def _parse_poetry_lock(self, content: str) -> dict[str, str]:
        """Parse poetry.lock to extract package versions."""
        packages = {}

        # Poetry lock files use TOML format
        lines = content.splitlines()
        current_package = None

        for line in lines:
            line = line.strip()
            if line == "[[package]]":
                current_package = {}
            elif line.startswith("name = ") and current_package is not None:
                name = line.split('"')[1]
                current_package["name"] = name
            elif line.startswith("version = ") and current_package is not None:
                version = line.split('"')[1]
                if "name" in current_package:
                    packages[current_package["name"]] = version

        return packages


# Export public API
__all__ = ["LockFileManager", "LockFileInfo"]
