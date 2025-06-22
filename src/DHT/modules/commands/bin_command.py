#!/usr/bin/env python3
"""
Bin command for DHT.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Create bin command module to show executable directory
# - Shows virtual environment bin/Scripts directory
# - Integrates with Prefect runner
#

"""
Bin command for DHT.

Prints the path to the executable files installation folder,
typically the virtual environment's bin or Scripts directory.
"""

import logging
import platform
from pathlib import Path
from typing import Any

from prefect import task

logger = logging.getLogger(__name__)


class BinCommand:
    """Bin command implementation."""

    def __init__(self):
        """Initialize bin command."""
        self.logger = logging.getLogger(__name__)

    @task(
        name="bin_command",
        description="Print executable files installation folder",
        tags=["dht", "bin", "executables"],
        retries=0,
    )
    def execute(self, **kwargs) -> dict[str, Any]:
        """
        Execute bin command to show executable directory.

        Args:
            **kwargs: Additional arguments (unused)

        Returns:
            Result dictionary
        """
        # Check for virtual environment
        venv_paths = [
            Path(".venv"),
            Path("venv"),
            Path("env"),
        ]

        venv_dir = None
        for path in venv_paths:
            if path.exists() and path.is_dir():
                venv_dir = path
                break

        if not venv_dir:
            # Check VIRTUAL_ENV environment variable
            import os

            venv_env = os.environ.get("VIRTUAL_ENV")
            if venv_env:
                venv_dir = Path(venv_env)

        if not venv_dir or not venv_dir.exists():
            return {"success": False, "error": "No virtual environment found. Run 'dhtl setup' first."}

        # Determine bin directory based on platform
        if platform.system() == "Windows":
            bin_dir = venv_dir / "Scripts"
        else:
            bin_dir = venv_dir / "bin"

        if not bin_dir.exists():
            return {"success": False, "error": f"Bin directory not found: {bin_dir}"}

        # Print the path
        print(str(bin_dir.resolve()))

        self.logger.info(f"Executable directory: {bin_dir}")

        return {
            "success": True,
            "message": "Executable directory found",
            "bin_dir": str(bin_dir.resolve()),
            "venv_dir": str(venv_dir.resolve()),
            "platform": platform.system(),
        }


# Module-level function for command registry
def bin_command(**kwargs) -> dict[str, Any]:
    """Execute bin command."""
    cmd = BinCommand()
    return cmd.execute(**kwargs)
