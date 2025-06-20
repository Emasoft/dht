#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create workspace command module for single workspace member operations
# - Handles running commands in a specific workspace member
# - Integrates with Prefect runner
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

logger = logging.getLogger(__name__)


class WorkspaceCommand:
    """Workspace command implementation."""

    def __init__(self):
        """Initialize workspace command."""
        self.logger = logging.getLogger(__name__)

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
            if not script:
                return {"success": False, "error": "Script name required for 'run' subcommand"}

            # Build command
            cmd = ["uv", "run", "--directory", str(target_member), script]
            if args:
                cmd.extend(args)

        elif subcommand == "exec":
            if not args:
                return {"success": False, "error": "Command required for 'exec' subcommand"}
            cmd = args

        elif subcommand == "upgrade":
            # For upgrade, packages are in script + args
            packages = []
            if script:
                packages.append(script)
            if args:
                packages.extend(args)
            if not packages:
                return {"success": False, "error": "Package name(s) required for 'upgrade' subcommand"}

            cmd = ["uv", "add", "--upgrade", "--directory", str(target_member)]
            cmd.extend(packages)

        elif subcommand == "remove":
            # For remove, packages are in script + args
            packages = []
            if script:
                packages.append(script)
            if args:
                packages.extend(args)
            if not packages:
                return {"success": False, "error": "Package name(s) required for 'remove' subcommand"}

            cmd = ["uv", "remove", "--directory", str(target_member)]
            cmd.extend(packages)

        else:
            return {
                "success": False,
                "error": f"Unknown subcommand: {subcommand}. Use 'run', 'exec', 'upgrade', or 'remove'",
            }

        # Execute command
        try:
            if subcommand == "exec":
                # For exec, run in the member directory
                result = subprocess.run(
                    cmd,
                    cwd=target_member,
                    capture_output=True,
                    text=True,
                    check=False,
                    shell=True if len(cmd) == 1 else False,
                    timeout=300,
                )
            else:
                # For run, upgrade, remove - uv handles the directory
                result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=300)

            return {
                "success": result.returncode == 0,
                "message": f"Command executed in {name}",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "workspace_member": str(target_member),
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out after 5 minutes",
                "workspace_member": str(target_member),
            }
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": str(e), "workspace_member": str(target_member)}


# Module-level function for command registry
def workspace_command(**kwargs) -> dict[str, Any]:
    """Execute workspace command."""
    cmd = WorkspaceCommand()
    return cmd.execute(**kwargs)
