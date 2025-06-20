#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create workspaces command module for UV workspace operations
# - Handles running commands across all workspace members
# - Integrates with Prefect runner
#

"""
Workspaces command for DHT.

Provides functionality to run commands across all workspace members,
leveraging UV's workspace support.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any

from prefect import task

try:
    import tomllib
except ImportError:
    import tomli as tomllib

logger = logging.getLogger(__name__)


class WorkspacesCommand:
    """Workspaces command implementation."""

    def __init__(self):
        """Initialize workspaces command."""
        self.logger = logging.getLogger(__name__)

    def detect_workspace_members(self, project_path: Path) -> list[Path]:
        """
        Detect workspace members from pyproject.toml.

        Args:
            project_path: Project root path

        Returns:
            List of paths to workspace members
        """
        pyproject_path = project_path / "pyproject.toml"
        if not pyproject_path.exists():
            return []

        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)

            workspace_config = data.get("tool", {}).get("uv", {}).get("workspace", {})
            if not workspace_config:
                return []

            members = workspace_config.get("members", [])
            exclude = workspace_config.get("exclude", [])

            # Resolve member paths
            member_paths = []
            for pattern in members:
                # Handle glob patterns
                if "*" in pattern:
                    for path in project_path.glob(pattern):
                        if path.is_dir() and (path / "pyproject.toml").exists():
                            # Check if excluded
                            excluded = False
                            for exc_pattern in exclude:
                                if path.match(exc_pattern):
                                    excluded = True
                                    break
                            if not excluded:
                                member_paths.append(path)
                else:
                    # Direct path
                    path = project_path / pattern
                    if path.exists() and (path / "pyproject.toml").exists():
                        member_paths.append(path)

            # Include root if it has pyproject.toml
            if (project_path / "pyproject.toml").exists():
                member_paths.insert(0, project_path)

            return member_paths

        except Exception as e:
            self.logger.error(f"Failed to parse workspace config: {e}")
            return []

    @task(
        name="workspaces_command",
        description="Run commands across workspace members",
        tags=["dht", "workspaces", "workspace"],
        retries=0,
    )
    def execute(
        self,
        subcommand: str,
        script: str | None = None,
        args: list[str] | None = None,
        only: list[str] | None = None,
        ignore: list[str] | None = None,
        only_fs: list[str] | None = None,
        ignore_fs: list[str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute workspaces command.

        Args:
            subcommand: Subcommand to run (run, exec, etc.)
            script: Script name for 'run' subcommand
            args: Arguments for the command
            only: Only run in packages matching these patterns
            ignore: Skip packages matching these patterns
            only_fs: Only run in packages with files matching these patterns
            ignore_fs: Skip packages with files matching these patterns
            **kwargs: Additional arguments

        Returns:
            Result dictionary
        """
        # Find workspace root
        project_path = Path.cwd()
        while project_path != project_path.parent:
            if (project_path / "pyproject.toml").exists():
                with open(project_path / "pyproject.toml", "rb") as f:
                    data = tomllib.load(f)
                if "tool" in data and "uv" in data["tool"] and "workspace" in data["tool"]["uv"]:
                    break
            project_path = project_path.parent
        else:
            return {"success": False, "error": "Not in a UV workspace. No workspace configuration found."}

        # Detect workspace members
        members = self.detect_workspace_members(project_path)
        if not members:
            return {"success": False, "error": "No workspace members found"}

        self.logger.info(f"Found {len(members)} workspace members")

        # Apply filters
        filtered_members = []
        for member in members:
            # Name filtering
            member_name = member.name

            if only:
                if not any(self._match_pattern(member_name, pattern) for pattern in only):
                    continue

            if ignore:
                if any(self._match_pattern(member_name, pattern) for pattern in ignore):
                    continue

            # File system filtering
            if only_fs:
                if not any(list(member.glob(pattern)) for pattern in only_fs):
                    continue

            if ignore_fs:
                if any(list(member.glob(pattern)) for pattern in ignore_fs):
                    continue

            filtered_members.append(member)

        if not filtered_members:
            return {"success": False, "error": "No workspace members match the filter criteria"}

        self.logger.info(f"Running in {len(filtered_members)} workspace members")

        # Execute command based on subcommand
        if subcommand == "run":
            return self._run_script(filtered_members, script, args)
        elif subcommand == "exec":
            return self._exec_command(filtered_members, args)
        else:
            return {"success": False, "error": f"Unknown subcommand: {subcommand}. Use 'run' or 'exec'"}

    def _match_pattern(self, name: str, pattern: str) -> bool:
        """Check if name matches glob pattern."""
        from fnmatch import fnmatch

        return fnmatch(name, pattern)

    def _run_script(self, members: list[Path], script: str | None, args: list[str] | None) -> dict[str, Any]:
        """Run a script in all workspace members."""
        if not script:
            return {"success": False, "error": "Script name required for 'run' subcommand"}

        results = {}
        all_success = True

        for member in members:
            self.logger.info(f"Running '{script}' in {member.name}")

            # Build command
            cmd = ["uv", "run", "--directory", str(member), script]
            if args:
                cmd.extend(args)

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=300)

                results[str(member)] = {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                }

                if result.returncode != 0:
                    all_success = False
                    self.logger.error(f"Script failed in {member.name}: {result.stderr}")

            except subprocess.TimeoutExpired:
                results[str(member)] = {"success": False, "error": "Command timed out"}
                all_success = False
            except Exception as e:
                results[str(member)] = {"success": False, "error": str(e)}
                all_success = False

        return {
            "success": all_success,
            "message": f"Ran script in {len(members)} workspace members",
            "results": results,
            "members_count": len(members),
            "failed_count": len([r for r in results.values() if not r.get("success", False)]),
        }

    def _exec_command(self, members: list[Path], args: list[str] | None) -> dict[str, Any]:
        """Execute shell command in all workspace members."""
        if not args:
            return {"success": False, "error": "Command required for 'exec' subcommand"}

        results = {}
        all_success = True

        for member in members:
            self.logger.info(f"Executing command in {member.name}")

            try:
                # Execute command in member directory
                result = subprocess.run(
                    args,
                    cwd=member,
                    capture_output=True,
                    text=True,
                    check=False,
                    shell=True if len(args) == 1 else False,
                    timeout=300,
                )

                results[str(member)] = {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                }

                if result.returncode != 0:
                    all_success = False
                    self.logger.error(f"Command failed in {member.name}")

            except subprocess.TimeoutExpired:
                results[str(member)] = {"success": False, "error": "Command timed out"}
                all_success = False
            except Exception as e:
                results[str(member)] = {"success": False, "error": str(e)}
                all_success = False

        return {
            "success": all_success,
            "message": f"Executed command in {len(members)} workspace members",
            "results": results,
            "members_count": len(members),
            "failed_count": len([r for r in results.values() if not r.get("success", False)]),
        }


# Module-level function for command registry
def workspaces_command(**kwargs) -> dict[str, Any]:
    """Execute workspaces command."""
    cmd = WorkspacesCommand()
    return cmd.execute(**kwargs)
