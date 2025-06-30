#!/usr/bin/env python3
"""
Upgrade command for DHT.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create upgrade command module for upgrading dependencies
# - Wraps uv add --upgrade functionality
# - Integrates with Prefect runner
#

"""
Upgrade command for DHT.

Provides a familiar interface for upgrading dependencies in a project,
wrapping the UV package manager's upgrade functionality.
"""

import logging
import subprocess
from typing import Any, cast

from ..prefect_compat import task

logger = logging.getLogger(__name__)


class UpgradeCommand:
    """Upgrade command implementation."""

    def __init__(self) -> None:
        """Initialize upgrade command."""
        self.logger = logging.getLogger(__name__)

    @task(
        name="upgrade_command",
        description="Upgrade dependencies",
        tags=["dht", "upgrade", "dependencies"],
        retries=1,
        retry_delay_seconds=5,
    )
    def execute(
        self, packages: list[str] | None = None, all: bool = False, dev: bool = False, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Execute upgrade command to upgrade dependencies.

        Args:
            packages: List of specific packages to upgrade (None = all)
            all: Upgrade all packages
            dev: Include development dependencies
            **kwargs: Additional arguments

        Returns:
            Result dictionary
        """
        if packages:
            self.logger.info(f"Upgrading packages: {', '.join(packages)}")
            # Use uv add --upgrade for specific packages
            cmd = ["uv", "add", "--upgrade"]
            cmd.extend(packages)

            if dev:
                cmd.append("--dev")
        else:
            # Upgrade all packages using uv sync
            self.logger.info("Upgrading all packages")
            cmd = ["uv", "sync", "--upgrade"]

            if dev:
                cmd.append("--dev")

        try:
            # Execute uv command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=600,  # 10 minutes timeout for upgrades
            )

            if packages:
                message = f"Upgraded {len(packages)} package(s)"
            else:
                message = "Upgraded all packages"

            self.logger.info(message)

            return {"success": True, "message": message, "packages": packages, "output": result.stdout}

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to upgrade packages: {e.stderr}")
            return {"success": False, "error": f"Failed to upgrade packages: {e.stderr}", "command": " ".join(cmd)}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out after 10 minutes"}
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": str(e)}


# Module-level function for command registry
def upgrade_command(packages: list[str] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Execute upgrade command."""
    cmd = UpgradeCommand()
    return cast(dict[str, Any], cmd.execute.fn(cmd, packages, **kwargs))
