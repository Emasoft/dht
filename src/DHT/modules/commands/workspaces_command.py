#!/usr/bin/env python3
"""
Workspaces Command module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create workspaces command module for UV workspace operations
# - Handles running commands across all workspace members
# - Integrates with Prefect runner
# - Refactored to use WorkspaceBase to reduce complexity
#

"""
Workspaces command for DHT.

Provides functionality to run commands across all workspace members,
leveraging UV's workspace support.
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from ..prefect_compat import task
from .workspace_base import WorkspaceBase

logger = logging.getLogger(__name__)


class WorkspacesCommand(WorkspaceBase):
    """Workspaces command implementation."""

    def detect_workspace_members(self, project_path: Path) -> list[Path]:
        """
        Detect workspace members from pyproject.toml.

        Args:
            project_path: Project root path

        Returns:
            List of paths to workspace members
        """
        config = self.parse_workspace_config(project_path)
        if not config:
            return []
        return self.resolve_workspace_members(project_path, config)

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
        **kwargs: Any,
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
        project_path = self.find_workspace_root()
        if not project_path:
            return {"success": False, "error": "Not in a UV workspace. No workspace configuration found."}

        # Detect workspace members
        members = self.detect_workspace_members(project_path)
        if not members:
            return {"success": False, "error": "No workspace members found"}

        self.logger.info(f"Found {len(members)} workspace members")

        # Apply filters
        filtered_members = self.filter_members_by_patterns(
            members, only=only, ignore=ignore, only_fs=only_fs, ignore_fs=ignore_fs
        )

        if not filtered_members:
            return {"success": False, "error": "No workspace members match the filter criteria"}

        self.logger.info(f"Running in {len(filtered_members)} workspace members")

        # Route to appropriate handler
        handlers: dict[str, Callable[[], dict[str, Any]]] = {
            "run": lambda: self._handle_run(filtered_members, script, args),
            "exec": lambda: self._handle_exec(filtered_members, script, args),
            "upgrade": lambda: self._handle_package_operation(filtered_members, "upgrade", script, args),
            "remove": lambda: self._handle_package_operation(filtered_members, "remove", script, args),
        }

        handler = handlers.get(subcommand)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown subcommand: {subcommand}. Use 'run', 'exec', 'upgrade', or 'remove'",
            }

        return handler()

    def _handle_run(self, members: list[Path], script: str | None, args: list[str] | None) -> dict[str, Any]:
        """Handle 'run' subcommand."""
        if not script:
            return {"success": False, "error": "Script name required for 'run' subcommand"}

        def build_command(member: Path) -> list[str]:
            cmd = ["uv", "run", "--directory", str(member), script]
            if args:
                cmd.extend(args)
            return cmd

        return self.execute_in_members(members, f"Running '{script}'", build_command)

    def _handle_exec(self, members: list[Path], script: str | None, args: list[str] | None) -> dict[str, Any]:
        """Handle 'exec' subcommand."""
        # For exec, the command is in script + args
        cmd_args: list[Any] = []
        if script:
            cmd_args.append(script)
        if args:
            cmd_args.extend(args)

        if not cmd_args:
            return {"success": False, "error": "Command required for 'exec' subcommand"}

        results: dict[str, Any] = {}
        all_success = True
        total = len(members)

        for idx, member in enumerate(members, 1):
            self.logger.info(f"[{idx}/{total}] Executing command in {member.name}...")
            result = self.execute_shell_in_directory(member, cmd_args)
            results[str(member)] = result
            if not result["success"]:
                all_success = False

        failed_count = len([r for r in results.values() if not r.get("success", False)])
        return {
            "success": all_success,
            "message": f"Executed command: {total - failed_count}/{total} succeeded",
            "results": results,
            "members_count": total,
            "success_count": total - failed_count,
            "failed_count": failed_count,
        }

    def _handle_package_operation(
        self, members: list[Path], operation: str, script: str | None, args: list[str] | None
    ) -> dict[str, Any]:
        """Handle package operations (upgrade/remove)."""
        # Collect packages from script + args
        packages: list[Any] = []
        if script:
            packages.append(script)
        if args:
            packages.extend(args)

        if not packages:
            return {"success": False, "error": f"Package name(s) required for '{operation}' subcommand"}

        # Validate package names
        is_valid, errors = self.validate_package_names(packages)
        if not is_valid:
            return {"success": False, "error": "Invalid package names: " + "; ".join(errors)}

        # Build appropriate command
        if operation == "upgrade":

            def build_command(member: Path) -> list[str]:
                return ["uv", "add", "--upgrade", "--directory", str(member)] + packages

            operation_name = "Upgrading packages"
        else:  # remove

            def build_command(member: Path) -> list[str]:
                return ["uv", "remove", "--directory", str(member)] + packages

            operation_name = "Removing packages"

        return self.execute_in_members(members, operation_name, build_command)


# Module-level function for command registry
def workspaces_command(**kwargs: Any) -> dict[str, Any]:
    """Execute workspaces command."""
    cmd = WorkspacesCommand()
    return cast(dict[str, Any], cmd.execute(**kwargs))
