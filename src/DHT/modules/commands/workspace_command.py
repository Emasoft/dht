#!/usr/bin/env python3
"""
Workspace Command module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create workspace command module for single workspace member operations
# - Handles running commands in a specific workspace member
# - Integrates with Prefect runner
# - Refactored to use WorkspaceBase to reduce complexity
#

"""
Workspace command for DHT.

Provides functionality to run commands in a specific workspace member.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any

from prefect import task

from .workspace_base import WorkspaceBase

logger = logging.getLogger(__name__)


class WorkspaceCommand(WorkspaceBase):
    """Workspace command implementation."""

    @task(
        name="workspace_command",
        description="Run command in specific workspace member",
        tags=["dht", "workspace"],
        retries=0,
    )
    def execute(
        self, name: str, subcommand: str, script: str | None = None, args: list[str] | None = None, **kwargs
    ) -> dict[str, Any]:
        """
        Execute workspace command in specific member.

        Args:
            name: Name of the workspace member
            subcommand: Subcommand to run (run, exec, etc.)
            script: Script name for 'run' subcommand
            args: Arguments for the command
            **kwargs: Additional arguments

        Returns:
            Result dictionary
        """
        # Import workspaces command to reuse member detection
        from .workspaces_command import WorkspacesCommand

        ws_cmd = WorkspacesCommand()

        # Find workspace root
        project_path = Path.cwd()
        members = ws_cmd.detect_workspace_members(project_path)

        if not members:
            return {"success": False, "error": "Not in a UV workspace"}

        # Find the specified member
        target_member = None
        for member in members:
            if member.name == name or str(member).endswith(name):
                target_member = member
                break

        if not target_member:
            return {
                "success": False,
                "error": f"Workspace member '{name}' not found",
                "available_members": [m.name for m in members],
            }

        self.logger.info(f"Running in workspace member: {target_member}")

        # Execute command based on subcommand
        if subcommand == "run":
            return self._handle_run(target_member, name, script, args)
        elif subcommand == "exec":
            return self._handle_exec(target_member, name, script, args)
        elif subcommand in ["upgrade", "remove"]:
            return self._handle_package_operation(target_member, name, subcommand, script, args)
        else:
            return {
                "success": False,
                "error": f"Unknown subcommand: {subcommand}. Use 'run', 'exec', 'upgrade', or 'remove'",
            }

    def _handle_run(self, member: Path, name: str, script: str | None, args: list[str] | None) -> dict[str, Any]:
        """Handle 'run' subcommand for single member."""
        if not script:
            return {"success": False, "error": "Script name required for 'run' subcommand"}

        cmd = ["uv", "run", "--directory", str(member), script]
        if args:
            cmd.extend(args)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=self.DEFAULT_TIMEOUT)
            return {
                "success": result.returncode == 0,
                "message": f"Command executed in {name}",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "workspace_member": str(member),
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {self.DEFAULT_TIMEOUT} seconds",
                "workspace_member": str(member),
            }
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": str(e), "workspace_member": str(member)}

    def _handle_exec(self, member: Path, name: str, script: str | None, args: list[str] | None) -> dict[str, Any]:
        """Handle 'exec' subcommand for single member."""
        # Build command from script + args
        cmd_args: list[Any] = []
        if script:
            cmd_args.append(script)
        if args:
            cmd_args.extend(args)

        if not cmd_args:
            return {"success": False, "error": "Command required for 'exec' subcommand"}

        result = self.execute_shell_in_directory(member, cmd_args)
        return {
            "success": result["success"],
            "message": f"Command executed in {name}",
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "returncode": result.get("returncode", -1),
            "workspace_member": str(member),
            "error": result.get("error"),
        }

    def _handle_package_operation(
        self, member: Path, name: str, operation: str, script: str | None, args: list[str] | None
    ) -> dict[str, Any]:
        """Handle package operations for single member."""
        # Collect packages
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

        # Build command
        if operation == "upgrade":
            cmd = ["uv", "add", "--upgrade", "--directory", str(member)] + packages
        else:  # remove
            cmd = ["uv", "remove", "--directory", str(member)] + packages

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=self.DEFAULT_TIMEOUT)
            return {
                "success": result.returncode == 0,
                "message": f"Package {operation} completed in {name}",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "workspace_member": str(member),
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {self.DEFAULT_TIMEOUT} seconds",
                "workspace_member": str(member),
            }
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": str(e), "workspace_member": str(member)}


# Module-level function for command registry
def workspace_command(**kwargs) -> dict[str, Any]:
    """Execute workspace command."""
    cmd = WorkspaceCommand()
    return cmd.execute(**kwargs)
