#!/usr/bin/env python3
"""
Workspace Base module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extract common workspace functionality to reduce duplication
# - Add progress tracking and error aggregation
# - Use 30 minute timeout as per CLAUDE.md
# - Improve modularity and reduce complexity
#

"""
Base functionality for workspace commands.

Provides common utilities for workspace operations to reduce code duplication
and improve maintainability.
"""

import logging
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib


class WorkspaceBase:
    """Base class for workspace operations."""

    # Default timeout in seconds (30 minutes as per CLAUDE.md)
    DEFAULT_TIMEOUT = 1800  # 30 minutes

    def __init__(self):
        """Initialize workspace base."""
        self.logger = logging.getLogger(__name__)

    def find_workspace_root(self) -> Path | None:
        """
        Find the workspace root by looking for pyproject.toml with workspace config.

        Returns:
            Path to workspace root or None if not found
        """
        current = Path.cwd()
        while current != current.parent:
            pyproject_path = current / "pyproject.toml"
            if pyproject_path.exists():
                try:
                    with open(pyproject_path, "rb") as f:
                        data = tomllib.load(f)
                    if "tool" in data and "uv" in data["tool"] and "workspace" in data["tool"]["uv"]:
                        return current
                except Exception as e:
                    self.logger.debug(f"Error reading {pyproject_path}: {e}")
            current = current.parent
        return None

    def parse_workspace_config(self, project_path: Path) -> dict[str, Any]:
        """
        Parse workspace configuration from pyproject.toml.

        Args:
            project_path: Path to project root

        Returns:
            Workspace configuration dict
        """
        pyproject_path = project_path / "pyproject.toml"
        if not pyproject_path.exists():
            return {}

        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            return data.get("tool", {}).get("uv", {}).get("workspace", {})
        except Exception as e:
            self.logger.error(f"Failed to parse workspace config: {e}")
            return {}

    def resolve_workspace_members(self, project_path: Path, config: dict[str, Any]) -> list[Path]:
        """
        Resolve workspace member paths from configuration.

        Args:
            project_path: Project root path
            config: Workspace configuration

        Returns:
            List of resolved member paths
        """
        members = config.get("members", [])
        exclude = config.get("exclude", [])
        member_paths = []

        # Resolve each member pattern
        for pattern in members:
            if "*" in pattern:
                # Glob pattern
                for path in project_path.glob(pattern):
                    if path.is_dir() and (path / "pyproject.toml").exists():
                        if not self._is_excluded(path, exclude):
                            member_paths.append(path)
            else:
                # Direct path
                path = project_path / pattern
                if path.exists() and (path / "pyproject.toml").exists():
                    if not self._is_excluded(path, exclude):
                        member_paths.append(path)

        # Include root if it has pyproject.toml
        if (project_path / "pyproject.toml").exists():
            member_paths.insert(0, project_path)

        return member_paths

    def _is_excluded(self, path: Path, exclude_patterns: list[str]) -> bool:
        """Check if path matches any exclude pattern."""
        for pattern in exclude_patterns:
            if path.match(pattern):
                return True
        return False

    def execute_in_members(
        self,
        members: list[Path],
        operation_name: str,
        build_command_func: Callable[[Path], list[str]],
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """
        Execute a command in multiple workspace members.

        Args:
            members: List of workspace member paths
            operation_name: Name of the operation (for logging)
            build_command_func: Function that builds command for a member
            timeout: Command timeout in seconds

        Returns:
            Result dictionary with success status and details
        """
        if timeout is None:
            timeout = self.DEFAULT_TIMEOUT

        results = {}
        all_success = True
        total = len(members)

        for idx, member in enumerate(members, 1):
            # Progress indicator
            self.logger.info(f"[{idx}/{total}] {operation_name} in {member.name}...")

            try:
                cmd = build_command_func(member)
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=timeout,
                    # Never use shell=True for security
                    shell=False,
                )

                success = result.returncode == 0
                results[str(member)] = {
                    "success": success,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                }

                if not success:
                    all_success = False
                    self.logger.error(f"Failed in {member.name}: {result.stderr.strip()}")
                else:
                    self.logger.info(f"✓ Success in {member.name}")

            except subprocess.TimeoutExpired:
                results[str(member)] = {"success": False, "error": f"Timed out after {timeout} seconds"}
                all_success = False
                self.logger.error(f"Timeout in {member.name}")
            except Exception as e:
                results[str(member)] = {"success": False, "error": str(e)}
                all_success = False
                self.logger.error(f"Error in {member.name}: {e}")

        # Summary
        failed_count = len([r for r in results.values() if not r.get("success", False)])
        success_count = total - failed_count

        return {
            "success": all_success,
            "message": f"{operation_name} completed: {success_count}/{total} succeeded",
            "results": results,
            "members_count": total,
            "success_count": success_count,
            "failed_count": failed_count,
        }

    def execute_shell_in_directory(
        self, directory: Path, args: list[str], timeout: int | None = None
    ) -> dict[str, Any]:
        """
        Safely execute shell command in a directory.

        Args:
            directory: Directory to execute in
            args: Command arguments (will be properly escaped)
            timeout: Command timeout in seconds

        Returns:
            Execution result
        """
        if timeout is None:
            timeout = self.DEFAULT_TIMEOUT

        try:
            # For safety, never use shell=True
            # If user wants shell features, they should explicitly use sh -c
            result = subprocess.run(
                args,
                cwd=directory,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
                shell=False,
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {timeout} seconds"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def filter_members_by_patterns(
        self,
        members: list[Path],
        only: list[str] | None = None,
        ignore: list[str] | None = None,
        only_fs: list[str] | None = None,
        ignore_fs: list[str] | None = None,
    ) -> list[Path]:
        """
        Filter workspace members by name and filesystem patterns.

        Args:
            members: List of member paths
            only: Include only members matching these name patterns
            ignore: Exclude members matching these name patterns
            only_fs: Include only members with files matching these patterns
            ignore_fs: Exclude members with files matching these patterns

        Returns:
            Filtered list of members
        """

        filtered = []

        for member in members:
            # Check name patterns
            if not self._matches_name_patterns(member.name, only, ignore):
                continue

            # Check filesystem patterns
            if not self._matches_fs_patterns(member, only_fs, ignore_fs):
                continue

            filtered.append(member)

        return filtered

    def _matches_name_patterns(self, name: str, only: list[str] | None, ignore: list[str] | None) -> bool:
        """Check if name matches include/exclude patterns."""
        from fnmatch import fnmatch

        if only and not any(fnmatch(name, pattern) for pattern in only):
            return False
        if ignore and any(fnmatch(name, pattern) for pattern in ignore):
            return False
        return True

    def _matches_fs_patterns(self, path: Path, only_fs: list[str] | None, ignore_fs: list[str] | None) -> bool:
        """Check if path contains files matching filesystem patterns."""
        if only_fs and not self._has_matching_files(path, only_fs):
            return False
        if ignore_fs and self._has_matching_files(path, ignore_fs):
            return False
        return True

    def _has_matching_files(self, path: Path, patterns: list[str]) -> bool:
        """Check if path contains any files matching the given patterns."""
        return any(list(path.glob(pattern)) for pattern in patterns)

    def validate_package_names(self, packages: list[str]) -> tuple[bool, list[str]]:
        """
        Validate package names for safety.

        Args:
            packages: List of package names to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        for pkg in packages:
            # Basic validation - package names should be safe
            if not pkg:
                errors.append("Empty package name")
            elif ".." in pkg or "/" in pkg or "\\" in pkg:
                errors.append(f"Invalid package name: {pkg}")
            elif pkg.startswith("-"):
                errors.append(f"Package name cannot start with dash: {pkg}")

        return len(errors) == 0, errors
