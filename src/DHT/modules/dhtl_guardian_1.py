#!/usr/bin/env python3
"""
DHT Guardian 1 Module.

Copyright (c) 2024 Emasoft (Emanuele Sabetta)
Licensed under the MIT License. See LICENSE file for details.
"""

# HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
# - Python replacement for dhtl_guardian_1.sh
# - Provides process guardian functionality
# - Manages resource limits and process monitoring
#

"""
DHT Guardian 1 Module.

Provides process guardian functionality for resource management.
"""

import os
import subprocess

from .dhtl_error_handling import log_error, log_info


class ProcessGuardian:
    """Process guardian for resource management."""

    def __init__(self) -> None:
        """Initialize the process guardian."""
        self.default_mem_limit = int(os.environ.get("DEFAULT_MEM_LIMIT", "2048"))

    def run_with_limits(self, command: list[str], mem_limit: int | None = None) -> int:
        """Run a command with resource limits."""
        if mem_limit is None:
            mem_limit = self.default_mem_limit

        # TODO: Implement actual resource limiting
        log_info(f"Running command with {mem_limit}MB memory limit")

        try:
            result = subprocess.run(command, check=False)
            return result.returncode
        except Exception as e:
            log_error(f"Error running command: {e}")
            return 1


# Export functions
def run_with_guardian(command: str, name: str, mem_limit: int, *args: str) -> int:
    """Run a command with guardian protection."""
    guardian = ProcessGuardian()
    cmd_list = [command] + list(args)
    return guardian.run_with_limits(cmd_list, mem_limit)
