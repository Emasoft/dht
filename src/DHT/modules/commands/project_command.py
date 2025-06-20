#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create project command module for root project operations
# - Handles running commands in root project only
# - Integrates with Prefect runner
#

"""
Project command for DHT.

Provides functionality to run commands in the root project only,
excluding workspace members.
"""

import logging
from typing import Any

from prefect import task

logger = logging.getLogger(__name__)


class ProjectCommand:
    """Project command implementation."""

    def __init__(self):
        """Initialize project command."""
        self.logger = logging.getLogger(__name__)

    @task(name="project_command", description="Run command in root project only", tags=["dht", "project"], retries=0)
    def execute(
        self, subcommand: str, script: str | None = None, args: list[str] | None = None, **kwargs
    ) -> dict[str, Any]:
        """
        Execute project command (root only).

        Args:
            subcommand: Subcommand to run (run, exec, etc.)
            script: Script name for 'run' subcommand
            args: Arguments for the command
            **kwargs: Additional arguments

        Returns:
            Result dictionary
        """
        # For project command, we just delegate to run command
        # but ensure we're in the root project directory

        if subcommand != "run":
            return {"success": False, "error": f"Project command only supports 'run' subcommand, got '{subcommand}'"}

        if not script:
            return {"success": False, "error": "Script name required for project run command"}

        # Import run command
        from ..dhtl_commands_standalone import run_command as run_cmd

        self.logger.info(f"Running script '{script}' in root project")

        # Prepare arguments for run command
        run_args = [script]
        if args:
            run_args.extend(args)

        # Execute via run command
        return run_cmd(run_args)


# Module-level function for command registry
def project_command(**kwargs) -> dict[str, Any]:
    """Execute project command."""
    cmd = ProjectCommand()
    return cmd.execute(**kwargs)
