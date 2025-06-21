#!/usr/bin/env python3

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create install command module (alias for setup)
# - Follows one-command-per-module pattern
# - Integrates with Prefect runner
#

"""
Install command for DHT.

This is an alias for the setup command, providing familiar syntax
for users coming from other package managers.
"""

import logging
from typing import Any

from prefect import task

logger = logging.getLogger(__name__)


class InstallCommand:
    """Install command implementation."""

    def __init__(self):
        """Initialize install command."""
        self.logger = logging.getLogger(__name__)

    @task(
        name="install_command",
        description="Install project dependencies (alias for setup)",
        tags=["dht", "install", "setup"],
        retries=1,
        retry_delay_seconds=5,
    )
    def execute(
        self,
        path: str = ".",
        python: str | None = None,
        dev: bool = False,
        from_requirements: bool = False,
        all_packages: bool = False,
        compile_bytecode: bool = False,
        editable: bool = True,
        index_url: str | None = None,
        install_pre_commit: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute install command (delegates to setup).

        Args:
            path: Project path
            python: Python version to use
            dev: Install development dependencies
            from_requirements: Import from requirements.txt
            all_packages: Install all workspace packages
            compile_bytecode: Compile Python files to bytecode
            editable: Install in editable mode
            index_url: Custom package index URL
            install_pre_commit: Install pre-commit hooks
            **kwargs: Additional arguments

        Returns:
            Result dictionary
        """
        # Import setup command and UV manager to avoid circular imports
        from ..dhtl_commands_setup import SetupCommand
        from ..uv_manager import UVManager

        self.logger.info("Running install command (delegating to setup)")

        # Create setup command instance and UV manager
        setup_cmd = SetupCommand()
        uv_manager = UVManager()

        # Delegate to setup with same arguments
        return setup_cmd.setup(
            uv_manager=uv_manager,
            path=path,
            python=python,
            dev=dev,
            from_requirements=from_requirements,
            all_packages=all_packages,
            compile_bytecode=compile_bytecode,
            editable=editable,
            index_url=index_url,
            install_pre_commit=install_pre_commit,
        )


# Module-level function for command registry
def install_command(**kwargs) -> dict[str, Any]:
    """Execute install command."""
    cmd = InstallCommand()
    return cmd.execute(**kwargs)
