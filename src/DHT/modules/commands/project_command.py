#!/usr/bin/env python3
"""
Project Command module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create project command module for root project operations
# - Handles running commands in root project only
# - Integrates with Prefect runner
# - Updated to use WorkspaceBase for consistency
#

"""
Project command for DHT.

Provides functionality to run commands in the root project only,
excluding workspace members.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, cast

from prefect import task

from .workspace_base import WorkspaceBase

logger = logging.getLogger(__name__)


class ProjectCommand(WorkspaceBase):
    """Project command implementation."""

    @task(
        name="project_command",
        description="Run command in root project only",
        tags=["dht", "project"],
        retries=0,
    )  # type: ignore[misc]
    def execute(
        self, subcommand: str, script: str | None = None, args: list[str] | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Execute project command in root only.

        Args:
            subcommand: Subcommand to run (currently only 'run')
            script: Script name for 'run' subcommand
            args: Arguments for the command
            **kwargs: Additional arguments

        Returns:
            Result dictionary
        """
        # Find workspace root
        project_path = self.find_workspace_root()
        if not project_path:
            # Not in a workspace, use current directory
            project_path = Path.cwd()

        self.logger.info(f"Running in root project: {project_path}")

        # Currently only 'run' is supported for project command
        if subcommand == "run":
            return self._handle_run(project_path, script, args)
        else:
            return {
                "success": False,
                "error": f"Unknown subcommand: {subcommand}. Only 'run' is supported for project command",
            }

    def _handle_run(self, project_path: Path, script: str | None, args: list[str] | None) -> dict[str, Any]:
        """Handle 'run' subcommand for root project."""
        if not script:
            return {"success": False, "error": "Script name required for 'run' subcommand"}

        # Build command - run in project root
        cmd = ["uv", "run", "--directory", str(project_path), script]
        if args:
            cmd.extend(args)

        self.logger.info(f"Running '{script}' in root project")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.DEFAULT_TIMEOUT,
            )

            return {
                "success": result.returncode == 0,
                "message": f"Script '{script}' executed in root project",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "project_path": str(project_path),
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Script timed out after {self.DEFAULT_TIMEOUT} seconds",
                "project_path": str(project_path),
            }
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "error": str(e),
                "project_path": str(project_path),
            }


# Module-level function for command registry
def project_command(**kwargs: Any) -> dict[str, Any]:
    """Execute project command."""
    cmd = ProjectCommand()
    return cast(dict[str, Any], cmd.execute(**kwargs))
