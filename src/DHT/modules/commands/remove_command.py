#!/usr/bin/env python3
"""
Remove command for DHT.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create remove command module for removing dependencies
# - Wraps uv remove functionality
# - Integrates with Prefect runner
#

"""
Remove command for DHT.

Provides a familiar interface for removing dependencies from a project,
wrapping the UV package manager's remove functionality.
"""

import logging
import subprocess
from typing import Any

from ..prefect_compat import task

logger = logging.getLogger(__name__)


class RemoveCommand:
    """Remove command implementation."""

    def __init__(self) -> None:
        """Initialize remove command."""
        self.logger = logging.getLogger(__name__)

    @task(
        name="remove_command",
        description="Remove dependencies from the project",
        tags=["dht", "remove", "dependencies"],
        retries=1,
        retry_delay_seconds=5,
    )
    def execute(self, packages: list[str], dev: bool = False, **kwargs: Any) -> dict[str, Any]:
        """
        Execute remove command to remove dependencies.

        Args:
            packages: List of packages to remove
            dev: Remove from development dependencies
            **kwargs: Additional arguments

        Returns:
            Result dictionary
        """
        if not packages:
            return {"success": False, "error": "No packages specified to remove"}

        self.logger.info(f"Removing packages: {', '.join(packages)}")

        # Build uv remove command
        cmd = ["uv", "remove"]

        # Add packages
        cmd.extend(packages)

        # Add flags
        if dev:
            cmd.append("--dev")

        try:
            # Execute uv remove
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300,  # 5 minutes timeout
            )

            self.logger.info("Successfully removed packages")

            return {
                "success": True,
                "message": f"Removed {len(packages)} package(s)",
                "packages": packages,
                "output": result.stdout,
            }

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to remove packages: {e.stderr}")
            return {"success": False, "error": f"Failed to remove packages: {e.stderr}", "command": " ".join(cmd)}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out after 5 minutes"}
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": str(e)}


# Module-level function for command registry
def remove_command(packages: list[str], **kwargs: Any) -> dict[str, Any]:
    """Execute remove command."""
    cmd = RemoveCommand()
    return cmd.execute.fn(cmd, packages, **kwargs)
