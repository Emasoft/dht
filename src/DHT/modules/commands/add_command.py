#!/usr/bin/env python3
"""
Add command for DHT.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create add command module for adding dependencies
# - Wraps uv add functionality
# - Integrates with Prefect runner
#

"""
Add command for DHT.

Provides a familiar interface for adding dependencies to a project,
wrapping the UV package manager's add functionality.
"""

import logging
import subprocess
from typing import Any

from prefect import task

logger = logging.getLogger(__name__)


class AddCommand:
    """Add command implementation."""

    def __init__(self):
        """Initialize add command."""
        self.logger = logging.getLogger(__name__)

    @task(
        name="add_command",
        description="Add dependencies to the project",
        tags=["dht", "add", "dependencies"],
        retries=1,
        retry_delay_seconds=5,
    )
    def execute(
        self,
        packages: list[str],
        dev: bool = False,
        optional: str | None = None,
        platform: str | None = None,
        python: str | None = None,
        editable: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute add command to add dependencies.

        Args:
            packages: List of packages to add
            dev: Add as development dependencies
            optional: Add to optional dependency group
            platform: Platform-specific dependency
            python: Python version constraint
            editable: Add as editable dependency
            **kwargs: Additional arguments

        Returns:
            Result dictionary
        """
        if not packages:
            return {"success": False, "error": "No packages specified to add"}

        self.logger.info(f"Adding packages: {', '.join(packages)}")

        # Build uv add command
        cmd = ["uv", "add"]

        # Add packages
        cmd.extend(packages)

        # Add flags
        if dev:
            cmd.append("--dev")

        if optional:
            cmd.extend(["--optional", optional])

        if platform:
            cmd.extend(["--platform", platform])

        if python:
            cmd.extend(["--python", python])

        if editable:
            cmd.append("--editable")

        try:
            # Execute uv add
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300,  # 5 minutes timeout
            )

            self.logger.info("Successfully added packages")

            return {
                "success": True,
                "message": f"Added {len(packages)} package(s)",
                "packages": packages,
                "output": result.stdout,
            }

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to add packages: {e.stderr}")
            return {"success": False, "error": f"Failed to add packages: {e.stderr}", "command": " ".join(cmd)}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out after 5 minutes"}
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": str(e)}


# Module-level function for command registry
def add_command(packages: list[str], **kwargs) -> dict[str, Any]:
    """Execute add command."""
    cmd = AddCommand()
    return cmd.execute(packages, **kwargs)
