#!/usr/bin/env python3
"""
act_command_builder.py - Command building for act execution

This module handles building act commands with various options and configurations.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Extracted from act_integration.py to reduce file size
# - Contains command building functionality for act
#

from __future__ import annotations

from pathlib import Path

from DHT.modules.act_integration_models import ActConfig


class ActCommandBuilder:
    """Builds act commands with appropriate options."""

    def __init__(self, project_path: Path, config: ActConfig):
        """Initialize command builder.

        Args:
            project_path: Path to project root
            config: Act configuration
        """
        self.project_path = Path(project_path).resolve()
        self.config = config
        self.act_config_path = self.project_path / ".venv" / "dht-act"

    def get_act_command(
        self,
        event: str = "push",
        job: str | None = None,
        use_container: bool = False,
        preferred_method: str | None = None
    ) -> list[str]:
        """Get act command with appropriate options.

        Args:
            event: GitHub event to simulate
            job: Specific job to run
            use_container: Use containerized act
            preferred_method: Preferred act method (gh-extension/standalone)

        Returns:
            List of command arguments
        """
        cmd = []

        if use_container:
            # Container commands are handled by container manager
            raise NotImplementedError("Use ActContainerManager for container execution")

        # Determine act command
        if preferred_method == "gh-extension" or self.config.use_gh_extension:
            cmd.extend(["gh", "act"])
        else:
            cmd.append("act")

        # Add event
        cmd.append(event)

        # Add job if specified
        if job:
            cmd.extend(["-j", job])

        # Platform configuration
        cmd.extend(["-P", f"{self.config.platform}={self.config.runner_image}"])

        # Container configuration
        cmd.extend(["--container-architecture", "linux/amd64"])

        # Use config file if it exists
        config_file = self.act_config_path / "act.json"
        if config_file.exists():
            cmd.extend(["--actor", "dht-runner"])
            cmd.extend(["--env-file", str(self.act_config_path / "env")])

            secrets_file = self.act_config_path / "secrets"
            if secrets_file.exists() and secrets_file.stat().st_size > 50:
                cmd.extend(["--secret-file", str(secrets_file)])

        # Bind workdir for better compatibility
        if self.config.bind_workdir:
            cmd.append("--bind")

        # Reuse containers for efficiency
        if self.config.reuse_containers:
            cmd.append("--reuse")

        # Artifact server
        if self.config.artifact_server_path:
            cmd.extend(["--artifact-server-path", self.config.artifact_server_path])

        # Cache server
        if self.config.cache_server_path:
            cmd.extend(["--cache-server-path", self.config.cache_server_path])

        return cmd

    def get_list_command(self, event: str = "push") -> list[str]:
        """Get command to list available jobs.

        Args:
            event: GitHub event to list jobs for

        Returns:
            List of command arguments
        """
        cmd = self.get_act_command(event, preferred_method=None)
        cmd.append("-l")
        return cmd

    def get_graph_command(self, event: str = "push") -> list[str]:
        """Get command to show workflow graph.

        Args:
            event: GitHub event to graph

        Returns:
            List of command arguments
        """
        cmd = self.get_act_command(event, preferred_method=None)
        cmd.append("-g")
        return cmd

    def get_dry_run_command(
        self,
        event: str = "push",
        job: str | None = None
    ) -> list[str]:
        """Get command for dry run.

        Args:
            event: GitHub event to simulate
            job: Specific job to run

        Returns:
            List of command arguments
        """
        cmd = self.get_act_command(event, job, preferred_method=None)
        cmd.append("-n")
        return cmd
